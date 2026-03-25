// SmartStore ERP — Tools Screens Connect (Phase J)
// DataHub, Invoice Auto, Bank Recon, Barcode, India Law — all real API

// ══════════════════════════════════════
//  DATA HUB — Dashboard Integration KPIs
// ══════════════════════════════════════

async function loadDataHub() {
  try {
    var dash = await apiCall('/api/data-hub/dashboard');

    // POS card KPIs
    setElText('dh-pos-sales', '\u20B9' + toMrNum(fmtAmt(dash.today.revenue)));
    setElText('dh-pos-bills', toMrNum(dash.today.bills));

    // Bank card KPIs — from recon summary
    try {
      var recon = await apiCall('/api/bank/recon-summary');
      setElText('dh-bank-balance', '\u20B9' + toMrNum(fmtAmt(recon.bank_totals.net)));
      setElText('dh-bank-txns', toMrNum(recon.bank_transactions.total));
    } catch(e) {
      setElText('dh-bank-balance', '\u2014');
      setElText('dh-bank-txns', '0');
    }

    // Sync log — real data summary
    var syncLog = document.getElementById('dh-sync-log');
    if (syncLog) {
      var now = new Date();
      var timeStr = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });

      var logHtml = '';
      logHtml += '<div style="display:flex;gap:10px;align-items:center;padding:5px 8px;background:rgba(16,185,129,0.06);border-radius:6px;">'
        + '<span style="color:var(--muted);">' + timeStr + '</span>'
        + '<span class="badge badge-green" style="font-size:8px;">POS</span>'
        + '<span style="color:var(--ink);">' + toMrNum(dash.today.bills) + ' bills today \u2014 \u20B9' + toMrNum(fmtAmt(dash.today.revenue)) + ' revenue</span>'
        + '</div>';

      logHtml += '<div style="display:flex;gap:10px;align-items:center;padding:5px 8px;background:rgba(59,130,246,0.06);border-radius:6px;">'
        + '<span style="color:var(--muted);">' + timeStr + '</span>'
        + '<span class="badge badge-blue" style="font-size:8px;">INVENTORY</span>'
        + '<span style="color:var(--ink);">' + toMrNum(dash.inventory.active_products) + ' products, stock value \u20B9' + toMrNum(fmtAmt(dash.inventory.stock_value)) + '</span>'
        + '</div>';

      if (dash.inventory.low_stock_alerts > 0) {
        logHtml += '<div style="display:flex;gap:10px;align-items:center;padding:5px 8px;background:rgba(239,68,68,0.06);border-radius:6px;">'
          + '<span style="color:var(--muted);">' + timeStr + '</span>'
          + '<span class="badge badge-red" style="font-size:8px;">ALERT</span>'
          + '<span style="color:var(--ink);">' + toMrNum(dash.inventory.low_stock_alerts) + ' low stock alerts!</span>'
          + '</div>';
      }

      logHtml += '<div style="display:flex;gap:10px;align-items:center;padding:5px 8px;background:rgba(234,179,8,0.06);border-radius:6px;">'
        + '<span style="color:var(--muted);">' + timeStr + '</span>'
        + '<span class="badge badge-orange" style="font-size:8px;">UDHAAR</span>'
        + '<span style="color:var(--ink);">Outstanding: \u20B9' + toMrNum(fmtAmt(dash.udhaar_outstanding)) + '</span>'
        + '</div>';

      logHtml += '<div style="display:flex;gap:10px;align-items:center;padding:5px 8px;background:rgba(16,185,129,0.06);border-radius:6px;">'
        + '<span style="color:var(--muted);">' + timeStr + '</span>'
        + '<span class="badge badge-green" style="font-size:8px;">MONTH</span>'
        + '<span style="color:var(--ink);">This month: ' + toMrNum(dash.this_month.bills) + ' bills, \u20B9' + toMrNum(fmtAmt(dash.this_month.revenue)) + '</span>'
        + '</div>';

      syncLog.innerHTML = logHtml;
    }

  } catch(e) {
    console.warn('DataHub load failed:', e.message);
  }
}


// ══════════════════════════════════════
//  INVOICE AUTOMATION — Sales Export
// ══════════════════════════════════════

