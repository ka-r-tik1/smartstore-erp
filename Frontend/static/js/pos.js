// SmartStore ERP — POS Connect (Phase D)
// Real API se product search + bill create

// ══════════════════════════════════════
//  D2: Product Search — Real API
// ══════════════════════════════════════

// Cache for searched products (avoid repeated API calls)
let productCache = {};

// Search products from backend API
async function posSearchProducts(query) {
  if (!query || query.length < 1) return [];
  try {
    const results = await apiCall('/api/products/?search=' + encodeURIComponent(query) + '&active_only=true&limit=10');
    // Cache results by barcode and id
    results.forEach(p => {
      if (p.barcode) productCache[p.barcode] = p;
      productCache['id_' + p.id] = p;
    });
    return results;
  } catch (err) {
    console.error('Product search error:', err);
    return [];
  }
}

// Override posOnInput — real-time search from API
const _origPosOnInput = window.posOnInput;
let _posSearchTimer = null;
let _posCurrentQuery = '';

window.posOnInput = function(val) {
  const status = document.getElementById('pos-scan-status');
  if (!status) return;

  val = val.trim();

  // In Marathi mode, search with English buffer (original typed text) — DB stores English names
  if (typeof currentLang !== 'undefined' && currentLang === 'mr') {
    const searchEl = document.getElementById('pos-barcode-input');
    if (searchEl && searchEl._mrBuf) val = searchEl._mrBuf.trim();
  }

  _posCurrentQuery = val;

  // Clear previous dropdown
  const existing = document.getElementById('pos-search-dropdown');
  if (existing) existing.remove();

  if (!val) { status.textContent = ''; return; }

  // First check cache — show status instantly but still show dropdown for batch selection
  if (productCache[val] || productCache[val.toUpperCase()]) {
    const prod = productCache[val] || productCache[val.toUpperCase()];
    status.textContent = '📦 ' + prod.name + ' — ₹' + toMrNum(prod.selling_price);
    status.style.color = 'var(--accent3)';
    showSearchDropdown([prod]);  // Show batch dropdown even for cached products
    return;
  }

  status.textContent = '🔍 Searching...';
  status.style.color = 'var(--muted)';

  // Debounce 250ms — cancel previous pending call
  clearTimeout(_posSearchTimer);
  _posSearchTimer = setTimeout(async function() {
    const query = _posCurrentQuery; // snapshot at this moment
    const results = await posSearchProducts(query);

    // Ignore if user has typed something else since
    if (_posCurrentQuery !== query) return;

    if (results.length > 0) {
      status.textContent = '📦 ' + results[0].name + ' — ₹' + toMrNum(results[0].selling_price) + ' (Stock: ' + toMrNum(results[0].stock_qty) + ')';
      status.style.color = 'var(--accent3)';
      showSearchDropdown(results);
    } else {
      status.textContent = '⚠ Not found — check spelling or add product';
      status.style.color = 'var(--warn)';
    }
  }, 250);
};

