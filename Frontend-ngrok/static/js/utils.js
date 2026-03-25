// SmartStore ERP — Utility Functions
// Extracted from inline scripts for modular use

// ── Sidebar Toggle ──
var sidebarOpen = true;

function toggleSidebar() {
  var sidebar = document.querySelector('.sidebar');
  var overlay = document.getElementById('sidebar-overlay');
  var bl1 = document.getElementById('bl1');
  var bl2 = document.getElementById('bl2');
  var bl3 = document.getElementById('bl3');
  var isMobile = window.innerWidth <= 768;
  sidebarOpen = !sidebarOpen;
  if (sidebarOpen) {
    sidebar.classList.remove('collapsed');
    if (isMobile && overlay) overlay.classList.add('active');
    if (bl1) bl1.style.transform = 'translateY(7px) rotate(45deg)';
    if (bl2) { bl2.style.opacity = '0'; bl2.style.transform = 'scaleX(0)'; }
    if (bl3) bl3.style.transform = 'translateY(-7px) rotate(-45deg)';
  } else {
    sidebar.classList.add('collapsed');
    if (overlay) overlay.classList.remove('active');
    if (bl1) bl1.style.transform = '';
    if (bl2) { bl2.style.opacity = '1'; bl2.style.transform = ''; }
    if (bl3) bl3.style.transform = '';
  }
}

function closeSidebarMobile() {
  var sidebar = document.querySelector('.sidebar');
  var overlay = document.getElementById('sidebar-overlay');
  var bl1 = document.getElementById('bl1');
  var bl2 = document.getElementById('bl2');
  var bl3 = document.getElementById('bl3');
  if (window.innerWidth <= 768) {
    sidebarOpen = false;
    sidebar.classList.add('collapsed');
    if (overlay) overlay.classList.remove('active');
    if (bl1) bl1.style.transform = '';
    if (bl2) { bl2.style.opacity = '1'; bl2.style.transform = ''; }
    if (bl3) bl3.style.transform = '';
  }
}

// ── Tab Switching ──
function switchPOTab(tab) {
  ['po-list','po-supplier'].forEach(function(t) {
    var el = document.getElementById('po-tab-'+t);
    var btn = document.getElementById('tab-'+t);
    if (el) el.style.display = t===tab ? 'block' : 'none';
    if (btn) btn.classList.toggle('active', t===tab);
  });
}

function switchOrderTab(tab) {
  ['orders','gst-invoice','hsn'].forEach(function(t) {
    var el = document.getElementById('orders-tab-'+t);
    if (el) el.style.display = t===tab ? 'block' : 'none';
    var btnId = 'tab-' + t;
    var btn = document.getElementById(btnId);
    if (btn) btn.classList.toggle('active', t===tab);
  });
}

function switchPayTab(tab) {
  ['payments','gstr1','itc'].forEach(function(t) {
    var el = document.getElementById('pay-tab-'+t);
    if (el) el.style.display = t===tab ? 'block' : 'none';
    var btn = document.getElementById('tab-'+t);
    if (btn) btn.classList.toggle('active', t===tab);
  });
}

// ── Marathi Number Converter ──
function toMrNum(val) {
  if (typeof currentLang === 'undefined' || currentLang !== 'mr') return String(val);
  var digits = ['०','१','२','३','४','५','६','७','८','९'];
  return String(val).replace(/\d/g, function(d) { return digits[d]; });
}

// ── GST Calculator ──
function numberToWords(n) {
  if(n===0) return 'Zero';
  var ones=['','One','Two','Three','Four','Five','Six','Seven','Eight','Nine','Ten','Eleven','Twelve','Thirteen','Fourteen','Fifteen','Sixteen','Seventeen','Eighteen','Nineteen'];
  var tens=['','','Twenty','Thirty','Forty','Fifty','Sixty','Seventy','Eighty','Ninety'];
  var convert = function(n) {
    if(n<20) return ones[n];
    if(n<100) return tens[Math.floor(n/10)]+(n%10?' '+ones[n%10]:'');
    if(n<1000) return ones[Math.floor(n/100)]+' Hundred'+(n%100?' '+convert(n%100):'');
    if(n<100000) return convert(Math.floor(n/1000))+' Thousand'+(n%1000?' '+convert(n%1000):'');
    if(n<10000000) return convert(Math.floor(n/100000))+' Lakh'+(n%100000?' '+convert(n%100000):'');
    return convert(Math.floor(n/10000000))+' Crore'+(n%10000000?' '+convert(n%10000000):'');
  };
  return convert(n);
}

