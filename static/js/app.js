/* PyOJ 前端通用脚本 */

/* ---------- 顶部轮播 Banner：自动循环 + 手动左右滑动 ---------- */
function initBanner() {
  const wrap = document.getElementById('banner');
  if (!wrap) return;
  const track = document.getElementById('bannerTrack');
  const dots = wrap.querySelectorAll('.banner-dot');
  const cards = track ? track.querySelectorAll('.banner-card') : [];
  if (!track || !cards.length) return;

  let idx = 0, timer = null;
  const bars = wrap.querySelectorAll('.bc-timer i');

  /* 进度条动画重播：让底部计时线和当前这张海报对齐（周期同为 4.2s） */
  function restartBars() {
    bars.forEach(function (b) {
      b.style.animation = 'none';
      void b.offsetWidth;            // 强制重排，动画才会重新开始
      b.style.animation = '';
    });
  }

  function go(i) {
    idx = (i + cards.length) % cards.length;
    track.style.transform = 'translateX(' + (-idx * 100) + '%)';
    dots.forEach(function (d, k) { d.classList.toggle('on', k === idx); });
    restartBars();
  }
  function start() { stop(); timer = setInterval(function () { go(idx + 1); }, 4200); }
  function stop() { if (timer) { clearInterval(timer); timer = null; } }

  go(0);
  start();

  wrap.addEventListener('mouseenter', stop);
  wrap.addEventListener('mouseleave', start);

  const prev = wrap.querySelector('.banner-arrow.prev');
  const next = wrap.querySelector('.banner-arrow.next');
  if (prev) prev.addEventListener('click', function (e) { e.preventDefault(); go(idx - 1); start(); });
  if (next) next.addEventListener('click', function (e) { e.preventDefault(); go(idx + 1); start(); });
  dots.forEach(function (d, k) {
    d.addEventListener('click', function (e) { e.preventDefault(); go(k); start(); });
  });

  /* 触摸滑动 */
  let x0 = null;
  wrap.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; stop(); },
                        { passive: true });
  wrap.addEventListener('touchend', function (e) {
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 40) go(idx + (dx < 0 ? 1 : -1));
    x0 = null;
    start();
  });

  /* 鼠标拖拽 */
  let dragging = false, sx = 0;
  wrap.addEventListener('mousedown', function (e) { dragging = true; sx = e.clientX; stop(); });
  wrap.addEventListener('mouseup', function (e) {
    if (!dragging) return;
    dragging = false;
    const dx = e.clientX - sx;
    if (Math.abs(dx) > 60) go(idx + (dx < 0 ? 1 : -1));
    start();
  });
  wrap.addEventListener('mouseleave', function () { dragging = false; });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initBanner);
} else {
  initBanner();
}

function toast(msg, ms) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('show'), ms || 2200);
}

async function post(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {})
  });
  if (res.status === 401) { toast('请先登录'); location.href = '/login'; return null; }
  return await res.json();
}

function esc(s) {
  return String(s === null || s === undefined ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/* 收藏切换 */
async function toggleFav(pid, btn) {
  const r = await post('/api/favorite', { pid: pid });
  if (!r || r.code !== 0) { toast(r ? r.msg : '操作失败'); return; }
  const on = r.data.fav;
  if (btn) {
    btn.textContent = on ? '★ 已收藏' : '☆ 收藏';
    btn.classList.toggle('btn-primary', on);
  }
  toast(r.msg);
}

/* 打卡 */
async function doCheckin(btn) {
  const r = await post('/api/checkin', {});
  if (!r) return;
  toast(r.msg);
  if (r.code === 0) {
    if (btn) { btn.disabled = true; btn.textContent = '✅ 今日已打卡'; }
    setTimeout(() => location.reload(), 900);
  }
}

/* ---------- 通用弹窗（科普卡片等） ---------- */
function closeModal() {
  const m = document.getElementById('modalMask');
  if (m) m.remove();
}

function openModal(inner) {
  closeModal();
  const mask = document.createElement('div');
  mask.className = 'modal-mask';
  mask.id = 'modalMask';
  mask.innerHTML = `<div class="modal">${inner}</div>`;
  mask.addEventListener('click', function (e) { if (e.target === mask) closeModal(); });
  document.body.appendChild(mask);
  requestAnimationFrame(function () { mask.classList.add('show'); });
}

/* 科普卡片弹窗
   o = { emoji, tag, kind, title, body, sub, foot, link } */
function showTip(o) {
  o = o || {};
  openModal(`
    <div class="tip-card ${o.kind || ''}">
      <div class="tip-emoji">${o.emoji || '🌱'}</div>
      ${o.tag ? `<span class="tip-tag">${esc(o.tag)}</span>` : ''}
      <h3 class="tip-title">${esc(o.title || '')}</h3>
      ${o.sub ? `<div class="tip-sub">${esc(o.sub)}</div>` : ''}
      <div class="tip-body">${esc(o.body || '')}</div>
      ${o.foot || ''}
      <div class="tip-actions">
        <button class="btn btn-primary" onclick="closeModal()">知道啦</button>
        ${o.link || ''}
      </div>
    </div>`);
}

document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') closeModal();
});