async function loadInvoiceAuto() {
  var tbody = document.getElementById('inv-auto-tbody');
  if (!tbody) return;

  try {
    var now = new Date();
    var startDate = now.getFullYear() + '-' + String(now.getMonth() + 1).padStart(2, '0') + '-01';
    var endDate = now.toISOString().substring(0, 10);

    var data = await apiCall('/api/invoice-auto/export-sales?start_date=' + startDate + '&end_date=' + endDate);
    var records = data.data || [];

    // KPIs
    var totalGST = records.reduce(function(s, r) { return s + (r.gst_amount || 0); }, 0);
    var totalRevenue = records.reduce(function(s, r) { return s + (r.item_total || 0); }, 0);
    var invoiceSet = {};
    records.forEach(function(r) { invoiceSet[r.invoice_number] = r.bill_total; });
    var totalBills = Object.keys(invoiceSet).length;
    var totalBillValue = Object.keys(invoiceSet).reduce(function(s, k) { return s + invoiceSet[k]; }, 0);

    setElText('inv-kpi-total', toMrNum(totalBills));
    setElText('inv-kpi-total-sub', 'Invoices this month');
    setElText('inv-kpi-items', toMrNum(data.total_records));
    setElText('inv-kpi-items-sub', 'Line items');
    setElText('inv-kpi-gst', '\u20B9' + toMrNum(fmtAmt(totalGST)));
    setElText('inv-kpi-gst-sub', 'Tax collected');
    setElText('inv-kpi-revenue', '\u20B9' + toMrNum(fmtAmt(totalBillValue)));
    setElText('inv-kpi-revenue-sub', 'This month');

    if (!records.length) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--muted);padding:16px;">No sales data this month</td></tr>';
      return;
    }

    // Group by invoice
    var invoices = {};
    records.forEach(function(r) {
      if (!invoices[r.invoice_number]) {
        invoices[r.invoice_number] = { date: r.date, products: [], total: r.bill_total, mode: r.payment_mode, gst: 0 };
      }
      invoices[r.invoice_number].products.push(r.product_name);
      invoices[r.invoice_number].gst += r.gst_amount;
    });

    var html = '';
    var keys = Object.keys(invoices);
    keys.forEach(function(inv, i) {
      var d = invoices[inv];
      var dateStr = d.date ? d.date.substring(0, 10) : '\u2014';
      var productNames = d.products.join(', ');
      var bgStyle = i % 2 === 0 ? 'background:rgba(240,250,255,0.4);' : '';

      html += '<tr style="' + bgStyle + '">'
        + '<td><span class="order-id">#' + escHtml(inv) + '</span></td>'
        + '<td>' + dateStr + '</td>'
        + '<td>\u2014</td>'
        + '<td><b>' + escHtml(productNames.substring(0, 40)) + '</b></td>'
        + '<td class="mono">\u20B9' + toMrNum(fmtAmt(d.total)) + '</td>'
        + '<td>\u2014</td>'
        + '<td><span style="color:var(--accent3);font-weight:700;">\u20B9' + toMrNum(fmtAmt(d.gst)) + '</span></td>'
        + '<td><span class="badge badge-green">' + escHtml(d.mode || 'cash').toUpperCase() + '</span></td>'
        + '</tr>';
    });

    tbody.innerHTML = html;
  } catch(e) {
    tbody.innerHTML = '<tr><td colspan="8" style="color:var(--warn);padding:16px;">' + escHtml(e.message) + '</td></tr>';
  }
}


// ══════════════════════════════════════
//  BANK RECONCILIATION
// ══════════════════════════════════════

async function loadBankRecon() {
  await Promise.all([
    loadReconKPIs(),
    loadReconTable()
  ]);
}

