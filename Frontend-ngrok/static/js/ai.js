// SmartStore ERP — AI Screens Connect (Phase I)
// Forecast, Chatbot, Fraud — all real API

// ══════════════════════════════════════
//  AI FORECAST SCREEN
// ══════════════════════════════════════

async function loadForecast() {
  await Promise.all([
    loadTrendingProducts(),
    loadReorderSuggestions(),
    loadSlowMovingInsights()
  ]);
}

// Trending products → bar chart + product mix
async function loadTrendingProducts() {
  var barsEl = document.getElementById('forecast-bars');
  var legendEl = document.getElementById('pie-legend');
  var recEl = document.getElementById('forecast-recommendation');
  if (!barsEl) return;

  try {
    var data = await apiCall('/api/ai/forecast/trending?days=30&top_n=6');
    var products = data.trending_products || [];

    if (!products.length) {
      barsEl.innerHTML = '<div style="text-align:center;color:var(--muted);padding:40px;">No sales data yet for forecast</div>';
      return;
    }

    // Find max qty for scaling
    var maxQty = Math.max.apply(null, products.map(function(p) { return p.total_qty_sold; }));

    var barColors = [
      'linear-gradient(180deg,#eab308,#ca8a04)',
      'linear-gradient(180deg,#84cc16,#65a30d)',
      'linear-gradient(180deg,#0f9e56,#0a7a3e)',
      'linear-gradient(180deg,#f59e0b,#d97706)',
      'linear-gradient(180deg,#3b82f6,#2563eb)',
      'linear-gradient(180deg,#ef4444,#dc2626)'
    ];
    var pieColors = ['#eab308', '#84cc16', '#0f9e56', '#f59e0b', '#3b82f6', '#ef4444'];

    var totalRevenue = products.reduce(function(s, p) { return s + p.total_revenue; }, 0);

    var html = '';
    products.forEach(function(p, i) {
      var pct = Math.round(p.total_qty_sold / maxQty * 100);
      var revStr = fmtAmt(p.total_revenue);

      html += '<div class="forecast-month">'
        + '<div class="fm-trend">' + toMrNum(p.total_qty_sold) + ' Pcs</div>'
        + '<div class="fm-bar-wrap"><div class="fm-bar" style="height:' + pct + '%; background:' + barColors[i % 6] + ';"><div class="fm-bar-pct">' + toMrNum(pct) + '%</div></div></div>'
        + '<div class="fm-name" style="font-size:10px;">' + escHtml(p.product_name.substring(0, 15)) + '</div>'
        + '<div class="fm-rev">\u20B9' + toMrNum(revStr) + '</div>'
        + '</div>';
    });

    barsEl.innerHTML = html;

    // Product mix legend
    if (legendEl) {
      var legendHtml = '';
      products.forEach(function(p, i) {
        var share = totalRevenue > 0 ? Math.round(p.total_revenue / totalRevenue * 100) : 0;
        legendHtml += '<div style="display:flex;align-items:center;gap:6px;">'
          + '<div style="width:8px;height:8px;border-radius:50%;background:' + pieColors[i % 6] + ';"></div>'
          + '<span style="font-size:10px;color:var(--ink);">' + escHtml(p.product_name.substring(0, 18)) + ' <b>' + toMrNum(share) + '%</b></span>'
          + '</div>';
      });
      legendEl.innerHTML = legendHtml;
    }

    // Recommendation
    if (recEl && products.length >= 2) {
      var top2 = products.slice(0, 2);
      recEl.innerHTML = '\uD83E\uDD16 AI Recommendation: Top sellers are <strong>' + escHtml(top2[0].product_name) + '</strong> (' + toMrNum(top2[0].total_qty_sold) + ' Pcs) and <strong>' + escHtml(top2[1].product_name) + '</strong> (' + toMrNum(top2[1].total_qty_sold) + ' Pcs). Ensure adequate stock levels.';
    }

    // Banner sub
    var bannerSub = document.getElementById('forecast-banner-sub');
    if (bannerSub) {
      bannerSub.textContent = 'Based on last 30 days sales data. ' + toMrNum(products.length) + ' trending products analyzed. Total revenue: \u20B9' + toMrNum(fmtAmt(totalRevenue));
    }

  } catch (e) {
    barsEl.innerHTML = '<div style="text-align:center;color:var(--warn);padding:40px;">' + escHtml(e.message) + '</div>';
  }
}

