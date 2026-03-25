// SmartStore ERP — Staff + Schemes Connect (Phase H)
// Real API se staff list, payroll, attendance, schemes

// ══════════════════════════════════════
//  STAFF SCREEN
// ══════════════════════════════════════

async function loadStaff() {
  await Promise.all([
    loadStaffKPIs(),
    loadStaffTable()
  ]);
}

async function loadStaffKPIs() {
  try {
    var staff = await apiCall('/api/staff/?limit=100');
    var activeStaff = staff.filter(function(s) { return s.is_active; });
    var totalSalary = activeStaff.reduce(function(sum, s) { return sum + s.salary; }, 0);

    setElText('staff-kpi-count', toMrNum(activeStaff.length));
    setElText('staff-kpi-salary', 'Total base: \u20B9' + toMrNum(fmtAmt(totalSalary)) + '/mo');

    // Try payroll summary
    var now = new Date();
    try {
      var payroll = await apiCall('/api/staff/payroll/summary/monthly?month=' + (now.getMonth() + 1) + '&year=' + now.getFullYear());
      setElText('staff-kpi-payroll', '\u20B9' + toMrNum(fmtAmt(payroll.total_net_salary || 0)));
      setElText('staff-kpi-payroll-sub', toMrNum(payroll.paid_count || 0) + ' paid, ' + toMrNum(payroll.pending_count || 0) + ' pending');
    } catch(e) {
      setElText('staff-kpi-payroll', '\u2014');
      setElText('staff-kpi-payroll-sub', 'No payroll generated yet');
    }

    // Today attendance
    var today = now.toISOString().substring(0, 10);
    try {
      var att = await apiCall('/api/staff/attendance/daily?date=' + today);
      var present = att.filter(function(a) { return a.status === 'present' || a.status === 'half_day'; }).length;
      setElText('staff-kpi-attendance', toMrNum(present) + '/' + toMrNum(activeStaff.length));
      setElText('staff-kpi-att-sub', 'Present today');
    } catch(e) {
      setElText('staff-kpi-attendance', '\u2014');
      setElText('staff-kpi-att-sub', 'No attendance marked today');
    }
  } catch (e) {
    console.warn('Staff KPI failed:', e.message);
  }
}

async function loadStaffTable() {
  var tbody = document.getElementById('staff-table-tbody');
  if (!tbody) return;

  try {
    var staff = await apiCall('/api/staff/?limit=50');

    if (!staff || !staff.length) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--muted);padding:16px;">No staff found</td></tr>';
      return;
    }

    // Try to get payroll for current month
    var now = new Date();
    var payrollMap = {};
    try {
      for (var i = 0; i < staff.length; i++) {
        var pr = await apiCall('/api/staff/payroll/' + staff[i].id + '?limit=1');
        if (pr && pr.length > 0 && pr[0].month === (now.getMonth() + 1) && pr[0].year === now.getFullYear()) {
          payrollMap[staff[i].id] = pr[0];
        }
      }
    } catch(e) {}

    var html = '';
    staff.forEach(function(s) {
      var p = payrollMap[s.id];
      var present = p ? p.days_present : '\u2014';
      var totalDays = p ? p.total_working_days : '\u2014';
      var deductions = p ? p.deductions : 0;
      var netPay = p ? p.net_salary : s.salary;
      var isPaid = p ? p.payment_status === 'paid' : false;

      var statusBadge = isPaid
        ? '<span style="background:#dcfce7;color:#166534;padding:3px 8px;border-radius:20px;font-size:11px;">Paid</span>'
        : '<span style="background:#fef9c3;color:#854d0e;padding:3px 8px;border-radius:20px;font-size:11px;">\u092A\u094D\u0930\u0932\u0902\u092C\u093F\u0924</span>';

      if (!s.is_active) {
        statusBadge = '<span style="background:#f3f4f6;color:#6b7280;padding:3px 8px;border-radius:20px;font-size:11px;">Inactive</span>';
      }

      html += '<tr style="border-bottom:1px solid #f3f4f6;">'
        + '<td style="padding:10px 12px;font-weight:600;">' + escHtml(s.name) + '</td>'
        + '<td style="text-align:center;">' + escHtml(s.role) + '</td>'
        + '<td style="text-align:right;">\u20B9' + toMrNum(fmtAmt(s.salary)) + '</td>'
        + '<td style="text-align:center;">' + toMrNum(present) + '/' + toMrNum(totalDays) + '</td>'
        + '<td style="text-align:right;">\u20B9' + toMrNum(200) + '</td>'
        + '<td style="text-align:right;color:' + (deductions > 0 ? '#f97316' : '#6b7280') + ';">' + (deductions > 0 ? '\u20B9' + toMrNum(fmtAmt(deductions)) : '\u2014') + '</td>'
        + '<td style="text-align:right;font-weight:700;">\u20B9' + toMrNum(fmtAmt(netPay)) + '</td>'
        + '<td style="text-align:center;">' + statusBadge + '</td>'
        + '</tr>';
    });

    tbody.innerHTML = html;
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="8" style="color:var(--warn);padding:16px;">' + escHtml(e.message) + '</td></tr>';
  }
}