function calcGST() {
  var qtyEl = document.getElementById('inv-qty');
  var rateEl = document.getElementById('inv-rate');
  if (!qtyEl || !rateEl) return;
  var qty = parseFloat(qtyEl.value)||0;
  var rate = parseFloat(rateEl.value)||0;
  var base = qty * rate;
  var prodVal = (document.getElementById('inv-product')?.value)||'';
  var parts = prodVal.split('|');
  var gstRate = parseFloat(parts[2]||5);
  var supply = (document.getElementById('inv-supply')?.value)||'intra';
  var tax = base * gstRate / 100;
  var total = base + tax;

  var fmt = function(n) { return '\u20B9'+Math.round(n).toLocaleString('en-IN'); };
  var prod = parts[0] || '';
  var hsn = parts[1] || '';
  var setVal = function(id, v) { var e = document.getElementById(id); if(e) e.textContent = v; };
  setVal('prev-prod', prod);
  setVal('prev-hsn', hsn);
  setVal('prev-qty', qty+'m');
  setVal('prev-prate', fmt(rate));
  setVal('prev-base', fmt(base));
  setVal('prev-taxable', fmt(base));
  setVal('prev-total', fmt(total));
  setVal('prev-invno', (document.getElementById('inv-no')?.value)||'');
  setVal('prev-date', (document.getElementById('inv-date')?.value)||'');
  setVal('prev-buyer', (document.getElementById('inv-buyer')?.value)||'\u2014');
  setVal('prev-gstin', (document.getElementById('inv-gstin')?.value)||'\u2014');

  var cgstRow = document.getElementById('cgst-row');
  var sgstRow = document.getElementById('sgst-row');
  var igstRow = document.getElementById('igst-row');
  if(supply==='intra') {
    if(cgstRow) { cgstRow.style.display='flex'; var s=cgstRow.querySelector('span'); if(s) s.textContent='CGST @'+(gstRate/2)+'%'; }
    if(sgstRow) { sgstRow.style.display='flex'; var s2=sgstRow.querySelector('span'); if(s2) s2.textContent='SGST @'+(gstRate/2)+'%'; }
    if(igstRow) igstRow.style.display='none';
    setVal('prev-cgst', fmt(tax/2));
    setVal('prev-sgst', fmt(tax/2));
  } else {
    if(cgstRow) cgstRow.style.display='none';
    if(sgstRow) sgstRow.style.display='none';
    if(igstRow) { igstRow.style.display='flex'; var s3=igstRow.querySelector('span'); if(s3) s3.textContent='IGST @'+gstRate+'%'; }
    setVal('prev-igst', fmt(tax));
  }
  var words = numberToWords(Math.round(total));
  setVal('prev-words', words+' Only');
}

function showGSTInvoice(orderId, buyer, product, qty, amount, hsn) {
  switchOrderTab('gst-invoice');
  setTimeout(function(){
    if(document.getElementById('inv-buyer')) document.getElementById('inv-buyer').value = buyer;
    if(document.getElementById('inv-no')) document.getElementById('inv-no').value = 'INV-2026-'+orderId;
    if(document.getElementById('inv-qty')) document.getElementById('inv-qty').value = qty;
    var rate = Math.round(parseInt(amount)/parseInt(qty));
    if(document.getElementById('inv-rate')) document.getElementById('inv-rate').value = rate;
    var sel = document.getElementById('inv-product');
    if(sel) for(var i=0;i<sel.options.length;i++) { if(sel.options[i].value.includes(hsn)){sel.selectedIndex=i;break;} }
    calcGST();
  },50);
}

function printGSTInvoice() {
  var preview = document.getElementById('gst-preview');
  if(!preview) return;
  var w = window.open('','_blank','width=800,height=600');
  w.document.write('<html><head><title>GST Bill \u2014 My Supermarket</title><style>body{font-family:Arial,sans-serif;padding:30px;font-size:13px;}table{width:100%;border-collapse:collapse;}th,td{border:1px solid #ccc;padding:6px 8px;}th{background:#f4f4f4;}b{font-weight:700;}</style></head><body>');
  w.document.write(preview.innerHTML);
  w.document.write('</body></html>');
  w.close();
}

