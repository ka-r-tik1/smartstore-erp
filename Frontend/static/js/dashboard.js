// SmartStore ERP — Dashboard Connect (Phase C)
// Real APIs se data fetch karke KPI cards, table, alerts update karta hai

// Product name EN↔MR map — used when rendering billing table in Marathi mode
var _PROD_MR_MAP = {
  'Amul Butter 500g': 'अमूल बटर 500g',
  'Tata Salt 1kg': 'टाटा मीठ 1kg',
  'Maggi Noodles 70g': 'मॅगी नूडल्स 70g',
  'Maggi 70g': 'मॅगी 70g',
  'Aashirvaad Atta 5kg': 'आशीर्वाद आटा 5kg',
  'Surf Excel 1kg': 'सर्फ एक्सेल 1kg',
  'Parle-G 800g': 'पार्ले-जी 800g',
  'Britannia Marie Gold 250g': 'ब्रिटानिया मेरी गोल्ड 250g',
  'Cadbury Dairy Milk 40g': 'कॅडबरी डेअरी मिल्क 40g',
  'Ariel 2kg': 'एरियल 2kg',
  'Dettol 500ml': 'डेटॉल 500ml',
  'Bread Loaf': 'पाव'
};
function _translateProdName(name) {
  if (typeof currentLang === 'undefined' || currentLang !== 'mr') return name;
  return _PROD_MR_MAP[name] || name;
}

// Format helpers
function formatRupees(amt) {
  if (amt >= 100000) return '₹' + toMrNum((amt / 100000).toFixed(2)) + 'L';
  if (amt >= 1000) return '₹' + toMrNum(amt.toLocaleString('en-IN'));
  return '₹' + toMrNum(amt);
}

function formatPercent(part, total) {
  if (!total || total === 0) return toMrNum(0) + '%';
  return toMrNum(Math.round((part / total) * 100)) + '% of today\'s sales';
}

// Main dashboard loader — called when dashboard screen opens
async function loadDashboard() {
  try {
    // Parallel fetch — sabhi APIs ek saath call karo
    const [summary, outstanding, lowStock, expiry, dashboard] = await Promise.allSettled([
      apiCall('/api/pos/today-summary'),
      apiCall('/api/dealers/summary/outstanding'),
      apiCall('/api/alerts/low-stock'),
      apiCall('/api/alerts/expiry?days_ahead=7'),
      apiCall('/api/alerts/dashboard')
    ]);

    // === KPI Row 1 — Main Metrics ===

    // Today's Sales
    if (summary.status === 'fulfilled') {
      const s = summary.value;
      const totalSale = s.total_sale || 0;
      const totalBills = s.total_bills || 0;
      document.getElementById('kpi-sales-val').textContent = formatRupees(totalSale);
      document.getElementById('kpi-sales-delta').textContent = toMrNum(totalBills) + ' bills today';

      // Footfall = total bills
      document.getElementById('kpi-footfall-val').textContent = toMrNum(totalBills);
      document.getElementById('kpi-footfall-delta').textContent = toMrNum(totalBills) + ' bills generated';

      // Payment breakdown
      const upi = s.upi || 0;
      const cash = s.cash || 0;
      const card = s.card || 0;

      document.getElementById('kpi-upi-val').textContent = formatRupees(upi);
      document.getElementById('kpi-upi-delta').textContent = formatPercent(upi, totalSale);

      document.getElementById('kpi-cash-val').textContent = formatRupees(cash);
      document.getElementById('kpi-cash-delta').textContent = formatPercent(cash, totalSale);

      document.getElementById('kpi-card-val').textContent = formatRupees(card);
      document.getElementById('kpi-card-delta').textContent = formatPercent(card, totalSale);
    } else {
      document.getElementById('kpi-sales-delta').textContent = '⚠ API Error';
    }

    // Outstanding (Udhaar)
    if (outstanding.status === 'fulfilled') {
      const o = outstanding.value;
      const total = o.total_outstanding || 0;
      const count = o.dealers_count || 0;
      document.getElementById('kpi-outstanding-val').textContent = formatRupees(total);
      document.getElementById('kpi-outstanding-delta').textContent = '↑ ' + toMrNum(count) + ' overdue dealers flagged';
    } else {
      document.getElementById('kpi-outstanding-delta').textContent = '⚠ API Error';
    }

    // Stock Alerts
    if (lowStock.status === 'fulfilled') {
      const ls = lowStock.value;
      const totalAlerts = ls.summary ? ls.summary.total_alerts : 0;
      document.getElementById('kpi-stock-alerts-val').textContent = toMrNum(totalAlerts);
      document.getElementById('kpi-stock-alerts-delta').textContent = totalAlerts > 0 ? 'Auto PO Ready' : 'All OK ✅';

      // Critical Stock panel update
      updateCriticalStock([...(ls.out_of_stock || []), ...(ls.critical_stock || [])]);
    } else {
      document.getElementById('kpi-stock-alerts-delta').textContent = '⚠ Error';
    }

    // Expiry Alerts
    if (expiry.status === 'fulfilled') {
      const ex = expiry.value;
      const expiryCount = (ex.summary ? ex.summary.expiring_soon : 0) ||
                          (ex.expiring_this_week ? ex.expiring_this_week.length : 0) ||
                          ((ex.already_expired ? ex.already_expired.length : 0) +
                          (ex.expiring_within_days ? ex.expiring_within_days.length : 0));
      document.getElementById('kpi-expiry-val').textContent = toMrNum(expiryCount);
      const _tExp = (typeof i18n !== 'undefined' && typeof currentLang !== 'undefined' && i18n[currentLang]) ? i18n[currentLang] : {};
      document.getElementById('kpi-expiry-delta').textContent = expiryCount > 0
        ? 'Products expire in 1–7 days!'
        : (_tExp.dash_no_expiry || 'No expiry alerts') + ' ✅';
    } else {
      document.getElementById('kpi-expiry-delta').textContent = '⚠ Error';
    }

    // AI Banner
    if (dashboard.status === 'fulfilled') {
      const d = dashboard.value;
      const alertCounts = d.alert_counts || {};
      const totalUrgent = (alertCounts.low_stock || 0) + (alertCounts.expiring_soon || 0) + (alertCounts.overdue_dealers || 0);
      document.getElementById('dash-ai-title').textContent = 'AI detected ' + toMrNum(totalUrgent) + ' urgent actions for today';

      // Build subtitle
      const parts = [];
      if (alertCounts.overdue_dealers > 0) parts.push(toMrNum(alertCounts.overdue_dealers) + ' dealers overdue');
      if (alertCounts.low_stock > 0) parts.push(toMrNum(alertCounts.low_stock) + ' items low stock 🚨');
      if (alertCounts.expiring_soon > 0) parts.push(toMrNum(alertCounts.expiring_soon) + ' items expiring');
      document.getElementById('dash-ai-sub').innerHTML = parts.join(' · ') || 'All systems normal ✅';
    }

    // Load today's activity table
    loadActivityTable();

  } catch (err) {
    console.error('Dashboard load error:', err);
  }
}

