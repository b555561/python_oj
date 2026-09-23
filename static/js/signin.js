/* ============================================================
   登录后的「每日签到弹窗」+ 撒落元素动画
   - 只在当天首次打开站点时弹一次（关闭后写 cookie pop_signin）
   - 打开瞬间撒下叶子/花瓣/果实等田园元素
   - 签到成功再撒一波更大的，并换成当天的祝福语
   ============================================================ */
(function () {
  var mask = document.getElementById('signinMask');
  if (!mask) return;

  var btn = document.getElementById('sgBtn');
  var later = document.getElementById('sgLater');
  var closeBtn = document.getElementById('sgX');
  var blessBox = document.getElementById('sgBless');
  var streakBox = document.getElementById('sgStreak');
  var today = mask.dataset.today || '';
  /* 撒落元素走全局 sgFall（app.js 提供，注册欢迎弹窗复用同一套） */
  var fall = window.sgFall || function () {};

  function open() {
    mask.hidden = false;
    mask.setAttribute('aria-hidden', 'false');
    requestAnimationFrame(function () { mask.classList.add('show'); });
    setTimeout(function () { fall(30); }, 150);
  }

  function close() {
    if (!mask || mask.dataset.closed === '1') return;
    mask.dataset.closed = '1';
    mask.classList.remove('show');
    if (today) {
      document.cookie = 'pop_signin=' + today + '; path=/; max-age=43200; samesite=lax';
    }
    setTimeout(function () {
      if (mask && mask.parentNode) mask.parentNode.removeChild(mask);
      var l = document.getElementById('sgLeaves');
      if (l) setTimeout(function () { if (l.parentNode) l.parentNode.removeChild(l); }, 2800);
    }, 280);
  }

  function done(text) {
    if (btn) { btn.textContent = text; btn.classList.add('done'); btn.disabled = true; }
  }

  if (btn && !btn.classList.contains('done')) {
    btn.addEventListener('click', async function () {
      btn.disabled = true;
      btn.textContent = '签到中…';
      var r = null;
      try { r = await post('/api/checkin', {}); } catch (e) { r = null; }
      if (r && r.code === 0) {
        done('✅ 签到成功 · 能量 +' + (r.data.e_gain || 0));
        if (streakBox && r.data.streak) streakBox.textContent = r.data.streak;
        if (blessBox && r.data.bless) {
          blessBox.innerHTML = '<span class="sg-em">' + (r.data.emoji || '🌾') +
            '</span><span>' + r.data.bless + '</span>';
        }
        fall(70);
        if (typeof toast === 'function') toast(r.msg);
        setTimeout(close, 1700);
      } else {
        if (r && r.code === 1) {                 /* 今天已打过卡 */
          done('✅ 今日已签到');
          setTimeout(close, 1200);
        } else {
          btn.disabled = false;
          btn.textContent = '🌾 再试一次';
        }
        if (r && typeof toast === 'function') toast(r.msg);
      }
    });
  }

  if (later) later.addEventListener('click', close);
  if (closeBtn) closeBtn.addEventListener('click', close);
  mask.addEventListener('click', function (e) { if (e.target === mask) close(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });

  /* 登录刚落地：延迟一点点，等页面骨架画完再弹 */
  setTimeout(open, 420);
})();