async function loadReconKPIs() {
  try {
    var data = await apiCall('/api/bank/recon-summary');

    setElText('recon-kpi-matched', toMrNum(data.bank_transactions.matched));
    setElText('recon-kpi-matched-sub', data.bank_transactions.match_rate + ' match rate');
    setElText('recon-kpi-unmatched', toMrNum(data.bank_transactions.unmatched));
    setElText('recon-kpi-unmatched-sub', data.bank_transactions.unmatched > 0 ? 'Manual match needed' : '\u2705 All matched');
    setElText('recon-kpi-bank', '\u20B9' + toMrNum(fmtAmt(data.bank_totals.net)));
    setElText('recon-kpi-bank-sub', 'Cr \u20B9' + toMrNum(fmtAmt(data.bank_totals.total_credit)) + ' - Dr \u20B9' + toMrNum(fmtAmt(data.bank_totals.total_debit)));
    setElText('recon-kpi-ledger', '\u20B9' + toMrNum(fmtAmt(data.ledger_totals.net)));
    setElText('recon-kpi-ledger-sub', 'Gap: \u20B9' + toMrNum(fmtAmt(data.difference)));

    // Banner
    var bannerTitle = document.getElementById('recon-banner-title');
    var bannerSub = document.getElementById('recon-banner-sub');
    if (bannerTitle) {
      bannerTitle.textContent = 'Bank Statement \u2014 ' + toMrNum(data.bank_transactions.total) + ' Transactions · Match rate: ' + data.bank_transactions.match_rate;
      bannerSub.textContent = toMrNum(data.bank_transactions.matched) + ' matched \u00B7 ' + toMrNum(data.bank_transactions.unmatched) + ' need review \u00B7 Gap: \u20B9' + toMrNum(fmtAmt(data.difference));
    }
  } catch(e) {
    console.warn('Recon KPIs failed:', e.message);
  }
}

async function loadReconTable() {
  var tbody = document.getElementById('recon-table-tbody');
  if (!tbody) return;

  try {
    var txns = await apiCall('/api/bank/transactions?limit=20');

    if (!txns || !txns.length) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--muted);padding:16px;">No bank transactions. Upload a statement to get started.</td></tr>';
      return;
    }

    var html = '';
    txns.forEach(function(t) {
      var dateStr = t.txn_date || '\u2014';
      var amount = t.credit > 0 ? t.credit : t.debit;
      var amtType = t.credit > 0 ? 'Credit' : 'Debit';
      var isMatched = t.is_matched;

      var statusBadge, bgStyle, actionBtn;
      if (isMatched) {
        statusBadge = '<span class="badge badge-green">\u2705 Matched</span>';
        bgStyle = 'background:rgba(236,253,245,0.5);';
        actionBtn = '<button class="po-btn" style="background:var(--muted);font-size:10px;" disabled>\u092A\u0942\u0930\u094D\u0923</button>';
      } else {
        statusBadge = '<span class="badge badge-orange">\u26A0 Unmatched</span>';
        bgStyle = 'background:rgba(255,237,200,0.4);';
        actionBtn = '<button class="po-btn" onclick="toast(&quot;Assign txn #' + t.id + ' to ERP entry&quot;, &quot;info&quot;)">Assign</button>';
      }

      var matchRef = isMatched ? ('#Ledger-' + t.matched_ledger_id) : '\u2014';
      var matchRefHtml = isMatched ? '<span class="order-id">' + matchRef + '</span>' : '<span style="color:var(--muted);">\u2014</span>';

      html += '<tr style="' + bgStyle + '">'
        + '<td>' + dateStr + '</td>'
        + '<td>' + escHtml(t.description || '\u2014') + '</td>'
        + '<td class="mono">\u20B9' + toMrNum(fmtAmt(amount)) + ' <span style="font-size:10px;color:var(--muted);">(' + amtType + ')</span></td>'
        + '<td>' + matchRefHtml + '</td>'
        + '<td class="mono">' + (isMatched ? '\u20B9' + toMrNum(fmtAmt(amount)) : '\u2014') + '</td>'
        + '<td class="mono" style="color:' + (isMatched ? 'var(--accent3)' : 'var(--warn)') + ';">' + (isMatched ? '\u20B9' + toMrNum(0) : '\u20B9' + toMrNum(fmtAmt(amount))) + '</td>'
        + '<td>' + statusBadge + '</td>'
        + '<td>' + actionBtn + '</td>'
        + '</tr>';
    });

    tbody.innerHTML = html;
  } catch(e) {
    tbody.innerHTML = '<tr><td colspan="8" style="color:var(--warn);padding:16px;">' + escHtml(e.message) + '</td></tr>';
  }
}


// ══════════════════════════════════════
//  BARCODE SCANNER — Real API
// ══════════════════════════════════════