// Critical Stock panel update
function updateCriticalStock(items) {
  const container = document.getElementById('dash-critical-stock');
  if (!container) return;

  // Keep the Send All POs button
  const btn = container.querySelector('button');

  if (items.length === 0) {
    container.innerHTML = '<div style="text-align:center; padding:20px; color:#22c55e; font-weight:600;">✅ All stock levels OK</div>';
    if (btn) container.appendChild(btn);
    return;
  }

  let html = '';
  items.forEach(item => {
    const pct = item.reorder_level > 0 ? Math.round((item.current_stock / item.reorder_level) * 100) : 0;
    const fillClass = pct <= 15 ? 'fill-red' : 'fill-orange';
    const icon = pct <= 15 ? ' 🚨' : '';
    const color = pct <= 15 ? 'var(--warn)' : 'var(--gold)';

    const _tCS = (typeof i18n !== 'undefined' && typeof currentLang !== 'undefined' && i18n[currentLang]) ? i18n[currentLang] : {};
    const unitLabel = item.unit === 'Pcs' ? (_tCS.lbl_pcs || 'Pcs') : (item.unit || (_tCS.lbl_pcs || 'Pcs'));
    html += `<div>
      <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:700; margin-bottom:5px;">
        <b>${item.name}</b> <span style="color:${color}">${toMrNum(pct)}% · ${toMrNum(item.current_stock)} ${unitLabel}${icon}</span>
      </div>
      <div class="mini-stock-bar"><div class="mini-stock-fill ${fillClass}" style="width:${Math.min(pct, 100)}%"></div></div>
    </div>`;
  });

  container.innerHTML = html;
  if (btn) container.appendChild(btn);
}

// Today's Activity table — bills + orders
async function loadActivityTable() {
  const tbody = document.getElementById('dash-activity-tbody');
  if (!tbody) return;

  try {
    // Fetch recent bills
    const bills = await apiCall('/api/pos/bills?limit=10');

    if (!bills || bills.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:20px; color:#94a3b8;">No bills today — POS se first bill banao! 🛒</td></tr>';
      return;
    }

    let html = '';
    bills.forEach(bill => {
      const items = bill.items || [];
      const itemText = items.map(i => _translateProdName(i.product_name) + ' × ' + toMrNum(i.qty || i.quantity || 0)).join(' + ');
      const totalQty = items.reduce((sum, i) => sum + (i.qty || i.quantity || 0), 0);
      const payMode = (bill.payment_mode || 'cash').toUpperCase();
      const _t = (typeof i18n !== 'undefined' && typeof currentLang !== 'undefined' && i18n[currentLang]) ? i18n[currentLang] : {};
      const paidLabel = _t.dash_paid || 'Paid';
      const walkinLabel = _t.lbl_walkin || 'Walk-in Customer';
      const pcsLabel = _t.lbl_pcs || 'Pcs';
      const statusBadge = bill.payment_status === 'paid' || bill.status === 'paid' || bill.status === 'completed'
        ? '<span class="badge badge-green">✅ ' + payMode + ' ' + paidLabel + '</span>'
        : '<span class="badge badge-orange">' + (_t.filter_pending || 'Pending') + '</span>';

      html += `<tr>
        <td><span class="order-id">#BILL-${bill.id}</span></td>
        <td>${bill.customer_name || walkinLabel}</td>
        <td><b>${itemText || 'N/A'}</b></td>
        <td>${toMrNum(totalQty)} ${pcsLabel}</td>
        <td><span class="badge" style="background:#e0f2fe;color:#0369a1;font-size:10px;">🛍️ POS</span></td>
        <td>${statusBadge}</td>
        <td class="mono">${formatRupees(bill.grand_total || bill.total || 0)}</td>
      </tr>`;
    });

    tbody.innerHTML = html;
  } catch (err) {
    console.error('Activity table error:', err);
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:#f87171;">⚠ Could not load bills</td></tr>';
  }
}

// Refresh button handler
function refreshDashboard() {
  loadDashboard();
}
