/* ============================================================
   注册页 · 表单填写引导
   ------------------------------------------------------------
   - 聚焦某个输入框 → 下方浮出该字段的填写说明（蒙布式提示条）
   - 输入过程中实时校验，给出通过 / 待修正的即时反馈
   - 提交时统一校验，不通过则阻止提交并聚焦第一个问题字段
   - 纯原生 JS + CSS，无任何第三方库
   ============================================================ */
(function () {
  var form = document.getElementById('regForm');
  if (!form) return;

  var FIELDS = [
    {
      input: document.getElementById('rgUser'),
      tip: document.getElementById('tipUser'),
      check: function (v) {
        if (!v) return ['', ''];
        if (v.length < 3) return ['bad', '还差 ' + (3 - v.length) + ' 个字符，用户名至少 3 位'];
        if (v.length > 20) return ['bad', '太长了，用户名最多 20 个字符'];
        if (!/^[A-Za-z0-9_]+$/.test(v)) return ['bad', '只能用字母、数字和下划线'];
        return ['ok', '✓ 这个用户名可以用'];
      }
    },
    {
      input: document.getElementById('rgNick'),
      tip: document.getElementById('tipNick'),
      check: function (v) {
        if (!v) return ['', ''];
        if (v.length > 16) return ['bad', '昵称最多 16 个字符'];
        return ['ok', '✓ 昵称没问题，留空也可以'];
      }
    },
    {
      input: document.getElementById('rgPwd'),
      tip: document.getElementById('tipPwd'),
      check: function (v) {
        if (!v) return ['', ''];
        if (v.length < 6) return ['bad', '还差 ' + (6 - v.length) + ' 位，密码至少 6 位'];
        if (/^\d+$/.test(v)) return ['bad', '全是数字不安全，加点字母吧'];
        return ['ok', '✓ 密码强度够用啦'];
      }
    }
  ];

  function showTip(f, state, text) {
    if (!f.tip) return;
    f.tip.textContent = text;
    f.tip.className = 'rg-tip' + (text ? ' show' : '') + (state ? ' ' + state : '');
  }

  function refresh(f, live) {
    if (!f.input) return;
    var v = f.input.value.trim();
    var r = f.check(v);
    /* 实时校验：只有已经填了内容才提示对错，避免刚聚焦就报红 */
    if (!live) { showTip(f, r[0], r[1]); mark(f, r[0]); return; }
    if (!v) { showTip(f, '', ''); mark(f, ''); return; }
    showTip(f, r[0], r[1]);
    mark(f, r[0]);
  }

  function mark(f, state) {
    if (!f.input) return;
    f.input.classList.remove('rg-bad', 'rg-ok');
    if (state === 'bad') f.input.classList.add('rg-bad');
    if (state === 'ok') f.input.classList.add('rg-ok');
  }

  FIELDS.forEach(function (f) {
    if (!f.input) return;
    var hint = f.input.getAttribute('data-tip') || '';

    f.input.addEventListener('focus', function () {
      /* 聚焦先展示填写说明；已填内容则直接展示校验结果 */
      var v = f.input.value.trim();
      if (v) { refresh(f, true); }
      else { showTip(f, '', hint); mark(f, ''); }
    });

    f.input.addEventListener('input', function () { refresh(f, true); });

    f.input.addEventListener('blur', function () {
      var v = f.input.value.trim();
      if (!v) { showTip(f, '', ''); mark(f, ''); }
      else { refresh(f, true); }
    });
  });

  form.addEventListener('submit', function (e) {
    var firstBad = null;
    FIELDS.forEach(function (f) {
      if (!f.input) return;
      var v = f.input.value.trim();
      var r = f.check(v);
      var required = f.input.hasAttribute('required');
      if (required && !v) {
        showTip(f, 'bad', f.input.getAttribute('data-tip') || '这一项必须填写');
        mark(f, 'bad');
        if (!firstBad) firstBad = f.input;
        return;
      }
      if (v && r[0] === 'bad') {
        showTip(f, 'bad', r[1]);
        mark(f, 'bad');
        if (!firstBad) firstBad = f.input;
      }
    });
    if (firstBad) {
      e.preventDefault();
      firstBad.focus();
      return false;
    }
    return true;
  });
})();