// Override onBarcodeInput to use real API
window.onBarcodeInput = function(val) {
  if (!val || val.length < 3) { hideScanResult(); return; }
  // Only auto-lookup when barcode is long enough (likely complete)
  if (val.length >= 8) {
    apiCall('/api/barcode/scan/' + encodeURIComponent(val.trim()))
      .then(function(prod) {
        currentProduct = {
          sku: prod.barcode,
          name: prod.name,
          price: prod.selling_price,
          stock: prod.stock_qty,
          hsn: '',
          gst: prod.gst_rate
        };
        var el = document.getElementById('scan-result');
        if (el) el.innerHTML = '<div style="background:#f0fdf4;border-radius:8px;padding:12px;border:1.5px solid #bbf7d0;">'
          + '<div style="font-weight:700;font-size:14px;">' + escHtml(prod.name) + '</div>'
          + '<div style="font-size:12px;color:#6b7280;margin-top:4px;">Barcode: ' + escHtml(prod.barcode) + ' \u00B7 Stock: ' + toMrNum(prod.stock_qty) + ' ' + escHtml(prod.unit) + ' \u00B7 \u20B9' + toMrNum(prod.selling_price) + ' \u00B7 GST: ' + toMrNum(prod.gst_rate) + '%</div>'
          + (prod.stock_alert ? '<div style="font-size:11px;color:#ef4444;margin-top:4px;">\u26A0 ' + escHtml(prod.stock_alert) + '</div>' : '')
          + '</div>';
        var qr = document.getElementById('qty-row');
        if (qr) qr.style.display = 'flex';
      })
      .catch(function(e) {
        var el = document.getElementById('scan-result');
        if (el) el.innerHTML = '<div style="background:#fef2f2;border-radius:8px;padding:12px;border:1.5px solid #fca5a5;">'
          + '<div style="font-weight:700;font-size:14px;color:#ef4444;">\u274C Product not found</div>'
          + '<div style="font-size:12px;color:#6b7280;margin-top:4px;">Barcode "' + escHtml(val) + '" not in database. Use \u2795 Add Product to register it.</div>'
          + '</div>';
      });
  }
};

// Override processScan
window.processScan = function() {
  var inp = document.getElementById('barcode-input');
  if (!inp || !inp.value.trim()) return;
  window.onBarcodeInput(inp.value.trim());
};


// ══════════════════════════════════════
//  INDIA LAW — GST Compliance + MSME + PT
// ══════════════════════════════════════

async function loadIndiaLaw() {
  await Promise.all([
    loadGSTCompliance(),
    loadMSMETimer(),
    loadPTData()
  ]);
}

async function loadGSTCompliance() {
  var container = document.getElementById('gst-compliance-list');
  if (!container) return;

  try {
    var data = await apiCall('/api/gst/compliance');

    var html = '';
    var checklist = data.checklist || [];

    // Overall status banner
    var statusColor = data.overall_status === 'ALL GOOD' ? '#166534' : data.overall_status === 'WARNINGS PRESENT' ? '#854d0e' : '#ef4444';
    var statusBg = data.overall_status === 'ALL GOOD' ? '#f0fdf4' : data.overall_status === 'WARNINGS PRESENT' ? '#fef9c3' : '#fef2f2';
    html += '<div style="background:' + statusBg + ';border-radius:8px;padding:12px;font-size:12px;color:' + statusColor + ';font-weight:600;margin-bottom:4px;">'
      + (data.overall_status === 'ALL GOOD' ? '\u2705 ' : '\u26A0\uFE0F ') + escHtml(data.overall_status)
      + ' \u2014 GSTIN: ' + escHtml(data.gstin)
      + '</div>';

    checklist.forEach(function(item) {
      var icon = item.status === 'OK' ? '\u2705' : '\u26A0\uFE0F';
      var bg = item.status === 'OK' ? '#f0fdf4' : '#fef9c3';
      var color = item.status === 'OK' ? '#166534' : '#854d0e';

      html += '<div style="display:flex;align-items:flex-start;gap:8px;background:' + bg + ';border-radius:8px;padding:10px 14px;">'
        + '<span style="font-size:14px;">' + icon + '</span>'
        + '<div><div style="font-size:12px;font-weight:600;color:' + color + ';">' + escHtml(item.check) + '</div>'
        + '<div style="font-size:11px;color:#6b7280;margin-top:2px;">' + escHtml(item.details) + '</div></div>'
        + '</div>';
    });

    container.innerHTML = html;
  } catch(e) {
    container.innerHTML = '<div style="color:var(--warn);padding:10px;">' + escHtml(e.message) + '</div>';
  }
}