// ══════════════════════════════════════
//  SCHEMES SCREEN
// ══════════════════════════════════════

async function loadSchemes() {
  await Promise.all([
    loadSchemeKPIs(),
    loadSchemeCards(),
    loadSchemePerfTable()
  ]);
}

async function loadSchemeKPIs() {
  try {
    var schemes = await apiCall('/api/schemes/?limit=100');
    var active = schemes.filter(function(s) { return s.is_active; });
    setElText('sch-kpi-active', toMrNum(active.length));
    setElText('sch-kpi-total', toMrNum(schemes.length));
  } catch(e) {
    console.warn('Scheme KPI failed:', e.message);
  }
}

async function loadSchemeCards() {
  var container = document.getElementById('scheme-active-list');
  if (!container) return;

  try {
    var schemes = await apiCall('/api/schemes/?limit=50');

    if (!schemes || !schemes.length) {
      container.innerHTML = '<div style="text-align:center;color:var(--muted);padding:16px;">No schemes created yet. Use the form to create one!</div>';
      return;
    }

    var html = '';
    schemes.forEach(function(s) {
      var isActive = s.is_active;
      var borderColor = isActive ? '#bbf7d0' : '#e2e8f0';
      var bgColor = isActive ? 'linear-gradient(135deg,#f0fdf4,#fff)' : 'linear-gradient(135deg,#f9fafb,#fff)';
      var statusBadge = isActive ? '<span class="badge badge-green">\uD83D\uDFE2 Live</span>' : '<span class="badge badge-gray">Inactive</span>';

      var typeLabel = s.scheme_type.toUpperCase().replace(/_/g, ' ');
      var discountInfo = '';
      if (s.discount_percent > 0) discountInfo = toMrNum(s.discount_percent) + '% off';
      if (s.discount_amount > 0) discountInfo = '\u20B9' + toMrNum(s.discount_amount) + ' off';
      if (s.buy_qty > 0 && s.get_qty > 0) discountInfo = 'Buy ' + toMrNum(s.buy_qty) + ' Get ' + toMrNum(s.get_qty);

      html += '<div style="border:1.5px solid ' + borderColor + ';border-radius:12px;padding:14px;background:' + bgColor + ';">'
        + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
        + '<div>'
        + '<span style="background:#dcfce7;color:#166534;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;">' + typeLabel + '</span>'
        + '<span style="font-size:14px;font-weight:700;margin-left:10px;">' + escHtml(s.name) + '</span>'
        + '</div>'
        + statusBadge
        + '</div>'
        + '<div style="font-size:13px;color:var(--muted);">' + escHtml(s.apply_on) + ': ' + escHtml(s.apply_value || 'All') + ' \u2014 <b style="color:var(--accent3);">' + discountInfo + '</b> · Min qty: ' + toMrNum(s.min_qty) + '</div>'
        + '<div style="display:flex;gap:16px;font-size:12px;margin-top:8px;flex-wrap:wrap;">'
        + '<span style="color:var(--muted);">\uD83D\uDCC5 ' + s.start_date + ' \u2013 ' + s.end_date + '</span>'
        + '</div>'
        + '</div>';
    });

    container.innerHTML = html;
  } catch (e) {
    container.innerHTML = '<div style="color:var(--warn);padding:16px;">' + escHtml(e.message) + '</div>';
  }
}

