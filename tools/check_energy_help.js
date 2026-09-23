/* 用 jsdom 验证「能量规则小图标 → 点击弹出规则弹窗」（菜园场景，第 17 轮）
   前置：先用 requests 登录并把 /farm 快照写到 %TEMP%/pyoj_farm.html
   用法：NODE_PATH=<node workspace>/node_modules node tools/check_energy_help.js
*/
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const html = fs.readFileSync(
  path.join(process.env.TEMP || 'C:/Users/Yangw/AppData/Local/Temp', 'pyoj_farm.html'),
  'utf8');

const vc = new VirtualConsole();
vc.on('jsdomError', (e) => console.log('[jsdomError]', String(e.message || '')));

const dom = new JSDOM(html, {
  url: 'http://127.0.0.1:8001/farm',
  pretendToBeVisual: true,
  virtualConsole: vc,
  runScripts: 'outside-only',
});
const { window } = dom;
const doc = window.document;

/* app.js 与 energy_help.js 用 outside-only 手动注入（页面脚本不联网加载） */
window.eval(fs.readFileSync('D:/python_oj/static/js/app.js', 'utf8'));
window.eval(fs.readFileSync('D:/python_oj/static/js/energy_help.js', 'utf8'));

let ok = 0, bad = 0;
function check(name, cond, extra) {
  if (cond) { ok++; console.log('  ✓ ' + name); }
  else { bad++; console.log('  ✗ ' + name + '  ' + (extra === undefined ? '' : extra)); }
}

console.log('\n=== 页头结构 ===');
const top = doc.querySelector('.sec-top');
check('菜园页头 .sec-top 存在', !!top);
check('页头含缩小版苗小序舞台', !!doc.querySelector('.sec-top .ms-wrap.sm .ms-stage.ms-farm'));
check('页头不含对话气泡', !top || !top.querySelector('.nan-say'));
check('页头不含说明段落', !top || !top.querySelector('.note'));
check('页头含能量值', !!top && /⚡\s*能量/.test(top.textContent));
check('页头含一键收获', !!top && /一键收获/.test(top.textContent));

console.log('\n=== 能量规则小图标 ===');
const btn = doc.querySelector('.energy-help');
check('小图标存在', !!btn);
check('小图标在页头内', !!btn && !!top && top.contains(btn));
check('小图标有 title 提示', !!btn && (btn.getAttribute('title') || '').length > 0);
check('小图标有无障碍标签', !!btn && (btn.getAttribute('aria-label') || '').length > 0);

console.log('\n=== 点击后弹出规则 ===');
check('openEnergyHelp 已定义', typeof window.openEnergyHelp === 'function');
check('点击前无弹窗', !doc.getElementById('modalMask'));
/* jsdom 用 runScripts:"outside-only" 时不编译页面内联 onclick，
   因此：先断言按钮确实绑了 openEnergyHelp()，再直接调用验证弹窗内容 */
check('小图标绑定 onclick=openEnergyHelp()',
  !!btn && (btn.getAttribute('onclick') || '').indexOf('openEnergyHelp()') >= 0,
  btn && btn.getAttribute('onclick'));
btn.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
window.eval('openEnergyHelp()');
const mask = doc.getElementById('modalMask');
check('点击后出现弹窗遮罩', !!mask);
const txt = mask ? mask.textContent : '';
check('弹窗标题为能量使用规则', /能量使用规则/.test(txt), txt.slice(0, 60));
check('弹窗含「赚能量」', /赚能量/.test(txt));
check('弹窗含「花能量」', /花能量/.test(txt));
for (const kw of ['每日打卡', '首次通过题目', '测验达标', '翻地', '播种', '浇水', '收获']) {
  check('规则含「' + kw + '」', txt.indexOf(kw) >= 0);
}
check('规则条目数 >= 10', mask ? mask.querySelectorAll('.eh-row').length >= 10 : false,
  mask ? mask.querySelectorAll('.eh-row').length : 0);

console.log('\n=== 关闭 ===');
window.closeModal();
check('可正常关闭', !doc.getElementById('modalMask'));

console.log('\n通过 ' + ok + ' 项，失败 ' + bad + ' 项');
process.exit(bad ? 1 : 0);