/* 代码框支持 Tab 缩进 */
document.addEventListener('keydown', function (e) {
  if (e.key === 'Tab' && e.target.classList && e.target.classList.contains('code')) {
    e.preventDefault();
    const t = e.target, s = t.selectionStart, en = t.selectionEnd;
    t.value = t.value.substring(0, s) + '    ' + t.value.substring(en);
    t.selectionStart = t.selectionEnd = s + 4;
  }
});

/* 渲染判题结果 */
function renderResult(box, res) {
  if (!box) return;
  const map = { accepted: 'ok', wrong: 'bad', error: 'bad', timeout: 'warn' };
  const cls = map[res.status] || 'warn';
  const titleMap = {
    accepted: '✅ 全部通过',
    wrong: '❌ 未通过',
    error: '⚠️ 运行出错',
    timeout: '⏰ 执行超时'
  };
  let html = `<div class="result ${cls}">`;
  html += `<strong>${titleMap[res.status] || res.status}</strong>`;
  if (res.status === 'accepted') {
    html += ` · ${res.passed}/${res.total} 个测试用例通过`;
  } else if (res.message) {
    html += ` · ${esc(res.message)}`;
  }
  if (res.passed !== undefined && res.status !== 'accepted') {
    html += ` · 通过 ${res.passed}/${res.total}`;
  }
  html += '</div>';

  const fails = (res.results || []).filter(r => !r.ok);
  if (fails.length) {
    html += `<div class="result bad"><strong>未通过的用例</strong>`;
    fails.slice(0, 5).forEach(r => {
      html += `<div class="case">输入 ${esc(JSON.stringify(r.args))} → 期望 ` +
        `${esc(JSON.stringify(r.expected))}，实际 ${esc(JSON.stringify(r.got))}` +
        (r.error ? ` （${esc(r.error)}）` : '') + `</div>`;
    });
    html += '</div>';
  }
  if (res.stdout && res.stdout.trim()) {
    html += `<div class="result warn"><strong>程序输出</strong><pre>${esc(res.stdout)}</pre></div>`;
  }
  box.innerHTML = html;
}


/* ---------- 撒落元素（田园 emoji）：签到弹窗 / 注册欢迎弹窗共用 ---------- */
function sgFall(n) {
  var EMOJI = ['🍃', '🌸', '🌾', '🍅', '🌻', '🌿', '🥕', '🌼', '✨'];
  var reduce = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) n = Math.min(n, 8);
  var l = document.getElementById('sgLeaves');
  if (!l) {
    l = document.createElement('div');
    l.id = 'sgLeaves';
    l.className = 'sg-leaves';
    document.body.appendChild(l);
  }
  for (var i = 0; i < n; i++) {
    var s = document.createElement('span');
    s.className = 'sg-leaf';
    s.textContent = EMOJI[Math.floor(Math.random() * EMOJI.length)];
    s.style.left = (Math.random() * 100).toFixed(2) + '%';
    s.style.fontSize = (15 + Math.random() * 17).toFixed(0) + 'px';
    s.style.setProperty('--dx', (Math.random() * 160 - 80).toFixed(0) + 'px');
    s.style.setProperty('--rot', (Math.random() * 900 - 450).toFixed(0) + 'deg');
    s.style.animationDuration = (1.9 + Math.random() * 1.7).toFixed(2) + 's';
    s.style.animationDelay = (Math.random() * 1.0).toFixed(2) + 's';
    s.addEventListener('animationend', function () { this.remove(); });
    l.appendChild(s);
  }
}
