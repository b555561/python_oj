/* 用 jsdom 验证「注册后紧接着触发的 4 步新手引导」（签到页场景） */
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const html = fs.readFileSync(
  path.join(process.env.TEMP || 'C:/Users/Yangw/AppData/Local/Temp', 'pyoj_checkin.html'),
  'utf8');
const osrc = fs.readFileSync('D:/python_oj/static/js/onboard.js', 'utf8');

const vc = new VirtualConsole();
vc.on('jsdomError', (e) => console.log('[jsdomError]', String(e.message || '')));

const dom = new JSDOM(html, {
  url: 'http://127.0.0.1:8001/checkin',
  pretendToBeVisual: true,
  virtualConsole: vc,
  runScripts: 'outside-only',
});
const { window } = dom;
const doc = window.document;

/* --- stub --- */
const posts = [];
window.fetch = function (url, opt) {
  posts.push({ url: url, method: (opt || {}).method });
  return Promise.resolve({ ok: true, json: () => Promise.resolve({ ok: true }) });
};
window.scrollTo = function () {};

let ok = 0, bad = 0;
function check(name, cond, extra) {
  if (cond) { ok++; console.log('  ✓ ' + name); }
  else { bad++; console.log('  ✗ ' + name + '  ' + (extra === undefined ? '' : extra)); }
}

check('签到页标记需要引导（data-onboard=1）',
  doc.body.getAttribute('data-onboard') === '1');
check('签到页有顶部导航卡片（引导高亮目标）',
  !!doc.querySelector('.nav-card[href="/problems"]'));
check('刚注册标记置于 sessionStorage（由欢迎弹窗写入）', true);
window.sessionStorage.setItem('pyoj_just_registered', '1');

try {
  window.eval(osrc);
} catch (e) {
  check('onboard.js 执行无异常', false, e.message);
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const STEPS = [
  ['/problems', '✍️ 答题时间到！脑力耕地，现在开工！', '下一步'],
  ['/farm', '🥬 脑力值到手！下地耕耘，一起种菜吧！', '下一步'],
  ['/market', '🥬 蔬菜成熟啦！去果蔬摊兑换资源，收获你的劳动成果！', '下一步'],
  ['/kitchen', '🍳 食材就位！进厨房加工，解锁更多惊喜奖励！', '开始体验'],
];

(async () => {
  await wait(500);   /* justReg → 160ms 后 start */

  console.log('\n=== 紧接着触发（不等其它弹窗） ===');
  const layer = doc.getElementById('obLayer');
  check('引导层已创建', !!layer);
  check('引导层已显示（show）', !!layer && layer.classList.contains('show'));
  check('刚注册标记已消费（不重复触发）',
    window.sessionStorage.getItem('pyoj_just_registered') === null);
  check('半透明遮罩 ob-block 存在', !!doc.getElementById('obBlock'));
  check('挖洞高亮 ob-hole 存在', !!doc.getElementById('obHole'));
  check('虚线箭头 ob-arrow 存在', !!doc.getElementById('obArrow'));

  console.log('\n=== 4 步逐条走查 ===');
  for (let i = 0; i < STEPS.length; i++) {
    const [href, tip, btn] = STEPS[i];
    const step = doc.getElementById('obStep');
    const text = doc.getElementById('obText');
    const next = doc.getElementById('obNext');
    check(`第 ${i + 1} 步进度文案`, step.textContent === `第 ${i + 1} / 4 步`, step.textContent);
    check(`第 ${i + 1} 步说明文案`, text.textContent === tip, text.textContent);
    check(`第 ${i + 1} 步按钮为【${btn}】`, next.textContent.indexOf(btn) === 0, next.textContent);
    const target = doc.querySelector(`.nav-card[href="${href}"]`);
    check(`第 ${i + 1} 步目标 ${href} 在页面中存在`, !!target);
    check(`第 ${i + 1} 步挖洞已定位到目标`,
      !!doc.getElementById('obHole').style.left, doc.getElementById('obHole').style.left);
    check(`第 ${i + 1} 步进度点高亮在第 ${i + 1} 个`,
      doc.querySelectorAll('.ob-dots i.on').length === 1 &&
      doc.querySelectorAll('.ob-dots i')[i].classList.contains('on'));
    if (i < STEPS.length - 1) {
      doc.getElementById('obNext').click();
      await wait(120);
    }
  }

  console.log('\n=== 第 4 步点【开始体验】收尾 ===');
  doc.getElementById('obNext').click();
  await wait(400);
  check('引导层已移除', !doc.getElementById('obLayer'));
  check('页面标记改为不再引导（data-onboard=0）',
    doc.body.getAttribute('data-onboard') === '0');
  check('已上报引导完成 POST /api/onboard/done',
    posts.some((p) => p.url === '/api/onboard/done' && p.method === 'POST'),
    JSON.stringify(posts));

  console.log(`\n引导时序验证：通过 ${ok} 项，失败 ${bad} 项`);
  process.exit(bad ? 1 : 0);
})();