// Search dropdown for multiple results — batch-wise rows
async function showSearchDropdown(results) {
  let existing = document.getElementById('pos-search-dropdown');
  if (existing) existing.remove();

  const inp = document.getElementById('pos-barcode-input');
  if (!inp) return;

  const dropdown = document.createElement('div');
  dropdown.id = 'pos-search-dropdown';

  // Use fixed positioning so no parent overflow clips the dropdown
  const rect = inp.getBoundingClientRect();
  const maxH = Math.min(320, window.innerHeight - rect.bottom - 12);
  dropdown.style.cssText = 'position:fixed;top:' + (rect.bottom + 6) + 'px;left:' + rect.left + 'px;width:' + rect.width + 'px;background:rgba(15,23,42,0.95);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,0.15);border-radius:12px;box-shadow:0 12px 40px rgba(0,0,0,0.4);z-index:99999;max-height:' + maxH + 'px;overflow-y:auto;';

  document.body.appendChild(dropdown);

  // Fetch ALL batch data in parallel — much faster than sequential
  const batchResults = await Promise.all(results.map(prod =>
    apiCall('/api/inventory/selling-batches/' + prod.id)
      .then(d => d.batches || [])
      .catch(() => [])
  ));

  results.forEach((prod, pi) => {
    const _dispName = (typeof _translateProdName === 'function') ? _translateProdName(prod.name) : prod.name;
    const batches = batchResults[pi];

    if (batches.length <= 1) {
      // Single price — 1 row
      const price = (batches.length === 1) ? batches[0].selling_price : prod.selling_price;
      const qty   = (batches.length === 1) ? batches[0].qty : prod.stock_qty;
      const item = document.createElement('div');
      item.style.cssText = 'padding:12px 16px;cursor:pointer;border-bottom:1px solid rgba(255,255,255,0.08);display:flex;justify-content:space-between;align-items:center;transition:background 0.2s;';
      item.innerHTML = '<div><b style="font-size:13px;color:#f8fafc;">' + _dispName + '</b><br><span style="font-size:11px;color:rgba(255,255,255,0.5);">' + (prod.barcode || '') + ' · ' + toMrNum(qty) + ' units</span></div><div style="font-weight:700;color:#4ade80;">₹' + toMrNum(price) + '</div>';
      item.onmouseover = function() { this.style.background = 'rgba(255,255,255,0.1)'; };
      item.onmouseout = function() { this.style.background = 'transparent'; };
      const _prod = Object.assign({}, prod, { selling_price: price });
      item.onclick = function() {
        posAddProductFromAPI(_prod);
        dropdown.remove();
        inp.value = '';
        inp.focus();
      };
      dropdown.appendChild(item);
    } else {
      // Multiple batches — one row per batch-price (latest first from API)
      batches.forEach((b, idx) => {
        const item = document.createElement('div');
        item.style.cssText = 'padding:10px 16px;cursor:pointer;border-bottom:1px solid rgba(255,255,255,0.08);display:flex;justify-content:space-between;align-items:center;transition:background 0.2s;';
        const latestBadge = idx === 0 ? '<span style="font-size:9px;background:#4ade80;color:#14532d;border-radius:4px;padding:1px 5px;margin-left:6px;font-weight:700;">LATEST</span>' : '';
        item.innerHTML =
          '<div><b style="font-size:13px;color:#f8fafc;">' + _dispName + latestBadge + '</b><br>' +
          '<span style="font-size:11px;color:rgba(255,255,255,0.5);">' + (prod.barcode || '') + ' · ' + toMrNum(b.qty) + ' units</span></div>' +
          '<div style="font-weight:700;color:#4ade80;font-size:15px;">₹' + toMrNum(b.selling_price) + '</div>';
        item.onmouseover = function() { this.style.background = 'rgba(255,255,255,0.1)'; };
        item.onmouseout = function() { this.style.background = 'transparent'; };
        const _prod = Object.assign({}, prod, { selling_price: b.selling_price });
        item.onclick = function() {
          posAddProductFromAPI(_prod);
          dropdown.remove();
          inp.value = '';
          inp.focus();
        };
        dropdown.appendChild(item);
      });
    }
  });

  // Close on click outside
  setTimeout(() => {
    document.addEventListener('click', function closeDD(e) {
      if (!dropdown.contains(e.target) && e.target !== inp) {
        dropdown.remove();
        document.removeEventListener('click', closeDD);
      }
    });
  }, 100);
}

