// SmartStore ERP — Inventory + Expiry Connect (Phase E)
// Real API se stock levels, movements, aur expiry data load karta hai

// ══════════════════════════════════════
//  INVENTORY SCREEN
// ══════════════════════════════════════

async function loadInventory() {
  await Promise.all([
    loadInvSummary(),
    loadStockLevels(),
    loadMovements()
  ]);
}

// Summary — low stock chip count update karo
async function loadInvSummary() {
  try {
    const s = await apiCall('/api/inventory/summary');
    const chip = document.getElementById('low-stock-chip');
    if (chip) chip.textContent = '⚠ Low Stock (' + toMrNum(s.low_stock_count) + ')';
  } catch (e) {
    console.warn('Inventory summary load failed:', e.message);
  }
}

// Stock Levels — saare products load karo with stock bars
async function loadStockLevels() {
  const container = document.getElementById('inv-stock-list');
  if (!container) return;
  container.innerHTML = '<div style="padding:16px;text-align:center;color:var(--muted);">Loading...</div>';

  try {
    const products = await apiCall('/api/products/?limit=100&active_only=true');

    if (!products || !products.length) {
      container.innerHTML = '<div style="padding:16px;text-align:center;color:var(--muted);">कोणतेही उत्पादन सापडले नाही</div>';
      return;
    }

    let html = '';
    products.forEach(function(p) {
      const reorder = p.reorder_level || 0;
      const stock = p.stock_qty || 0;
      const ratio = reorder > 0 ? Math.min(stock / reorder, 1) : 1;
      const pct = Math.max(Math.round(ratio * 100), 3);

      var isMr = typeof currentLang !== 'undefined' && currentLang === 'mr';
      let status, badgeClass, fillClass, isLow;
      if (ratio <= 0.2) {
        status = isMr ? '🚨 गंभीर' : '🚨 Critical'; badgeClass = 'badge-red'; fillClass = 'fill-red'; isLow = true;
      } else if (ratio <= 0.6) {
        status = isMr ? '⚠ कमी' : '⚠ Low'; badgeClass = 'badge-orange'; fillClass = 'fill-orange'; isLow = true;
      } else {
        status = '✅ OK'; badgeClass = 'badge-green'; fillClass = 'fill-green'; isLow = false;
      }

      var pcsLabel = isMr ? 'नग' : 'Pcs';
      var currentLabel = isMr ? 'सध्या' : 'Current';
      var minLabel = isMr ? 'किमान' : 'Min';
      var noPOLabel = isMr ? 'PO नाही' : 'No PO';
      var displayName = (isMr && p.name_mr) ? p.name_mr : p.name;

      // Category Marathi mapping
      var catMap = { Dairy: 'दुग्ध', Grocery: 'किराणा', Biscuits: 'बिस्किटे', Snacks: 'स्नॅक्स', Beverages: 'पेये', Cleaning: 'स्वच्छता', 'Personal Care': 'वैयक्तिक काळजी', Chocolates: 'चॉकलेट्स', Oil: 'तेल', Bakery: 'बेकरी', General: 'सामान्य', 'Instant Food': 'झटपट अन्न' };
      var catName = p.category || 'General';
      var displayCat = isMr ? (catMap[catName] || catName) : catName;

      const poBtn = isLow
        ? '<button class="po-btn" onclick="toast(\'PO feature Phase G mein aayega\', \'info\')">⚡ खरेदी आदेश पाठवा</button>'
        : '<button class="po-btn disabled" disabled>' + noPOLabel + '</button>';

      html += '<div class="stock-alert-row" data-status="' + (isLow ? 'lowstock' : 'ok') + '">'
        + '<div class="stock-label">'
        + '<div class="stock-item-name"><b>' + escHtml(displayName) + '</b></div>'
        + '<div class="stock-item-sku">' + escHtml(p.barcode || '—') + ' · ' + escHtml(displayCat) + '</div>'
        + '</div>'
        + '<div class="stock-bar-wrap">'
        + '<div class="stock-bar-meta">'
        + '<span>' + currentLabel + ': ' + toMrNum(stock) + ' ' + pcsLabel + '</span>'
        + '<span style="color:var(--warn)">' + minLabel + ': ' + toMrNum(reorder) + ' ' + pcsLabel + '</span>'
        + '</div>'
        + '<div class="stock-bar"><div class="stock-bar-fill ' + fillClass + '" style="width:' + pct + '%"></div></div>'
        + '</div>'
        + '<span class="badge ' + badgeClass + '">' + status + '</span>'
        + poBtn
        + '</div>';
    });

    container.innerHTML = html;
    setupInvFilters();

  } catch (e) {
    container.innerHTML = '<div style="padding:16px;color:var(--warn);">Error: ' + escHtml(e.message) + '</div>';
  }
}

