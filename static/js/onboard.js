/* ==========================================================================
   首次登录 · 分步 Onboarding 新手蒙层引导
   ------------------------------------------------------------------
   - 只有「注册后还没走完引导」的用户会触发（body[data-onboard="1"]）
   - 半透明灰色遮罩盖住全屏，只在目标位置开一个「洞」把它高亮出来
   - 白色虚线箭头从提示卡指向目标，附文字说明
  - 严格 4 步：题库 → 菜园 → 果蔬摊 → 厨房（第 4 步按钮为【开始体验】）
  - 走完 / 跳过 → POST /api/onboard/done 写库，老用户永不再弹
   ========================================================================== */
(function () {
  var body = document.body;
  if (!body || body.getAttribute('data-onboard') !== '1') return;

  var STEPS = [
    { sel: '.nav-card[href="/problems"]', tip: '✍️ 答题时间到！脑力耕地，现在开工！' },
    { sel: '.nav-card[href="/farm"]',     tip: '🥬 脑力值到手！下地耕耘，一起种菜吧！' },
    { sel: '.nav-card[href="/market"]',   tip: '🥬 蔬菜成熟啦！去果蔬摊兑换资源，收获你的劳动成果！' },
    { sel: '.nav-card[href="/kitchen"]',  tip: '🍳 食材就位！进厨房加工，解锁更多惊喜奖励！' }
  ];

  var layer, block, hole, svg, card, elStep, elText, elNext, elSkip, elDots;
  var cur = -1, target = null, started = false, finished = false;

  function mk(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }

  function build() {
    layer = mk('div', 'ob-layer'); layer.id = 'obLayer';

    block = mk('div', 'ob-block'); block.id = 'obBlock';
    hole = mk('div', 'ob-hole'); hole.id = 'obHole';

    svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'ob-arrow');
    svg.setAttribute('id', 'obArrow');
    svg.setAttribute('aria-hidden', 'true');

    card = mk('div', 'ob-card'); card.id = 'obCard';
    card.setAttribute('role', 'dialog');
    card.setAttribute('aria-modal', 'true');
    card.setAttribute('aria-label', '新手引导');

    elStep = mk('div', 'ob-step'); elStep.id = 'obStep';
    elText = mk('div', 'ob-text'); elText.id = 'obText';

    var foot = mk('div', 'ob-foot');
    elSkip = mk('button', 'ob-skip', '跳过引导'); elSkip.id = 'obSkip';
    elSkip.type = 'button';
    elDots = mk('span', 'ob-dots'); elDots.id = 'obDots';
    elNext = mk('button', 'ob-next', '下一步 <b>→</b>'); elNext.id = 'obNext';
    elNext.type = 'button';
    foot.appendChild(elSkip);
    foot.appendChild(elDots);
    foot.appendChild(elNext);

    card.appendChild(elStep);
    card.appendChild(elText);
    card.appendChild(foot);

    layer.appendChild(block);
    layer.appendChild(hole);
    layer.appendChild(svg);
    layer.appendChild(card);
    document.body.appendChild(layer);

    elNext.addEventListener('click', function () {
      if (cur >= STEPS.length - 1) finish(); else go(cur + 1);
    });
    elSkip.addEventListener('click', finish);

    /* 点在高亮区域上 = 下一步（遮罩吃掉其余所有点击） */
    block.addEventListener('click', function (e) {
      var r = target && target.getBoundingClientRect();
      if (r && e.clientX >= r.left - 6 && e.clientX <= r.right + 6 &&
          e.clientY >= r.top - 6 && e.clientY <= r.bottom + 6) {
        if (cur >= STEPS.length - 1) finish(); else go(cur + 1);
      }
    });

    window.addEventListener('resize', place);
    window.addEventListener('scroll', place, true);
  }

  function dots(i) {
    var h = '';
    for (var k = 0; k < STEPS.length; k++) {
      h += '<i class="' + (k === i ? 'on' : '') + '"></i>';
    }
    elDots.innerHTML = h;
  }

  function go(i) {
    if (i >= STEPS.length) { finish(); return; }
    var st = STEPS[i];
    target = null;
    if (st.sel) {
      var el = document.querySelector(st.sel);
      if (!el) { go(i + 1); return; }   /* 该项不存在就跳过 */
      target = el;
    }
    cur = i;
    elStep.textContent = '第 ' + (i + 1) + ' / ' + STEPS.length + ' 步';
    elText.textContent = st.tip;
    dots(i);
    elNext.innerHTML = (i === STEPS.length - 1)
      ? '开始体验 <b>→</b>' : '下一步 <b>→</b>';
    elNext.className = (i === STEPS.length - 1) ? 'ob-next done' : 'ob-next';
    card.className = 'ob-card' + (st.sel ? '' : ' ob-final');
    block.className = 'ob-block' + (st.sel ? '' : ' full');
    /* 滚动到目标：无论环境是否支持，都不能影响引导本身继续走 */
    try {
      if (target && typeof target.scrollIntoView === 'function') {
        try { target.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' }); }
        catch (e) { target.scrollIntoView(); }   /* 老浏览器只支持无参调用 */
      }
    } catch (e2) { /* 环境不支持滚动，忽略 */ }
    requestAnimationFrame(place);
    setTimeout(place, 400);            /* 等平滑滚动落位再重排 */
  }

  function place() {
    if (!card || !layer) return;
    var vw = window.innerWidth, vh = window.innerHeight;
    var cw = card.offsetWidth, ch = card.offsetHeight;

    if (!target) {                      /* 最后一步：无高亮，整屏压暗 */
      hole.style.display = 'none';
      svg.style.display = 'none';
      svg.innerHTML = '';
      card.style.left = Math.max(12, Math.round((vw - cw) / 2)) + 'px';
      card.style.top = Math.max(12, Math.round((vh - ch) / 2)) + 'px';
      return;
    }

    var r = target.getBoundingClientRect();
    hole.style.display = 'block';
    hole.style.left = Math.round(r.left - 5) + 'px';
    hole.style.top = Math.round(r.top - 5) + 'px';
    hole.style.width = Math.round(r.width + 10) + 'px';
    hole.style.height = Math.round(r.height + 10) + 'px';

    var below = (r.bottom + ch + 120) < vh;     /* 目标在上半屏 → 卡片放下方 */
    var top = below ? r.bottom + 86 : r.top - ch - 86;
    top = Math.min(Math.max(top, 12), Math.max(12, vh - ch - 12));
    var left = r.left + r.width / 2 - cw / 2;
    left = Math.min(Math.max(left, 12), Math.max(12, vw - cw - 12));
    card.style.left = Math.round(left) + 'px';
    card.style.top = Math.round(top) + 'px';

    /* 白色虚线箭头：从提示卡指向目标 */
    var sx = left + cw / 2;
    var sy = below ? top : top + ch;
    var ex = r.left + r.width / 2;
    var ey = below ? r.bottom + 8 : r.top - 8;
    var mx = (sx + ex) / 2 + (below ? 54 : -54);
    var my = (sy + ey) / 2;
    var ang = Math.atan2(ey - my, ex - mx);
    var L = 15;
    var a1x = ex - L * Math.cos(ang - 0.5), a1y = ey - L * Math.sin(ang - 0.5);
    var a2x = ex - L * Math.cos(ang + 0.5), a2y = ey - L * Math.sin(ang + 0.5);

    svg.style.display = 'block';
    svg.innerHTML =
      '<path d="M' + sx + ' ' + sy + ' Q' + mx + ' ' + my + ' ' + ex + ' ' + ey + '" ' +
      'fill="none" stroke="#fff" stroke-width="2.6" stroke-dasharray="7 6" ' +
      'stroke-linecap="round" opacity=".95"/>' +
      '<polygon points="' + ex + ',' + ey + ' ' + a1x + ',' + a1y + ' ' + a2x + ',' + a2y + '" ' +
      'fill="#fff"/>';
  }

  function finish() {
    if (finished) return;
    finished = true;
    if (layer) {
      layer.classList.remove('show');
      setTimeout(function () { if (layer.parentNode) layer.parentNode.removeChild(layer); }, 280);
    }
    body.setAttribute('data-onboard', '0');
    try {
      fetch('/api/onboard/done', { method: 'POST', credentials: 'same-origin' });
    } catch (e) { /* 忽略：下次访问再补写 */ }
  }

  function start() {
    if (started || finished) return;
    started = true;
    build();
    requestAnimationFrame(function () { layer.classList.add('show'); });
    go(0);
  }

  /* 等前面的弹窗（注册欢迎 / 每日签到）关掉再开始，避免叠在一起 */
  function waitGone(id, fallback) {
    var t0 = Date.now();
    (function poll() {
      var el = document.getElementById(id);
      if (!el || el.parentNode === null) { start(); return; }
      if (Date.now() - t0 > fallback) { start(); return; }
      setTimeout(poll, 400);
    })();
  }

  var wm = document.getElementById('welcomeMask');
  var sm = document.getElementById('signinMask');

  /* 刚从注册欢迎弹窗跳转过来（签到页）→ 立刻开始，做到「紧接着触发」 */
  var justReg = false;
  try {
    justReg = sessionStorage.getItem('pyoj_just_registered') === '1';
    if (justReg) sessionStorage.removeItem('pyoj_just_registered');
  } catch (e) { /* ignore */ }

  if (justReg) {
    setTimeout(start, 160);
  } else if (wm) {
    document.addEventListener('pyoj:welcomeClosed', start);
    setTimeout(start, 25000);          /* 兜底：欢迎窗异常时也要能进引导 */
  } else if (sm) {
    waitGone('signinMask', 40000);
  } else {
    setTimeout(start, 700);
  }

  window.PYOJ_ONBOARD = { start: start, finish: finish, next: function () { go(cur + 1); } };
})();