// Reorder suggestions → supplier pre-order table
async function loadReorderSuggestions() {
  var tbody = document.getElementById('forecast-reorder-tbody');
  if (!tbody) return;

  try {
    var data = await apiCall('/api/ai/forecast/reorder-suggestions');
    var suggestions = data.suggestions || [];

    if (!suggestions.length) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--accent3);padding:16px;">\u2705 All stock levels healthy — no reorder needed!</td></tr>';
      return;
    }

    var html = '';
    suggestions.forEach(function(s, i) {
      var urgencyBadge = s.urgency === 'URGENT'
        ? '<span style="background:#fee2e2;color:#ef4444;padding:2px 8px;border-radius:20px;font-size:10px;font-weight:700;">URGENT</span>'
        : '<span style="background:#fef3c7;color:#d97706;padding:2px 8px;border-radius:20px;font-size:10px;font-weight:700;">SOON</span>';

      html += '<tr>'
        + '<td><b>' + escHtml(s.product_name) + '</b> ' + urgencyBadge + '</td>'
        + '<td>' + toMrNum(s.current_stock) + ' Pcs (' + toMrNum(s.days_of_stock_left) + ' days left)</td>'
        + '<td>' + toMrNum(s.suggested_order_qty) + ' Pcs</td>'
        + '<td class="mono">\u20B9' + toMrNum(fmtAmt(s.estimated_cost)) + '</td>'
        + '<td>' + toMrNum(s.avg_daily_sales) + '/day</td>'
        + '<td><button class="po-btn" onclick="toast(&quot;\u26A1 PO for ' + escHtml(s.product_name).replace(/"/g, '') + ' — go to Purchase screen&quot;, &quot;info&quot;)">PO \u092A\u093E\u0920\u0935\u093E</button></td>'
        + '</tr>';
    });

    tbody.innerHTML = html;
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="6" style="color:var(--warn);padding:16px;">' + escHtml(e.message) + '</td></tr>';
  }
}

// Slow moving + insights
async function loadSlowMovingInsights() {
  var container = document.getElementById('forecast-insights');
  if (!container) return;

  try {
    var data = await apiCall('/api/ai/forecast/slow-moving?days=30');
    var slow = data.slow_moving_products || [];

    var html = '';

    var isMr = typeof currentLang !== 'undefined' && currentLang === 'mr';

    // Slow moving insight
    if (slow.length > 0) {
      var topProds = slow.slice(0, 3).map(function(s) { return escHtml(s.product_name) + ' (' + toMrNum(s.stock_qty) + ' Pcs)'; }).join(', ');
      html += '<div class="insight-card red">'
        + '<div class="insight-card-label" style="color:var(--warn)">\u26A0 ' + (isMr ? 'डेड स्टॉक अलर्ट' : 'Dead Stock Alert') + '</div>'
        + '<div class="insight-card-title">' + toMrNum(slow.length) + ' ' + (isMr ? 'उत्पादने ३० दिवसांत विकली नाहीत' : 'products not sold in 30 days') + '</div>'
        + '<div class="insight-card-body">' + (isMr ? 'डेड स्टॉक मूल्य' : 'Dead stock value') + ': \u20B9' + toMrNum(fmtAmt(data.total_dead_stock_value)) + '. '
        + (isMr ? 'टॉप' : 'Top') + ': ' + topProds
        + '. ' + (isMr ? 'सूट द्या किंवा सप्लायरला परत करा.' : 'Consider discounting or returning to supplier.') + '</div>'
        + '</div>';
    } else {
      html += '<div class="insight-card green">'
        + '<div class="insight-card-label" style="color:var(--accent3)">\u2705 ' + (isMr ? 'स्टॉक स्थिती' : 'Stock Health') + '</div>'
        + '<div class="insight-card-title">' + (isMr ? 'डेड स्टॉक आढळला नाही' : 'No dead stock detected') + '</div>'
        + '<div class="insight-card-body">' + (isMr ? 'सर्व उत्पादने गेल्या ३० दिवसांत विकली गेली. स्टॉक टर्नओव्हर चांगला आहे!' : 'All products with stock have been sold in the last 30 days. Inventory turnover looking healthy!') + '</div>'
        + '</div>';
    }

    // General AI insight
    html += '<div class="insight-card purple">'
      + '<div class="insight-card-label" style="color:var(--ai)">\uD83E\uDD16 ' + (isMr ? 'AI अंतर्दृष्टी' : 'AI Insight') + '</div>'
      + '<div class="insight-card-title">' + (isMr ? 'मागणी विश्लेषण सक्रिय' : 'Demand Analysis Active') + '</div>'
      + '<div class="insight-card-body">' + (isMr ? 'SmartStore AI विक्री वेग, स्टॉक पातळी आणि हंगामी नमुने तपासतो. वर Reorder सूचना तक्ता पहा.' : 'SmartStore AI monitors sales velocity, stock levels, and seasonal patterns. Check the Reorder Suggestions table above for actionable recommendations.') + '</div>'
      + '</div>';

    container.innerHTML = html;
  } catch (e) {
    container.innerHTML = '<div style="color:var(--warn);padding:16px;">' + escHtml(e.message) + '</div>';
  }
}


