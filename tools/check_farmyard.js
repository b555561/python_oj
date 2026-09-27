/* 农场前端自检（离线 jsdom）：
   1. 3D 网格渲染出 GRID×GRID 个格子
   2. 侧边栏渲染出配件卡片与分类按钮
   3. 点击配件卡 → 选中手持；点击空格 → 发出摆放请求（模拟 fetch）
   4. 拆除模式、缩放、转视角按钮可点且状态正确
   5. 全程无 JS 运行时错误
*/
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const FILE = process.argv[2] || path.join(__dirname, '..', 'preview', '_farm_slim.html');
let OK = 0, BAD = 0;
function check(name, cond, extra) {
  if (cond) { OK++; console.log('  ✓ ' + name); }
  else { BAD++; console.log('  ✗ ' + name + (extra !== undefined ? '  << ' + extra : '')); }
}

const errors = [];
const vc = new VirtualConsole();
vc.on('jsdomError', e => errors.push(String(e && e.message || e)));
vc.on('error', (...a) => errors.push(a.join(' ')));

const html = fs.readFileSync(FILE, 'utf8');
const dom = new JSDOM(html, {
  runScripts: 'dangerously', pretendToBeVisual: true, url: 'http://127.0.0.1:8001/farm',
  virtualConsole: vc,
});
const { window } = dom;
const doc = window.document;

setTimeout(() => {
  console.log('\n=== 1. 3D 地皮渲染 ===');
  const cells = doc.querySelectorAll('#yardCells .yard-cell');
  check('格子数量 = 14×14 = 196', cells.length === 196, cells.length);
  const stage = doc.getElementById('yardStage');
  check('舞台设置了 --grid', stage && stage.style.getPropertyValue('--grid') === '14',
    stage && stage.style.getPropertyValue('--grid'));
  check('视角变量已写入（--rx/--rz）',
    doc.getElementById('yardView').style.getPropertyValue('--rz') === '45deg');
  check('地面已渲染', !!doc.querySelector('.yard-ground'));

  console.log('\n=== 2. 侧边栏配件 ===');
  const cats = doc.querySelectorAll('#yardCats .yard-cat');
  check('分类按钮 7 个', cats.length === 7, cats.length);
  const items = doc.querySelectorAll('#yardItems .yard-item');
  check('配件卡片已渲染（默认地面分类）', items.length >= 5, items.length);
  check('卡片上有价格', /⚡\d+/.test(doc.getElementById('yardItems').textContent));
  check('卡片上有库存角标', doc.querySelectorAll('#yardItems .yi-own').length > 0);

  console.log('\n=== 3. 交互：选配件 → 点地皮摆放 ===');
  window.fetch = () => Promise.resolve({
    status: 200, json: () => Promise.resolve(
      { code: 0, msg: 'ok', data: { qty: 11 } }),
  });
  const first = items[0];
  first.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
  const handEl = doc.getElementById('yardHand');
  check('点配件后显示「手上拿着」', handEl.style.display !== 'none' && handEl.textContent.length > 2,
    handEl.textContent);
  check('配件卡高亮为选中', doc.querySelectorAll('#yardItems .yard-item.on').length === 1);

  const emptyCell = Array.from(cells).find(c => !c.dataset.k);
  emptyCell.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
  setTimeout(() => {
    check('点击空格后地皮上出现方块', doc.querySelectorAll('#yardObjs .cube').length >= 1,
      doc.querySelectorAll('#yardObjs .cube').length);
    const cube = doc.querySelector('#yardObjs .cube');
    check('方块有顶面 + 四个侧面',
      cube && cube.querySelectorAll('i.fc-top').length === 1 &&
      cube.querySelectorAll('i.fc-front, i.fc-back, i.fc-left, i.fc-right').length === 4);
    check('方块带 --h 高度与 --c 颜色',
      cube && cube.style.getPropertyValue('--h') !== '' && cube.style.getPropertyValue('--c') !== '');

    console.log('\n=== 4. 工具条 ===');
    const erase = doc.getElementById('yardErase');
    erase.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
    check('拆除模式可切换', erase.classList.contains('on') &&
      doc.getElementById('yardCells').className.indexOf('erase') >= 0);
    const rzBefore = doc.getElementById('yardView').style.getPropertyValue('--rz');
    doc.getElementById('yardRot').dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
    check('转视角改变了 --rz',
      doc.getElementById('yardView').style.getPropertyValue('--rz') !== rzBefore);
    doc.getElementById('yardZin').dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
    check('放大改变了 --zoom',
      parseFloat(doc.getElementById('yardView').style.getPropertyValue('--zoom')) > 1);
    doc.getElementById('yardReset').dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
    check('复位回到默认视角',
      doc.getElementById('yardView').style.getPropertyValue('--zoom') === '1');

    console.log('\n=== 5. 底部统计 ===');
    check('统计条已填充', /已摆/.test(doc.getElementById('yardFoot').textContent),
      doc.getElementById('yardFoot').textContent.slice(0, 60));
    check('文案强调没有任务没有关卡',
      /没有任务/.test(doc.getElementById('yardFoot').textContent));

    console.log('\n=== 6. 运行时错误 ===');
    check('没有 JS 运行时错误', errors.length === 0, errors.slice(0, 2).join(' | '));

    console.log('\n========================================================');
    console.log('农场前端自检：通过 ' + OK + ' 项，失败 ' + BAD + ' 项');
    console.log('========================================================');
    process.exit(BAD ? 1 : 0);
  }, 60);
}, 400);