// Add product to cart from API data — batch-price tracking
function posAddProductFromAPI(prod) {
  const existing = posCart.find(i => i.product_id === prod.id);
  if (existing) {
    if (existing.qty >= prod.stock_qty) {
      toast('Stock limit! Only ' + toMrNum(prod.stock_qty) + ' available.', 'warn');
      return;
    }
    // Track this batch price separately — keeps display price unchanged
    const batchEntry = existing.batches.find(b => b.price === prod.selling_price);
    if (batchEntry) { batchEntry.qty++; }
    else { existing.batches.push({ price: prod.selling_price, qty: 1 }); }
    existing.qty++;
    // Keep display price as is (user wants ₹26 to stay)
  } else {
    if (prod.stock_qty <= 0) {
      toast(prod.name + ' out of stock!', 'warn');
      return;
    }
    posCart.push({
      product_id: prod.id,
      barcode: prod.barcode || '',
      name: prod.name,
      price: prod.selling_price,       // display price
      hsn: prod.hsn_code || '—',
      gst: prod.gst_rate || 0,
      qty: 1,
      stock: prod.stock_qty,
      batches: [{ price: prod.selling_price, qty: 1 }]  // batch tracking
    });
  }
  posRenderCart();
  const status = document.getElementById('pos-scan-status');
  if (status) {
    status.textContent = '✅ ' + prod.name + ' added';
    setTimeout(() => { if (status) status.textContent = ''; }, 2000);
  }
}

// Override posAddByBarcode — search API instead of localStorage
const _origPosAddByBarcode = window.posAddByBarcode;
window.posAddByBarcode = async function() {
  const inp = document.getElementById('pos-barcode-input');
  if (!inp) return;
  const val = inp.value.trim();
  if (!val) return;

  // Check cache first
  const cached = productCache[val] || productCache[val.toUpperCase()];
  if (cached) {
    posAddProductFromAPI(cached);
    inp.value = '';
    inp.focus();
    return;
  }

  // Search API
  const status = document.getElementById('pos-scan-status');
  if (status) { status.textContent = '🔍 Searching...'; status.style.color = 'var(--muted)'; }

  const results = await posSearchProducts(val);
  if (results.length === 1) {
    posAddProductFromAPI(results[0]);
    inp.value = '';
  } else if (results.length > 1) {
    showSearchDropdown(results);
  } else {
    toast('Product "' + val + '" not found. Add it in Products section.', 'warn');
    inp.value = '';
  }
  inp.focus();
};

// Override posAddProduct (quick buttons) — use API data
const _origPosAddProduct = window.posAddProduct;
window.posAddProduct = async function(barcode) {
  // Check cache
  const cached = productCache[barcode];
  if (cached) {
    posAddProductFromAPI(cached);
    return;
  }

  // Search by barcode
  const results = await posSearchProducts(barcode);
  const match = results.find(p => p.barcode === barcode);
  if (match) {
    posAddProductFromAPI(match);
  } else {
    toast('Product not found for barcode: ' + barcode, 'warn');
  }
};

// ══════════════════════════════════════
//  D5: Checkout — POST /api/pos/bill
// ══════════════════════════════════════

// ══════════════════════════════════════
//  D6: Recent Bills — Real API
// ══════════════════════════════════════

