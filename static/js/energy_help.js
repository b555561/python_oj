/* ==========================================================================
   能量规则弹窗 —— 菜园 / 果蔬摊 / 厨房 顶部的「⚡」小图标点它弹出
   依赖 app.js 里的 openModal / closeModal
   ========================================================================== */

var ENERGY_RULES = {
  earn: [
    ['📅', '每日打卡', '+10'],
    ['✅', '首次通过题目', '+8'],
    ['🔁', '重复通过已 AC 的题', '+2'],
    ['📝', '测验达标', '+30'],
    ['✍️', '学习圈发帖', '+5'],
    ['🍳', '发布菜肴到学习圈', '+40 ~ 230'],
    ['🪙', '果蔬摊金币兑换', '按当日汇率']
  ],
  cost: [
    ['⛏️', '翻地', '-5'],
    ['🌱', '播种', '按作物定价'],
    ['💧', '浇水（每次顶 10 分钟）', '-8'],
    ['🌾', '收获', '返还更多能量']
  ]
};

function openEnergyHelp() {
  var rows = function (list) {
    return list.map(function (r) {
      return '<div class="eh-row">' +
             '<span class="eh-e">' + r[0] + '</span>' +
             '<span class="eh-n">' + r[1] + '</span>' +
             '<span class="eh-v">' + r[2] + '</span>' +
             '</div>';
    }).join('');
  };
  openModal(
    '<div class="tip-card energy">' +
    '  <div class="tip-emoji">⚡</div>' +
    '  <span class="tip-tag">能量使用规则</span>' +
    '  <h3 class="tip-title">能量怎么赚，又花在哪儿</h3>' +
    '  <div class="tip-sub">能量是这个园子的水与肥，攒着不会生息，花出去才长东西 🌱</div>' +
    '  <div class="eh-block">' +
    '    <div class="eh-h">赚能量</div>' + rows(ENERGY_RULES.earn) +
    '  </div>' +
    '  <div class="eh-block">' +
    '    <div class="eh-h">花能量</div>' + rows(ENERGY_RULES.cost) +
    '  </div>' +
    '  <div class="tip-actions">' +
    '    <button class="btn btn-primary" onclick="closeModal()">知道啦</button>' +
    '  </div>' +
    '</div>'
  );
}
