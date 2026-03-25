// SmartStore ERP — Orders + Purchase Orders Connect (Phase G)
// Real API se sales orders, PO list, supplier ledger

// ══════════════════════════════════════
//  ORDERS SCREEN (Sales Orders tab)
// ══════════════════════════════════════

async function loadOrders() {
  var tbody = document.getElementById('orders-table-tbody');
  if (!tbody) return;

  try {
    var orders = await apiCall('/api/orders/?limit=20');

    if (!orders || !orders.length) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--muted);">No orders yet</td></tr>';
      return;
    }

    var html = '';
    orders.forEach(function(o, i) {
      var dateStr = o.created_at ? o.created_at.substring(0, 10) : '\u2014';
      var items = o.items || [];
      var productNames = items.map(function(it) { return it.product_name; }).join(', ') || '\u2014';
      var totalQty = items.reduce(function(s, it) { return s + it.qty; }, 0);

      // Status badge
      var statusBadge;
      if (o.payment_status === 'paid') {
        statusBadge = '<span class="badge badge-green">\u2705 Paid</span>';
      } else if (o.payment_status === 'pending') {
        statusBadge = '<span class="badge badge-red">\u26A0 Pending</span>';
      } else if (o.payment_status === 'cancelled') {
        statusBadge = '<span class="badge badge-gray">Cancelled</span>';
      } else {
        statusBadge = '<span class="badge badge-blue">' + escHtml(o.payment_status) + '</span>';
      }

      var bgStyle = i % 2 === 0 ? 'background:rgba(255,255,255,0.3);' : 'background:rgba(255,255,255,0.1);';
      if (o.payment_status === 'pending') bgStyle = 'background:rgba(255,220,220,0.2);';

      var amtStyle = o.payment_status === 'pending' ? 'color:var(--warn)' : '';

      html += '<tr style="' + bgStyle + '">'
        + '<td><span class="order-id">#' + escHtml(o.invoice_number) + '</span></td>'
        + '<td>' + dateStr + '</td>'
        + '<td>' + (o.dealer_id || '\u2014') + '</td>'
        + '<td><b>' + escHtml(productNames.substring(0, 40)) + '</b></td>'
        + '<td>' + toMrNum(totalQty) + ' Pcs</td>'
        + '<td class="mono" style="' + amtStyle + '">\u20B9' + toMrNum(fmtAmt(o.grand_total)) + '</td>'
        + '<td>' + statusBadge + '</td>'
        + '<td>' + escHtml(o.payment_mode || '\u2014').toUpperCase() + '</td>'
        + '</tr>';
    });

    tbody.innerHTML = html;
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="8" style="color:var(--warn);">' + escHtml(e.message) + '</td></tr>';
  }
}


// ══════════════════════════════════════
//  PURCHASE ORDERS SCREEN
// ══════════════════════════════════════

async function loadPurchase() {
  await Promise.all([
    loadPOKPIs(),
    loadPOTable(),
    loadSupplierCards()
  ]);
}

// PO KPIs — count from PO list
async function loadPOKPIs() {
  try {
    var pos = await apiCall('/api/purchase/?limit=200');
    var total = pos.length;
    var pending = pos.filter(function(p) { return p.status === 'draft' || p.status === 'approved'; }).length;
    var received = pos.filter(function(p) { return p.status === 'received'; }).length;
    var totalValue = pos.reduce(function(s, p) { return s + p.grand_total; }, 0);

    setElText('po-kpi-total', toMrNum(total));
    setElText('po-kpi-pending', toMrNum(pending));
    setElText('po-kpi-value', '\u20B9' + toMrNum(fmtAmt(totalValue)));
    setElText('po-kpi-received', toMrNum(received));
  } catch (e) {
    console.warn('PO KPIs failed:', e.message);
  }
}