// ── PO & Reminders ──
function sendPO(btnId, item) {
  var btn = document.getElementById(btnId);
  if(!btn) return;
  btn.textContent = '\u2705 PO Sent!';
  btn.classList.add('sent'); btn.disabled = true;
  if (typeof toast === 'function') toast('\uD83D\uDCE6 PO Sent: ' + item.split(' - ')[0].substring(0,28), 'success');
  setTimeout(function() { btn.disabled = false; btn.classList.remove('sent'); btn.textContent = '\u26A1 Send Purchase Order'; }, 4000);
}

function sendBulkPO() {
  var origTexts = {};
  ['bulk-po-btn', 'bulk-po-btn2'].forEach(function(id) {
    var b = document.getElementById(id);
    if (b) {
      origTexts[id] = b.textContent;
      b.textContent = '\u2705 All POs Sent!';
      b.style.background = '#0f9e56';
      b.disabled = true;
    }
  });
  setTimeout(function() {
    ['bulk-po-btn', 'bulk-po-btn2'].forEach(function(id) {
      var b = document.getElementById(id);
      if (b) {
        b.textContent = origTexts[id];
        b.style.background = '';
        b.disabled = false;
      }
    });
  }, 3000);
}

function sendAllReminders() {
  var overlay = document.getElementById('reminder-overlay');
  var countEl = document.getElementById('reminder-count-num');
  var bar = document.getElementById('reminder-bar');
  if (!overlay || !countEl || !bar) { if(typeof toast==='function') toast('Reminders sent!','success'); return; }
  overlay.classList.add('show');
  var count = 3;
  countEl.textContent = count;
  bar.style.width = '100%';
  var interval = setInterval(function() {
    count--;
    countEl.textContent = count;
    bar.style.width = (count / 3 * 100) + '%';
    if (count <= 0) {
      clearInterval(interval);
      setTimeout(function() {
        overlay.classList.remove('show');
        var result = document.getElementById('reminder-result');
        if (result) { result.classList.add('show'); setTimeout(function(){result.classList.remove('show');}, 5000); }
        if(typeof toast==='function') toast('3 reminders sent via WhatsApp!', 'success');
      }, 600);
    }
  }, 1000);
}

// ── AI Pie Chart ──
var pieData = [
  { label: 'Amul Butter 500g', pct: 42, color: '#7c3aed' },
  { label: 'Tata Salt 1kg', pct: 34, color: '#e53e3e' },
  { label: 'Maggi Noodles 70g', pct: 24, color: '#d97706' }
];

function drawPie(hovered) {
  if (typeof hovered === 'undefined') hovered = -1;
  var canvas = document.getElementById('forecastPie');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');
  var cx = 70, cy = 70, r = 55, inner = 30;
  ctx.clearRect(0, 0, 140, 140);
  var startAngle = -Math.PI / 2;
  pieData.forEach(function(d, i) {
    var slice = (d.pct / 100) * 2 * Math.PI;
    var isHov = hovered === i;
    var offset = isHov ? 7 : 0;
    var midAngle = startAngle + slice / 2;
    var ox = Math.cos(midAngle) * offset;
    var oy = Math.sin(midAngle) * offset;
    ctx.beginPath();
    ctx.moveTo(cx + ox, cy + oy);
    ctx.arc(cx + ox, cy + oy, isHov ? r + 5 : r, startAngle, startAngle + slice);
    ctx.arc(cx + ox, cy + oy, inner, startAngle + slice, startAngle, true);
    ctx.closePath();
    if (isHov) { ctx.shadowColor = d.color; ctx.shadowBlur = 16; }
    ctx.fillStyle = d.color;
    ctx.globalAlpha = isHov ? 1 : 0.88;
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.globalAlpha = 1;
    startAngle += slice;
  });
  ctx.beginPath();
  ctx.arc(cx, cy, inner - 1, 0, 2 * Math.PI);
  ctx.fillStyle = 'white';
  ctx.fill();
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
  var legend = document.getElementById('pie-legend');
  if (!legend) return;
  legend.innerHTML = pieData.map(function(d,i) {
    return '<div style="display:flex;align-items:center;gap:8px;padding:5px 8px;border-radius:8px;background:rgba(255,255,255,0.6);border:1px solid rgba(255,255,255,0.8);transition:all 0.2s;cursor:default;">' +
      '<div style="width:10px;height:10px;border-radius:3px;background:'+d.color+';flex-shrink:0;box-shadow:0 1px 6px '+d.color+'66;"></div>' +
      '<span style="font-family:Mukta,sans-serif;font-size:11px;font-weight:600;color:#2d3748;flex:1;">'+d.label+'</span>' +
      '<span style="font-family:Mukta,sans-serif;font-size:10px;color:'+d.color+';font-weight:700;">'+d.pct+'%</span></div>';
  }).join('');
}

