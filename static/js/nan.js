/* ==========================================================================
   一、导航卡片：给当前页面所在项加高亮
   二、全局悬浮 AI 助手「苗小序」：可拖拽 + 浮层对话 + 语音输入
      —— 不跳转页面，收起后只留小图标，任何页面都在
   ========================================================================== */

function initNavCards() {
  const links = document.querySelectorAll('.nav-card');
  const path = location.pathname;
  let best = null, bestLen = 0;
  links.forEach(function (a) {
    const href = a.getAttribute('href') || '';
    if (href === '/' || !href) return;
    if (path === href || path.indexOf(href + '/') === 0) {
      if (href.length > bestLen) { bestLen = href.length; best = a; }
    }
  });
  links.forEach(function (a) { a.classList.remove('on'); });
  if (best) best.classList.add('on');
}

const NAN = (function () {
  let fab, panel, body, input, sendBtn, micBtn, minBtn, xBtn;
  let history = [];
  let opened = false;
  let recog = null;
  const POS_KEY = 'nanFabPos';
  const state = { svg: '<span>🌱</span>' };

  function svgOf(box) {
    const s = box ? box.querySelector('svg') : null;
    return s ? s.outerHTML : '<span>🌱</span>';
  }

  function addMsg(who, txt) {
    const row = document.createElement('div');
    row.className = 'np-msg ' + (who === 'me' ? 'me' : 'ai');
    if (who === 'me') {
      row.innerHTML = '<div class="np-av">我</div><div class="np-bub"></div>';
    } else {
      row.innerHTML = '<div class="np-av">' + state.svg + '</div><div class="np-bub"></div>';
    }
    row.querySelector('.np-bub').textContent = txt;
    body.appendChild(row);
    body.scrollTop = body.scrollHeight;
    return row.querySelector('.np-bub');
  }

  /* 面板跟随悬浮图标摆放，并限制在视口内 */
  function place() {
    if (!opened) return;
    const r = fab.getBoundingClientRect();
    const pw = panel.offsetWidth, ph = panel.offsetHeight;
    let left = r.right - pw;
    if (left + pw > window.innerWidth - 10) left = window.innerWidth - pw - 10;
    if (left < 10) left = 10;
    let top = r.top - ph - 12;
    if (top < 10) top = Math.min(r.bottom + 12, window.innerHeight - ph - 10);
    if (top < 10) top = 10;
    panel.style.left = Math.round(left) + 'px';
    panel.style.top = Math.round(top) + 'px';
  }

  function open() {
    if (opened) return;
    opened = true;
    panel.hidden = false;
    fab.classList.add('open');
    place();
    if (!body.children.length) {
      addMsg('ai', '嗨～我是苗小序 🌱\n有什么 Python 上的问题，尽管问我吧！\n' +
                   '也可以点下面的快捷问题，或者按 🎤 用语音提问～');
    }
    setTimeout(function () { input.focus(); }, 60);
  }

  function close() {
    opened = false;
    panel.hidden = true;
    fab.classList.remove('open');
    stopVoice();
  }

  async function send(q) {
    q = (q || '').trim();
    if (!q) return;
    if (fab.dataset.login !== '1') {
      addMsg('ai', '要先登录才能和我聊天哦～ 登录后我就能陪你刷题啦 🌱');
      return;
    }
    addMsg('me', q);
    input.value = '';
    const bub = addMsg('ai', '');
    bub.innerHTML = '<span class="np-typing"><i></i><i></i><i></i></span>让我想想…';
    sendBtn.disabled = true;

    const r = await post('/api/ai/chat', { message: q, action: 'chat', history: history });
    sendBtn.disabled = false;
    if (!r) { bub.textContent = '网络好像不太顺畅，稍后再试一次～'; return; }
    if (r.code !== 0) { bub.textContent = r.msg || '我好像卡住了…'; return; }
    bub.textContent = r.data.text;
    history.push({ role: 'user', content: q });
    history.push({ role: 'assistant', content: r.data.text });
    if (history.length > 16) history = history.slice(-16);
    body.scrollTop = body.scrollHeight;
  }

  /* ---------- 语音输入：浏览器本地识别，识别完自动发送 ---------- */
  function stopVoice() {
    if (recog) { try { recog.stop(); } catch (e) { /* ignore */ } }
    if (micBtn) micBtn.classList.remove('on');
  }

  function startVoice() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      toast('当前浏览器不支持语音输入，可换 Chrome / Edge 试试');
      return;
    }
    if (micBtn.classList.contains('on')) { stopVoice(); return; }
    try {
      recog = new SR();
    } catch (e) {
      toast('语音识别初始化失败');
      return;
    }
    recog.lang = 'zh-CN';
    recog.interimResults = true;
    recog.continuous = false;
    let finalText = '';
    micBtn.classList.add('on');
    recog.onresult = function (ev) {
      let interim = '';
      for (let i = ev.resultIndex; i < ev.results.length; i++) {
        const t = ev.results[i][0].transcript;
        if (ev.results[i].isFinal) { finalText += t; } else { interim += t; }
      }
      input.value = finalText + interim;
    };
    recog.onerror = function (ev) {
      micBtn.classList.remove('on');
      if (ev.error === 'not-allowed') { toast('麦克风权限被拒绝，请在浏览器地址栏允许'); }
      else if (ev.error !== 'aborted') { toast('语音识别失败：' + ev.error); }
    };
    recog.onend = function () {
      micBtn.classList.remove('on');
      const said = (finalText || input.value || '').trim();
      if (said) { send(said); }
    };
    try { recog.start(); } catch (e) { micBtn.classList.remove('on'); }
  }

  /* ---------- 拖拽：鼠标 / 触摸统一用 Pointer 事件 ---------- */
  /* ------------------------------------------------------------------
     分板块动作：苗小序在不同页面加载不同的田园动作（纯 CSS @keyframes）
       菜园 /farm    → 循环 耕地 → 浇水 → 施肥（每步 2.2s，一轮 6.6s）
       厨房 /kitchen → 循环 切菜 → 做菜（每步 1.8s，一轮 3.6s）
       商店 /shop    → 循环 原地转圈 + 招手（一轮 3.4s）
       果蔬摊 /market→ 循环 原地转圈 + 挥手（一轮 3.4s）
       其余页面      → 不加动作类，保持常驻待机，不重复动作
     说明：JS 只负责按路径加 class + 轮换阶段，动作本身全由 CSS 关键帧完成，
           不引入任何外部动画库，保证页面加载流畅。
     ------------------------------------------------------------------ */
  var ACT_STEPS = {
    farm:    { texts: ['耕地', '浇水', '施肥'], step: 2200 },
    kitchen: { texts: ['切菜', '做菜'], step: 1800 },
    shop:    { texts: ['招手'], step: 3400 },
    market:  { texts: ['挥手'], step: 3400 }
  };
  var ACT_CLASSES = ['act-farm', 'act-kitchen', 'act-shop', 'act-market'];
  var PHASES = ['ph-0', 'ph-1', 'ph-2'];
  var actTimer = null;

  function pageActMode() {
    var p = location.pathname || '/';
    if (p.indexOf('/farm') === 0) return 'farm';
    if (p.indexOf('/kitchen') === 0) return 'kitchen';
    if (p.indexOf('/shop') === 0) return 'shop';
    if (p.indexOf('/market') === 0) return 'market';
    return '';
  }

  function initActMode() {
    var mode = pageActMode();
    var label = document.getElementById('nfAct');
    if (actTimer) { clearInterval(actTimer); actTimer = null; }
    ACT_CLASSES.forEach(function (c) { fab.classList.remove(c); });
    PHASES.forEach(function (c) { fab.classList.remove(c); });

    if (!mode) {                       /* 其余页面：不做动作 */
      if (label) { label.textContent = ''; label.classList.remove('on'); }
      fab.removeAttribute('data-act');
      return;
    }

    fab.classList.add('act-' + mode);
    fab.setAttribute('data-act', mode);
    var cfg = ACT_STEPS[mode];
    var texts = cfg.texts;
    var k = 0;

    function setPhase(i) {
      PHASES.forEach(function (c) { fab.classList.remove(c); });
      fab.classList.add('ph-' + (i % 3));
    }

    function tick() {
      if (label) {
        label.textContent = texts[k % texts.length];
        label.classList.add('on');
      }
      /* 阶段 class 与文字同步：CSS 据此播放对应的道具与身体动作 */
      setPhase(k % texts.length);
      k++;
    }
    tick();
    if (texts.length > 1) actTimer = setInterval(tick, cfg.step);
  }

  function initDrag() {
    let dragging = false, moved = false, sx = 0, sy = 0, ox = 0, oy = 0;

    function clamp(x, y) {
      const w = fab.offsetWidth, h = fab.offsetHeight;
      return [Math.max(6, Math.min(x, window.innerWidth - w - 6)),
              Math.max(6, Math.min(y, window.innerHeight - h - 6))];
    }
    function setPos(x, y) {
      const p = clamp(x, y);
      fab.style.left = p[0] + 'px';
      fab.style.top = p[1] + 'px';
      fab.style.right = 'auto';
      fab.style.bottom = 'auto';
    }

    try {
      const saved = JSON.parse(localStorage.getItem(POS_KEY) || 'null');
      if (saved && typeof saved.x === 'number' && typeof saved.y === 'number') {
        setPos(saved.x, saved.y);
      }
    } catch (e) { /* ignore */ }

    fab.addEventListener('pointerdown', function (e) {
      if (e.button && e.button !== 0) { return; }
      dragging = true; moved = false;
      sx = e.clientX; sy = e.clientY;
      const r = fab.getBoundingClientRect();
      ox = e.clientX - r.left; oy = e.clientY - r.top;
      if (fab.setPointerCapture) {
        try { fab.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
      }
      fab.classList.add('dragging');
    });

    fab.addEventListener('pointermove', function (e) {
      if (!dragging) { return; }
      if (!moved && (Math.abs(e.clientX - sx) > 5 || Math.abs(e.clientY - sy) > 5)) {
        moved = true;
      }
      if (moved) { setPos(e.clientX - ox, e.clientY - oy); place(); }
    });

    function endDrag() {
      if (!dragging) { return; }
      dragging = false;
      fab.classList.remove('dragging');
      if (moved) {
        const r = fab.getBoundingClientRect();
        try {
          localStorage.setItem(POS_KEY, JSON.stringify(
            { x: Math.round(r.left), y: Math.round(r.top) }));
        } catch (e) { /* ignore */ }
      } else {
        if (opened) { close(); } else { open(); }   // 没拖动 = 点击
      }
      setTimeout(function () { moved = false; }, 0);
    }
    fab.addEventListener('pointerup', endDrag);
    fab.addEventListener('pointercancel', function () {
      dragging = false;
      fab.classList.remove('dragging');
    });

    fab.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        if (opened) { close(); } else { open(); }
      }
    });

    window.addEventListener('resize', place);
    window.addEventListener('scroll', place, { passive: true });
  }

  function init() {
    fab = document.getElementById('nanFab');
    panel = document.getElementById('nanPanel');
    if (!fab || !panel) { return; }
    body = document.getElementById('npBody');
    input = document.getElementById('npText');
    sendBtn = document.getElementById('npSend');
    micBtn = document.getElementById('npMic');
    minBtn = document.getElementById('npMin');
    xBtn = document.getElementById('npX');

    state.svg = svgOf(panel.querySelector('.np-head .np-av'));

    initActMode();

    initDrag();

    sendBtn.addEventListener('click', function () { send(input.value); });
    micBtn.addEventListener('click', startVoice);
    minBtn.addEventListener('click', close);
    xBtn.addEventListener('click', close);

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        send(input.value);
      }
    });

    const quick = document.getElementById('npQuick');
    if (quick) {
      quick.addEventListener('click', function (e) {
        const b = e.target.closest ? e.target.closest('button[data-q]') : null;
        if (b) { send(b.getAttribute('data-q')); }
      });
    }

    window.NAN = { open: open, close: close, send: send };
  }

  return { init: init };
})();

function bootNan() {
  initNavCards();
  NAN.init();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootNan);
} else {
  bootNan();
}