// Recent Stock Movements — last 10
async function loadMovements() {
  const tbody = document.getElementById('inv-movements-tbody');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--muted);">Loading...</td></tr>';

  try {
    const moves = await apiCall('/api/inventory/movements?limit=10');

    if (!moves || !moves.length) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--muted);">कोणतीही हालचाल नाही</td></tr>';
      return;
    }

    let html = '';
    moves.forEach(function(m) {
      const isIn = m.qty > 0;
      const typeMap = {
        purchase_in: 'IN', return_in: 'IN', adjustment: 'ADJ',
        damage_out: 'OUT', sale_out: 'SOLD'
      };
      const typeLabel = typeMap[m.movement_type] || (isIn ? 'IN' : 'OUT');
      const badgeClass = isIn ? 'badge-green' : 'badge-red';
      const dateStr = m.created_at ? m.created_at.substring(0, 10) : '—';
      const ref = m.reference || '—';
      const note = m.notes ? ' · ' + m.notes : '';

      html += '<tr>'
        + '<td>' + dateStr + '</td>'
        + '<td>#' + m.product_id + '</td>'
        + '<td><span class="badge ' + badgeClass + '">' + typeLabel + '</span></td>'
        + '<td>' + toMrNum(Math.abs(m.qty)) + ' Pcs</td>'
        + '<td class="order-id">' + escHtml(ref) + '</td>'
        + '<td style="font-size:11px;color:var(--muted);">' + escHtml(m.created_by || '—') + escHtml(note) + '</td>'
        + '</tr>';
    });

    tbody.innerHTML = html;

  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="6" style="color:var(--warn);">' + escHtml(e.message) + '</td></tr>';
  }
}

// Filter chips — All / Low Stock
function setupInvFilters() {
  document.querySelectorAll('#screen-inventory .filter-chip').forEach(function(chip) {
    chip.onclick = function() {
      document.querySelectorAll('#screen-inventory .filter-chip').forEach(function(c) {
        c.classList.remove('active');
      });
      this.classList.add('active');
      const filter = this.dataset.filter;
      document.querySelectorAll('#inv-stock-list .stock-alert-row').forEach(function(row) {
        if (filter === 'lowstock') {
          row.style.display = row.dataset.status === 'lowstock' ? '' : 'none';
        } else {
          row.style.display = '';
        }
      });
    };
  });
}


// ══════════════════════════════════════
//  EXPIRY SCREEN
// ══════════════════════════════════════

async function loadExpiry() {
  try {
    // Get all expiry alerts for next 30 days
    const alerts = await apiCall('/api/inventory/expiry-alerts?days=30');

    const urgent = alerts.filter(function(a) { return a.days_left <= 3; });
    const soon   = alerts.filter(function(a) { return a.days_left > 3 && a.days_left <= 7; });
    const safe   = alerts.filter(function(a) { return a.days_left > 7; });

    // KPI cards
    setElText('exp-kpi-critical', urgent.length);
    setElText('exp-kpi-7days', urgent.length + soon.length);
    // Wastage = stock-out damage_out mein se calculate nahi hota yahan, so keep as placeholder
    // setElText('exp-kpi-wastage', '—');
    setElText('exp-kpi-disposed', '—');  // damage_out history Phase I mein

    // Badge counts
    setElText('exp-badge-urgent', urgent.length);
    setElText('exp-badge-soon', soon.length);
    setElText('exp-badge-safe', safe.length);
    setElText('exp-badge-disposed', '—');

    // Pipeline columns
    renderExpiryCol('exp-col-urgent', urgent, 'var(--warn)', 'badge-red', '🚨');
    renderExpiryCol('exp-col-soon',   soon,   '#fde68a',    'badge-orange', '⚠️');
    renderExpiryCol('exp-col-safe',   safe,   '#bbf7d0',    'badge-green', '✅');

    // Disposed column — show damage_out movements as proxy
    loadDisposedCol();

  } catch (e) {
    console.error('Expiry load failed:', e.message);
    ['exp-col-urgent','exp-col-soon','exp-col-safe'].forEach(function(id) {
      setElHtml(id, '<div class="prod-card" style="border-color:#fca5a5;">Error: ' + escHtml(e.message) + '</div>');
    });
  }
}

