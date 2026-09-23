/* ============================================================
   注册成功后的「全屏欢迎弹窗」—— 严格时序的原生 CSS @keyframes 动画
   ------------------------------------------------------------
   时序（全部由 CSS 关键帧驱动，JS 只负责编排与对齐，零第三方库）：
     阶段 1  放大版苗小序挥手说话 + 对话气泡自我介绍（同时播放合成问候音）
     阶段 2  苗小序缓慢缩小 + 原地完整旋转一圈，飞回页面角落悬浮位置
     阶段 3  落位后尺寸与右下角悬浮小图标完全一致
     阶段 4  亮光消散特效，对话气泡随人物一同消失
     阶段 5  整套动画播完，自动关闭弹窗 → 跳转签到页 /checkin
   老用户登录不会带 welcome_new 这个 cookie，因此登录流程完全不变。
   ============================================================ */
(function () {
  var mask = document.getElementById('welcomeMask');

  /* 首页导语区：默认单行省略，点一下展开完整文案 */
  var note = document.getElementById('welcomeNote');
  if (note) {
    note.style.cursor = 'pointer';
    note.addEventListener('click', function () { note.classList.toggle('open'); });
  }

  if (!mask) return;

  var hero = document.getElementById('wlcHero');
  var bubble = document.getElementById('wlcBubble');
  var flash = document.getElementById('wlcFlash');
  var lines = document.getElementById('wlcLines');
  var hint = document.getElementById('wlcHint');
  var fab = document.getElementById('nanFab');
  var done = false;

  var reduce = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* 时序（毫秒） */
  var T_INTRO = 4200;    /* 阶段 1：挥手 + 自我介绍 */
  var T_FLY = 2600;      /* 阶段 2：缩小 + 旋转一圈飞回 */
  var T_FLASH = 900;     /* 阶段 4：亮光消散 + 气泡消失 */
  var T_FADE = 480;      /* 阶段 5：遮罩淡出 */

  if (reduce) { T_INTRO = 900; T_FLY = 500; T_FLASH = 320; T_FADE = 200; }

  var timers = [];
  function later(fn, ms) { timers.push(setTimeout(fn, ms)); }
  function clearTimers() { timers.forEach(clearTimeout); timers = []; }

  /* ---------------- cookie ---------------- */
  function setCookie(name, val, days) {
    document.cookie = name + '=' + val + '; path=/; max-age=' + (days * 86400) + '; samesite=lax';
  }
  function delCookie(name) {
    document.cookie = name + '=; path=/; max-age=0; samesite=lax';
  }
  function todayStr() {
    var d = new Date();
    return d.getFullYear() + '-' +
      ('0' + (d.getMonth() + 1)).slice(-2) + '-' +
      ('0' + d.getDate()).slice(-2);
  }

  /* ---------------- 问候音（Web Audio 合成，无外部音频文件） ---------------- */
  function playGreet() {
    try {
      var AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      var ctx = new AC();
      if (ctx.state === 'suspended' && ctx.resume) ctx.resume();
      /* 上行四音：C5 E5 G5 E5 —— 轻快的「你好呀」 */
      var notes = [523.25, 659.25, 783.99, 659.25];
      notes.forEach(function (f, i) {
        var o = ctx.createOscillator(), g = ctx.createGain();
        o.type = 'sine';
        o.frequency.value = f;
        var t = ctx.currentTime + i * 0.24;
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(0.16, t + 0.04);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.46);
        o.connect(g); g.connect(ctx.destination);
        o.start(t); o.stop(t + 0.5);
      });
      /* 挥手的两声轻响 */
      [0.98, 1.22].forEach(function (d) {
        var o2 = ctx.createOscillator(), g2 = ctx.createGain();
        o2.type = 'triangle';
        o2.frequency.value = 880;
        var t2 = ctx.currentTime + d;
        g2.gain.setValueAtTime(0.0001, t2);
        g2.gain.exponentialRampToValueAtTime(0.10, t2 + 0.03);
        g2.gain.exponentialRampToValueAtTime(0.0001, t2 + 0.28);
        o2.connect(g2); g2.connect(ctx.destination);
        o2.start(t2); o2.stop(t2 + 0.3);
      });
      later(function () { try { ctx.close(); } catch (e) { /* ignore */ } }, 2600);
    } catch (e) { /* 音频不可用时静默降级，不影响动画 */ }
  }

  /* ---------------- 定位：把 hero 摆到屏幕中央偏上 ---------------- */
  function placeHero() {
    var vw = window.innerWidth, vh = window.innerHeight;
    var w = hero.offsetWidth || 220, h = hero.offsetHeight || 220;
    var cx = vw / 2;
    var cy = Math.max(h / 2 + 40, vh * 0.36);
    hero.style.left = Math.round(cx - w / 2) + 'px';
    hero.style.top = Math.round(cy - h / 2) + 'px';
  }

  /* 气泡挂在 hero 右侧；右边放不下就挂到上方
     注意：只切换挂载方位类，绝不能整体重写 className —— 会清掉 in / go / gone
     状态类，而 .wlc-bubble 默认 opacity:0，气泡就再也显示不出来了 */
  function setBubbleSide(pos) {
    if (!bubble) return;
    if (pos === 'right') { bubble.classList.add('right'); bubble.classList.remove('top'); }
    else { bubble.classList.add('top'); bubble.classList.remove('right'); }
  }
  function placeBubble() {
    if (!bubble) return;
    var r = hero.getBoundingClientRect();
    var bw = bubble.offsetWidth || 240;
    var vw = window.innerWidth;
    if (r.right + bw + 18 < vw) {
      setBubbleSide('right');
      bubble.style.left = Math.round(r.right - 18) + 'px';
      bubble.style.top = Math.round(r.top + r.height * 0.16) + 'px';
    } else {
      setBubbleSide('top');
      bubble.style.left = Math.round(Math.max(12, r.left + r.width / 2 - bw / 2)) + 'px';
      bubble.style.top = Math.round(Math.max(12, r.top - bubble.offsetHeight - 14)) + 'px';
    }
  }

  /* ---------------- 阶段 2：计算飞回悬浮图标的位移与缩放 ---------------- */
  function flyBack() {
    var r = hero.getBoundingClientRect();
    var target;
    if (fab) {
      /* 关掉悬浮球的漂浮动画，量一个稳定位置，落位才能完全对齐 */
      fab.classList.add('nf-static');
      target = fab.getBoundingClientRect();
    } else {
      target = { left: window.innerWidth - 88, top: window.innerHeight - 92,
                 width: 66, height: 66 };
    }

    var hw = hero.offsetWidth || 220;
    var sw = hero.querySelector('svg');
    var svgW = sw ? (sw.offsetWidth || parseFloat(sw.getAttribute('width')) || 220) : hw;
    var fabSvg = 46;                          /* 悬浮图标内苗小序的显示尺寸 */
    var k = Math.max(0.05, fabSvg / svgW);    /* 缩到与悬浮图标一致的比例 */

    var dx = (target.left + target.width / 2) - (r.left + r.width / 2);
    var dy = (target.top + target.height / 2) - (r.top + r.height / 2);

    hero.style.setProperty('--dx', Math.round(dx) + 'px');
    hero.style.setProperty('--dy', Math.round(dy) + 'px');
    hero.style.setProperty('--k', k);
    hero.style.setProperty('--fly', T_FLY + 'ms');
    hero.classList.add('go');
    if (bubble) bubble.classList.add('go');
    if (lines) lines.classList.add('go');
  }

  /* ---------------- 阶段 3+4：对齐尺寸、亮光消散 ---------------- */
  function landAndFade() {
    /* 阶段 3：交给 left/top + 尺寸接管，尺寸与角落悬浮小图标完全一致（66×66 / 苗小序 46） */
    hero.classList.remove('go');
    hero.classList.remove('in');
    hero.style.transform = 'none';
    hero.style.opacity = '1';
    if (fab) {
      var t = fab.getBoundingClientRect();
      hero.style.left = Math.round(t.left + t.width / 2 - 33) + 'px';
      hero.style.top = Math.round(t.top + t.height / 2 - 33) + 'px';
      hero.style.width = '66px';
      hero.style.height = '66px';
      var svg = hero.querySelector('svg');
      if (svg) { svg.setAttribute('width', '46'); svg.setAttribute('height', '46'); }
      fab.classList.remove('nf-static');
      fab.classList.add('nf-welcome-pop');
    }
    hero.classList.add('landed');

    /* 阶段 4：亮光消散 + 气泡随人物一同消失 */
    if (flash) flash.classList.add('on');
    if (bubble) { bubble.classList.remove('go'); bubble.classList.add('gone'); }
    hero.classList.add('gone');
    if (hint) hint.textContent = '苗小序回到角落啦，随时可以找它聊天～';

    later(closeAndGo, T_FLASH);
  }

  /* ---------------- 阶段 5：关闭弹窗 → 跳转签到页 ---------------- */
  function closeAndGo() {
    if (done) return;
    done = true;
    clearTimers();
    /* 一次性标记：欢迎只看一次，刷新 / 下次登录都不再弹 */
    delCookie('welcome_new');
    /* 注册当天不再自动弹每日签到窗，避免和新手指引抢戏（签到页可手动签到） */
    setCookie('pop_signin', todayStr(), 1);
    if (mask) mask.classList.remove('show');

    /* 标记「刚注册完」，下一站（签到页）的新手引导据此立即开始，做到「紧接着触发」 */
    try { sessionStorage.setItem('pyoj_just_registered', '1'); } catch (e) { /* ignore */ }
    try {
      document.dispatchEvent(new CustomEvent('pyoj:welcomeClosed'));
    } catch (e) { /* 老浏览器忽略 */ }

    later(function () {
      window.location.replace('/checkin');
    }, T_FADE);
  }

  /* 允许用户提前跳过（Esc / 点击空白处），仍然走完整收尾流程 */
  mask.addEventListener('click', function (e) { if (e.target === mask) closeAndGo(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeAndGo(); });

  /* ---------------- 开场 ---------------- */
  function open() {
    mask.hidden = false;
    mask.setAttribute('aria-hidden', 'false');
    requestAnimationFrame(function () {
      mask.classList.add('show');
      /* hero 先摆好位置再出场 */
      placeHero();
      hero.classList.add('in');
      requestAnimationFrame(placeBubble);
      if (bubble) bubble.classList.add('in');
      if (lines) lines.classList.add('in');
      playGreet();
      if (window.sgFall) window.sgFall(26);
    });

    /* 阶段 1 → 2 */
    later(flyBack, T_INTRO);
  }

  /* 飞行结束交给 CSS animationend 回调，保证「旋转完整一圈后才落位」 */
  if (hero) {
    hero.addEventListener('animationend', function (e) {
      if (e.animationName === 'wlcFly') landAndFade();
    });
    /* 兜底：极端情况下 animationend 没触发也要继续 */
    later(function () { if (!done && hero.classList.contains('go')) landAndFade(); },
      T_INTRO + T_FLY + 900);
  }

  window.addEventListener('resize', function () {
    if (done || !hero || hero.classList.contains('go')) return;
    placeHero(); placeBubble();
  });

  later(open, 320);
})();
