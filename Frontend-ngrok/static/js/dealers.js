// SmartStore ERP — Dealers + Payments Connect (Phase F)
// Real API se dealer list, udhaar, outstanding, payment ledger

// ══════════════════════════════════════
//  DEALERS SCREEN
// ══════════════════════════════════════

async function loadDealers() {
  await Promise.all([
    loadDealerFlagCards(),
    loadDealerTable()
  ]);
}

// Top flagged dealer cards (outstanding wale)
async function loadDealerFlagCards() {
  const container = document.getElementById('dealer-flag-cards');
  const bannerSub = document.getElementById('dealer-banner-sub');
  if (!container) return;

  try {
    const summary = await apiCall('/api/dealers/summary/outstanding');
    const total = summary.total_outstanding || 0;
    const count = summary.dealers_count || 0;
    const top = summary.top_defaulters || [];

    if (bannerSub) {
      bannerSub.textContent = toMrNum(count) + ' dealers with outstanding. Total: \u20B9' + toMrNum(fmtAmt(total));
    }

    if (!top.length) {
      container.innerHTML = '<div class="dealer-card good" style="flex:1;"><div class="ai-tag" style="color:var(--accent3);">\u2705 ALL CLEAR</div>'
        + '<div class="dealer-name">No outstanding udhaar!</div>'
        + '<div class="dealer-amount" style="color:var(--accent3);">\u20B90 \u0925\u0915\u0940\u0924</div>'
        + '<button class="reminder-btn neutral">\u2705 No Action Needed</button></div>';
      return;
    }

    let html = '';
    top.forEach(function(d, i) {
      const ratio = d.credit_limit > 0 ? d.outstanding / d.credit_limit : 1;
      let cardClass, tagText, tagColor;
      if (ratio >= 0.8) {
        cardClass = 'critical'; tagText = '\uD83D\uDEA9 HIGH RISK'; tagColor = 'var(--warn)';
      } else if (ratio >= 0.5) {
        cardClass = 'warning'; tagText = '\u26A0\uFE0F WATCH'; tagColor = 'var(--gold)';
      } else {
        cardClass = 'good'; tagText = '\u2705 LOW RISK'; tagColor = 'var(--accent3)';
      }

      html += '<div class="dealer-card ' + cardClass + '" style="cursor:pointer;">'
        + '<div class="ai-tag" style="color:' + tagColor + ';">' + tagText + '</div>'
        + '<div class="dealer-name">' + escHtml(d.name) + '</div>'
        + '<div class="dealer-amount" style="color:' + tagColor + ';">\u20B9' + toMrNum(fmtAmt(d.outstanding)) + ' \u0925\u0915\u0940\u0924</div>'
        + '<div class="dealer-meta"><span>Limit: \u20B9' + toMrNum(fmtAmt(d.credit_limit)) + '</span><span>' + (d.phone || '\u2014') + '</span></div>'
        + '<button class="reminder-btn" onclick="collectPaymentPrompt(' + d.id + ',\'' + escHtml(d.name) + '\',' + d.outstanding + ')">\uD83D\uDCB0 Payment Collect</button>'
        + '</div>';
    });

    container.innerHTML = html;
  } catch (e) {
    if (container) container.innerHTML = '<div style="padding:16px;color:var(--warn);">' + escHtml(e.message) + '</div>';
  }
}

// All dealers table
async function loadDealerTable() {
  const tbody = document.getElementById('dealer-table-tbody');
  if (!tbody) return;

  try {
    const dealers = await apiCall('/api/dealers/?limit=50');

    if (!dealers || !dealers.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--muted);">\u0915\u094B\u0923\u0924\u0947\u0939\u0940 dealer \u0928\u093E\u0939\u0940</td></tr>';
      return;
    }

    let html = '';
    dealers.forEach(function(d) {
      const outstanding = d.outstanding || 0;
      const limit = d.credit_limit || 0;
      const ratio = limit > 0 ? outstanding / limit : 0;

      let badgeClass, badgeText;
      if (outstanding === 0) {
        badgeClass = 'badge-green'; badgeText = '\u2705 \u0938\u094D\u0935\u0C1A\u094D\u091B';
      } else if (ratio >= 0.8) {
        badgeClass = 'badge-red'; badgeText = '\uD83D\uDEA9 \u0909\u091A\u094D\u091A \u091C\u094B\u0916\u0940\u092E';
      } else if (ratio >= 0.5) {
        badgeClass = 'badge-orange'; badgeText = '\u26A0 \u0932\u0915\u094D\u0937 \u0926\u094D\u092F\u093E';
      } else {
        badgeClass = 'badge-blue'; badgeText = '\u0915\u092E\u0940 \u091C\u094B\u0916\u0940\u092E';
      }

      const typeLabel = d.dealer_type === 'supplier' ? 'Supplier' : d.dealer_type === 'both' ? 'Both' : 'Customer';
      const amtStyle = outstanding > 0 ? (ratio >= 0.8 ? 'color:var(--warn)' : 'color:var(--gold)') : 'color:var(--accent3)';
      const actionBtn = outstanding > 0
        ? '<button class="po-btn" onclick="collectPaymentPrompt(' + d.id + ',\'' + escHtml(d.name) + '\',' + outstanding + ')">\uD83D\uDCB0 Collect</button>'
        : '<span style="font-size:12px;color:var(--muted);">\u2014</span>';

      html += '<tr>'
        + '<td><b>' + escHtml(d.name) + '</b><br><span style="font-size:10px;color:var(--muted);">' + typeLabel + '</span></td>'
        + '<td>' + escHtml(d.phone || '\u2014') + '</td>'
        + '<td>\u20B9' + toMrNum(fmtAmt(limit)) + '</td>'
        + '<td class="mono" style="' + amtStyle + '">\u20B9' + toMrNum(fmtAmt(outstanding)) + '</td>'
        + '<td>' + escHtml(d.address || '\u2014') + '</td>'
        + '<td><span class="badge ' + badgeClass + '">' + badgeText + '</span></td>'
        + '<td>' + actionBtn + '</td>'
        + '</tr>';
    });

    tbody.innerHTML = html;
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="7" style="color:var(--warn);">' + escHtml(e.message) + '</td></tr>';
  }
}