function renderExpiryCol(colId, items, borderColor, badgeClass, icon) {
  const col = document.getElementById(colId);
  if (!col) return;

  if (!items.length) {
    col.innerHTML = '<div class="prod-card" style="border-color:#e2e8f0;text-align:center;color:var(--muted);font-size:12px;">कोणतेही नाही ✓</div>';
    return;
  }

  let html = '';
  items.forEach(function(a) {
    const expDate = a.expiry_date || '—';
    const batch   = a.batch_number || '—';
    const daysMsg = a.days_left === 0 ? 'आज एक्स्पायर!' : toMrNum(a.days_left) + ' दिवस शिल्लक';

    html += '<div class="prod-card" style="border-color:' + borderColor + ';">'
      + '<div class="prod-card-title"><b>' + escHtml(a.product_name) + '</b></div>'
      + '<div class="prod-card-meta">' + toMrNum(a.qty) + ' Pcs · Batch ' + escHtml(batch) + ' · Exp: ' + expDate + '</div>'
      + '<span class="badge ' + badgeClass + '" style="font-size:10.5px;display:inline-flex;">'
      + icon + ' ' + daysMsg
      + '</span>'
      + '</div>';
  });

  col.innerHTML = html;
}

async function loadDisposedCol() {
  const col = document.getElementById('exp-col-disposed');
  if (!col) return;

  try {
    const moves = await apiCall('/api/inventory/movements?movement_type=damage_out&limit=5');
    if (!moves || !moves.length) {
      col.innerHTML = '<div class="prod-card" style="border-color:#e2e8f0;text-align:center;color:var(--muted);font-size:12px;">कोणतेही नाही ✓</div>';
      setElText('exp-badge-disposed', 0);
      setElText('exp-kpi-disposed', 0);
      return;
    }
    setElText('exp-badge-disposed', moves.length);
    setElText('exp-kpi-disposed', moves.length);

    let html = '';
    moves.forEach(function(m) {
      const dateStr = m.created_at ? m.created_at.substring(0, 10) : '—';
      html += '<div class="prod-card" style="border-color:#e2e8f0;">'
        + '<div class="prod-card-title">#' + m.product_id + ' — Damage Out</div>'
        + '<div class="prod-card-meta">' + toMrNum(Math.abs(m.qty)) + ' Pcs · ' + dateStr + '</div>'
        + '<span class="badge badge-gray" style="font-size:10.5px;display:inline-flex;">'
        + escHtml(m.reference || m.notes || 'Written Off')
        + '</span>'
        + '</div>';
    });
    col.innerHTML = html;
  } catch (e) {
    col.innerHTML = '<div style="padding:10px;color:var(--muted);font-size:12px;">—</div>';
  }
}


// ══════════════════════════════════════
//  HELPERS
// ══════════════════════════════════════

function setElText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function setElHtml(id, html) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = html;
}

function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}


// ══════════════════════════════════════
//  HOOK INTO showScreen
// ══════════════════════════════════════

const _origShowScreenInv = window.showScreen;
window.showScreen = function(id) {
  if (_origShowScreenInv) _origShowScreenInv(id);
  if (id === 'inventory') loadInventory();
  if (id === 'expiry') loadExpiry();
};