async function loadMSMETimer() {
  var container = document.getElementById('msme-list');
  if (!container) return;

  try {
    // Get purchase orders to check MSME payment timers
    var pos = await apiCall('/api/purchase/?limit=20');
    var pending = pos.filter(function(p) { return p.status === 'approved' || p.status === 'received'; });

    if (!pending.length) {
      container.innerHTML = '<div style="background:#f0fdf4;border-radius:8px;padding:12px;text-align:center;color:#166534;font-size:12px;">\u2705 No pending MSME payments</div>';
      return;
    }

    var html = '';
    pending.forEach(function(po) {
      var created = new Date(po.created_at);
      var now = new Date();
      var daysElapsed = Math.floor((now - created) / (1000 * 60 * 60 * 24));
      var daysLeft = 45 - daysElapsed;

      var bgColor, textColor;
      if (daysLeft <= 3) {
        bgColor = '#fef2f2'; textColor = '#ef4444';
      } else if (daysLeft <= 10) {
        bgColor = '#fff7ed'; textColor = '#f97316';
      } else {
        bgColor = '#f0fdf4'; textColor = '#10b981';
      }

      var statusText = daysLeft <= 0 ? '\uD83D\uDEA8 OVERDUE!' : (daysLeft <= 7 ? '\u26A0\uFE0F ' + toMrNum(daysLeft) + ' days left' : '\u2705 On track');

      html += '<div style="background:' + bgColor + ';border-radius:8px;padding:12px;display:flex;justify-content:space-between;align-items:center;">'
        + '<div><div style="font-weight:600;font-size:13px;">' + escHtml(po.po_number) + '</div>'
        + '<div style="font-size:11px;color:#9ca3af;">Supplier #' + po.supplier_id + ' \u00B7 \u20B9' + toMrNum(fmtAmt(po.grand_total)) + '</div></div>'
        + '<div style="text-align:right;"><div style="font-size:20px;font-weight:800;color:' + textColor + ';">Day ' + toMrNum(daysElapsed) + '</div>'
        + '<div style="font-size:11px;color:' + textColor + ';">' + statusText + '</div></div>'
        + '</div>';
    });

    container.innerHTML = html;
  } catch(e) {
    container.innerHTML = '<div style="color:var(--warn);padding:10px;">' + escHtml(e.message) + '</div>';
  }
}

async function loadPTData() {
  try {
    var staff = await apiCall('/api/staff/?limit=100');
    var activeStaff = staff.filter(function(s) { return s.is_active; });
    var count = activeStaff.length;

    var now = new Date();
    var month = now.toLocaleString('en-IN', { month: 'long' });
    var ptRate = (now.getMonth() === 1) ? 300 : 200; // February = 300
    var totalPT = count * ptRate;

    var ptMonth = document.getElementById('pt-month');
    var ptAmount = document.getElementById('pt-amount');
    var ptTotal = document.getElementById('pt-total');

    if (ptMonth) ptMonth.textContent = month;
    if (ptAmount) ptAmount.textContent = '\u20B9' + toMrNum(ptRate);
    if (ptTotal) ptTotal.textContent = '\u20B9' + toMrNum(fmtAmt(totalPT));
  } catch(e) {
    console.warn('PT data failed:', e.message);
  }
}


// ══════════════════════════════════════
//  HOOK INTO showScreen
// ══════════════════════════════════════

var _origShowScreenTools = window.showScreen;
window.showScreen = function(id) {
  if (_origShowScreenTools) _origShowScreenTools(id);
  if (id === 'datahub') loadDataHub();
  if (id === 'invoice-auto') loadInvoiceAuto();
  if (id === 'bank-recon') loadBankRecon();
  if (id === 'india-law') loadIndiaLaw();
  // barcode scanner is interactive — no data load needed
};