// Collect payment prompt
function collectPaymentPrompt(dealerId, dealerName, outstanding) {
  const amt = prompt('\uD83D\uDCB0 ' + dealerName + ' se kitna collect kiya?\nOutstanding: \u20B9' + toMrNum(fmtAmt(outstanding)) + '\n\nAmount (Rs):');
  if (!amt || isNaN(amt) || Number(amt) <= 0) return;

  const mode = prompt('Payment mode? (cash / upi / card)', 'cash');
  if (!mode) return;

  collectPayment(dealerId, Number(amt), mode);
}

async function collectPayment(dealerId, amount, mode) {
  try {
    await apiCall('/api/dealers/collect-payment', 'POST', {
      dealer_id: dealerId,
      amount: amount,
      payment_mode: mode,
      reference: 'Manual collection',
      notes: 'Collected via ERP'
    });
    toast('\u2705 \u20B9' + toMrNum(fmtAmt(amount)) + ' collected! Outstanding updated.', 'success');
    loadDealers(); // Refresh
  } catch (e) {
    toast('\u274C ' + e.message, 'error');
  }
}


// ══════════════════════════════════════
//  PAYMENTS SCREEN
// ══════════════════════════════════════

async function loadPayments() {
  await Promise.all([
    loadPayKPIs(),
    loadPayLedger()
  ]);
}

// Daily report KPIs
async function loadPayKPIs() {
  try {
    const r = await apiCall('/api/payments/daily-report');
    setElText('pay-kpi-in', '\u20B9' + toMrNum(fmtAmt(r.total_money_in)));
    setElText('pay-kpi-out', '\u20B9' + toMrNum(fmtAmt(r.total_money_out)));

    const netEl = document.getElementById('pay-kpi-net');
    if (netEl) {
      const net = r.net_cash_flow;
      netEl.textContent = (net >= 0 ? '+' : '') + '\u20B9' + toMrNum(fmtAmt(Math.abs(net)));
      netEl.style.color = net >= 0 ? 'var(--accent3)' : 'var(--warn)';
    }
    setElText('pay-kpi-count', toMrNum(r.total_entries));
  } catch (e) {
    console.warn('Daily report failed:', e.message);
  }
}

// Payment ledger table
async function loadPayLedger() {
  const tbody = document.getElementById('pay-ledger-tbody');
  if (!tbody) return;

  try {
    const entries = await apiCall('/api/payments/ledger?limit=20');

    if (!entries || !entries.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--muted);">\u0915\u094B\u0923\u0924\u0947\u0939\u0940 entry \u0928\u093E\u0939\u0940</td></tr>';
      return;
    }

    const inTypes = ['sale_in', 'udhaar_collect', 'manual_in'];

    let html = '';
    entries.forEach(function(e) {
      const isIn = inTypes.indexOf(e.entry_type) >= 0;
      const badgeClass = isIn ? 'badge-green' : 'badge-red';
      const badgeText = isIn ? '\u2B06 IN' : '\u2B07 OUT';
      const amtColor = isIn ? 'color:var(--accent3)' : 'color:var(--warn)';
      const typeLabel = e.entry_type.replace(/_/g, ' ').toUpperCase();

      html += '<tr>'
        + '<td>' + (e.entry_date || '\u2014') + '</td>'
        + '<td><span class="badge ' + badgeClass + '">' + badgeText + '</span><br>'
        + '<span style="font-size:10px;color:var(--muted);">' + typeLabel + '</span></td>'
        + '<td>' + escHtml(e.description || '\u2014') + '</td>'
        + '<td class="mono" style="' + amtColor + '">\u20B9' + toMrNum(fmtAmt(e.amount)) + '</td>'
        + '<td>' + (e.payment_mode || '\u2014').toUpperCase() + '</td>'
        + '<td>' + escHtml(e.dealer_name || '\u2014') + '</td>'
        + '<td style="font-size:11px;color:var(--muted);">' + escHtml(e.created_by || '\u2014') + '</td>'
        + '</tr>';
    });

    tbody.innerHTML = html;
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="7" style="color:var(--warn);">' + escHtml(e.message) + '</td></tr>';
  }
}


// ══════════════════════════════════════
//  HELPERS
// ══════════════════════════════════════

function fmtAmt(n) {
  if (n === null || n === undefined) return '0';
  n = Number(n);
  if (n >= 100000) return (n / 100000).toFixed(2).replace(/\.?0+$/, '') + 'L';
  if (n >= 1000) return n.toLocaleString('en-IN');
  return String(n);
}

// Reuse escHtml and setElText from inventory.js if already loaded
if (typeof escHtml === 'undefined') {
  function escHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
}
if (typeof setElText === 'undefined') {
  function setElText(id, val) {
    var el = document.getElementById(id);
    if (el) el.textContent = val;
  }
}


// ══════════════════════════════════════
//  HOOK INTO showScreen
// ══════════════════════════════════════

var _origShowScreenDlr = window.showScreen;
window.showScreen = function(id) {
  if (_origShowScreenDlr) _origShowScreenDlr(id);
  if (id === 'dealers') loadDealers();
  if (id === 'payments') loadPayments();
};