async function loadSchemePerfTable() {
  var tbody = document.getElementById('scheme-perf-tbody');
  if (!tbody) return;

  try {
    var schemes = await apiCall('/api/schemes/?limit=50');

    if (!schemes || !schemes.length) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:16px;">No schemes</td></tr>';
      return;
    }

    var html = '';
    schemes.forEach(function(s) {
      var typeLabel = s.scheme_type.replace(/_/g, ' ');
      var discountInfo = '';
      if (s.discount_percent > 0) discountInfo = toMrNum(s.discount_percent) + '%';
      if (s.discount_amount > 0) discountInfo = '\u20B9' + toMrNum(s.discount_amount);
      if (s.buy_qty > 0) discountInfo = 'B' + toMrNum(s.buy_qty) + 'G' + toMrNum(s.get_qty);

      var statusBadge = s.is_active ? '<span class="badge badge-green">Live</span>' : '<span class="badge badge-gray">Ended</span>';

      html += '<tr style="border-bottom:1px solid #f3f4f6;">'
        + '<td style="padding:10px 12px;font-weight:600;">' + escHtml(s.name) + '</td>'
        + '<td>' + typeLabel + ' ' + discountInfo + '</td>'
        + '<td style="text-align:right;">\u2014</td>'
        + '<td style="text-align:right;">\u2014</td>'
        + '<td style="text-align:right;color:var(--accent3);font-weight:700;">\u2014</td>'
        + '<td style="text-align:center;">' + statusBadge + '</td>'
        + '</tr>';
    });

    tbody.innerHTML = html;
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="6" style="color:var(--warn);padding:16px;">' + escHtml(e.message) + '</td></tr>';
  }
}

// Scheme create from the form
function schemeCreate() {
  var name = document.getElementById('sch-name');
  var type = document.getElementById('sch-type');
  var discount = document.getElementById('sch-discount');
  var minqty = document.getElementById('sch-minqty');
  var start = document.getElementById('sch-start');
  var end = document.getElementById('sch-end');

  if (!name || !name.value) { toast('Scheme name required!', 'error'); return; }
  if (!start || !start.value || !end || !end.value) { toast('Start and End dates required!', 'error'); return; }

  var typeMap = {
    'Flat Discount (\u20B9 off)': 'flat_off',
    'Percentage Discount (%)': 'percent_off',
    'Combo / Bundle': 'combo',
    'Buy X Get Y Free': 'buy_x_get_y',
    'Min Qty Discount': 'flat_off'
  };

  var schemeType = typeMap[type.value] || 'flat_discount';
  var discVal = Number(discount.value) || 0;

  var body = {
    name: name.value,
    scheme_type: schemeType,
    discount_percent: schemeType === 'percent_off' ? discVal : 0,
    discount_amount: schemeType === 'flat_off' ? discVal : 0,
    buy_qty: 0,
    get_qty: 0,
    apply_on: 'all',
    min_qty: Number(minqty.value) || 1,
    start_date: start.value,
    end_date: end.value
  };

  apiCall('/api/schemes/', 'POST', body).then(function() {
    toast('\u2705 Scheme "' + name.value + '" created!', 'success');
    name.value = '';
    discount.value = '';
    loadSchemes();
  }).catch(function(e) {
    toast('\u274C ' + e.message, 'error');
  });
}


// ══════════════════════════════════════
//  HOOK INTO showScreen
// ══════════════════════════════════════

var _origShowScreenStf = window.showScreen;
window.showScreen = function(id) {
  if (_origShowScreenStf) _origShowScreenStf(id);
  if (id === 'staff') loadStaff();
  if (id === 'schemes') loadSchemes();
};