// ── Chat Language Toggle ──
var chatLangMarathi = false;
var _mrBuf = '';

function toggleChatLang() {
  chatLangMarathi = !chatLangMarathi;
  var btn = document.getElementById('chat-lang-btn');
  var input = document.getElementById('chat-input');
  var hint = document.getElementById('chat-lang-hint');
  _mrBuf = '';
  if (input) input.value = '';
  if (chatLangMarathi) {
    if (btn) { btn.textContent = '\u092E\u093E'; btn.classList.add('active'); }
    if (input) input.placeholder = 'Type your message here...';
    if (hint) { hint.innerHTML = '\u2328\uFE0F Marathi Mode'; hint.classList.add('show'); setTimeout(function(){hint.classList.remove('show');}, 4000); }
  } else {
    if (btn) { btn.textContent = 'EN'; btn.classList.remove('active'); }
    if (input) input.placeholder = 'Ask anything \u2014 stock, sales, expiry, schemes, dealers...';
    if (hint) { hint.innerHTML = '\u2328\uFE0F English mode'; hint.classList.add('show'); setTimeout(function(){hint.classList.remove('show');}, 3000); }
  }
  if (input) input.focus();
}

// ── DataHub ──
var dhData = [];
var dhHeaders = [];
var dhSheetURL = '';

function setDHStatus(type, msg) {
  var el = document.getElementById('dh-status');
  if (!el) return;
  el.className = 'dh-status ' + type;
  el.textContent = msg;
}

function renderDHTable(data) {
  // Placeholder — actual rendering handled by tools.js loadDataHub
}

function loadSheetData() {
  setDHStatus('loading', 'Connecting to Google Sheet...');
  setTimeout(function() {
    setDHStatus('connected', 'Sheet connected (demo mode)');
    if(typeof toast==='function') toast('Google Sheet connected!', 'success');
  }, 1500);
}

function refreshDataHub() {
  if(dhSheetURL) { loadSheetData(); return; }
  if(typeof loadDataHub === 'function') { loadDataHub(); return; }
  setDHStatus('loading','Refreshing...');
  var btn = document.getElementById('refresh-btn');
  if(btn) btn.classList.add('spinning');
  setTimeout(function(){
    setDHStatus('connected','Data refreshed');
    if(btn) btn.classList.remove('spinning');
  }, 800);
}

function connectSheet() {
  var urlInput = document.getElementById('sheet-url-input');
  var url = urlInput ? urlInput.value.trim() : '';
  if(!url) { setDHStatus('error','Please paste a Google Sheet URL'); return; }
  dhSheetURL = url;
  loadSheetData();
}

function exportTableCSV() {
  if(typeof toast==='function') toast('CSV exported!', 'success');
  // If DataHub has real data, export it
  var table = document.querySelector('#screen-datahub table');
  if (!table) { alert('No data to export'); return; }
  var csv = '';
  var rows = table.querySelectorAll('tr');
  rows.forEach(function(row) {
    var cols = row.querySelectorAll('td, th');
    var rowData = [];
    cols.forEach(function(col) { rowData.push('"' + col.textContent.replace(/"/g,'""') + '"'); });
    csv += rowData.join(',') + '\n';
  });
  var a = document.createElement('a');
  a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
  a.download = 'datahub-export-'+Date.now()+'.csv';
  a.click();
}