// PO Table
async function loadPOTable() {
  var tbody = document.getElementById('po-table-tbody');
  if (!tbody) return;

  try {
    var pos = await apiCall('/api/purchase/?limit=50');

    if (!pos || !pos.length) {
      tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;color:var(--muted);">No purchase orders yet</td></tr>';
      return;
    }

    // Cache supplier names
    var supplierCache = {};
    try {
      var suppliers = await apiCall('/api/dealers/?dealer_type=supplier&limit=50');
      suppliers.forEach(function(s) { supplierCache[s.id] = s.name; });
      var bothTypes = await apiCall('/api/dealers/?dealer_type=both&limit=50');
      bothTypes.forEach(function(s) { supplierCache[s.id] = s.name; });
    } catch(e) {}

    var html = '';
    pos.forEach(function(po, i) {
      var dateStr = po.created_at ? po.created_at.substring(0, 10) : '\u2014';
      var supplierName = supplierCache[po.supplier_id] || '#' + po.supplier_id;
      var items = po.items || [];
      var productNames = items.map(function(it) { return it.product_name; }).join(', ') || '\u2014';
      var totalQty = items.reduce(function(s, it) { return s + it.qty_ordered; }, 0);

      // Status badge + action
      var statusBadge, actionBtn;
      if (po.status === 'draft') {
        statusBadge = '<span class="badge badge-blue">Draft</span>';
        actionBtn = '<button class="po-btn" onclick="approvePO(' + po.id + ')">Approve</button>';
      } else if (po.status === 'approved') {
        statusBadge = '<span class="badge badge-orange">Approved</span>';
        actionBtn = '<button class="po-btn" onclick="toast(\'Receive flow Phase G mein\', \'info\')">Receive</button>';
      } else if (po.status === 'received') {
        statusBadge = '<span class="badge badge-green">Received</span>';
        actionBtn = '<button class="po-btn" style="background:var(--muted);color:#fff;" disabled>\u0935\u0942\u0930\u094D\u0923</button>';
      } else if (po.status === 'cancelled') {
        statusBadge = '<span class="badge badge-red">Cancelled</span>';
        actionBtn = '<span style="font-size:11px;color:var(--muted);">\u2014</span>';
      } else {
        statusBadge = '<span class="badge badge-gray">' + po.status + '</span>';
        actionBtn = '\u2014';
      }

      var bgStyle = po.status === 'received' ? 'background:rgba(240,255,245,0.4);' :
                    po.status === 'cancelled' ? 'background:rgba(255,240,240,0.3);' :
                    i % 2 === 0 ? 'background:rgba(255,255,255,0.3);' : 'background:rgba(255,255,255,0.1);';

      html += '<tr style="' + bgStyle + '">'
        + '<td><span class="order-id">#' + escHtml(po.po_number) + '</span></td>'
        + '<td>' + dateStr + '</td>'
        + '<td>' + escHtml(supplierName) + '</td>'
        + '<td><b>' + escHtml(productNames.substring(0, 35)) + '</b></td>'
        + '<td>' + toMrNum(totalQty) + ' Pcs</td>'
        + '<td class="mono">\u20B9' + toMrNum(fmtAmt(po.grand_total)) + '</td>'
        + '<td>' + (po.expected_date || '\u2014') + '</td>'
        + '<td>' + statusBadge + '</td>'
        + '<td>' + actionBtn + '</td>'
        + '</tr>';
    });

    tbody.innerHTML = html;
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="9" style="color:var(--warn);">' + escHtml(e.message) + '</td></tr>';
  }
}

// Approve PO
async function approvePO(poId) {
  try {
    await apiCall('/api/purchase/' + poId + '/approve', 'POST');
    toast('\u2705 PO approved!', 'success');
    loadPurchase();
  } catch (e) {
    toast('\u274C ' + e.message, 'error');
  }
}

// Supplier Ledger Cards
async function loadSupplierCards() {
  var container = document.getElementById('po-supplier-cards');
  if (!container) return;

  try {
    var suppliers = await apiCall('/api/dealers/?dealer_type=supplier&limit=20');
    var bothTypes = await apiCall('/api/dealers/?dealer_type=both&limit=20');
    var allSuppliers = suppliers.concat(bothTypes);

    if (!allSuppliers.length) {
      container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--muted);">No suppliers found</div>';
      return;
    }

    var colors = ['#dbeafe,#bfdbfe', '#d1fae5,#a7f3d0', '#fce7f3,#fbcfe8', '#fef3c7,#fde68a', '#e0e7ff,#c7d2fe'];
    var icons = ['\uD83C\uDFED', '\uD83C\uDFD7\uFE0F', '\u2697\uFE0F', '\uD83D\uDE9A', '\uD83D\uDCE6'];

    var html = '';
    allSuppliers.forEach(function(s, i) {
      var bg = colors[i % colors.length];
      var icon = icons[i % icons.length];

      html += '<div class="panel" style="padding:20px;">'
        + '<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">'
        + '<div style="width:40px;height:40px;border-radius:10px;background:linear-gradient(135deg,' + bg + ');display:flex;align-items:center;justify-content:center;font-size:20px;">' + icon + '</div>'
        + '<div>'
        + '<div style="font-weight:700;font-size:14px;">' + escHtml(s.name) + '</div>'
        + '<div style="font-size:11px;color:var(--muted);">' + escHtml(s.address || '\u2014') + '</div>'
        + '</div></div>'
        + '<div style="display:flex;flex-direction:column;gap:6px;font-size:12px;">'
        + '<div style="display:flex;justify-content:space-between;"><span style="color:var(--muted);">Phone</span><strong>' + escHtml(s.phone || '\u2014') + '</strong></div>'
        + '<div style="display:flex;justify-content:space-between;"><span style="color:var(--muted);">GSTIN</span><strong style="font-size:10px;">' + escHtml(s.gstin || '\u2014') + '</strong></div>'
        + '<div style="display:flex;justify-content:space-between;"><span style="color:var(--muted);">Credit Limit</span><strong class="mono">\u20B9' + toMrNum(fmtAmt(s.credit_limit)) + '</strong></div>'
        + '<div style="display:flex;justify-content:space-between;"><span style="color:var(--muted);">Outstanding</span><strong class="mono" style="color:' + (s.outstanding > 0 ? 'var(--warn)' : 'var(--accent3)') + ';">\u20B9' + toMrNum(fmtAmt(s.outstanding)) + '</strong></div>'
        + '</div>'
        + '<button class="po-btn" style="width:100%;margin-top:12px;" onclick="toast(\'New PO for ' + escHtml(s.name) + ' — Phase G complete!\', \'info\')">+ New PO</button>'
        + '</div>';
    });

    container.innerHTML = html;
  } catch (e) {
    container.innerHTML = '<div style="padding:20px;color:var(--warn);">' + escHtml(e.message) + '</div>';
  }
}


// ══════════════════════════════════════
//  HOOK INTO showScreen
// ══════════════════════════════════════

var _origShowScreenOrd = window.showScreen;
window.showScreen = function(id) {
  if (_origShowScreenOrd) _origShowScreenOrd(id);
  if (id === 'orders') loadOrders();
  if (id === 'purchase') loadPurchase();
};