// ══════════════════════════════════════
//  CHATBOT SCREEN — Real API
// ══════════════════════════════════════

// Override sendChat (chip click)
window.sendChat = function(chip) {
  var text = chip.textContent;
  addMessage(text, true);
  addTypingIndicator();
  chatbotAsk(text);
};

// Override sendChatInput (user types + Enter)
window.sendChatInput = function() {
  var input = document.getElementById('chat-input');
  if (!input || !input.value.trim()) return;
  var displayText = input.value;
  addMessage(displayText, true);

  // Get English buffer for API (Marathi transliteration stored in _mrBuf)
  var queryText = (typeof _mrBuf !== 'undefined' && _mrBuf) ? _mrBuf : displayText;
  input.value = '';
  if (typeof _mrBuf !== 'undefined') _mrBuf = '';

  addTypingIndicator();
  chatbotAsk(queryText);
};

// Override triggerChat (quick command buttons)
window.triggerChat = function(text) {
  showScreen('chatbot');
  setTimeout(function() {
    addMessage(text, true);
    addTypingIndicator();
    chatbotAsk(text);
  }, 100);
};

// Real API call to chatbot
function chatbotAsk(message) {
  apiCall('/api/ai/chatbot/ask', 'POST', { message: message })
    .then(function(resp) {
      removeTypingIndicator();
      addMessage(resp.answer, false);
    })
    .catch(function(e) {
      removeTypingIndicator();
      addMessage('\u274C Error: ' + e.message, false);
    });
}


// ══════════════════════════════════════
//  FRAUD DETECTION SCREEN
// ══════════════════════════════════════

async function loadFraud() {
  await Promise.all([
    loadFraudDashboard(),
    loadFraudFlaggedBills(),
    loadFraudMonitor()
  ]);
}

// Fraud dashboard KPIs
async function loadFraudDashboard() {
  try {
    var data = await apiCall('/api/ai/fraud/dashboard?days=30');

    setElText('fraud-kpi-flagged', toMrNum(data.indicators.unusual_bill_amounts + data.indicators.high_discount_bills));
    var totalFlagged = data.indicators.unusual_bill_amounts + data.indicators.high_discount_bills;
    setElText('fraud-kpi-flagged-sub', totalFlagged > 0 ? '\u2191 Review needed' : '\u2705 All clear');

    setElText('fraud-kpi-risk', toMrNum(data.risk_score) + '/' + toMrNum(100));
    var riskColor = data.risk_level === 'HIGH' ? '#ef4444' : data.risk_level === 'MEDIUM' ? '#f59e0b' : '#22c55e';
    var riskEl = document.getElementById('fraud-kpi-risk');
    if (riskEl) riskEl.style.color = riskColor;
    setElText('fraud-kpi-risk-sub', data.risk_level + ' risk');

    setElText('fraud-kpi-total', toMrNum(data.total_bills));
    setElText('fraud-kpi-total-sub', 'Last 30 days');

    setElText('fraud-kpi-cash', toMrNum(data.indicators.cash_percentage) + '%');
    setElText('fraud-kpi-cash-sub', data.indicators.cash_percentage > 60 ? '\u26A0 Cash heavy' : 'Balanced mix');

    // Banner
    var bannerTitle = document.getElementById('fraud-banner-title');
    var bannerSub = document.getElementById('fraud-banner-sub');
    if (bannerTitle) {
      if (totalFlagged > 0) {
        bannerTitle.textContent = 'AI Fraud Monitor \u2014 ' + toMrNum(totalFlagged) + ' Suspicious Transactions Detected';
        bannerSub.textContent = 'Risk score: ' + toMrNum(data.risk_score) + '/' + toMrNum(100) + '. ' + (data.recommendations.filter(Boolean).join(' · ') || 'Review flagged items below.');
      } else {
        bannerTitle.textContent = 'AI Fraud Monitor \u2014 All Clear \u2705';
        bannerTitle.style.color = '#166534';
        bannerSub.textContent = 'No suspicious transactions detected. Risk score: ' + toMrNum(data.risk_score) + '/' + toMrNum(100);
        bannerSub.style.color = '#22c55e';
      }
    }

  } catch (e) {
    setElText('fraud-kpi-flagged', '\u2014');
    setElText('fraud-kpi-risk', '\u2014');
    console.warn('Fraud dashboard failed:', e.message);
  }
}

