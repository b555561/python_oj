/* 用 jsdom 验证「注册欢迎弹窗」的动画时序编排（不依赖真实浏览器渲染） */
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const html = fs.readFileSync(
  path.join(process.env.TEMP || 'C:/Users/Yangw/AppData/Local/Temp', 'pyoj_home_new.html'),
  'utf8');
const wsrc = fs.readFileSync('D:/python_oj/static/js/welcome.js', 'utf8');

const vc = new VirtualConsole();
let navMsg = '';
vc.on('jsdomError', (e) => {
  const m = String(e.message || '');
  if (/Not implemented: navigation/.test(m)) navMsg = m;
  else console.log('[jsdomError]', m);
});

const dom = new JSDOM(html, {
  url: 'http://127.0.0.1:8001/',
  pretendToBeVisual: true,
  virtualConsole: vc,
  runScripts: 'outside-only',
});
const { window } = dom;
const doc = window.document;

/* --- stub --- */
window.matchMedia = () => ({ matches: false, addListener() {}, addEventListener() {} });
class GainStub {
  constructor() { this.gain = { setValueAtTime() {}, exponentialRampToValueAtTime() {} }; }
  connect() {}
}
class OscStub {
  constructor() { this.frequency = { value: 0 }; }
  connect() {}
  start() {}
  stop() {}
}
window.AudioContext = class {
  constructor() { this.state = 'running'; this.currentTime = 0; this.destination = {}; }
  createOscillator() { return new OscStub(); }
  createGain() { return new GainStub(); }
  resume() {}
  close() {}
};

let ok = 0, bad = 0;
function check(name, cond, extra) {
  if (cond) { ok++; console.log('  ✓ ' + name); }
  else { bad++; console.log('  ✗ ' + name + '  ' + (extra === undefined ? '' : extra)); }
}

const hero = doc.getElementById('wlcHero');
const bubble = doc.getElementById('wlcBubble');
const flash = doc.getElementById('wlcFlash');
const fab = doc.getElementById('nanFab');
const mask = doc.getElementById('welcomeMask');
const lines = doc.getElementById('wlcLines');

check('页面含欢迎弹窗节点', !!(hero && bubble && flash && mask));
check('悬浮图标节点存在', !!fab);

try {
  window.eval(wsrc);
} catch (e) {
  check('welcome.js 执行无异常', false, e.message);
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  await wait(900);

  console.log('\n=== 阶段 1：放大版苗小序出场 + 对话气泡自我介绍 ===');
  check('弹窗已显示（show）', mask.classList.contains('show'));
  check('苗小序已出场（hero.in）', hero.classList.contains('in'), hero.className);
  check('对话气泡已弹出（bubble.in，否则 opacity:0 看不见）',
    bubble.classList.contains('in'), bubble.className);
  check('气泡已定位（挂右侧或上方）',
    bubble.classList.contains('right') || bubble.classList.contains('top'), bubble.className);
  check('气泡有具体定位坐标', !!bubble.style.left && !!bubble.style.top,
    bubble.style.left + ',' + bubble.style.top);
  check('欢迎文案已入场（lines.in）', !!lines && lines.classList.contains('in'));
  check('苗小序已摆放到屏幕中（left/top 已设）', !!hero.style.left && !!hero.style.top);
  const svg0 = hero.querySelector('svg');
  check('放大版尺寸 220px（远大于悬浮图标 46）',
    svg0 && svg0.getAttribute('width') === '220', svg0 && svg0.getAttribute('width'));

  console.log('\n=== 阶段 2：缓慢缩小 + 原地旋转一圈，飞回悬浮位 ===');
  await wait(4200);   /* 累计 ≈5.1s，已过 T_INTRO(4.2s)+开场(0.32s) */
  check('进入飞回阶段（hero.go）', hero.classList.contains('go'), hero.className);
  check('已算出位移变量 --dx/--dy',
    !!hero.style.getPropertyValue('--dx') && !!hero.style.getPropertyValue('--dy'),
    hero.style.getPropertyValue('--dx') + ',' + hero.style.getPropertyValue('--dy'));
  const k = parseFloat(hero.style.getPropertyValue('--k'));
  check('已算出缩放比例 --k（明显小于 1，缩到悬浮图标大小）', k > 0 && k < 0.5, String(k));
  check('飞行时长已写入 --fly', /2600ms/.test(hero.style.getPropertyValue('--fly')));
  check('悬浮球漂浮动画已暂停（nf-static，保证落位精确）',
    fab.classList.contains('nf-static'), fab.className);
  check('气泡同步缩小（bubble.go）', bubble.classList.contains('go'), bubble.className);

  /* 模拟 CSS 动画播完：wlcFly 结束 */
  const ev = new window.Event('animationend');
  ev.animationName = 'wlcFly';
  hero.dispatchEvent(ev);
  await wait(150);

  console.log('\n=== 阶段 3：落位，尺寸与角落悬浮小图标完全一致 ===');
  check('落位态（hero.landed）', hero.classList.contains('landed'), hero.className);
  check('已移除飞行/出场动画类（go/in）',
    !hero.classList.contains('go') && !hero.classList.contains('in'), hero.className);
  check('尺寸设为 66×66（与悬浮图标一致）',
    hero.style.width === '66px' && hero.style.height === '66px',
    hero.style.width + '×' + hero.style.height);
  const svg1 = hero.querySelector('svg');
  check('苗小序缩到 46px（与悬浮图标内一致）',
    svg1 && svg1.getAttribute('width') === '46' && svg1.getAttribute('height') === '46',
    svg1 && svg1.getAttribute('width'));
  check('悬浮球恢复漂浮并高亮（nf-welcome-pop）',
    !fab.classList.contains('nf-static') && fab.classList.contains('nf-welcome-pop'),
    fab.className);

  console.log('\n=== 阶段 4：亮光消散 + 气泡随人物一同消失 ===');
  check('亮光特效触发（flash.on）', flash.classList.contains('on'));
  check('人物淡出（hero.gone）', hero.classList.contains('gone'), hero.className);
  check('气泡同步消失（bubble.gone）',
    bubble.classList.contains('gone') && !bubble.classList.contains('go'), bubble.className);

  console.log('\n=== 阶段 5：自动关闭 → 跳转签到页 ===');
  await wait(1800);
  check('遮罩已淡出（show 移除）', !mask.classList.contains('show'));
  check('welcome_new cookie 已清除', !/welcome_new=1/.test(doc.cookie), doc.cookie);
  check('写入 pop_signin（注册当天不抢戏）', /pop_signin=/.test(doc.cookie), doc.cookie);
  check('标记刚注册（sessionStorage）',
    window.sessionStorage.getItem('pyoj_just_registered') === '1');
  check('自动跳转到签到页 /checkin',
    !!navMsg, navMsg || '(未捕获到跳转)');

  console.log(`\n时序验证：通过 ${ok} 项，失败 ${bad} 项`);
  process.exit(bad ? 1 : 0);
})();