async function loadRecentBills() {
  const tbody = document.getElementById('pos-recent-bills');
  if (!tbody) return;

  try {
    const bills = await apiCall('/api/pos/bills?limit=6');
    if (!bills || bills.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="padding:20px;text-align:center;color:var(--muted);">No bills yet — create your first bill! 🛒</td></tr>';
      return;
    }

    const payStyles = {
      upi: { bg: '#dbeafe', color: '#1d4ed8', icon: '📲 UPI' },
      cash: { bg: '#dcfce7', color: '#166534', icon: '💵 Cash' },
      card: { bg: '#f3e8ff', color: '#7c3aed', icon: '💳 Card' },
      udhaar: { bg: '#fef3c7', color: '#92400e', icon: '📒 Udhaar' }
    };

    tbody.innerHTML = bills.map(bill => {
      const time = new Date(bill.created_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
      const items = bill.items || [];
      const itemText = items.map(i => (typeof _translateProdName === 'function' ? _translateProdName(i.product_name || 'Item') : (i.product_name || 'Item')) + ' ×' + toMrNum(i.qty || 0)).join(' + ');
      const pm = payStyles[bill.payment_mode] || payStyles.cash;
      const amount = bill.grand_total || 0;

      return '<tr style="border-bottom:1px solid #f3f4f6;">' +
        '<td style="padding:8px 12px;"><span class="order-id">#BILL-' + bill.id + '</span></td>' +
        '<td style="color:var(--muted);font-size:12px;">' + time + '</td>' +
        '<td style="font-size:12px;">' + itemText + '</td>' +
        '<td><span style="background:' + pm.bg + ';color:' + pm.color + ';padding:2px 8px;border-radius:20px;font-size:10px;font-weight:700;">' + pm.icon + '</span></td>' +
        '<td style="text-align:right;font-weight:700;">₹' + toMrNum(amount) + '</td>' +
        '<td><button class="po-btn" onclick="toast(\'Reprinting BILL-' + bill.id + '...\',\'info\')" style="font-size:11px;">🖨️</button></td>' +
        '</tr>';
    }).join('');
  } catch (err) {
    console.error('Recent bills error:', err);
    tbody.innerHTML = '<tr><td colspan="6" style="padding:20px;text-align:center;color:#f87171;">⚠ Could not load bills</td></tr>';
  }
}

// Load recent bills when POS screen opens + reload PRODUCT_DB when barcode screen opens
const __origShowScreen = window.showScreen;
window.showScreen = function(id) {
  __origShowScreen(id);
  if (id === 'pos') {
    loadRecentBills();
  }
  if (id === 'barcode') {
    if (typeof loadProductDBFromAPI === 'function') loadProductDBFromAPI();
  }
};

// ══════════════════════════════════════
//  D5: Checkout — POST /api/pos/bill
// ══════════════════════════════════════

// Override posCheckout — real API call
const _origPosCheckout = window.posCheckout;
window.posCheckout = async function() {
  if (posCart.length === 0) {
    toast('Cart is empty! Add products first.', 'warn');
    return;
  }

  // Build request body — send batch_prices for correct backend total
  const items = posCart.map(item => ({
    product_id: item.product_id,
    qty: item.qty,
    selling_price: item.price,
    batch_prices: item.batches || [{ price: item.price, qty: item.qty }]
  }));

  // Get dealer_id from customer dropdown
  const custSelect = document.getElementById('pos-customer-type');
  let dealer_id = null;
  if (custSelect && custSelect.value !== 'walkin') {
    // Map customer name to dealer_id (will need real mapping later)
    // For now, pass null — backend handles walk-in
  }

  // Get discount
  const discountEl = document.getElementById('pos-discount');
  let discount = 0;
  if (discountEl) {
    const discText = discountEl.textContent.replace('₹', '').replace(',', '').trim();
    discount = parseFloat(discText) || 0;
  }

  const body = {
    items: items,
    dealer_id: dealer_id,
    payment_mode: posPaymentMethod,
    discount: discount,
    notes: null
  };

  // Disable checkout button
  const checkoutBtn = document.querySelector('[onclick*="posCheckout"]');
  if (checkoutBtn) {
    checkoutBtn.disabled = true;
    checkoutBtn.textContent = '⏳ Creating Bill...';
  }

  try {
    const bill = await apiCall('/api/pos/bill', 'POST', body);

    // Success!
    const pm = { upi: '📲 UPI', cash: '💵 Cash', card: '💳 Card' }[posPaymentMethod] || 'UPI';
    toast(bill.invoice_number + ' created! ₹' + toMrNum(bill.grand_total || 0) + ' via ' + pm + ' ✅', 'success');

    // Clear cart
    posCart = [];
    posRenderCart();

    // Refresh recent bills list
    loadRecentBills();

    // Refresh dashboard data if function exists
    if (typeof loadDashboard === 'function') {
      loadDashboard();
    }

  } catch (err) {
    toast('Bill failed: ' + err.message, 'error');
    console.error('Checkout error:', err);
  } finally {
    // Re-enable button
    if (checkoutBtn) {
      checkoutBtn.disabled = false;
      checkoutBtn.textContent = '✅ Checkout & Print Bill';
    }
  }
};