// Flagged bills table
async function loadFraudFlaggedBills() {
  var tbody = document.getElementById('fraud-flagged-tbody');
  if (!tbody) return;

  try {
    var data = await apiCall('/api/ai/fraud/unusual-bills?days=30&threshold=2.0');
    var bills = data.suspicious_bills || [];

    if (!bills.length) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--accent3);padding:16px;">\u2705 No suspicious bills found — all transactions normal!</td></tr>';
      return;
    }

    var html = '';
    bills.forEach(function(b) {
      var riskBadge = b.risk_level === 'HIGH'
        ? '<span style="background:#fee2e2;color:#ef4444;padding:3px 10px;border-radius:20px;font-weight:700;font-size:12px;">' + toMrNum(Math.abs(b.z_score)) + ' Z</span>'
        : '<span style="background:#fef3c7;color:#d97706;padding:3px 10px;border-radius:20px;font-weight:700;font-size:12px;">' + toMrNum(Math.abs(b.z_score)) + ' Z</span>';

      var riskColor = b.risk_level === 'HIGH' ? '#ef4444' : 'var(--gold)';
      var bgStyle = b.risk_level === 'HIGH' ? 'background:rgba(255,220,220,0.3);' : 'background:rgba(255,237,200,0.3);';
      var dateStr = b.date ? b.date.substring(0, 10) : '\u2014';

      html += '<tr style="' + bgStyle + '">'
        + '<td><span class="order-id">#' + escHtml(b.invoice_number) + '</span></td>'
        + '<td>' + dateStr + '</td>'
        + '<td>\u2014</td>'
        + '<td class="mono" style="color:' + riskColor + ';">\u20B9' + toMrNum(fmtAmt(b.amount)) + '</td>'
        + '<td><span class="badge badge-' + (b.risk_level === 'HIGH' ? 'red' : 'orange') + '">' + escHtml(b.payment_mode || 'Bill') + '</span></td>'
        + '<td style="font-size:11px;color:' + riskColor + ';">' + escHtml(b.reason) + '</td>'
        + '<td>' + riskBadge + '</td>'
        + '<td><button class="po-btn" style="background:' + riskColor + ';" onclick="toast(&quot;Bill #' + escHtml(b.invoice_number) + ' noted for review&quot;, &quot;info&quot;)">Review</button></td>'
        + '</tr>';
    });

    tbody.innerHTML = html;
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="8" style="color:var(--warn);padding:16px;">' + escHtml(e.message) + '</td></tr>';
  }
}

// All transactions monitor from recent bills
async function loadFraudMonitor() {
  var tbody = document.getElementById('fraud-monitor-tbody');
  if (!tbody) return;

  try {
    var orders = await apiCall('/api/orders/?limit=10');

    if (!orders || !orders.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:16px;">No recent transactions</td></tr>';
      return;
    }

    // Get unusual bills to mark flagged ones
    var flaggedInvoices = {};
    try {
      var flagData = await apiCall('/api/ai/fraud/unusual-bills?days=30&threshold=2.0');
      (flagData.suspicious_bills || []).forEach(function(b) {
        flaggedInvoices[b.invoice_number] = b;
      });
    } catch(e) {}

    var html = '';
    orders.forEach(function(o, i) {
      var dateStr = o.created_at ? o.created_at.substring(0, 10) : '\u2014';
      var isFlagged = flaggedInvoices[o.invoice_number];
      var statusBadge, scoreColor, score;

      if (isFlagged) {
        statusBadge = '<span class="badge badge-red">\uD83D\uDEA8 Flagged</span>';
        scoreColor = isFlagged.risk_level === 'HIGH' ? '#ef4444' : 'var(--gold)';
        score = Math.abs(isFlagged.z_score);
      } else {
        statusBadge = '<span class="badge badge-green">\u2705 Cleared</span>';
        scoreColor = 'var(--accent3)';
        score = '\u2014';
      }

      var bgStyle = isFlagged ? 'background:rgba(255,220,220,0.2);' : (i % 2 === 0 ? 'background:rgba(240,250,255,0.4);' : '');

      html += '<tr style="' + bgStyle + '">'
        + '<td><span class="order-id">#' + escHtml(o.invoice_number) + '</span></td>'
        + '<td>' + dateStr + '</td>'
        + '<td>' + (o.dealer_id || 'Walk-in') + '</td>'
        + '<td class="mono">\u20B9' + toMrNum(fmtAmt(o.grand_total)) + '</td>'
        + '<td>' + escHtml(o.payment_mode || '\u2014').toUpperCase() + '</td>'
        + '<td>' + statusBadge + '</td>'
        + '<td style="color:' + scoreColor + ';font-weight:700;">' + score + '</td>'
        + '</tr>';
    });

    tbody.innerHTML = html;
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="7" style="color:var(--warn);padding:16px;">' + escHtml(e.message) + '</td></tr>';
  }
}


// ══════════════════════════════════════
//  HOOK INTO showScreen
// ══════════════════════════════════════

var _origShowScreenAI = window.showScreen;
window.showScreen = function(id) {
  if (_origShowScreenAI) _origShowScreenAI(id);
  if (id === 'ai-forecast') loadForecast();
  if (id === 'fraud') loadFraud();
  // chatbot doesn't need data load — it's interactive
};
