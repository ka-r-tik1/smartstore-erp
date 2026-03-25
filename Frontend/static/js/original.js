// Global showScreen — must be available before other JS files load
window.showScreen = function(id) {
  document.querySelectorAll('.screen').forEach(function(s) { s.classList.remove('active'); });
  document.querySelectorAll('.nav-item').forEach(function(n) { n.classList.remove('active'); });
  var scr = document.getElementById('screen-' + id);
  if (scr) scr.classList.add('active');
  var titles = {
    dashboard: 'Dashboard Overview', inventory: 'Inventory Management',
    pos: 'POS Billing · Quick Sale', orders: 'Sales & Billing',
    purchase: 'Purchases · Supplier Ledger',
    expiry: 'Expiry & Wastage Tracker', schemes: 'Schemes & Offers',
    dealers: 'Udhaar Ledger · Customer Credit', payments: 'Payment Ledger · UPI & Cash',
    'ai-forecast': 'AI Demand Forecast · Seasonal Trends', chatbot: 'AI Chat Assistant',
    fraud: 'Fraud Sentry · Transaction Monitor',
    'invoice-auto': 'GST e-Invoice · OCR Auto-Fill',
    'bank-recon': 'MSME 45-Day Timer · Compliance',
    datahub: 'Data Hub · Reports & Analytics',
    staff: 'Staff Advances · Salary Ledger',
    'india-law': 'India Law & Compliance',
    barcode: 'Barcode Scanner · POS'
  };
  var breadcrumbs = {
    dashboard: 'Dashboard', inventory: 'Inventory', pos: 'POS Billing',
    orders: 'Sales Orders', purchase: 'Purchases', dealers: 'Dealers',
    expiry: 'Expiry / Wastage', schemes: 'Schemes / Offers',
    payments: 'Payments', 'ai-forecast': 'AI Forecast', chatbot: 'AI Chat',
    fraud: 'Fraud Sentry', 'invoice-auto': 'GST e-Invoice',
    'bank-recon': 'Bank Recon', datahub: 'Data Hub', staff: 'Staff',
    'india-law': 'Compliance', barcode: 'Barcode / POS'
  };
  var pt = document.getElementById('page-title');
  if (pt) pt.textContent = titles[id] || id;
  var bc = document.getElementById('breadcrumb-current');
  if (bc) bc.textContent = breadcrumbs[id] || id;
  document.querySelectorAll('.nav-item').forEach(function(n) {
    if (n.getAttribute('onclick') && n.getAttribute('onclick').includes("'" + id + "'")) n.classList.add('active');
  });
};

  // Live clock
  function updateClock() {
    const now = new Date();
    const days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
    const months = ['जाने','फेब्रु','मार्च','एप्रि','मे','जून','जुलै','ऑग','सप्टे','ऑक्टो','नोव्हे','डिसे'];
    const day = days[now.getDay()];
    const date = now.getDate();
    const month = months[now.getMonth()];
    const year = now.getFullYear();
    const h = String(now.getHours()).padStart(2,'0');
    const m = String(now.getMinutes()).padStart(2,'0');
    const s = String(now.getSeconds()).padStart(2,'0');
    const dateEl = document.getElementById('live-date');
    const timeEl = document.getElementById('live-time');
    if(dateEl) dateEl.textContent = `${day}, ${date} ${month} ${year}`;
    if(timeEl) timeEl.textContent = `🕐 ${h}:${m}:${s}`;
  }
  updateClock();
  setInterval(updateClock, 1000);

  // ── FORECAST PIE CHART ──
  var pieData = [
    { label: 'अमूल बटर 500g', pct: 42, color: '#7c3aed' },
    { label: 'टाटा मीठ 1kg', pct: 34, color: '#e53e3e' },
    { label: 'मॅगी नूडल्स 70g', pct: 24, color: '#d97706' },
  ];
  const monthProducts = {
    'मार्च': [{ n:'अमूल बटर 500g', p:42 },{ n:'टाटा मीठ 1kg', p:34 },{ n:'मॅगी नूडल्स 70g', p:24 }],
    'एप्रि': [{ n:'अमूल बटर 500g', p:38 },{ n:'टाटा मीठ 1kg', p:36 },{ n:'मॅगी नूडल्स 70g', p:26 }],
    'मे': [{ n:'अमूल बटर 500g', p:44 },{ n:'टाटा मीठ 1kg', p:30 },{ n:'मॅगी नूडल्स 70g', p:26 }],
    'जून': [{ n:'टाटा मीठ 1kg', p:40 },{ n:'अमूल बटर 500g', p:35 },{ n:'मॅगी नूडल्स 70g', p:25 }],
    'जुलै': [{ n:'मॅगी नूडल्स 70g', p:38 },{ n:'अमूल बटर 500g', p:34 },{ n:'टाटा मीठ 1kg', p:28 }],
    'ऑग': [{ n:'मॅगी नूडल्स 70g', p:40 },{ n:'अमूल बटर 500g', p:32 },{ n:'टाटा मीठ 1kg', p:28 }],
  };
  const pieColors = ['#7c3aed','#e53e3e','#d97706','#0f9e56','#3b82f6'];

  let hoveredSlice = -1;

  function drawPie(hovered = -1) {
    const canvas = document.getElementById('forecastPie');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const cx = 70, cy = 70, r = 55, inner = 30;
    ctx.clearRect(0, 0, 140, 140);
    let startAngle = -Math.PI / 2;
    pieData.forEach((d, i) => {
      const slice = (d.pct / 100) * 2 * Math.PI;
      const isHov = hovered === i;
      const offset = isHov ? 7 : 0;
      const midAngle = startAngle + slice / 2;
      const ox = Math.cos(midAngle) * offset;
      const oy = Math.sin(midAngle) * offset;
      ctx.beginPath();
      ctx.moveTo(cx + ox, cy + oy);
      ctx.arc(cx + ox, cy + oy, isHov ? r + 5 : r, startAngle, startAngle + slice);
      ctx.arc(cx + ox, cy + oy, inner, startAngle + slice, startAngle, true);
      ctx.closePath();
      if (isHov) {
        ctx.shadowColor = d.color;
        ctx.shadowBlur = 16;
      }
      ctx.fillStyle = d.color;
      ctx.globalAlpha = isHov ? 1 : 0.88;
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.globalAlpha = 1;
      startAngle += slice;
    });
    // White inner circle
    ctx.beginPath();
    ctx.arc(cx, cy, inner - 1, 0, 2 * Math.PI);
    ctx.fillStyle = 'white';
    ctx.fill();
    // Center text
    ctx.fillStyle = '#2d3748';
    ctx.font = '600 10px Mukta, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    if (hovered >= 0) {
      ctx.fillStyle = pieData[hovered].color;
      ctx.font = 'bold 13px Mukta, sans-serif';
      ctx.fillText(pieData[hovered].pct + '%', cx, cy - 5);
      ctx.font = '600 8px Mukta, sans-serif';
      ctx.fillStyle = '#64748b';
      ctx.fillText(pieData[hovered].label.split(' ')[0], cx, cy + 8);
    } else {
      ctx.fillStyle = '#4a5568';
      ctx.fillText('Product', cx, cy - 5);
      ctx.fillText('Mix', cx, cy + 8);
    }
  }

  function buildPieLegend() {
    const legend = document.getElementById('pie-legend');
    if (!legend) return;
    legend.innerHTML = pieData.map((d,i) => `
      <div style="display:flex;align-items:center;gap:8px;padding:5px 8px;border-radius:8px;
        background:rgba(255,255,255,0.6);border:1px solid rgba(255,255,255,0.8);
        backdrop-filter:blur(8px);transition:all 0.2s;cursor:default;"
        onmouseenter="this.style.transform='translateX(3px)';this.style.boxShadow='0 2px 10px ${d.color}33'"
        onmouseleave="this.style.transform='';this.style.boxShadow=''">
        <div style="width:10px;height:10px;border-radius:3px;background:${d.color};flex-shrink:0;
          box-shadow:0 1px 6px ${d.color}66;"></div>
        <span style="font-family:'Mukta',sans-serif;font-size:11px;font-weight:600;color:#2d3748;flex:1;">${d.label}</span>
        <span style="font-family:'Mukta',sans-serif;font-size:10px;color:${d.color};font-weight:700;">${d.pct}%</span>
      </div>`).join('');
  }

  function showMonthDetail(month, demandPct) {
    const panel = document.getElementById('month-detail-panel');
    const nameEl = document.getElementById('detail-month-name');
    const pctEl = document.getElementById('detail-demand-pct');
    const prodsEl = document.getElementById('detail-products');
    const products = monthProducts[month] || [];
    nameEl.textContent = month;
    pctEl.textContent = demandPct + '% demand';
    prodsEl.innerHTML = products.map((p,i) => `
      <div style="display:flex;flex-direction:column;gap:3px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span style="font-family:'Mukta',sans-serif;font-size:10px;font-weight:600;color:#2d3748;">${p.n}</span>
          <span style="font-family:'Mukta',sans-serif;font-size:9px;font-weight:700;color:${pieColors[i]};">${p.p}%</span>
        </div>
        <div style="height:4px;background:rgba(0,0,0,0.06);border-radius:4px;overflow:hidden;">
          <div style="height:100%;width:${p.p}%;background:${pieColors[i]};border-radius:4px;
            box-shadow:0 0 6px ${pieColors[i]}88;transition:width 0.5s ease;"></div>
        </div>
      </div>`).join('');
    panel.style.width = '200px';
    panel.style.borderLeft = '1px solid var(--border)';
  }

  window.addEventListener('load', () => { drawPie(); buildPieLegend(); });

  // Risk banner SVG border trace
  function initRiskBorder() {
    const banner = document.getElementById('risk-banner');
    const svg = document.getElementById('risk-border-svg');
    const rect = document.getElementById('risk-border-rect');
    if (!banner || !svg || !rect) return;
    const w = banner.offsetWidth;
    const h = banner.offsetHeight;
    svg.setAttribute('width', w + 2);
    svg.setAttribute('height', h + 2);
    rect.setAttribute('width', w);
    rect.setAttribute('height', h);
    const perimeter = 2 * (w + h);
    rect.style.setProperty('--perimeter', perimeter + 'px');
    svg.style.setProperty('--perimeter', perimeter + 'px');
  }
  window.addEventListener('load', initRiskBorder);
  window.addEventListener('resize', initRiskBorder);

  // Sidebar toggle — X when open, burger when closed
  var sidebarOpen = true;
  function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const bl1 = document.getElementById('bl1');
    const bl2 = document.getElementById('bl2');
    const bl3 = document.getElementById('bl3');
    const isMobile = window.innerWidth <= 768;
    sidebarOpen = !sidebarOpen;
    if (sidebarOpen) {
      sidebar.classList.remove('collapsed');
      if (isMobile && overlay) overlay.classList.add('active');
      bl1.style.transform = 'translateY(7px) rotate(45deg)';
      bl2.style.opacity = '0'; bl2.style.transform = 'scaleX(0)';
      bl3.style.transform = 'translateY(-7px) rotate(-45deg)';
    } else {
      sidebar.classList.add('collapsed');
      if (overlay) overlay.classList.remove('active');
      bl1.style.transform = '';
      bl2.style.opacity = '1'; bl2.style.transform = '';
      bl3.style.transform = '';
    }
  }
  function closeSidebarMobile() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const bl1 = document.getElementById('bl1');
    const bl2 = document.getElementById('bl2');
    const bl3 = document.getElementById('bl3');
    if (window.innerWidth <= 768) {
      sidebarOpen = false;
      sidebar.classList.add('collapsed');
      if (overlay) overlay.classList.remove('active');
      bl1.style.transform = '';
      bl2.style.opacity = '1'; bl2.style.transform = '';
      bl3.style.transform = '';
    }
  }
  // Init sidebar state on load
  window.addEventListener('DOMContentLoaded', () => {
    const bl1 = document.getElementById('bl1');
    const bl2 = document.getElementById('bl2');
    const bl3 = document.getElementById('bl3');
    const sidebar = document.querySelector('.sidebar');
    if (window.innerWidth <= 768) {
      // Mobile: start collapsed (hidden), show burger lines
      if (sidebar) sidebar.classList.add('collapsed');
      sidebarOpen = false;
      if (bl1) bl1.style.transform = '';
      if (bl2) { bl2.style.opacity = '1'; bl2.style.transform = ''; }
      if (bl3) bl3.style.transform = '';
    } else {
      // Desktop: start open, show X
      if (bl1) bl1.style.transform = 'translateY(7px) rotate(45deg)';
      if (bl2) { bl2.style.opacity = '0'; bl2.style.transform = 'scaleX(0)'; }
      if (bl3) bl3.style.transform = 'translateY(-7px) rotate(-45deg)';
    }
  });

  function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const scr = document.getElementById('screen-' + id);
    if (scr) scr.classList.add('active');
    const titles = {
      dashboard: 'Dashboard Overview', inventory: 'Inventory Management',
      pos: 'POS Billing · Quick Sale', orders: 'Sales & Billing',
      purchase: 'Purchases · Supplier Ledger',
      expiry: 'Expiry & Wastage Tracker', schemes: 'Schemes & Offers',
      dealers: 'Udhaar Ledger · Customer Credit', payments: 'Payment Ledger · UPI & Cash',
      'ai-forecast': 'AI Demand Forecast · Seasonal Trends', chatbot: 'AI Chat Assistant',
      fraud: 'Fraud Sentry · Transaction Monitor',
      'invoice-auto': 'GST e-Invoice · OCR Auto-Fill',
      'bank-recon': 'MSME 45-Day Timer · Compliance',
      datahub: 'Data Hub · Reports & Analytics',
      staff: 'Staff Advances · Salary Ledger',
      'india-law': 'India Law & Compliance',
      barcode: 'Barcode Scanner · POS'
    };
    const breadcrumbs = {
      dashboard: 'Dashboard', inventory: 'Inventory', pos: 'POS Billing',
      orders: 'Sales Orders', purchase: 'Purchases', dealers: 'Dealers',
      expiry: 'Expiry / Wastage', schemes: 'Schemes / Offers',
      payments: 'Payments', 'ai-forecast': 'AI Forecast', chatbot: 'AI Chat',
      fraud: 'Fraud Sentry', 'invoice-auto': 'GST e-Invoice',
      'bank-recon': 'Bank Recon', datahub: 'Data Hub', staff: 'Staff',
      'india-law': 'Compliance', barcode: 'Barcode / POS'
    };
    document.getElementById('page-title').textContent = titles[id] || id;
    const bc = document.getElementById('breadcrumb-current');
    if (bc) bc.textContent = breadcrumbs[id] || id;
    document.querySelectorAll('.nav-item').forEach(n => {
      if (n.getAttribute('onclick') && n.getAttribute('onclick').includes("'" + id + "'")) n.classList.add('active');
    });
    if (id === 'ai-forecast') setTimeout(() => { drawPie(); buildPieLegend(); }, 30);
  }

  function sendPO(btnId, item) {
    const btn = document.getElementById(btnId);
    if(!btn) return;
    btn.textContent = '✅ PO पाठवले!';
    btn.classList.add('sent'); btn.disabled = true;
    toast('📦 PO पाठवले: ' + item.split(' - ')[0].substring(0,28) + '…', 'success');
    setTimeout(() => { btn.disabled = false; btn.classList.remove('sent'); btn.textContent = '⚡ खरेदी आदेश पाठवा'; }, 4000);
  }

  function sendAllReminders() {
    const overlay = document.getElementById('reminder-overlay');
    const countEl = document.getElementById('reminder-count-num');
    const bar = document.getElementById('reminder-bar');
    overlay.classList.add('show');
    let count = 3;
    countEl.textContent = count;
    bar.style.width = '100%';
    const interval = setInterval(() => {
      count--;
      countEl.textContent = count;
      bar.style.width = (count / 3 * 100) + '%';
      if (count <= 0) {
        clearInterval(interval);
        setTimeout(() => {
          overlay.classList.remove('show');
          // Show result
          const result = document.getElementById('reminder-result');
          if (result) { result.classList.add('show'); setTimeout(()=>result.classList.remove('show'), 5000); }
          toast('📲 3 reminders sent via WhatsApp!', 'success');
        }, 600);
      }
    }, 1000);
  }

  function sendReminder(cardId, btnId) {
    const btn = document.getElementById(btnId);
    if(!btn) return;
    const original = btn.textContent;
    btn.textContent = '✅ पाठवले!';
    btn.classList.add('sent'); btn.disabled = true;
    const card = document.getElementById(cardId);
    const name = card ? (card.querySelector('.dealer-name')?.textContent||'Dealer') : 'Dealer';
    toast('📲 WhatsApp reminder sent to ' + name.substring(0,22), 'success');
    setTimeout(() => {
      btn.textContent = original;
      btn.classList.remove('sent');
      btn.disabled = false;
    }, 3000);
  }

  function sendBulkPO() {
    const origTexts = {};
    ['bulk-po-btn', 'bulk-po-btn2'].forEach(id => {
      const b = document.getElementById(id);
      if (b) {
        origTexts[id] = b.textContent;
        b.textContent = '✅ All POs पाठवले!';
        b.style.background = '#0f9e56';
        b.disabled = true;
      }
    });
    setTimeout(() => {
      ['bulk-po-btn', 'bulk-po-btn2'].forEach(id => {
        const b = document.getElementById(id);
        if (b) {
          b.textContent = origTexts[id];
          b.style.background = '';
          b.disabled = false;
        }
      });
    }, 3000);
  }

  const chatResponses = {
    'what stock is low?': '🔴 Critical Stock Alert:\n\n• अमूल बटर 500g — 45 Pcs left (min: 200 Pcs) — 22% ⚠️ Critical\n• मॅगी नूडल्स 70g — 38 Pcs left (min: 100 Pcs) — 10% 🚨 Urgent\n• टाटा मीठ 1kg — 120 Pcs left (min: 300 Pcs) — 28% ⚠️ Low\n\nEstimated stockout: मॅगी नूडल्स 70g in 2 days!\n\nShall I raise POs to अमूल डिस्ट्रिब्युटर, HUL डिस्ट्रिब्युटर & Tata Consumer Distributor now?',
    "who hasn't paid?": '🚩 थकीत देयके:\n\n• मेट्रो होलसेल, पुणे — ₹3.24L — 45 दिवस ⚠️ High Risk\n• रामेश्वर ट्रेडर्स, सोलापूर — ₹1.82L — 32 दिवस 🟡 Watch\n• जनता किराणा — ₹62,400 — Invoice due 🔵 Due Soon\n\nTotal outstanding: ₹5.68L across 3 buyers.\nAvg delay trend: 12 → 31 → 45 दिवस (worsening)\n\nShall I send WhatsApp + Email reminders to all?',
    "today's sales?": '🛒 Today\'s Billing — 05 Mar 2026 | My Supermarket:\n\n• Footfall: 347 customers\n• Bills generated: 312 invoices\n• UPI collections: ₹1,22,400 ✅\n• Cash collections: ₹44,250\n• Card collections: ₹17,600\n\n💰 Total today: ₹1,84,250\n📦 Top seller today: अमूल बटर 500g (86 Pcs)\n\nAI Tip: Evening rush expected — restock checkout counter.',
    'best selling product?': '📊 Top Products — Last 90 Days:\n\n1. अमूल बटर 500g — 4,200 Pcs — ₹11.76L (42% of revenue)\n2. टाटा मीठ 1kg — 12,400 Pcs — ₹3.47L (34%)\n3. मॅगी नूडल्स 70g — 17,200 Pcs — ₹2.41L (24%)\n\nAI Tip: अमूल बटर 500g demand +18% this month. Ensure minimum 200 Pcs stock.',
    'send payment reminder to all थकीत dealers': '📲 Sending reminders now...\n\n✅ मेट्रो होलसेल — WhatsApp + Email sent\n✅ शर्मा किराणा — WhatsApp + Email sent\n✅ जनता किराणा — WhatsApp sent\n\nAll 3 buyers notified. I\'ll monitor responses and escalate if no reply in 48 hours. Payment ledger updated.',
    'generate daily report': '📊 Daily Report — 05 Mar 2026 | My Supermarket\n\n🛒 Footfall: 347 | Bills: 312\n💰 Revenue: ₹1,84,250\n• UPI: ₹1,22,400 | Cash: ₹44,250 | Card: ₹17,600\n📦 Items sold: 843 units across all categories\n🔴 Alerts: मॅगी नूडल्स 70g low stock — 2 days to stockout\n\nReport sent to your WhatsApp. PDF saved in ERP.',
    'which items need reorder?': '📦 Reorder Required Now:\n\n🚨 मॅगी नूडल्स 70g — 38 Pcs remaining — Order 500 Pcs from HUL डिस्ट्रिब्युटर (₹7,000) URGENT\n🔴 अमूल बटर 500g — 45 Pcs remaining — Order 300 Pcs from अमूल डिस्ट्रिब्युटर (₹84,000)\n🟡 टाटा मीठ 1kg — 120 Pcs remaining — Order 400 Pcs from Tata Consumer Distributor (₹11,200)\n\nTotal PO value: ₹1,02,200\n\nShall I send all 3 POs automatically?',
    'what should i focus on today?': '🎯 AI Priority List — Today, 05 Mar 2026:\n\n1. 🚨 Call मेट्रो होलसेल — ₹3.24L, 45 दिवस थकीत\n2. ⚡ Emergency PO — मॅगी नूडल्स 70g (stockout in 2 days!)\n3. 📅 Check expiry — 3 items near expiry this week\n4. 🎁 Activate weekend scheme — Maggi combo offer\n5. 📈 Evening restock — अमूल बटर 500g counter\n\nTarget revenue today: ₹2L\nGood morning! You\'ve got this 💪',
    'show revenue summary': '💰 Revenue Summary:\n\nToday: ₹1,84,250\nThis Month (Mar 2026): ₹38.4L\nLast Month (Feb 2026): ₹31.8L (+20.7%)\nThis Quarter: ₹94.6L\nThis Year: ₹1.24Cr\n\nTop wholesale buyer: रामेश्वर ट्रेडर्स — ₹12.4L\nTop product: अमूल बटर 500g — ₹11.76L (Q1)\n\nAI Forecast: May 2026 expected ₹52L+ due to summer + wedding season.',
    'show all pending orders': '🧾 Pending Wholesale Orders (6 active):\n\n• #SO-2247 — शर्मा किराणा — टाटा मीठ 1kg 600 Pcs — ₹16,800 — Due 08 Mar\n• #SO-2246 — रामेश्वर ट्रेडर्स — अमूल बटर 500g 200 Pcs — ₹56,000 — Due 10 Mar\n• #SO-2245 — सिटी होलसेल — मॅगी नूडल्स 70g 400 Pcs — ₹5,600 — Due 07 Mar\n• #SO-2244 — जनता किराणा — अमूल बटर 500g 150 Pcs — ₹42,000 — ⚠️ देयक थकीत\n• #SO-2242 — शर्मा किराणा — टाटा मीठ 1kg 800 Pcs — ₹22,400 — ⚠️ देयक थकीत\n• #SO-2241 — मेट्रो होलसेल — मॅगी नूडल्स 70g 200 Pcs — ₹2,800 — प्रक्रियेत\n\nTotal pending value: ₹1,45,600',
    'show buying summary': '🛒 Buying Summary (Purchases):\n\nThis Month:\n• अमूल डिस्ट्रिब्युटर — अमूल बटर 500g 500 Pcs — ₹1,40,000\n• Tata Consumer Distributor — टाटा मीठ 1kg 1200 Pcs — ₹33,600\n• Nestlé Distributor — मॅगी नूडल्स 70g 1000 Pcs — ₹14,000\n\nTotal purchased this month: ₹1,87,600\nप्रलंबित खरेदी · Pending: ₹1,02,200 (reorder)\nTop supplier: अमूल डिस्ट्रिब्युटर — ₹6.8L this year\n\nAI Tip: Stock up on beverages before April summer season.',
    'show selling summary': '💰 Selling Summary:\n\nThis Month Sales:\n• अमूल बटर 500g — 1,400 Pcs — ₹3.92L\n• टाटा मीठ 1kg — 3,200 Pcs — ₹89,600\n• मॅगी नूडल्स 70g — 5,100 Pcs — ₹71,400\n\nTotal this month: ₹38.4L\nWalk-in customers: 8,900 | Wholesale buyers: 12\nNew orders this week: 6\nAvg bill value: ₹589\n\nBest performing day: Saturday (₹2.8L)',
    'show inventory': '📦 Full Inventory Status:\n\n🔴 Critical:\n• मॅगी नूडल्स 70g — 38 Pcs (10%) — 2 days to stockout\n• अमूल बटर 500g — 45 Pcs (22%) — 3 days to stockout\n\n🟡 Low:\n• टाटा मीठ 1kg — 120 Pcs (28%)\n\n✅ Adequate:\n• अमूल बटर 500g — 200 Pcs (68%)\n• टाटा मीठ 1kg — 300 Pcs (64%)\n• मॅगी नूडल्स 70g — 250 Pcs (72%)\n\nTotal SKUs: 3 | Critical: 2 | Low: 1 | OK: 0',
    'show dealers': '👥 Wholesale Buyer Overview (12 total):\n\n🔴 High Risk (2):\n• मेट्रो होलसेल, पुणे — ₹3.24L थकीत — 45 दिवस\n• (1 more flagged internally)\n\n🟡 Watch (1):\n• रामेश्वर ट्रेडर्स, सोलापूर — ₹1.82L थकीत — 32 दिवस\n\n✅ Good Standing (9):\n• शर्मा किराणा, पुणे — ₹0 — Always on-time\n• सिटी होलसेल, पुणे — ₹0 — Top buyer\n• जनता किराणा, नाशिक — ₹0 — Regular\n\nTotal credit extended: ₹84L\nTotal outstanding: ₹5.06L',
    'show finance': '📊 Finance Overview:\n\nRevenue (Mar 2026): ₹38.4L\nExpenses (Mar 2026): ₹18.2L\nGross Profit: ₹20.2L (52.6% margin)\n\nCash Flow:\n• Receivable: ₹18.6L (from wholesale buyers)\n• Payable: ₹6.1L (to suppliers)\n• Net: +₹12.5L\n\nGST collected: ₹3.84L\nPending invoices: 8 invoices — ₹7.8L\n\nAI Note: April–June summer season will boost beverage sales by est. +40%.',
    'expiring items': '📅 Near-Expiry Items:\n\n🔴 Expiring this week (3 items):\n• अमूल बटर 500g — Batch B-2203 — 12 Pcs — Exp: 07 Mar\n• मॅगी नूडल्स 70g — Batch M-1104 — 8 Pcs — Exp: 09 Mar\n• टाटा मीठ 1kg — Batch T-3301 — 22 Pcs — Exp: 10 Mar\n\n🟡 Expiring next week (5 items)\n\nFEFO compliance: 94% ✅\nWritten off this month: ₹1,240\n\nAction: Apply discount stickers on Batch B-2203 today.',
    'active offers': '🎁 Active Schemes (3):\n\n• Buy 2 मॅगी 70g, Get 1 Free — Active till 15 Mar ✅\n• अमूल बटर ₹20 off on ₹500+ bill — Active till 31 Mar\n• Weekend Combo: Butter + Maggi + Salt = ₹299 — Sat/Sun only\n\nRedeemed today: 47 times | Revenue impact: -₹940\nBest performer: Maggi BOGO — 38 redemptions',
    'daily collection': '💰 Today\'s Collection — 05 Mar 2026:\n\n💳 UPI (PhonePe/GPay): ₹1,22,400 (66%)\n💵 Cash: ₹44,250 (24%)\n🏦 Card: ₹17,600 (10%)\n\nTotal: ₹1,84,250\nBills: 312 invoices\nAvg bill value: ₹590\n\nPeak hour: 6pm–8pm (94 bills)\nShift cashier: Ravi — 156 bills ✅',
    'hello': 'नमस्ते! 👋 How can I help you today? I can answer questions about your stock, sales, expiry, schemes, billing, wholesale buyers, payments, forecasts — anything in your My Supermarket ERP!',
    'hi': 'Hi there! 👋 What would you like to know about your store today?',
    'help': '🤖 I can help you with:\n\n🛒 Sales & Billing — today\'s collection, footfall, POS\n📦 Stock — levels, reorder alerts, supplier POs\n📅 Expiry — near-expiry items, FEFO compliance\n🎁 Schemes — active offers, redemptions\n👥 Buyers — wholesale payments, udhaar, reminders\n💰 Finance — revenue, expenses, cash flow\n📈 Forecast — demand prediction, seasonal trends\n\nJust type your question naturally!\n\nभाषा · Languages: English, हिन्दी, मराठी, Hinglish — सब समझता हूँ! 🇮🇳',

    // Hindi
    'stock kya hai': '📦 स्टॉक स्थिति:\n\n🔴 क्रिटिकल:\n• मॅगी नूडल्स 70g — 38 Pcs (10%) — 2 दिन में खत्म 🚨\n• अमूल बटर 500g — 45 Pcs (22%) — 3 दिन में खत्म\n\n🟡 कम स्टॉक:\n• टाटा मीठ 1kg — 120 Pcs (28%)\n\nक्या मैं अभी PO भेजूं?',
    'kaun nahi bhar raha': '🚩 बकाया भुगतान:\n\n• मेट्रो होलसेल, पुणे — ₹3.24L — 45 दिन से बकाया ⚠️\n• रामेश्वर ट्रेडर्स, सोलापूर — ₹1.82L — 32 दिन 🟡\n• जनता किराणा — ₹62,400 — इनवॉइस देय 🔵\n\nकुल बकाया: ₹5.68L\nक्या मैं सभी को रिमाइंडर भेजूं?',
    'aaj ki bikri': '🛒 आज की बिक्री — My Supermarket:\n\n• Footfall: 347 ग्राहक\n• Bills: 312 invoices\n• UPI: ₹1,22,400 ✅\n• Cash: ₹44,250\n• Card: ₹17,600\n\n💰 कुल: ₹1,84,250\nटॉप प्रोडक्ट: अमूल बटर 500g (86 Pcs)',
    'revenue batao': '💰 राजस्व सारांश:\n\nआज: ₹1,84,250\nइस महीने: ₹38.4L\nपिछला महीना: ₹31.8L (+20.7%)\nइस तिमाही: ₹94.6L\n\nटॉप बायर: रामेश्वर ट्रेडर्स — ₹12.4L\nटॉप प्रोडक्ट: अमूल बटर 500g — ₹11.76L\n\nAI अनुमान: मई में ₹52L+ की उम्मीद',
    'kya karna chahiye aaj': '🎯 आज की AI प्राथमिकता सूची:\n\n1. 🚨 मेट्रो होलसेल को कॉल करें (₹3.24L, 45 दिन)\n2. ⚡ मॅगी नूडल्स 70g का PO भेजें (2 दिन में खत्म!)\n3. 📅 Batch B-2203 पर Discount sticker लगाएं\n4. 🎁 Weekend Combo scheme activate करें\n5. 📦 शाम को अमूल बटर 500g restock करें\n\nलक्ष्य: आज ₹2L! 💪',
    'mujhe help chahiye': '🤖 मैं इन चीज़ों में मदद कर सकता हूँ:\n\n🛒 Billing — आज की बिक्री, collection\n📦 स्टॉक — स्तर, अलर्ट, PO\n📅 Expiry — नजदीकी एक्सपायरी\n🎁 Schemes — ऑफर, redemption\n👥 Buyers — payment, udhaar, reminder\n💰 वित्त — आय, व्यय, नकदी प्रवाह\n\nहिन्दी, मराठी, Hinglish — सब समझता हूँ! 🇮🇳',

    // Marathi (Romanized)
    'stock sanga': '📦 स्टॉक स्थिती:\n\n🔴 गंभीर:\n• मॅगी नूडल्स 70g — 38 Pcs (10%) — 2 दिवसात संपेल 🚨\n• अमूल बटर 500g — 45 Pcs (22%) — 3 दिवसात संपेल\n\n🟡 कमी स्टॉक:\n• टाटा मीठ 1kg — 120 Pcs (28%)\n\nPO पाठवू का आता?',
    'kunala dili nahi': '🚩 थकीत पेमेंट:\n\n• मेट्रो होलसेल, पुणे — ₹3.24L — 45 दिवस ⚠️\n• रामेश्वर ट्रेडर्स, सोलापूर — ₹1.82L — 32 दिवस\n• जनता किराणा — ₹62,400 — इनव्हॉइस देय\n\nसर्वांना रिमाइंडर पाठवू का?',
    'aajchi vikri': '🛒 आजची विक्री — My Supermarket:\n\n• Footfall: 347 ग्राहक\n• Bills: 312\n• UPI: ₹1,22,400 ✅\n• Cash: ₹44,250\n\n💰 एकूण: ₹1,84,250\nटॉप प्रोडक्ट: अमूल बटर 500g (86 Pcs)',
    'mahsul sanga': '💰 महसूल सारांश:\n\nआज: ₹1,84,250\nया महिन्यात: ₹38.4L\nमागील महिना: ₹31.8L (+20.7%)\n\nटॉप बायर: रामेश्वर ट्रेडर्स — ₹12.4L\nAI अंदाज: मे मध्ये ₹52L+',

    // Marathi (Devanagari keyboard)
    'स्टॉक सांगा': '📦 स्टॉक स्थिती:\n\n🔴 गंभीर:\n• मॅगी नूडल्स 70g — 38 Pcs (10%) — 2 दिवसात संपेल 🚨\n• अमूल बटर 500g — 45 Pcs (22%) — 3 दिवसात संपेल\n\n🟡 कमी स्टॉक:\n• टाटा मीठ 1kg — 120 Pcs (28%)\n\nPO पाठवू का आता?',
    'कुणाला दिली नाही': '🚩 थकीत पेमेंट:\n\n• मेट्रो होलसेल, पुणे — ₹3.24L — 45 दिवस ⚠️\n• रामेश्वर ट्रेडर्स, सोलापूर — ₹1.82L — 32 दिवस\n• जनता किराणा — ₹62,400 — इनव्हॉइस देय\n\nसर्वांना रिमाइंडर पाठवू का?',
    'आजची विक्री': '🛒 आजची विक्री — My Supermarket:\n\n• Footfall: 347 ग्राहक\n• Bills: 312\n• UPI: ₹1,22,400 ✅\n• Cash: ₹44,250\n\n💰 एकूण: ₹1,84,250\nटॉप प्रोडक्ट: अमूल बटर 500g (86 Pcs)',
    'महसूल सांगा': '💰 महसूल सारांश:\n\nआज: ₹1,84,250\nया महिन्यात: ₹38.4L\nमागील महिना: ₹31.8L (+20.7%)\n\nटॉप बायर: रामेश्वर ट्रेडर्स — ₹12.4L\nAI अंदाज: मे मध्ये ₹52L+',
    'आज काय करू': '🎯 आजच्या प्राधान्य यादी:\n\n1. 🚨 मेट्रो होलसेल ला कॉल करा (₹3.24L, 45 दिवस)\n2. ⚡ मॅगी नूडल्स 70g चा PO पाठवा (2 दिवसात संपेल!)\n3. 📅 Batch B-2203 वर सवलत स्टिकर लावा\n4. 🎁 Weekend Combo scheme चालू करा\n5. 📦 संध्याकाळी अमूल बटर 500g restock करा\n\nलक्ष्य: आज ₹2L! 💪',
    'मला मदत हवी': '🤖 मी या गोष्टींमध्ये मदत करू शकतो:\n\n🛒 बिलिंग — आजची विक्री, collection\n📦 स्टॉक — पातळी, अलर्ट, PO\n📅 एक्स्पायरी — जवळची एक्स्पायरी\n🎁 योजना — ऑफर, redemption\n👥 विक्रेते — पेमेंट, उधारी, रिमाइंडर\n💰 वित्त — आय, खर्च, रोख प्रवाह\n\nमराठी, हिंदी, English — सर्व समजतं! 🇮🇳',
    'एक्स्पायरी': '📅 एक्स्पायरी अलर्ट:\n\n🔴 या आठवड्यात संपणारे (3):\n• अमूल बटर 500g — Batch B-2203 — 12 Pcs — Exp: 07 Mar\n• मॅगी नूडल्स 70g — Batch M-1104 — 8 Pcs — Exp: 09 Mar\n• टाटा मीठ 1kg — Batch T-3301 — 22 Pcs — Exp: 10 Mar\n\n🟡 पुढील आठवड्यात (5 items)\n\nFEFO अनुपालन: 94% ✅\nया महिन्यात Write-off: ₹1,240\n\nकृती: Batch B-2203 वर आज सवलत स्टिकर लावा.',
    'योजना': '🎁 चालू योजना (3):\n\n• 2 मॅगी 70g घ्या, 1 मोफत — 15 Mar पर्यंत ✅\n• अमूल बटर ₹500+ बिलावर ₹20 सूट — 31 Mar पर्यंत\n• Weekend Combo: बटर + मॅगी + मीठ = ₹299 — शनि/रवि\n\nआज वापरलेले: 47 वेळा | Revenue impact: -₹940',
    'विक्रेते': '👥 विक्रेते सारांश (12 एकूण):\n\n🔴 उच्च जोखीम (2):\n• मेट्रो होलसेल, पुणे — ₹3.24L थकीत — 45 दिवस\n\n🟡 निरीक्षण (1):\n• रामेश्वर ट्रेडर्स, सोलापूर — ₹1.82L थकीत — 32 दिवस\n\n✅ चांगले (9):\n• शर्मा किराणा, पुणे — ₹0 — नेहमी वेळेवर\n\nएकूण थकीत: ₹5.06L',
    'खरेदी': '🛍️ खरेदी ऑर्डर — March 2026\n\nएकूण PO: 12 | मूल्य: ₹6.8L\n\n⏳ प्रलंबित:\n• #PUR-851 | अमूल डिस्ट्रिब्युटर | अमूल बटर 500g 500 Pcs | ₹1,40,000\n• #PUR-850 | Tata Consumer Distributor | टाटा मीठ 1kg 800 Pcs | ₹22,400\n• #PUR-849 | Nestlé Distributor | मॅगी नूडल्स 70g 200 Pcs | ₹2,800 ⚠️ तातडी!\n\n✅ प्राप्त:\n• #PUR-848 | अमूल डिस्ट्रिब्युटर | अमूल बटर 500g 300 Pcs | ₹84,000',
    'पेमेंट': '💳 पेमेंट स्थिती — March 2026\n\n📥 या महिन्यात मिळाले: ₹14.2L\n📤 एकूण थकीत: ₹18.6L\n\n🚨 OVERDUE:\n• मेट्रो होलसेल | ₹3,24,000 | 45 दिवस → Escalate!\n• शर्मा किराणा | ₹1,82,500 | 32 दिवस → स्मरण करा\n\n🕐 आगामी:\n• सिटी होलसेल | ₹95,000 | 20 Mar\n\nएकूण तातडी वसुली: ₹5,06,500',

    // Hinglish
    'stock low hai': '🔴 Stock Critical Alert:\n\n• मॅगी नूडल्स 70g — sirf 38 Pcs bacha (10%) — 2 din mein khatam! 🚨\n• अमूल बटर 500g — sirf 45 Pcs bacha (22%) — 3 din mein khatam\n• टाटा मीठ 1kg — 120 Pcs (28%) — thoda aur hai\n\nKya main abhi PO bhejun?',
    'kaun payment nahi kar raha': '🚩 थकीत देयके:\n\n• मेट्रो होलसेल — ₹3.24L — 45 din se nahi diya ⚠️\n• रामेश्वर ट्रेडर्स — ₹1.82L — 32 din 🟡\n• जनता किराणा — ₹62,400 — invoice due hai\n\nTotal: ₹5.68L baki hai\nReminder bhejun kya?',
    'aaj kya karna hai': '🎯 Aaj ki priority list:\n\n1. 🚨 मेट्रो होलसेल ko call karo (₹3.24L baki)\n2. ⚡ मॅगी नूडल्स 70g ka PO bhejo (2 din mein khatam!)\n3. 📅 Expiry batch B-2203 pe discount sticker lagao\n4. 🎁 Weekend Maggi combo scheme chalao\n\nTarget: ₹2L aaj! 💪',
    'aaj ki sale': '🛒 Aaj ki sale — My Supermarket:\n\nFootfall: 347 | Bills: 312\nUPI: ₹1,22,400 | Cash: ₹44,250 | Card: ₹17,600\n\n💰 Total: ₹1,84,250\nTop seller: अमूल बटर 500g — 86 Pcs\n\nPeak time: 6pm–8pm — counter pe stock ready rakho!',
    'kitna kamaaya': '💰 Revenue breakdown:\n\nAaj: ₹1,84,250\nIs mahine: ₹38.4L\nPichla mahina: ₹31.8L (+21%)\n\nBest seller: अमूल बटर 500g — ₹11.76L\nTop buyer: रामेश्वर ट्रेडर्स — ₹12.4L\n\nMay mein ₹52L+ hone wala hai — summer season aa raha hai! 🚀',
    'mujhe sab batao': '📊 ERP Full Summary:\n\n💰 Aaj ki kamaai: ₹1,84,250\n🛒 Footfall: 347 | Bills: 312\n📦 Low stock items: 3 (2 critical)\n📅 Expiring this week: 3 items\n🎁 Active schemes: 3\n👥 Overdue buyers: 2 (₹5.06L)\n🚨 Action needed: मॅगी नूडल्स 70g PO URGENT!\n\nSabse pehle Maggi ka PO bhejo — 2 din mein khatam!'
  };

  function addMessage(text, isUser) {
    const msgs = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'msg ' + (isUser ? 'user' : 'bot');
    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.style.whiteSpace = 'pre-line';
    bubble.textContent = text;
    div.appendChild(bubble);
    const time = document.createElement('div');
    time.className = 'msg-time';
    time.textContent = 'Just now';
    div.appendChild(time);
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function getResponse(text) {
    const q = text.toLowerCase().trim();
    const has = (...words) => words.some(w => q.includes(w));

    // ── GREETINGS ──
    if (['hi','hii','hello','hey','helo','hiya'].includes(q))
      return '👋 Hello! Main My Supermarket ka AI assistant hoon. Aaj revenue ₹1.84L hai, 312 bills hain aur 3 stock alerts hain. Kya jaanna chahte ho?';
    if (has('namaste','namaskar','नमस्ते','नमस्कार','kem cho','kasa ahes'))
      return 'नमस्ते! 🙏 Main aapka ERP AI hoon — har cheez jaanta hoon. Inventory, billing, payments, expiry, schemes — kuch bhi pucho!';
    if (has('hello','good morning','good evening','sup','wassup'))
      return '😊 Hey! My Supermarket AI ready hai. Aaj ₹1.84L revenue, 312 bills, 2 थकीत dealers. Kya help chahiye?';

    // ── TODAY / SUMMARY ──
    if (has('aaj','today','abhi','right now','abhi kya','aaj ka','आज','काय चालू'))
      return `📊 Aaj ka Business Summary — ' + new Date().toLocaleDateString('en-IN',{day:'numeric',month:'long',year:'numeric'}) + '\n\n💰 Today\'s Sales: ₹1,84,250 (↑18% vs last week)\n🛒 Footfall: 347 | Bills: 312 | Avg bill: ₹590\n💳 UPI: ₹1,22,400 | Cash: ₹44,250 | Card: ₹17,600\n🚨 Low Stock: 3 items critical (<b>मॅगी नूडल्स 70g</b> 10%, अमूल बटर 500g 22%)\n📅 Expiring this week: 3 batches — action needed\n💳 Outstanding from buyers: ₹5.06L (2 overdue)\n\nSabse urgent: मॅगी नूडल्स 70g sirf 2 din ka stock bacha hai!`;

    // ── REVENUE / FINANCE ──
    if (has('revenue','aaj kitna','today sale','today sell','aaj ki kamai','kitna hua','kitna aaya','आज कितना','कमाई','income','kitna kamaya','paise','महसूल','आज किती','उत्पन्न','कमाई किती'))
      return `💰 Aaj ka Revenue: ₹1,84,250\n↑ 18% last week se zyada\n\n📅 March 2026 Total Sales:\n• <b>अमूल बटर 500g</b> → ₹3,92,000 (1,400 Pcs)\n• <b>टाटा मीठ 1kg</b> → ₹89,600 (3,200 Pcs)\n• <b>मॅगी नूडल्स 70g</b> → ₹71,400 (5,100 Pcs)\n\n📦 Total Revenue (Mar 2026): ₹38.4L\n💸 GST Collected: ₹49,026\n💳 Received This Month: ₹14.2L\n⚠️ Outstanding from buyers: ₹5.06L abhi bhi baaki hai`;

    // ── ORDERS ──
    if (has('order','orders','sale order','so-','so2','dispatch','bikri','ऑर्डर','kaunse order','order list','new order','आदेश','विक्री आदेश','ऑर्डर यादी'))
      return `📋 Active Wholesale Orders (34 total):\n\n#SO-2247 | शर्मा किराणा | अमूल बटर 500g 200 Pcs | ₹56,000 | ✅ पाठवले\n#SO-2246 | सिटी होलसेल | टाटा मीठ 1kg 500 Pcs | ₹14,000 | 🔄 प्रक्रियेत\n#SO-2245 | मेट्रो होलसेल | मॅगी नूडल्स 70g 300 Pcs | ₹4,200 | 🔄 प्रक्रियेत\n#SO-2244 | जनता किराणा | अमूल बटर 500g 150 Pcs | ₹42,000 | 🚨 देयक थकीत\n#SO-2243 | रामेश्वर ट्रेडर्स | <b>मॅगी नूडल्स 70g</b> 400 Pcs | ₹5,600 | ✅ पाठवले\n#SO-2242 | शर्मा किराणा | टाटा मीठ 1kg 800 Pcs | ₹22,400 | 🚨 देयक थकीत\n\n⚠️ 2 orders payment due — ₹64,400 pending collection!`;

    if (has('pending order','payment due order','baki order','unpaid order'))
      return `🚨 देयक थकीत Orders:\n\n#SO-2244 | जनता किराणा | अमूल बटर 500g | ₹62,400 | Due: 01 Mar (7 दिवस थकीत)\n#SO-2242 | शर्मा किराणा | अमूल बटर 500g | ₹1,82,500 | Due: 26 Feb (11 दिवस थकीत)\n\nTotal pending from orders: ₹2,44,900\nस्मरणपत्र पाठवा किंवा /payments वर जा!`;

    if (has('dispatched','dispatch','deliver','bheja','delivered'))
      return `✅ Aaj 8 wholesale deliveries dispatched:\n\n#SO-2247 | शर्मा किराणा | अमूल बटर 500g 200 Pcs | ₹56,000\n#SO-2243 | रामेश्वर ट्रेडर्स | मॅगी नूडल्स 70g 400 Pcs | ₹5,600\n#SO-2238 | सिटी होलसेल | टाटा मीठ 1kg 400 Pcs | Delivered 03 Mar\n#SO-2235 | शर्मा किराणा | अमूल बटर 500g 300 Pcs | Delivered 02 Mar`;

    // ── STORE OPERATIONS ──
    if (has('billing','pos','sales today','aaj ki bikri','footfall','counter','cashier','bill','checkout','बिलिंग','काउंटर','बिल','विक्री आज'))
      return `🛒 Today\'s Store Operations — ' + new Date().toLocaleDateString('en-IN',{day:'numeric',month:'long',year:'numeric'}) + '\n\n📊 Stats: Footfall 347 | Bills 312 | Avg bill ₹590\n\n💰 COLLECTION:\n• UPI (PhonePe/GPay): ₹1,22,400 (66%) ✅\n• Cash: ₹44,250 (24%)\n• Card: ₹17,600 (10%)\n• Total: ₹1,84,250\n\n📦 TOP SELLERS TODAY:\n• अमूल बटर 500g — 86 Pcs\n• टाटा मीठ 1kg — 124 Pcs\n• मॅगी नूडल्स 70g — 97 Pcs\n\n🕐 PEAK HOURS:\n• 10am–12pm: 78 bills\n• 6pm–8pm: 94 bills (restock counter before evening rush!)`;

    if (has('expiry','expire','expiring','wastage','waste','nuke','fefo','batch','एक्स्पायरी','कालबाह्य','नासाडी','बॅच'))
      return `📅 Near-Expiry Alert — ' + new Date().toLocaleDateString('en-IN',{day:'numeric',month:'long',year:'numeric'}) + '\n\n🔴 EXPIRING THIS WEEK (3):\n• अमूल बटर 500g — Batch B-2203 | 12 Pcs | Exp: 07 Mar\n• मॅगी नूडल्स 70g — Batch M-1104 | 8 Pcs | Exp: 09 Mar\n• टाटा मीठ 1kg — Batch T-3301 | 22 Pcs | Exp: 10 Mar\n\n🟡 EXPIRING NEXT WEEK (5 items)\n\nFEFO Compliance: 94% ✅\nWritten off this month: ₹1,240\n\nAction: Apply discount stickers on Batch B-2203 today to sell before expiry!`;

    if (has('scheme','offer','discount','combo','bogo','buy get','promo','योजना','ऑफर','सवलत','सूट','कॉम्बो'))
      return `🎁 Active Schemes — ' + new Date().toLocaleDateString('en-IN',{day:'numeric',month:'long',year:'numeric'}) + '\n\n✅ ACTIVE (3):\n• Buy 2 मॅगी 70g, Get 1 Free — till 15 Mar\n• अमूल बटर ₹20 off on ₹500+ bill — till 31 Mar\n• Weekend Combo: Butter + Maggi + Salt = ₹299 — Sat/Sun only\n\nRedeemed today: 47 times | Revenue impact: -₹940\nBest scheme: Maggi BOGO — 38 redemptions\n\nAdd new scheme: /schemes screen pe jao!`;

    // ── INVENTORY / STOCK ──
    if (has('stock','inventory','maal','saman','kitna bacha','material','raw','warehouse','गोदाम','माल','साठा','स्टॉक','item','items'))
      return `📦 Stock Status — ' + new Date().toLocaleDateString('en-IN',{day:'numeric',month:'long',year:'numeric'}) + '\n\n🚨 CRITICAL:\n• मॅगी नूडल्स 70g (SKU-003) → 38 Pcs | Min: 100 | Only 10% left! 🚨\n• अमूल बटर 500g (SKU-001) → 45 Pcs | Min: 200 | 22% — runs out in 3 days!\n\n⚠️ LOW STOCK:\n• टाटा मीठ 1kg (SKU-002) → 120 Pcs | Min: 300 | 28% — PO pending\n\n✅ OK:\n• अमूल बटर 500g → 200 Pcs (68%) ✅\n• टाटा मीठ 1kg → 300 Pcs (64%) ✅\n• मॅगी नूडल्स 70g → 250 Pcs (72%) ✅\n\n🤖 AI Recommendation: मॅगी नूडल्स 70g EMERGENCY — PO bhejo aaj hi!`;

    if (has('amul butter','amul batr','amul stock','sku-001','sku001'))
      return `📦 अमूल बटर 500g — Stock Detail\n\nSKU: SKU-001 | Supplier: अमूल डिस्ट्रिब्युटर (पुणे)\nCurrent Stock: 45 Pcs\nMinimum Required: 200 Pcs\nStock Level: 22% 🚨 LOW\n\nRecent Movements:\n• 04 Mar: 86 Pcs sold (retail billing)\n• Pending PO: #PUR-851 (200 Pcs, ₹56,000) — expected 10 Mar\n\nPeak season mein demand 3x hogi — abhi aur order karo!`;

    if (has('maggi stock','maggi kitna','sku-003','noodles stock'))
      return `🍜 मॅगी नूडल्स 70g — Stock Detail\n\nSKU: SKU-003 | Supplier: Nestlé Distributor (पुणे)\nCurrent Stock: 38 Pcs\nMinimum Required: 200 Pcs\nStock Level: 10% 🚨🚨 CRITICAL!\n\nAt current sales rate → stock khatam in 2 DAYS!\nPending PO: #PUR-849 (200 Pcs, ₹2,800) — expected 07 Mar\n\n⚠️ Weekend rush se pehle stock khatam ho sakta hai!\nTurant Nestlé Distributor ko call karo!`;

    if (has('tata salt','tata namak','sku-002','namak stock'))
      return `🧂 टाटा मीठ 1kg — Stock Detail\n\nSKU: SKU-002 | Supplier: Tata Consumer Distributor (पुणे)\nCurrent Stock: 120 Pcs\nMinimum Required: 300 Pcs\nLevel: 40% ⚠️ LOW\n\nPending PO: #PUR-850 (300 Pcs, ₹8,400) — expected 08 Mar\nNote: GST EXEMPT product — 0% tax\n\nPeak season ke liye aur stock maintain karo!`;

    if (has('stock movement','movement','in out','grn','gatepass','aaya','gaya','माल हालचाल','आला','गेला','स्टॉक हालचाल'))
      return `📋 Recent Stock Movements:\n\n04 Mar | अमूल बटर 500g | SOLD 86 Pcs | POS-441 | काउंटर\n04 Mar | टाटा मीठ 1kg | SOLD 140 Pcs | POS-440 | काउंटर\n03 Mar | टाटा मीठ 1kg | IN 500 Pcs | GRN-218 | मुख्य गोदाम\n03 Mar | मॅगी नूडल्स 70g | SOLD 200 Pcs | POS-439 | काउंटर\n\nIN = supplier se maal aaya. SOLD = retail/wholesale sale.`;

    // ── DEALERS ──
    if (has('dealer','dealers','customer','client','party','grahak','ग्राहक','distributor','sabhi dealer','all dealer','dealer list','विक्रेते','विक्रेता','पार्टी','ग्राहक यादी'))
      return `🤝 Dealer Overview — 5 Key Dealers\n\n🚩 HIGH RISK:\n• मेट्रो होलसेल (पुणे) | ₹3,24,000 थकीत | 45 दिवस late | 3rd time! Credit limit ₹5L\n\n⚠️ WATCH:\n• शर्मा किराणा (सोलापूर) | ₹1,82,500 थकीत | 32 दिवस late | Seasonal pattern\n\n🔵 LOW RISK:\n• सिटी होलसेल (सांगली) | ₹95,000 pending | 18 दिवस | Due 20 Mar\n• मेट्रो होलसेल (मुंबई) | ₹2,10,000 | 12 दिवस | Under limit\n\n✅ PERFECT:\n• शर्मा किराणा (पुणे) | ₹0 थकीत | Always on-time | Pre-approved ₹10L limit\n\nTotal outstanding: ₹8,11,500`;

    if (has('metro wholesale','metro holsale','3.24','3,24','45 day','high risk dealer'))
      return `🚩 मेट्रो होलसेल — HIGH RISK!\n\nCity: पुणे | Credit Limit: ₹5L\nOutstanding: ₹3,24,000\nOverdue: 45 दिवस (Invoice: INV-1842, due 18 Jan)\nOccurrence: 3rd time repeat offender!\n\n🤖 AI अंतर्दृष्टी: Avg payment delay jumped 12→31→45 दिवस over 3 quarters. Pattern worsening!\n\nRecommendation:\n1. New credit band karo turant\n2. WhatsApp reminder bhejo\n3. Aur ₹3.24L nahi aaya to legal notice\n\nEscalate button Payments screen pe hai.`;

    if (has('sharma kirana solapur','rameshwar traders','solapur','1.82','1,82','32 day'))
      return `⚠️ शर्मा किराणा — Watch!\n\nCity: सोलापूर | Credit Limit: ₹3L\nOutstanding: ₹1,82,500\nOverdue: 32 दिवस (Invoice: INV-1831, due 01 Feb)\nNote: Inter-state supply (MH→KA) — IGST applicable\n\n🤖 AI अंतर्दृष्टी: Seasonal Q4 cash flow pattern. Likely temporary — suggest payment plan.\n\nRecommendation: Payment plan mein 2 installments mein collect karo. Full escalation abhi nahi.`;

    if (has('sharma kirana pune','best dealer','sabse accha dealer','top dealer'))
      return `⭐ शर्मा किराणा — Best Dealer!\n\nCity: पुणे | Credit Limit: ₹10L (highest!)\nOutstanding: ₹0 — ZERO थकीत!\nPayment History: 18 consecutive on-time payments\nStatus: ✅ AI Cleared — Good Standing\n\nLatest Order: SO-2247 | अमूल बटर 500g 2000 Pcs | ₹48,000 | पाठवले\nLast Delivery: DO-441 dispatched 03 Mar (100% fulfilled)\n\n🤖 AI says: Inhe priority dena chahiye — best customer hai aapka!`;

    if (has('send reminder','reminder bhejo','reminder send','whatsapp','notice','स्मरणपत्र','रिमाइंडर','नोटीस पाठवा'))
      return `📲 Payment स्मरणपत्रे:\n\n✅ मेट्रो होलसेल ko reminder bhej sakte ho:\nINV-1842 | ₹3,24,000 | 45 दिवस थकीत\n→ Payments screen pe "Escalate" button click karo\n\n✅ शर्मा किराणा:\nINV-1831 | ₹1,82,500 | 32 दिवस थकीत\n→ Dealers screen pe WhatsApp स्मरणपत्र button आहे\n\nYa phir /dealers type karo — wahan "सर्वांना स्मरणपत्र" button hai ek click mein sab ko!`;

    // ── PAYMENTS / OUTSTANDING ──
    if (has('payment','pay','outstanding','baki','due','थकीत','ledger','collection','nahi diya','paisa aaya','kitna baki','बाकी','पेमेंट','देयक','वसुली','उधारी'))
      return `💳 Payment Status — March 2026\n\n📥 Received This Month: ₹14.2L\n📤 Total Outstanding: ₹18.6L\n⏱️ Avg Collection Days: 22\n📊 On-Time Rate: 76%\n\n🚨 OVERDUE:\n• मेट्रो होलसेल | INV-1842 | ₹3,24,000 | 45 DAYS OVERDUE → Escalate!\n• शर्मा किराणा | INV-1831 | ₹1,82,500 | 32 दिवस → स्मरण करा\n\n🕐 UPCOMING DUE:\n• सिटी होलसेल | INV-1849 | ₹95,000 | Due 20 Mar (16 days left)\n• शर्मा किराणा | INV-1847 | ₹2,10,000 | Due 18 Mar ✅ On track\n\nTotal urgent collection needed: ₹5,06,500`;

    if (has('kitna baaki','total outstanding','total due','pura outstanding','sabka milake'))
      return `📊 Total Outstanding Breakdown:\n\n• मेट्रो होलसेल: ₹3,24,000 (OVERDUE 45d)\n• शर्मा किराणा: ₹1,82,500 (OVERDUE 32d)\n• सिटी होलसेल: ₹95,000 (due 20 Mar)\n• मेट्रो होलसेल: ₹2,10,000 (12 दिवस)\n\nTotal: ₹8,11,500 outstanding\nOverdue only: ₹5,06,500\n\nSabse urgent मेट्रो होलसेल hai — 45 din ho gaye, legal notice ka waqt aa gaya!`;

    if (has('itc','input tax','gstr-2','gstr2','2a','reconcil'))
      return `🔄 ITC (Input Tax Credit) Status:\n\nITC Available: ₹31,248\nITC Utilised: ₹19,950\nITC Balance: ₹11,298 (carry forward)\nGST Payable after set-off: ₹37,728\n\n✅ Matched suppliers: अमूल डिस्ट्रिब्युटर, Tata Consumer Distributor, Nestlé Distributor\n⚠️ Pending 2A match: Nestlé Distributor (PUR-837, ₹2,688 ITC)\n\nGSTR-1 filing due: 11 April 2026`;

    if (has('gstr-1','gstr1','gst filing','filing','return'))
      return `📋 GSTR-1 सारांश — March 2026\n\nTotal Outward Supply: ₹5,79,400\nTotal GST Collected: ₹49,026\nB2B Invoices: 6\nFiling Due: 11 April 2026\n\nTop invoices:\n• INV-1849 | सिटी होलसेल | ₹1,26,000\n• INV-1847 | SuperMart | ₹50,400\n• INV-1831 | QuickShop (IGST inter-state) | ₹1,93,450\n\n⚠️ INV-1831 रामेश्वर ट्रेडर्स सोलापूर — inter-state (MH→KA), IGST ₹10,950 lagega\n\n/invoice pe jao ya /bank pe jao aur file karo!`;

    // ── PURCHASE / SUPPLIERS ──
    if (has('purchase','purchas','po','supplier','vendor','kharidi','khareed','stock buy','खरीद','पीओ','order diya','पुरवठादार','खरेदी ऑर्डर'))
      return `🛍️ Purchase Orders — March 2026\n\nTotal POs: 12 | Value: ₹6.8L | On-Time Rate: 82%\nPending Delivery: 4 POs\n\n⏳ PENDING:\n• #PUR-851 | अमूल डिस्ट्रिब्युटर | अमूल बटर 500g 500 Pcs | ₹1,40,000 | Expected 10 Mar\n• #PUR-850 | Tata Consumer Distributor | टाटा मीठ 1kg 800 Pcs | ₹22,400 | Expected 08 Mar\n• #PUR-849 | Nestlé Distributor | मॅगी नूडल्स 70g 200 Pcs | ₹2,800 | Expected 07 Mar ⚠️ URGENT!\n\n✅ RECEIVED:\n• #PUR-848 | अमूल डिस्ट्रिब्युटर | अमूल बटर 500g 300 Pcs | ₹84,000 | Received 05 Mar\n• #PUR-847 | Tata Consumer Distributor | टाटा मीठ 1kg 500 Pcs | ₹14,000 | Received 03 Mar\n\n❌ CANCELLED:\n• #PUR-845 | अमूल डिस्ट्रिब्युटर | अमूल बटर 500g 100 Pcs | ₹28,000 | Reorder available`;

    if (has('amul supplier','amul distributor','amul wala','pur-851'))
      return `🧈 अमूल डिस्ट्रिब्युटर — Supplier Details\n\nLocation: पुणे | Products: अमूल बटर 500g\nTotal Orders: 8 POs | Total Value: ₹4.2L\nOn-Time Rate: 87% ✅\nActive PO: #PUR-851 (200 Pcs, ₹56,000, expected 10 Mar)\n\nBest supplier for अमूल बटर 500g. Lead time 7 days.`;

    if (has('tata supplier','tata distributor','tata consumer','pur-850'))
      return `🧂 Tata Consumer Distributor — Supplier Details\n\nLocation: पुणे | Products: टाटा मीठ 1kg\nTotal Orders: 6 POs | Total Value: ₹1.8L\nOn-Time Rate: 80% ✅\nActive PO: #PUR-850 (300 Pcs, ₹8,400, expected 08 Mar)\n\nKal delivery expected — stock low hai toh follow up karo!`;

    if (has('hul distributor','nestle distributor','mumbai supplier','maggi supplier','noodles supplier'))
      return `🍜 Nestlé Distributor — Supplier Details\n\nLocation: पुणे | Products: मॅगी नूडल्स 70g\nTotal Orders: 5 POs | Total Value: ₹62,000\nOn-Time Rate: 76% ⚠️ (Lowest among 3 suppliers)\nActive PO: #PUR-849 (200 Pcs, ₹2,800, expected 07 Mar)\n\nमॅगी नूडल्स 70g critical hai — sirf 2 din ka stock bacha! Unhe call karo aur delivery advance karne bolo!`;

    // ── FORECAST ──
    if (has('forecast','predict','season','peak','demand','mausam','future','aage','march','april','may','june','मौसम','भविष्य','trend','अंदाज','हंगाम','मागणी'))
      return `📈 AI Demand Forecast — Next 6 Months\n\nMar 2026 → ₹38.4L (↑12%) — Abhi chal raha hai\nApr 2026 → ₹44L (↑18%) — Badhega\nMay 2026 → ₹59L (↑35%) 🔥 PEAK SEASON!\nJun 2026 → ₹52L (↑8%) — High demand\nJul 2026 → ₹35L (−5%) — Girna shuru\nAug 2026 → ₹28L (−22%) — Off season\n\n🤖 AI Recommendations:\n• अमूल बटर 500g 200 Pcs → अमूल डिस्ट्रिब्युटर (₹56,000) — Order NOW\n• टाटा मीठ 1kg 300 Pcs → Tata Consumer Distributor (₹8,400)\n• मॅगी नूडल्स 70g 200 Pcs → Nestlé Distributor (₹2,800) — EMERGENCY!\n\n💡 Dairy prices expected to rise 8% by May — abhi stock karo!\n💡 अमूल बटर & मॅगी demand 3x hogi festive season mein (May-Jun)`;

    if (has('wedding','shaadi','शादी','3.2x','festive season','festival season'))
      return `💒 Wedding Season Forecast:\n\nMay–June mein shaadi ka season aata hai jab:\n• अमूल बटर 500g ki demand: 3.2x normal se zyada\n• मॅगी नूडल्स 70g ki demand: 2.8x increase expected\n• Mostly caterers, event managers, bulk buyers order karte hain\n\nAI Recommendation: Abhi se 3 SKUs ka advance stock rakho!\nPending PO bheji — expected delivery 12 Mar — stock ready rakho!`;

    // ── PRODUCTS / GST / HSN ──
    if (has('product','products','kya banta','kya banate','items','sku','sabse zyada','best seller','bestsell','top product','उत्पादन','वस्तू','सर्वाधिक','टॉप प्रोडक्ट'))
      return `🏆 Products — Bestsellers:\n\n1. 🥇 अमूल बटर 500g (HSN 04051000, 12% GST)\n   → ₹3,92,000 sold this month | Top seller!\n2. 🥈 टाटा मीठ 1kg (HSN 25010010, 0% GST — EXEMPT)\n   → ₹89,600 | Essential daily staple\n3. 🥉 मॅगी नूडल्स 70g (HSN 19023010, 18% GST)\n   → ₹71,400 | Fast-moving FMCG — critical stock!\n\nअमूल बटर 500g sabse zyada bika is mahine!`;

    if (has('hsn','gst rate','tax rate','kitna gst','percent gst','gst kitna','जीएसटी दर','कर दर','किती जीएसटी','एचएसएन'))
      return `📦 HSN Codes & GST Rates:\n\n• अमूल बटर 500g → HSN 04051000 | GST 12% (CGST 6% + SGST 6%)\n• टाटा मीठ 1kg → HSN 25010010 | GST 0% — EXEMPT!\n• मॅगी नूडल्स 70g → HSN 19023010 | GST 18% (CGST 9% + SGST 9%)\n\nIntra-state (Maharashtra) → CGST + SGST split\nInter-state (e.g. MH→KA रामेश्वर ट्रेडर्स) → IGST full rate\n\nGSTR-1 due: 11 April 2026. /invoice pe jao invoice generate karne ke liye!`;

    if (has('invoice','gst invoice','bill','print invoice','generate invoice','invoic','इनव्हॉइस','जीएसटी बिल','बिल तयार','पावती'))
      return `🧾 GST बिल Generator\n\nCompany: MY SUPERMARKET PVT LTD\nGSTIN: 27AABCS1234Z1ZX\nAddress: Karad, Satara 415110, Maharashtra\n\nProducts available:\n• अमूल बटर 500g — HSN 04051000 — 12% GST\n• टाटा मीठ 1kg — HSN 25010010 — 0% GST (EXEMPT)\n• मॅगी नूडल्स 70g — HSN 19023010 — 18% GST\n\nInvoice banane ke liye: /invoice type karo ya Orders screen pe "GST बिल" button dabao!`;

    if (has('auto match','auto matched','auto-match','matched','2a match','reconcil','itc match'))
      return `🔄 "Auto Matched" kya hota hai? (ITC Reconciliation)\n\nJab aap suppliers se khareedari karte ho, wo log apna GST government ko bharte hain (GSTR-1).\nGovernment aapke liye ek list banati hai — GSTR-2A — jisme dikhta hai kis supplier ne GST bhara.\n\n✅ "Auto Matched" matlab:\nAapke purchase invoice ka GST aur supplier ke GSTR-1 mein exact match hua.\nAap wo GST apna Input Tax Credit (ITC) ke roop mein claim kar sakte ho!\n\n⚠️ "Pending 2A" matlab:\nSupplier ne abhi apna return nahi bhara — Nestlé Distributor ka PUR-837 ₹2,688 ITC pending hai.\n\nAapka ITC balance: ₹11,298 carry forward ho raha April mein.`;

    if (has('bank','reconcil','recon','bank statement','utr','neft','rtgs','transaction'))
      return `🏦 Bank Reconciliation:\n\nBank recon screen pe aap dekh sakte ho:\n• Bank statement se transactions\n• ERP entries se match/unmatch\n• Auto-reconciliation AI se\n\n/bank type karo Bank Recon screen kholne ke liye.\n\nTip: शर्मा किराणा ka INV-1831 ₹1,82,500 — inter-state IGST ke saath file hua hai (MH→KA). Bank mein ye amount track karo!`;

    if (has('fraud','suspicious','anomal','risk','alert','dhokha','pakdo','फसवणूक','संशयित','धोका','जोखीम'))
      return `🚨 Fraud Detection Alerts:\n\nAI ne kuch suspicious patterns pakde hain:\n• Unusual order patterns detect ho rahe hain\n• Duplicate invoice risk monitoring active\n• High-value transactions auto-flagged\n\nमेट्रो होलसेल 45-day थकीत — fraud nahi lekin deliberate delay ho sakta hai!\n\n/fraud type karo Fraud Detection screen dekhne ke liye.`;

    // ── COMPANY / ERP INFO ──
    if (has('company','my supermarket','hamari company','humara','apna','gstin','address','karad'))
      return `🏪 Company Details:\n\nName: MY SUPERMARKET PVT LTD\nBrand: My Supermarket\nGSTIN: 27AABCS1234Z1ZX\nAddress: Karad, Satara 415110, Maharashtra\nState Code: 27 (Maharashtra)\n\nKey Products: अमूल बटर 500g (HSN 04051000, 12%), टाटा मीठ 1kg (HSN 25010010, 0%), मॅगी नूडल्स 70g (HSN 19023010, 18%)\nSuppliers: अमूल डिस्ट्रिब्युटर (पुणे), Tata Consumer Distributor (पुणे), Nestlé Distributor (पुणे)\nKey Buyers: मेट्रो होलसेल, शर्मा किराणा, सिटी होलसेल, रामेश्वर ट्रेडर्स, जनता किराणा`;

    if (has('erp','kya hai','kya karta','system','supermarket erp','software'))
      return `🧠 My Supermarket ERP — Full Explanation:\n\nYe ek smart ERP system hai specifically Indian FMCG retail stores ke liye.\n\nScreens:\n📊 /dashboard — daily overview, KPIs, alerts\n📦 /inventory — stock levels, auto-reorder\n🛍️ /pos — POS billing, barcode scan, GST invoices\n📅 /expiry — expiry tracking, wastage management\n🎁 /schemes — offers, combos, discount schemes\n🛒 /orders — sales orders, HSN reports\n🛒 /purchase — purchase orders, supplier ledger\n🤝 /dealers — dealer credit, risk analysis\n💰 /payments — ledger, GSTR-1, ITC tracker\n🔮 /forecast — 6-month AI demand forecast\n🧾 /invoice — GST invoice generator\n🏦 /bank — bank reconciliation\n🚨 /fraud — AI fraud detection\n📊 /data — analytics hub\n\nKoi bhi screen open karne ke liye / slash command use karo!`;

    // ── FOCUS / PRIORITY ──
    if (has('focus','priority','kya karu','important','urgent','aaj kya','pehle kya','first','sabse pehle','help me','काय करू','प्राधान्य','महत्त्वाचे','तातडी','आधी काय'))
      return `🎯 Aaj ke Top Priorities — ' + new Date().toLocaleDateString('en-IN',{day:'numeric',month:'long',year:'numeric'}) + ':\n\n1. 🚨 मॅगी नूडल्स 70g order karo AAJ — sirf 2 din ka stock! (Nestlé Distributor call)\n2. ⚖️ मेट्रो होलसेल ₹3,24,000 — 45 दिवस थकीत, escalate karo\n3. 📅 EXP-001 अमूल बटर 500g — kal expire hoga, discount lao ya return karo\n4. 📦 PUR-849 मॅगी नूडल्स 70g delivery track karo (07 Mar expected)\n5. 🔮 Peak season May ke liye bulk PO bhejo abhi\n\nSabse pehle मॅगी नूडल्स 70g — weekend rush se pehle stock aana chahiye!`;

    if (has('what is','kya hai','matlab','matlab kya','explain','samjhao','bata','btao','meaning','काय आहे','म्हणजे काय','समजावून सांगा','अर्थ'))
      return `🤔 Kya explain karna chahte ho? Yeh sab samjha sakta hoon:\n\n• "auto matched kya hai" → ITC reconciliation explain\n• "HSN code kya hai" → GST product codes\n• "ITC kya hai" → Input Tax Credit\n• "GSTR-1 kya hai" → GST return filing\n• "credit limit kya hai" → dealer credit explain\n• "PO kya hai" → Purchase Order\n• "expiry kya karu" → expiry/wastage management\n• "scheme kya hai" → offers & promotions explain\n\nKoi bhi term likhke pucho — main simple Hindi mein samjhaunga!`;

    if (has('delivery order kya','do kya','dispatch kya','do matlab'))
      return `🚚 Delivery Order (DO) kya hota hai?\n\nJab koi dealer/customer order karta hai aur hum uska maal dispatch karte hain, tab ek "Delivery Order" create hota hai.\n\nExample:\nशर्मा किराणा ne 2000 Pcs अमूल बटर 500g manga\n→ DO-441 create hua\n→ Counter #3 se dispatch\n→ 100% fulfilled, delivered\n\nDelivery Order ka safar:\nPlanned → Picking → Dispatched → Delivered ✅\n\nHar DO ka ek number hota hai (DO-441, DO-442...) aur wo ek specific dealer ke order se linked hota hai.`;

    if (has('credit limit kya','credit limit matlab','limit kya'))
      return `💳 Credit Limit kya hota hai?\n\nYe wo maximum amount hai jitna ek dealer udhaar le sakta hai bina pehle payment kiye.\n\nExamples:\n• शर्मा किराणा → ₹10L credit limit (best dealer, kabhi late nahi)\n• मेट्रो होलसेल → ₹5L limit, lekin ₹3.24L already थकीत!\n• शर्मा किराणा → ₹3L limit, ₹1.82L थकीत\n\nJab dealer credit limit ke paas pahunch jaata hai, AI automatically flag karta hai aur naya order rokne ka suggestion deta hai.`;

    if (has('po kya','purchase order kya','po matlab','purchase order matlab'))
      return `🛍️ Purchase Order (PO) kya hota hai?\n\nJab humein suppliers se stock khareedna hota hai, hum ek "Purchase Order" bhejte hain.\n\nExample:\nअमूल बटर 500g stock 12% — critical!\n→ PO #PUR-851 create kiya\n→ अमूल डिस्ट्रिब्युटर (पुणे) ko bheja\n→ 500 Pcs, ₹1,20,000\n→ Expected delivery: 10 March\n\nPO lifecycle:\nCreated → Sent to Supplier → Pending → Received ✅ (ya Cancelled ❌)`;

    if (has('gst kya','gst matlab','goods and service','tax kya'))
      return `🧾 GST kya hota hai? (Simple explanation)\n\nGST = Goods and Services Tax\nIndia mein har product/service pe government ko tax dena padta hai.\n\nMy Supermarket ke products ke GST rates:\n• अमूल बटर 500g → 12% GST (HSN 04051000 — Dairy)\n• टाटा मीठ 1kg → 0% GST — EXEMPT! (HSN 25010010)\n• मॅगी नूडल्स 70g → 18% GST (HSN 19023010 — Instant Food)\n\nIntra-state (Maharashtra ke andar):\n→ CGST half + SGST half = full rate\n\nInter-state (Maharashtra se bahar):\n→ IGST full rate apply hota hai\n\nHar mahine GSTR-1 file karni padti hai — next due: 11 April 2026.`;

    // ── HELP ──
    if (has('help','commands','kya puchu','kya puch sakta','madad','मदद','मदत','what can you','abilities','मला मदत','काय विचारू','सहाय्य'))
      return `🤖 Main sab kuch jaanta hoon! Ye pucho:\n\n📊 BUSINESS:\n"aaj kitna revenue" | "summary do" | "focus kya karu"\n\n📦 STOCK:\n"stock status" | "amul butter kitna bacha" | "maggi stock"\n\n🛍️ POS BILLING:\n"aaj ki bikri" | "today sales" | "best selling product"\n\n👥 DEALERS:\n"dealer list" | "Metro Wholesale थकीत" | "best dealer kaun"\n\n💰 PAYMENTS:\n"outstanding kitna" | "kiska payment nahi aaya" | "GSTR-1"\n\n🛒 PURCHASE:\n"PO status" | "supplier list" | "kya order kiya"\n\n📅 EXPIRY:\n"expiry alert" | "kya expire ho raha" | "wastage report"\n\n🎁 SCHEMES:\n"kaunsi scheme chal rahi" | "offer lagao" | "discount karo"\n\n📈 FORECAST:\n"May mein kitna revenue" | "peak season kab"\n\n📖 TERMS:\n"HSN code kya hai" | "ITC kya hai" | "credit limit kya hai"\n\nHindi, English, Hinglish — sab samajhta hoon! 🇮🇳`;

    // ── FALLBACK — still smart ──
    return `🤖 Samjha! "${text}" ke baare mein:\n\nMain is query ko identify kar raha hoon... Aapka sawaal shayad in topics se related hai:\n\n📊 Business data → "aaj ka summary" likho\n📦 Stock/Inventory → "stock status" likho\n🛍️ POS Billing → "aaj ki bikri" likho\n💰 Payments → "outstanding" likho\n👥 Dealers → "dealer list" likho\n📅 Expiry → "expiry alert" likho\n📈 Future → "forecast" likho\n\nYa seedha pucho — main har ERP data jaanta hoon! Hindi/English/Hinglish sab chalega 🇮🇳\n\nType "help" for all questions you can ask.`;
  }

  function addTypingIndicator() {
    const msgs = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'msg bot'; div.id = 'typing-indicator';
    div.innerHTML = '<div class="msg-bubble"><div class="typing-bubble"><span></span><span></span><span></span></div></div>';
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function removeTypingIndicator() {
    const t = document.getElementById('typing-indicator');
    if (t) t.remove();
  }

  function sendChat(chip) {
    const text = chip.textContent;
    addMessage(text, true);
    addTypingIndicator();
    setTimeout(() => { removeTypingIndicator(); addMessage(getResponse(text), false); }, 900);
  }

  function sendChatInput() {
    const input = document.getElementById('chat-input');
    if (!input.value.trim()) return;
    addMessage(input.value, true);
    const devVal = input.value; // Devanagari (displayed)
    const engVal = _mrBuf || devVal; // English buffer (for keyword matching)
    input.value = '';
    _mrBuf = '';
    addTypingIndicator();
    setTimeout(() => {
      removeTypingIndicator();
      let resp = getResponse(devVal);
      // If Devanagari gave fallback, try English buffer too
      if (chatLangMarathi && resp.startsWith('🤖 Samjha!') && engVal !== devVal) {
        resp = getResponse(engVal);
      }
      addMessage(resp, false);
    }, 950);
  }

  // ══════════════════════════════════════════
  // MARATHI PHONETIC TRANSLITERATION ENGINE
  // ══════════════════════════════════════════
  var chatLangMarathi = true;
  var _mrBuf = ''; // hidden English buffer

  const _MR = (function(){
    const H = '\u094D'; // halant
    // Consonants (longest key first in each check)
    const C = {
      'ksh':'क्ष','dny':'ज्ञ','chh':'छ',
      'kh':'ख','gh':'घ','ng':'ङ','ch':'च','jh':'झ',
      'Th':'ठ','Dh':'ढ','th':'थ','dh':'ध','ph':'फ','bh':'भ',
      'sh':'श','Sh':'ष','tr':'त्र','gy':'ज्ञ',
      'k':'क','K':'ख','g':'ग','G':'घ','c':'च','C':'छ',
      'j':'ज','J':'झ','T':'ट','D':'ड','N':'ण',
      't':'त','d':'द','n':'न','p':'प','f':'फ',
      'b':'ब','B':'भ','m':'म','y':'य','r':'र',
      'l':'ल','L':'ळ','v':'व','w':'व','s':'स','h':'ह',
      'x':'क्ष','q':'क','z':'झ'
    };
    // Independent vowels
    const VI = {
      'aa':'आ','ai':'ऐ','au':'औ','ee':'ई','oo':'ऊ','Au':'ॲ','O':'ऑ',
      'a':'अ','A':'आ','i':'इ','I':'ई','u':'उ','U':'ऊ',
      'e':'ए','o':'ओ','E':'ऐ','Ri':'ऋ'
    };
    // Vowel matras (after consonant)
    const VM = {
      'aa':'\u093E','ai':'\u0948','au':'\u094C','ee':'\u0940','oo':'\u0942','O':'\u0949',
      'a':'','A':'\u093E','i':'\u093F','I':'\u0940','u':'\u0941','U':'\u0942',
      'e':'\u0947','o':'\u094B','E':'\u0948','Ri':'\u0943'
    };
    function convert(input) {
      let out='', i=0, ac=false; // ac = after consonant
      while(i < input.length) {
        let ch = input[i], f = false;
        // Space, punctuation, numbers — pass through
        if(' ,.?!;:-₹@#/\\()[]{}"\'+=%&*'.includes(ch) || (ch>='0' && ch<='9')) {
          out += ch; ac = false; i++; continue;
        }
        // Anusvara (ं) and Visarga (ः)
        if(ch === 'M' && ac) { out += '\u0902'; ac = false; i++; continue; }
        if(ch === 'H' && ac && i+1 < input.length && !' aeiouAEIOU'.includes(input[i+1]||'')) { out += '\u0903'; ac = false; i++; continue; }
        // Try consonants (longest first: 3, 2, 1)
        for(let l = 3; l >= 1; l--) {
          let s = input.substr(i, l);
          if(C[s]) { if(ac) out += H; out += C[s]; ac = true; i += l; f = true; break; }
        }
        if(f) continue;
        // Try vowels (longest first: 2, 1)
        for(let l = 2; l >= 1; l--) {
          let s = input.substr(i, l);
          if(ac && VM.hasOwnProperty(s)) { out += VM[s]; ac = false; i += l; f = true; break; }
          if(!ac && VI[s]) { out += VI[s]; ac = false; i += l; f = true; break; }
        }
        if(f) continue;
        // No match — pass through
        out += ch; ac = false; i++;
      }
      return out;
    }
    return { convert: convert };
  })();

  // ── INPUT HANDLER ──
  (function initMarathiInput() {
    const inp = document.getElementById('chat-input');
    inp.addEventListener('keydown', function(e) {
      if(!chatLangMarathi) return; // English mode — normal typing
      if(e.ctrlKey || e.altKey || e.metaKey) return; // allow shortcuts
      if(e.key === 'Enter') { return; } // let existing handler send (it clears _mrBuf)
      if(e.key === 'Escape' || e.key === 'Tab') return; // let through
      if(e.key === 'Backspace') {
        e.preventDefault();
        if(_mrBuf.length > 0) { _mrBuf = _mrBuf.slice(0, -1); this.value = _MR.convert(_mrBuf); }
        return;
      }
      if(e.key === 'Delete') { e.preventDefault(); return; }
      if(e.key.length === 1) { // printable character
        e.preventDefault();
        _mrBuf += e.key;
        this.value = _MR.convert(_mrBuf);
      }
    });
    // Handle paste
    inp.addEventListener('paste', function(e) {
      if(!chatLangMarathi) return;
      e.preventDefault();
      const text = (e.clipboardData || window.clipboardData).getData('text');
      _mrBuf += text;
      this.value = _MR.convert(_mrBuf);
    });
  })();

  // ── GLOBAL MARATHI KEYBOARD (all text inputs) ──
  var _mrGlobalActive = false;

  function _mrGlobalKeydown(e) {
    var el = e.target;
    if (!el || !['INPUT','TEXTAREA'].includes(el.tagName)) return;
    // Skip non-text inputs and chat-input (has its own handler)
    var t = (el.type || '').toLowerCase();
    if (['number','email','password','date','time','month','week','range','color','file','checkbox','radio','submit','button','reset','hidden'].includes(t)) return;
    if (el.id === 'chat-input') return;
    if (e.ctrlKey || e.altKey || e.metaKey) return;
    var skip = ['Enter','Escape','Tab','ArrowUp','ArrowDown','ArrowLeft','ArrowRight',
                'Home','End','PageUp','PageDown','Insert','CapsLock','Shift','Control',
                'Alt','Meta','F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12'];
    if (skip.includes(e.key)) return;
    if (e.key === 'Backspace') {
      e.preventDefault();
      var buf = el._mrBuf || '';
      buf = buf.slice(0, -1);
      el._mrBuf = buf;
      el.value = _MR.convert(buf);
      el.dispatchEvent(new Event('input', {bubbles: true}));
      return;
    }
    if (e.key === 'Delete') {
      e.preventDefault();
      el._mrBuf = '';
      el.value = '';
      el.dispatchEvent(new Event('input', {bubbles: true}));
      return;
    }
    if (e.key.length === 1) {
      e.preventDefault();
      var buf2 = (el._mrBuf || '') + e.key;
      el._mrBuf = buf2;
      el.value = _MR.convert(buf2);
      el.dispatchEvent(new Event('input', {bubbles: true}));
    }
  }

  function _mrGlobalFocusOut(e) {
    // Clear buffer when input loses focus (fresh start next time)
    if (e.target && e.target._mrBuf !== undefined) e.target._mrBuf = '';
  }

  window.enableMarathiKeyboard = function() {
    if (_mrGlobalActive) return;
    _mrGlobalActive = true;
    // Clear all visible text inputs when switching to MR mode
    document.querySelectorAll('input[type="text"], input[type="search"], input:not([type]), textarea').forEach(function(el) {
      if (el.id === 'chat-input') return;
      el._mrBuf = '';
      el.value = '';
    });
    document.addEventListener('keydown', _mrGlobalKeydown, true);
    document.addEventListener('focusout', _mrGlobalFocusOut, true);
  };

  window.disableMarathiKeyboard = function() {
    if (!_mrGlobalActive) return;
    _mrGlobalActive = false;
    document.removeEventListener('keydown', _mrGlobalKeydown, true);
    document.removeEventListener('focusout', _mrGlobalFocusOut, true);
    // Clear all buffers
    document.querySelectorAll('input, textarea').forEach(function(el) { el._mrBuf = ''; });
  };

  // If page already loaded in MR mode (applyLanguage ran before original.js loaded), enable now
  if (typeof currentLang !== 'undefined' && currentLang === 'mr') {
    window.enableMarathiKeyboard();
  }

  // ── LANGUAGE TOGGLE ──
  function toggleChatLang() {
    chatLangMarathi = !chatLangMarathi;
    const btn = document.getElementById('chat-lang-btn');
    const input = document.getElementById('chat-input');
    const hint = document.getElementById('chat-lang-hint');
    _mrBuf = ''; // clear buffer on switch
    input.value = '';
    if (chatLangMarathi) {
      btn.textContent = 'मा';
      btn.classList.add('active');
      input.placeholder = 'मराठीत टाइप करा — namaste → नमस्ते';
      hint.innerHTML = '⌨️ मराठी मोड · English keyboard वरून मराठी लिहा — <b>मा</b> दाबा EN साठी';
      hint.classList.add('show');
      setTimeout(() => hint.classList.remove('show'), 4000);
    } else {
      btn.textContent = 'EN';
      btn.classList.remove('active');
      input.placeholder = 'Ask anything — stock, sales, expiry, schemes, dealers...';
      hint.innerHTML = '⌨️ English mode · Type normally — press <b>मा</b> for Marathi';
      hint.classList.add('show');
      setTimeout(() => hint.classList.remove('show'), 3000);
    }
    input.focus();
  }

  function triggerChat(text) {
    showScreen('chatbot');
    setTimeout(() => {
      addMessage(text, true);
      addTypingIndicator();
      setTimeout(() => { removeTypingIndicator(); addMessage(getResponse(text), false); }, 900);
    }, 100);
  }

  // ══════ DATA HUB ══════
  var dhData = [];
  var dhHeaders = [];
  var dhSheetURL = '';
  let dhAutoRefreshTimer = null;

  function setDHStatus(type, text) {
    const dot = document.getElementById('dh-dot');
    const txt = document.getElementById('dh-status-text');
    if(!dot || !txt) return;
    dot.className = 'dh-status-dot ' + type;
    txt.textContent = text;
    if(type === 'connected') {
      const now = new Date();
      const syncLabel = (typeof i18n !== 'undefined' && typeof currentLang !== 'undefined' && i18n[currentLang]) ? (i18n[currentLang].dh_last_sync || 'Last sync') : 'Last sync';
      document.getElementById('dh-last-sync').textContent = syncLabel + ': ' + now.toLocaleTimeString('en-IN');
    }
  }

  function connectSheet() {
    const url = document.getElementById('sheet-url-input')?.value?.trim();
    if(!url) { setDHStatus('error','Please paste a Google Sheet URL'); return; }
    dhSheetURL = url;
    loadSheetData();
  }

  function extractSheetId(url) {
    const m = url.match(/\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/);
    return m ? m[1] : null;
  }

  async function loadSheetData() {
    setDHStatus('loading','Connecting to Google Sheet...');
    const btn = document.getElementById('refresh-btn');
    if(btn) btn.classList.add('spinning');
    const sheetId = extractSheetId(dhSheetURL);
    if(!sheetId) { setDHStatus('error','Invalid Google Sheet URL. Make sure it is public.'); if(btn) btn.classList.remove('spinning'); return; }
    const csvUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/export?format=csv`;
    try {
      const res = await fetch(csvUrl);
      if(!res.ok) throw new Error('Could not fetch sheet');
      const csv = await res.text();
      parseAndRenderCSV(csv, 'Google Sheet');
      document.getElementById('sheet-connected-info').style.display = 'block';
      setDHStatus('connected', '✅ Google Sheet connected — live data loaded');
    } catch(e) {
      setDHStatus('error','❌ Cannot load sheet. Make sure sharing is set to "Anyone with link".');
    }
    if(btn) btn.classList.remove('spinning');
  }

  function parseAndRenderCSV(csv, source) {
    const lines = csv.trim().split('\n').map(l => l.split(',').map(c => c.replace(/^"|"$/g,'').trim()));
    if(lines.length < 2) { setDHStatus('error','Sheet appears empty.'); return; }
    dhHeaders = lines[0];
    dhData = lines.slice(1).map(row => {
      const obj = {};
      dhHeaders.forEach((h,i) => obj[h] = row[i]||'');
      return obj;
    });
    renderDHTable(dhData);
    updateDHStats(source);
  }

  function renderDHTable(data) {
    const table = document.getElementById('dh-table');
    const empty = document.getElementById('dh-empty-state');
    const count = document.getElementById('dh-row-count');
    if(!data.length) { table.style.display='none'; empty.style.display='flex'; return; }
    empty.style.display = 'none';
    table.style.display = 'table';
    const rowsLabel = (typeof i18n !== 'undefined' && typeof currentLang !== 'undefined' && i18n[currentLang]) ? (i18n[currentLang].dh_rows || 'rows') : 'rows';
    count.textContent = data.length + ' ' + rowsLabel;
    let html = '<thead><tr>' + dhHeaders.map(h=>`<th>${h}</th>`).join('') + '</tr></thead><tbody>';
    data.forEach(row => {
      html += '<tr>' + dhHeaders.map(h => `<td>${row[h]||'—'}</td>`).join('') + '</tr>';
    });
    html += '</tbody>';
    table.innerHTML = html;
  }

  function filterDHTable() {
    const q = document.getElementById('dh-search')?.value?.toLowerCase()||'';
    if(!q) { renderDHTable(dhData); return; }
    const filtered = dhData.filter(row => Object.values(row).some(v => v.toLowerCase().includes(q)));
    renderDHTable(filtered);
  }

  function updateDHStats(source) {
    const card = document.getElementById('dh-stats-card');
    const body = document.getElementById('dh-stats-body');
    if(!card || !body) return;
    card.style.display = 'block';
    const numCols = dhHeaders.filter(h => dhData.some(r => !isNaN(parseFloat(r[h])))).length;
    body.innerHTML = `
      <div class="mini-row"><span class="mini-label">Source</span><span class="mini-val" style="color:var(--ai);font-size:11px;">${source}</span></div>
      <div class="mini-row"><span class="mini-label">Total Rows</span><span class="mini-val">${dhData.length}</span></div>
      <div class="mini-row"><span class="mini-label">Columns</span><span class="mini-val">${dhHeaders.length}</span></div>
      <div class="mini-row"><span class="mini-label">Numeric Cols</span><span class="mini-val" style="color:var(--accent3)">${numCols}</span></div>
      <div class="mini-row"><span class="mini-label">Last Updated</span><span class="mini-val" style="font-size:10px;">${new Date().toLocaleTimeString('en-IN')}</span></div>
    `;
  }

  function handleFileImport(e) {
    const file = e.target.files[0];
    if(!file) return;
    const nameEl = document.getElementById('dh-file-name');
    nameEl.style.display = 'block';
    nameEl.textContent = '📄 ' + file.name;
    setDHStatus('loading','Reading file...');
    const reader = new FileReader();
    if(file.name.endsWith('.json')) {
      reader.onload = ev => {
        try {
          const json = JSON.parse(ev.target.result);
          const arr = Array.isArray(json) ? json : [json];
          dhHeaders = Object.keys(arr[0]||{});
          dhData = arr;
          renderDHTable(dhData);
          updateDHStats(file.name);
          setDHStatus('connected','✅ JSON file imported — ' + arr.length + ' records');
        } catch { setDHStatus('error','❌ Invalid JSON file'); }
      };
      reader.readAsText(file);
    } else {
      reader.onload = ev => {
        parseAndRenderCSV(ev.target.result, file.name);
        const _rowsLbl = (typeof i18n !== 'undefined' && typeof currentLang !== 'undefined' && i18n[currentLang]) ? (i18n[currentLang].dh_rows || 'rows') : 'rows';
        setDHStatus('connected','✅ File imported — ' + dhData.length + ' ' + _rowsLbl);
      };
      reader.readAsText(file);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    document.getElementById('dh-dropzone').classList.remove('dh-dropzone-active');
    const file = e.dataTransfer.files[0];
    if(!file) return;
    handleFileImport({target:{files:[file]}});
  }

  function refreshDataHub() {
    if(dhSheetURL) { loadSheetData(); return; }
    if(dhData.length) {
      setDHStatus('loading','ताजेटवानाing...');
      const btn = document.getElementById('refresh-btn');
      if(btn) btn.classList.add('spinning');
      setTimeout(()=>{
        renderDHTable(dhData);
        setDHStatus('connected','✅ Data refreshed');
        if(btn) btn.classList.remove('spinning');
      }, 800);
    } else {
      setDHStatus('error','No data source connected yet');
    }
  }

  function exportTableCSV() {
    if(!dhData.length) { alert('No data to export'); return; }
    let csv = dhHeaders.join(',') + '\n';
    dhData.forEach(row => { csv += dhHeaders.map(h => '"'+(row[h]||'')+'"').join(',') + '\n'; });
    const a = document.createElement('a');
    a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
    a.download = 'datahub-export-'+Date.now()+'.csv';
    a.click();
  }

  // ── GST TAB SWITCHING ──
  function switchOrderTab(tab) {
    ['orders','gst-invoice','hsn'].forEach(t => {
      document.getElementById('orders-tab-'+t).style.display = t===tab ? 'block' : 'none';
      document.getElementById('tab-'+( t==='gst-invoice'?'gst-invoice':t==='hsn'?'hsn':'orders')).classList.toggle('active', t===tab);
    });
  }
  function switchPOTab(tab) {
    ['po-list','po-supplier'].forEach(t => {
      document.getElementById('po-tab-'+t).style.display = t===tab ? 'block' : 'none';
      document.getElementById('tab-'+t).classList.toggle('active', t===tab);
    });
  }
  function switchPayTab(tab) {
    ['payments','gstr1','itc'].forEach(t => {
      document.getElementById('pay-tab-'+t).style.display = t===tab ? 'block' : 'none';
      document.getElementById('tab-'+(t==='payments'?'payments':t==='gstr1'?'gstr1':'itc')).classList.toggle('active', t===tab);
    });
  }

  // ── GST INVOICE CALC ──
  function updateGSTRate() { calcGST(); }
  function calcGST() {
    const qty = parseFloat(document.getElementById('inv-qty')?.value)||0;
    const rate = parseFloat(document.getElementById('inv-rate')?.value)||0;
    const base = qty * rate;
    const prodVal = document.getElementById('inv-product')?.value||'';
    const gstRate = parseFloat(prodVal.split('|')[2]||5);
    const supply = document.getElementById('inv-supply')?.value||'intra';
    const tax = base * gstRate / 100;
    const total = base + tax;

    const fmt = n => '₹'+Math.round(n).toLocaleString('en-IN');
    const [prod,hsn] = prodVal.split('|');
    if(document.getElementById('prev-prod')) document.getElementById('prev-prod').textContent = prod||'';
    if(document.getElementById('prev-hsn')) document.getElementById('prev-hsn').textContent = hsn||'';
    if(document.getElementById('prev-qty')) document.getElementById('prev-qty').textContent = qty+'m';
    if(document.getElementById('prev-prate')) document.getElementById('prev-prate').textContent = fmt(rate);
    if(document.getElementById('prev-base')) document.getElementById('prev-base').textContent = fmt(base);
    if(document.getElementById('prev-taxable')) document.getElementById('prev-taxable').textContent = fmt(base);
    if(document.getElementById('prev-total')) document.getElementById('prev-total').textContent = fmt(total);
    if(document.getElementById('prev-invno')) document.getElementById('prev-invno').textContent = document.getElementById('inv-no')?.value||'';
    if(document.getElementById('prev-date')) document.getElementById('prev-date').textContent = document.getElementById('inv-date')?.value||'';
    if(document.getElementById('prev-buyer')) document.getElementById('prev-buyer').textContent = document.getElementById('inv-buyer')?.value||'—';
    if(document.getElementById('prev-gstin')) document.getElementById('prev-gstin').textContent = document.getElementById('inv-gstin')?.value||'—';
    if(supply==='intra') {
      document.getElementById('cgst-row').style.display='flex';
      document.getElementById('sgst-row').style.display='flex';
      document.getElementById('igst-row').style.display='none';
      document.getElementById('cgst-row').querySelector('span').textContent='CGST @'+(gstRate/2)+'%';
      document.getElementById('sgst-row').querySelector('span').textContent='SGST @'+(gstRate/2)+'%';
      if(document.getElementById('prev-cgst')) document.getElementById('prev-cgst').textContent=fmt(tax/2);
      if(document.getElementById('prev-sgst')) document.getElementById('prev-sgst').textContent=fmt(tax/2);
    } else {
      document.getElementById('cgst-row').style.display='none';
      document.getElementById('sgst-row').style.display='none';
      document.getElementById('igst-row').style.display='flex';
      document.getElementById('igst-row').querySelector('span').textContent='IGST @'+gstRate+'%';
      if(document.getElementById('prev-igst')) document.getElementById('prev-igst').textContent=fmt(tax);
    }
    // Amount in words (simple)
    const words = numberToWords(Math.round(total));
    if(document.getElementById('prev-words')) document.getElementById('prev-words').textContent = words+' Only';
  }

  function numberToWords(n) {
    if(n===0) return 'Zero';
    const ones=['','One','Two','Three','Four','Five','Six','Seven','Eight','Nine','Ten','Eleven','Twelve','Thirteen','Fourteen','Fifteen','Sixteen','Seventeen','Eighteen','Nineteen'];
    const tens=['','','Twenty','Thirty','Forty','Fifty','Sixty','Seventy','Eighty','Ninety'];
    const convert = n => {
      if(n<20) return ones[n];
      if(n<100) return tens[Math.floor(n/10)]+(n%10?' '+ones[n%10]:'');
      if(n<1000) return ones[Math.floor(n/100)]+' Hundred'+(n%100?' '+convert(n%100):'');
      if(n<100000) return convert(Math.floor(n/1000))+' Thousand'+(n%1000?' '+convert(n%1000):'');
      if(n<10000000) return convert(Math.floor(n/100000))+' Lakh'+(n%100000?' '+convert(n%100000):'');
      return convert(Math.floor(n/10000000))+' Crore'+(n%10000000?' '+convert(n%10000000):'');
    };
    return convert(n);
  }

  function showGSTInvoice(orderId, buyer, product, qty, amount, hsn) {
    switchOrderTab('gst-invoice');
    setTimeout(()=>{
      if(document.getElementById('inv-buyer')) document.getElementById('inv-buyer').value = buyer;
      if(document.getElementById('inv-no')) document.getElementById('inv-no').value = 'INV-2026-'+orderId;
      if(document.getElementById('inv-qty')) document.getElementById('inv-qty').value = qty;
      const rate = Math.round(parseInt(amount)/parseInt(qty));
      if(document.getElementById('inv-rate')) document.getElementById('inv-rate').value = rate;
      // Select matching product
      const sel = document.getElementById('inv-product');
      if(sel) for(let i=0;i<sel.options.length;i++) { if(sel.options[i].value.includes(hsn)){sel.selectedIndex=i;break;} }
      calcGST();
    },50);
  }

  function printGSTInvoice() {
    const preview = document.getElementById('gst-preview');
    if(!preview) return;
    const w = window.open('','_blank','width=800,height=600');
    w.document.write('<html><head><title>GST बिल — My Supermarket</title><style>body{font-family:Arial,sans-serif;padding:30px;font-size:13px;}table{width:100%;border-collapse:collapse;}th,td{border:1px solid #ccc;padding:6px 8px;}th{background:#f4f4f4;}b{font-weight:700;}</style></head><body>');
    w.document.write(preview.innerHTML);
    w.document.write('</body></html>');
    setTimeout(()=>w.print(),300);
  }

  // Init GST calc on load
  setTimeout(calcGST, 200);
  // Prefill today's date in all date inputs
  (function() {
    const today = new Date().toISOString().split('T')[0];
    const dateFields = ['inv-date'];
    dateFields.forEach(id => { const el = document.getElementById(id); if(el && !el.value) el.value = today; });
    // PT month display
    const ptMonth = document.getElementById('pt-month');
    if(ptMonth) ptMonth.textContent = new Date().toLocaleString('en-IN',{month:'long'});
    const ptAmt = document.getElementById('pt-amount');
    const ptTotal = document.getElementById('pt-total');
    if(ptAmt) {
      const isFeb = new Date().getMonth() === 1;
      ptAmt.textContent = isFeb ? '₹300' : '₹200';
      if(ptTotal) ptTotal.textContent = isFeb ? '₹1,800' : '₹1,200';
    }
  })();
  document.querySelectorAll('.filter-chip').forEach(chip => {
    chip.addEventListener('click', function() {
      const parent = this.parentElement;
      // Reset all chips in this group
      parent.querySelectorAll('.filter-chip').forEach(c => {
        c.classList.remove('active');
        c.style.background = '';
        c.style.color = '';
        c.style.borderColor = '';
        c.style.boxShadow = '';
        // Restore low-stock chip default
        if (c.dataset.filter === 'lowstock' || c.id === 'low-stock-chip') {
          c.style.color = 'var(--warn)';
          c.style.borderColor = '#fca5a5';
          c.style.background = 'linear-gradient(135deg,#fff8f8,#fff2f2)';
        }
      });
      this.classList.add('active');
      const f = this.dataset.filter;
      if (!f) return; // no data-filter → use default CSS active style
      if (f === 'all' || f === 'orders-all') {
        this.style.background = 'linear-gradient(135deg,#4a5568,#2d3748)';
        this.style.color = 'white';
        this.style.borderColor = '#4a5568';
        this.style.boxShadow = '0 4px 14px rgba(74,85,104,0.35), 0 2px 6px rgba(74,85,104,0.2)';
      } else if (f === 'raw') {
        this.style.background = 'linear-gradient(135deg,#d97706,#b45309)';
        this.style.color = 'white';
        this.style.borderColor = '#d97706';
        this.style.boxShadow = '0 4px 14px rgba(217,119,6,0.4), 0 8px 24px rgba(217,119,6,0.2)';
      } else if (f === 'finished') {
        this.style.background = 'linear-gradient(135deg,#0f9e56,#0a7a3e)';
        this.style.color = 'white';
        this.style.borderColor = '#0f9e56';
        this.style.boxShadow = '0 4px 14px rgba(15,158,86,0.4), 0 8px 24px rgba(15,158,86,0.2)';
      } else if (f === 'lowstock') {
        this.style.background = 'linear-gradient(135deg,#e53e3e,#c53030)';
        this.style.color = 'white';
        this.style.borderColor = 'var(--warn)';
        this.style.boxShadow = '0 4px 16px rgba(217,38,38,0.35), 0 8px 24px rgba(217,38,38,0.2)';
      }
    });
  });

// ── Screen-switch hooks (barcode init, POS init, dashboard load, i18n title) ──
// Uses var to avoid let/const redeclaration with inline script
var _origShowScreenBridge = window.showScreen;
window.showScreen = function(id) {
  _origShowScreenBridge(id);
  // Barcode screen init
  if (id === 'barcode') {
    if (typeof renderScanLog === 'function') renderScanLog();
    if (typeof setScanMode === 'function') setScanMode('sale');
    setTimeout(function() { var el = document.getElementById('barcode-input'); if(el) el.focus(); }, 100);
  }
  // POS screen init
  if (id === 'pos') {
    if (typeof posRenderCart === 'function') posRenderCart();
    if (typeof posSelectPayment === 'function') posSelectPayment('upi');
    setTimeout(function() { var el = document.getElementById('pos-barcode-input'); if(el) el.focus(); }, 100);
  }
  // India Law - PT month
  if (id === 'india-law') {
    var m = new Date().getMonth();
    var isFeb = m === 1;
    var mEl = document.getElementById('pt-month');
    var aEl = document.getElementById('pt-amount');
    var tEl = document.getElementById('pt-total');
    if (mEl) mEl.textContent = new Date().toLocaleString('en-IN',{month:'long'});
    if (aEl) aEl.textContent = isFeb ? '₹300' : '₹200';
    if (tEl) tEl.textContent = isFeb ? '₹1,800' : '₹1,200';
  }
  // Dashboard load
  if (id === 'dashboard' && typeof loadDashboard === 'function') {
    loadDashboard();
  }
  // i18n page title
  if (typeof i18n !== 'undefined' && typeof currentLang !== 'undefined') {
    var dict = i18n[currentLang];
    var ptKey = 'pt_' + id.replace('-', '_');
    var titleEl = document.getElementById('page-title');
    if (titleEl && dict && dict[ptKey]) titleEl.textContent = dict[ptKey];
  }
};

// === BLOCK 2: Transliteration + Notepad + Misc ===

(function(){
  var RULES=[
    ['shri','श्री'],['shra','श्र'],['ksh','क्ष'],
    ['dny','ज्ञ'],['gyn','ज्ञ'],['tr','त्र'],
    ['kh','ख'],['gh','घ'],['ch','च'],['Ch','छ'],['jh','झ'],
    ['Th','ठ'],['Dh','ढ'],['th','थ'],['dh','ध'],['ph','फ'],['bh','भ'],
    ['sh','श'],['Sh','ष'],['rr','ऱ'],
    ['aa','आ'],['ii','ई'],['uu','ऊ'],['ee','ई'],['oo','ऊ'],
    ['ai','ऐ'],['au','औ'],
    ['A','आ'],['I','इ'],['U','उ'],['E','ए'],['O','ओ'],
    ['a','अ'],['i','ई'],['u','ऊ'],['e','ए'],['o','ओ'],
    ['k','क'],['g','ग'],['c','क'],['j','ज'],
    ['T','ट'],['D','ड'],['N','ण'],['L','ळ'],
    ['t','त'],['d','द'],['n','न'],
    ['p','प'],['b','ब'],['m','म'],
    ['y','य'],['r','र'],['l','ल'],['v','व'],['w','व'],
    ['s','स'],['h','ह'],['f','फ'],['z','झ'],['q','क'],
    ['M','ं'],['H','ः'],['_','्']
  ];
  var VM={'अ':'','आ':'ा','इ':'ि','ई':'ी',
           'उ':'ु','ऊ':'ू','ए':'े','ऐ':'ै',
           'ओ':'ो','औ':'ौ'};
  var H='्';

  function tr(roman){
    var out='',i=0;
    while(i<roman.length){
      var code=roman.charCodeAt(i);
      if(roman[i]===' '||(code>=0x0900&&code<=0x097F)||
         (code>=48&&code<=57)||(code>=33&&code<=47)||
         (code>=58&&code<=64)||(code>=91&&code<=96)||(code>=123&&code<=126)||
         code===8377){
        out+=roman[i++]; continue;
      }
      var matched=false;
      for(var ri=0;ri<RULES.length;ri++){
        var rom=RULES[ri][0],dev=RULES[ri][1];
        if(roman.substr(i,rom.length)===rom){
          var last=out.length?out[out.length-1]:'';
          var isV=dev in VM;
          if(isV){
            if(last===H){out=out.slice(0,-1);out+=VM[dev];}
            else{out+=dev;}
          } else {
            out+=dev+H;
          }
          i+=rom.length; matched=true; break;
        }
      }
      if(!matched){out+=roman[i++];}
    }
    return out;
  }

  // KEY FIX: maintain a roman buffer per element
  // We store the raw roman keystrokes and retransliterate from scratch each time
  function attach(el){
    if(!el||el._mr)return; el._mr=true;
    var romanBuf=''; // raw roman input buffer

    el.addEventListener('keydown',function(e){
      // Backspace: remove last roman char from buffer
      if(e.key==='Backspace'){
        if(romanBuf.length>0){
          romanBuf=romanBuf.slice(0,-1);
          e.preventDefault();
          el.value=tr(romanBuf);
          el.setSelectionRange(el.value.length,el.value.length);
          el.dispatchEvent(new Event('input',{bubbles:true}));
        }
        return;
      }
      // Enter/arrows etc — don't intercept
      if(e.key.length!==1)return;
      // Space resets word boundary but keeps it in buffer
      if(e.key===' '){
        romanBuf+=' '; e.preventDefault();
        el.value=tr(romanBuf);
        el.setSelectionRange(el.value.length,el.value.length);
        el.dispatchEvent(new Event('input',{bubbles:true}));
        return;
      }
      // Normal char: append to roman buffer, retransliterate
      romanBuf+=e.key;
      e.preventDefault();
      el.value=tr(romanBuf);
      el.setSelectionRange(el.value.length,el.value.length);
      // Fire input event so other handlers (like search, AI detect) still work
      el.dispatchEvent(new Event('input',{bubbles:true}));
    });

    // Reset buffer if user clicks away and back (they may have edited externally)
    el.addEventListener('focus',function(){
      // Sync buffer from current value if it looks like it was set externally
      // (e.g. AI populating the field)
    });
  }

  function init(){
    ['chat-input','np-ai-input','np-search-input','np-textarea','dh-search','inv-buyer']
      .forEach(function(id){attach(document.getElementById(id));});
    document.querySelectorAll('input.search-input[lang="mr"]').forEach(attach);
  }

  document.readyState==='loading'
    ?document.addEventListener('DOMContentLoaded',init)
    :(init(),setTimeout(init,600));
})();

