/* 农场（/farm）—— 自由建造的 3D 小农场
   纯原生 JS，无第三方库。
   核心：点配件 → 买到手 → 点地皮摆放 → 随时搬走 / 拆除（拆了退回背包）。
   没有任务、没有关卡、没有必须完成的顺序，想怎么搭就怎么搭。
*/
(function () {
  var dataEl = document.getElementById('yard-data');
  if (!dataEl) return;                 // 非农场页不执行

  var DATA = JSON.parse(dataEl.textContent || '{}');
  var GRID = DATA.grid || 14;
  var ITEMS = {};                      // key -> 配件
  (DATA.items || []).forEach(function (it) { ITEMS[it.key] = it; });

  var board = {};                      // "x,y" -> item_key
  (DATA.board || []).forEach(function (b) { board[b.x + ',' + b.y] = b.key; });
  var own = DATA.own || {};            // key -> 数量
  var energy = DATA.energy || 0;

  var hand = null;                     // 手上拿着的：{key, from:{x,y}|null}
  var sel = null;                      // 选中的格子：{x,y}
  var tool = 'place';                  // place | erase
  var cat = 'ground';

  var view = document.getElementById('yardView');
  var stage = document.getElementById('yardStage');
  var cellsEl = document.getElementById('yardCells');
  var objsEl = document.getElementById('yardObjs');
  var ghost = document.getElementById('yardGhost');
  var itemsEl = document.getElementById('yardItems');
  var catsEl = document.getElementById('yardCats');
  var handEl = document.getElementById('yardHand');
  var selEl = document.getElementById('yardSel');
  var footEl = document.getElementById('yardFoot');
  if (!view || !stage) return;

  var zoom = 1, rz = 45, rx = 56;

  function k(x, y) { return x + ',' + y; }
  function at(x, y) { return board[k(x, y)]; }

  /* ---------------- 渲染 ---------------- */
  function renderCells() {
    var html = '';
    for (var y = 0; y < GRID; y++) {
      for (var x = 0; x < GRID; x++) {
        html += '<div class="yard-cell" data-x="' + x + '" data-y="' + y + '"' +
                ' style="left:calc(' + x + ' * var(--tile));top:calc(' + y + ' * var(--tile));"></div>';
      }
    }
    cellsEl.innerHTML = html;
  }

  function cubeHTML(x, y, key) {
    var it = ITEMS[key];
    if (!it) return '';
    var flat = it.h <= 0.12;
    var water = (key === 'water' || key === 'pond');
    var still = (it.cat === 'build' || flat);
    var cls = 'cube' + (flat ? ' flat' : '') + (water ? ' water' : '') + (still ? ' still' : '') +
              (sel && sel.x === x && sel.y === y ? ' sel' : '');
    return '<div class="' + cls + '" data-x="' + x + '" data-y="' + y + '" style="' +
           '--h:' + it.h + ';--lift:' + (it.lift || 0) + ';--c:' + it.color + ';' +
           'left:calc(' + x + ' * var(--tile));top:calc(' + y + ' * var(--tile));">' +
           '<i class="fc-sh"></i><i class="fc-top"></i>' +
           '<i class="fc-front"></i><i class="fc-back"></i>' +
           '<i class="fc-left"></i><i class="fc-right"></i>' +
           (it.emoji ? '<b class="fc-em"><span>' + it.emoji + '</span></b>' : '') +
           '</div>';
  }

  function renderObjs() {
    var html = '';
    Object.keys(board).forEach(function (kk) {
      var p = kk.split(',');
      html += cubeHTML(+p[0], +p[1], board[kk]);
    });
    objsEl.innerHTML = html;
  }

  function renderItems() {
    var html = '';
    (DATA.cats || []).forEach(function (c) {
      if (c.key !== cat) return;
      (DATA.catalog || []).forEach(function (it) {
        if (it.cat !== cat) return;
        var n = own[it.key] || 0;
        var on = hand && hand.key === it.key;
        html += '<button type="button" class="yard-item' + (n ? '' : ' no') + (on ? ' on' : '') +
                '" data-key="' + it.key + '" title="' + it.name + '：' + it.desc + '">' +
                '<span class="yi-em">' + (it.emoji || '🟩') + '</span>' +
                '<span class="yi-n">' + it.name + '</span>' +
                '<span class="yi-d">' + it.desc + '</span>' +
                '<span class="yi-b"><span class="yi-p">⚡' + it.price + '</span>' +
                (n ? '<span class="yi-own">×' + n + '</span>' : '') + '</span></button>';
      });
    });
    itemsEl.innerHTML = html;
  }

  function renderCats() {
    var html = '';
    (DATA.cats || []).forEach(function (c) {
      html += '<button type="button" class="yard-cat' + (c.key === cat ? ' on' : '') +
              '" data-cat="' + c.key + '">' + c.icon + ' ' + c.name + '</button>';
    });
    catsEl.innerHTML = html;
  }

  function renderBar() {
    if (hand) {
      var it = ITEMS[hand.key] || {};
      handEl.style.display = '';
      handEl.innerHTML = (it.emoji ? it.emoji + ' ' : '') + it.name +
        (hand.from ? '（搬家中，点空地放下）' : '（点地皮摆放）') +
        ' <a href="javascript:;" id="handCancel" style="color:#b45309;">✕</a>';
      var a = document.getElementById('handCancel');
      if (a) a.onclick = function () { hand = null; afterChange(); };
    } else {
      handEl.style.display = 'none';
    }

    if (sel && at(sel.x, sel.y)) {
      var s = ITEMS[at(sel.x, sel.y)] || {};
      selEl.style.display = '';
      selEl.innerHTML = '选中 ' + (s.emoji || '') + ' ' + s.name +
        ' <a href="javascript:;" id="selMove" style="color:#2f7a45;">搬走</a>' +
        ' · <a href="javascript:;" id="selDel" style="color:#b45309;">拆除</a>' +
        ' · <a href="javascript:;" id="selCancel">✕</a>';
      var m = document.getElementById('selMove');
      var d = document.getElementById('selDel');
      var c = document.getElementById('selCancel');
      if (m) m.onclick = function () {
        hand = { key: at(sel.x, sel.y), from: { x: sel.x, y: sel.y } };
        sel = null; tool = 'place'; afterChange();
      };
      if (d) d.onclick = function () { doRemove(sel.x, sel.y); };
      if (c) c.onclick = function () { sel = null; afterChange(); };
    } else {
      selEl.style.display = 'none';
    }

    cellsEl.className = 'yard-cells' + (tool === 'erase' ? ' erase' : '');
    var placed = Object.keys(board).length;
    var kinds = {};
    Object.keys(board).forEach(function (kk) { kinds[board[kk]] = 1; });
    var ownKinds = 0;
    Object.keys(own).forEach(function (kk) { if (own[kk] > 0) ownKinds++; });
    footEl.innerHTML = '已摆 <b>' + placed + '</b> 个 · 用了 <b>' + Object.keys(kinds).length +
      '</b> 种配件 · 背包还有 <b>' + ownKinds + '</b> 种 · 地皮 <b>' + GRID + '×' + GRID + '</b>' +
      '<span class="yf-tip">没有任务、没有关卡：想摆哪儿摆哪儿，拆掉的东西会回到背包 ✨</span>';
  }

  function renderGhost() {
    if (!hand) { ghost.className = 'yard-ghost'; return; }
    var it = ITEMS[hand.key];
    if (!it) { ghost.className = 'yard-ghost'; return; }
    ghost.className = 'yard-ghost on';
    ghost.style.setProperty('--h', it.h);
    ghost.style.setProperty('--lift', it.lift || 0);
    ghost.style.setProperty('--c', it.color);
    ghost.innerHTML = '<i class="fc-top"></i>' +
      (it.emoji ? '<b class="fc-em"><span>' + it.emoji + '</span></b>' : '');
  }

  function afterChange() {
    renderObjs(); renderItems(); renderBar(); renderGhost();
  }

  function setEnergy(v) {
    energy = v;
    var el = document.querySelector('.energy-tag');
    if (el) el.textContent = '⚡ 能量 ' + v;
  }

  /* ---------------- 动作 ---------------- */
  async function doBuy(key) {
    var r = await post('/api/yard/buy', { key: key, n: 1 });
    if (!r) return;
    toast(r.msg);
    if (r.code === 0) {
      own[key] = (own[key] || 0) + 1;
      if (r.data && r.data.energy !== undefined) setEnergy(r.data.energy);
      hand = { key: key, from: null };
      sel = null; tool = 'place';
      afterChange();
    }
  }

  async function doPlace(x, y, key) {
    var r = await post('/api/yard/place', { x: x, y: y, key: key });
    if (!r) return;
    toast(r.msg);
    if (r.code === 0) {
      board[k(x, y)] = key;
      own[key] = Math.max(0, (own[key] || 1) - 1);
      if (own[key] === 0) hand = null;         // 用完了就把手上的放下
      sel = null;
      afterChange();
    }
  }

  async function doMove(fx, fy, tx, ty) {
    var r = await post('/api/yard/move', { fx: fx, fy: fy, tx: tx, ty: ty });
    if (!r) return;
    toast(r.msg);
    if (r.code === 0) {
      var a = board[k(fx, fy)], b = board[k(tx, ty)];
      delete board[k(fx, fy)];
      board[k(tx, ty)] = a;
      if (b) { board[k(fx, fy)] = b; }          // 两格都有东西 → 对调
      hand = null; sel = null;
      afterChange();
    }
  }

  async function doRemove(x, y) {
    var key = at(x, y);
    if (!key) { toast('这格本来就是空的'); return; }
    var r = await post('/api/yard/remove', { x: x, y: y });
    if (!r) return;
    toast(r.msg);
    if (r.code === 0) {
      delete board[k(x, y)];
      own[key] = (own[key] || 0) + 1;
      sel = null;
      afterChange();
    }
  }

  async function doClear() {
    if (!window.confirm('把地皮清空？所有配件都会退回背包，随时能重新摆。')) return;
    var r = await post('/api/yard/clear', {});
    if (!r) return;
    toast(r.msg);
    if (r.code === 0) {
      Object.keys(board).forEach(function (kk) { own[board[kk]] = (own[board[kk]] || 0) + 1; });
      board = {}; hand = null; sel = null;
      afterChange();
    }
  }

  /* ---------------- 交互 ---------------- */
  function onCellClick(x, y) {
    var key = at(x, y);
    if (tool === 'erase') {
      if (key) doRemove(x, y); else toast('这格是空的，不用拆');
      return;
    }
    if (hand) {
      if (key) {
        if (hand.from) doMove(hand.from.x, hand.from.y, x, y);   // 有东西就对调
        else toast('这格已经有东西啦，先点它选中，可以搬走或拆掉');
      } else {
        if (hand.from) doMove(hand.from.x, hand.from.y, x, y);
        else doPlace(x, y, hand.key);
      }
      return;
    }
    if (key) { sel = { x: x, y: y }; afterChange(); return; }
    toast('先在左边挑一个配件（背包里没有就点一下买）');
  }

  var down = null, dragged = false;
  cellsEl.addEventListener('pointerdown', function (e) {
    var c = e.target.closest ? e.target.closest('.yard-cell') : null;
    if (!c) return;
    down = { x: +c.dataset.x, y: +c.dataset.y };
    dragged = false;
  });
  cellsEl.addEventListener('pointerup', function (e) {
    var c = e.target.closest ? e.target.closest('.yard-cell') : null;
    if (!c || !down) { down = null; return; }
    var x = +c.dataset.x, y = +c.dataset.y;
    if (x !== down.x || y !== down.y) {
      if (at(down.x, down.y)) { dragged = true; doMove(down.x, down.y, x, y); }
    }
    down = null;
  });
  cellsEl.addEventListener('click', function (e) {
    var c = e.target.closest ? e.target.closest('.yard-cell') : null;
    if (!c) return;
    if (dragged) { dragged = false; return; }
    onCellClick(+c.dataset.x, +c.dataset.y);
  });
  cellsEl.addEventListener('pointermove', function (e) {
    var c = e.target.closest ? e.target.closest('.yard-cell') : null;
    if (!c) { renderGhostOff(); return; }
    if (!hand) { renderGhostOff(); return; }
    var x = +c.dataset.x, y = +c.dataset.y;
    ghost.className = 'yard-ghost on';
    ghost.style.left = 'calc(' + x + ' * var(--tile))';
    ghost.style.top = 'calc(' + y + ' * var(--tile))';
    var cc = c.classList;
    cc.add(at(x, y) ? (hand.from ? 'can' : 'bad') : 'can');
  });
  cellsEl.addEventListener('pointerleave', renderGhostOff);
  function renderGhostOff() { ghost.className = 'yard-ghost'; }

  itemsEl.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('.yard-item') : null;
    if (!b) return;
    var key = b.dataset.key;
    if ((own[key] || 0) > 0) {
      hand = (hand && hand.key === key) ? null : { key: key, from: null };
      sel = null; tool = 'place';
      afterChange();
    } else {
      doBuy(key);          // 背包没有 → 点一下就买（能量不够会提示）
    }
  });

  catsEl.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('.yard-cat') : null;
    if (!b) return;
    cat = b.dataset.cat;
    renderCats(); renderItems();
  });

  function bind(id, fn) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('click', fn);
  }
  bind('yardErase', function () {
    tool = tool === 'erase' ? 'place' : 'erase';
    var b = document.getElementById('yardErase');
    if (b) b.classList.toggle('on', tool === 'erase');
    renderBar();
  });
  bind('yardClear', doClear);
  bind('yardZin', function () { zoom = Math.min(2.2, zoom + 0.15); applyView(); });
  bind('yardZout', function () { zoom = Math.max(0.45, zoom - 0.15); applyView(); });
  bind('yardRot', function () { rz = (rz + 90) % 360; applyView(); });
  bind('yardReset', function () { zoom = 1; rz = 45; rx = 56; applyView(); });

  function applyView() {
    view.style.setProperty('--zoom', zoom);
    view.style.setProperty('--rz', rz + 'deg');
    view.style.setProperty('--rx', rx + 'deg');
  }

  /* ---------------- 起飞 ---------------- */
  stage.style.setProperty('--grid', GRID);
  applyView();
  renderCells(); renderCats(); afterChange();

  window.yardPickDragFrom = function (x, y) { down = { x: x, y: y }; };
})();
