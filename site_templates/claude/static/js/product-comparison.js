(function () {
  'use strict';

  var ICONS = {
    plus: '<path d="M12 5v14M5 12h14"/>',
    eye: '<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6S2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="2.5"/>',
    eyeOff: '<path d="m3 3 18 18M10.6 6.2A9.7 9.7 0 0 1 12 6c6 0 9.5 6 9.5 6a16.5 16.5 0 0 1-2.1 2.8M6.2 6.2C3.8 8 2.5 12 2.5 12s3.5 6 9.5 6a9.5 9.5 0 0 0 3.1-.5M9.9 9.9a3 3 0 0 0 4.2 4.2"/>',
    reset: '<path d="M4 4v5h5M4.6 9A8 8 0 1 1 4 14"/>',
    copy: '<rect x="8" y="8" width="11" height="11" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    left: '<path d="M19 12H5m6-6-6 6 6 6"/>',
    right: '<path d="M5 12h14m-6-6 6 6-6 6"/>',
    detail: '<path d="M14 5h5v5M19 5l-8 8"/><path d="M19 13v5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"/>',
    inquiry: '<path d="M21 11.5a8.4 8.4 0 0 1-9 8 9.4 9.4 0 0 1-4-.9L3 20l1.4-4A8 8 0 1 1 21 11.5Z"/><path d="M8 12h.01M12 12h.01M16 12h.01"/>'
  };

  function text(value) { return String(value == null ? '' : value); }
  function safeHref(value) {
    var href = text(value).trim();
    return /^(?:https?:\/\/|mailto:|tel:|#|\/)/i.test(href) ? href : '#';
  }
  function safeImage(value) {
    var src = text(value).trim();
    return /^(?:https?:\/\/|\/|data:image\/)/i.test(src) ? src : '';
  }
  function el(name, className, content) {
    var node = document.createElement(name);
    if (className) node.className = className;
    if (content != null) node.textContent = text(content);
    return node;
  }
  function icon(name) {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    svg.innerHTML = ICONS[name] || ICONS.detail;
    return svg;
  }
  function setIconControl(node, iconName, label, showLabel) {
    if (!node) return;
    node.replaceChildren(icon(iconName));
    node.appendChild(el('span', showLabel ? 'pc-action-text' : 'pc-sr-only', label));
    node.setAttribute('aria-label', label);
    node.setAttribute('title', label);
  }

  function fillGroupFilter(groupFilter, payload) {
    // “对比分类”下拉：列出全站所有产品对比页，选中项跳转到对应对比页。
    // 选项值为页面 URL，当前页用 current_page_key 匹配并选中。
    if (!groupFilter) return;
    var pages = Array.isArray(payload.comparison_pages) ? payload.comparison_pages : [];
    // 少于 2 个对比页时下拉无意义，直接隐藏，避免出现只有一项的空壳
    if (pages.length < 2) { groupFilter.parentNode.hidden = true; return; }
    groupFilter.innerHTML = '';
    pages.forEach(function (page) {
      var option = document.createElement('option');
      option.value = text(page.url);
      option.textContent = text(page.title);
      if (text(page.key) === text(payload.current_page_key)) option.selected = true;
      groupFilter.appendChild(option);
    });
  }

  // 无产品时的操作区：外观与有产品时一致，但除“对比分类”下拉外全部禁用置灰。
  // 只做静态呈现，不绑定加入/搜索等交互（那些在无数据下没有意义）。
  function initEmptyToolbar(root, payload) {
    var totalProducts = Array.isArray(payload.products) ? payload.products.length : 0;
    // 图标按钮沿用统一渲染，保证图标/间距和有产品时完全一致，再统一禁用
    setIconControl(root.querySelector('[data-pc-add]'), 'plus', '加入对比', true);
    setIconControl(root.querySelector('[data-pc-hide-same]'), 'eyeOff', '隐藏相同项', false);
    setIconControl(root.querySelector('[data-pc-reset]'), 'reset', '恢复默认', false);
    setIconControl(root.querySelector('[data-pc-share]'), 'copy', '复制对比链接', false);
    // 搜索框与所有操作按钮禁用（分类下拉除外）
    root.querySelectorAll('[data-pc-search],[data-pc-add],[data-pc-hide-same],[data-pc-reset],[data-pc-share]')
      .forEach(function (node) { node.disabled = true; });
    // 产品下拉给出“没有可对比的产品”提示并禁用
    var candidate = root.querySelector('[data-pc-candidate]');
    if (candidate) {
      candidate.innerHTML = '';
      var prompt = document.createElement('option');
      prompt.value = '';
      prompt.disabled = true;
      prompt.textContent = '没有可对比的产品';
      candidate.appendChild(prompt);
      candidate.value = '';
      candidate.disabled = true;
    }
    var limit = root.querySelector('[data-pc-limit]');
    if (limit) limit.textContent = '已选择 0 / ' + totalProducts + ' 个产品';
    // “对比分类”下拉照常可用，选中后跳转到对应对比页
    var groupFilter = root.querySelector('[data-pc-group-filter]');
    fillGroupFilter(groupFilter, payload);
    if (groupFilter) groupFilter.addEventListener('change', function () {
      var url = groupFilter.value;
      if (url && url !== window.location.pathname) window.location.href = url;
    });
  }

  function init(root) {
    if (root.dataset.pcReady === '1') return;
    root.dataset.pcReady = '1';
    var payloadNode = root.querySelector('[data-pc-payload]');
    var payload;
    try { payload = JSON.parse(payloadNode ? payloadNode.textContent : '{}'); } catch (error) { return; }
    var products = Array.isArray(payload.products) ? payload.products : [];
    // 无产品时不初始化对比表，但操作区仍照常显示：把搜索/加入/操作按钮全部置灰，
    // 产品下拉给出“没有可对比的产品”提示、已选 0/0，只保留“对比分类”下拉可用，
    // 让用户能一键跳到其他有产品的对比页。
    if (!products.length) { initEmptyToolbar(root, payload); return; }
    // 真实产品数只用于计数和交互；displaySlots 是最小视觉槽位数，不随产品总数扩张。
    // 实际选中数达到该值后不再补占位列，超过时表格按真实选中数自然扩展。
    var totalProducts = products.length;
    var displaySlots = Math.max(1, parseInt(payload.display_slots, 10) || 5);
    var byId = {};
    products.forEach(function (product) { byId[text(product.id)] = product; });
    function defaultSelection() {
      var ids = (payload.default_ids || []).map(text).filter(function (id, index, values) {
        return byId[id] && values.indexOf(id) === index;
      }).slice(0, totalProducts);
      return ids.length ? ids : products.slice(0, Math.min(3, products.length)).map(function (product) { return text(product.id); });
    }
    var query = new URL(window.location.href).searchParams.get('compare');
    var selected = (query ? query.split(',') : []).map(text).filter(function (id, index, values) {
      return byId[id] && values.indexOf(id) === index;
    }).slice(0, totalProducts);
    if (!selected.length) selected = defaultSelection();
    var state = {selected: selected, hideSame: false, search: ''};
    var head = root.querySelector('[data-pc-head]');
    var body = root.querySelector('[data-pc-body]');
    var groupsNav = root.querySelector('[data-pc-groups]');
    var candidate = root.querySelector('[data-pc-candidate]');
    var groupFilter = root.querySelector('[data-pc-group-filter]');
    var limit = root.querySelector('[data-pc-limit]');
    var empty = root.querySelector('[data-pc-empty]');
    var hideSameButton = root.querySelector('[data-pc-hide-same]');
    var tableScroll = root.querySelector('.pc-table-scroll');
    var table = root.querySelector('.pc-table');
    var groupsAside = root.querySelector('.pc-groups');
    var stickyHead = el('div', 'pc-sticky-head');
    var stickyHeadScroll = el('div', 'pc-sticky-head-scroll');
    var floatingScroll = el('div', 'pc-floating-scroll');
    var floatingSpacer = el('div', 'pc-floating-scroll-spacer');
    var viewportFrame = 0;
    var syncingHorizontal = false;
    stickyHead.setAttribute('aria-hidden', 'true');
    stickyHead.appendChild(stickyHeadScroll);
    floatingScroll.setAttribute('role', 'region');
    floatingScroll.setAttribute('aria-label', '产品表格横向滚动条');
    floatingScroll.tabIndex = 0;
    floatingScroll.appendChild(floatingSpacer);
    root.appendChild(stickyHead);
    root.appendChild(floatingScroll);

    setIconControl(root.querySelector('[data-pc-add]'), 'plus', '加入对比', true);
    setIconControl(hideSameButton, 'eyeOff', '隐藏相同项', false);
    setIconControl(root.querySelector('[data-pc-reset]'), 'reset', '恢复默认', false);
    setIconControl(root.querySelector('[data-pc-share]'), 'copy', '复制对比链接', false);

    function currentProducts() { return state.selected.map(function (id) { return byId[id]; }).filter(Boolean); }
    function headerHeight() {
      var siteHeader = document.querySelector('.site-header');
      if (siteHeader) return Math.max(0, siteHeader.getBoundingClientRect().bottom);
      var value = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--header-height'));
      return Number.isFinite(value) ? value : 64;
    }
    function stickyTop() {
      var top = headerHeight();
      if (window.innerWidth <= 760 && groupsAside) top += groupsAside.offsetHeight;
      return top;
    }
    function syncHorizontal(source) {
      if (syncingHorizontal) return;
      syncingHorizontal = true;
      var left = source.scrollLeft;
      if (source !== tableScroll) tableScroll.scrollLeft = left;
      if (source !== stickyHeadScroll) stickyHeadScroll.scrollLeft = left;
      if (source !== floatingScroll) floatingScroll.scrollLeft = left;
      syncingHorizontal = false;
    }
    function updateViewportUi() {
      viewportFrame = 0;
      if (!tableScroll || !head.children.length) return;
      var tableRect = tableScroll.getBoundingClientRect();
      var headRect = head.getBoundingClientRect();
      var top = stickyTop();
      var headHeight = head.offsetHeight;
      var stickyVisible = headRect.top <= top && tableRect.bottom > top + headHeight;
      stickyHead.classList.toggle('is-visible', stickyVisible);
      root.classList.toggle('pc-sticky-active', stickyVisible);
      stickyHead.style.top = top + 'px';
      stickyHead.style.left = tableRect.left + 'px';
      stickyHead.style.width = tableRect.width + 'px';
      stickyHeadScroll.scrollLeft = tableScroll.scrollLeft;

      var overflows = tableScroll.scrollWidth > tableScroll.clientWidth + 1;
      var tableInView = tableRect.top < window.innerHeight - 20 && tableRect.bottom > top + 20;
      var nativeScrollbarVisible = tableRect.bottom > 0 && tableRect.bottom <= window.innerHeight;
      var floatingVisible = overflows && tableInView && !nativeScrollbarVisible;
      floatingScroll.classList.toggle('is-visible', floatingVisible);
      floatingScroll.style.left = Math.max(0, tableRect.left) + 'px';
      floatingScroll.style.width = Math.min(tableRect.width, window.innerWidth - Math.max(0, tableRect.left)) + 'px';
      floatingScroll.style.bottom = '10px';
      floatingSpacer.style.width = tableScroll.scrollWidth + 'px';
      floatingScroll.scrollLeft = tableScroll.scrollLeft;
    }
    function requestViewportUpdate() {
      if (!viewportFrame) viewportFrame = window.requestAnimationFrame(updateViewportUi);
    }
    function rebuildStickyHead() {
      if (!table || !head.children.length) return;
      stickyHeadScroll.innerHTML = '';
      var cloneTable = table.cloneNode(false);
      cloneTable.classList.add('pc-table--sticky');
      cloneTable.style.width = table.scrollWidth + 'px';
      cloneTable.appendChild(head.cloneNode(true));
      stickyHeadScroll.appendChild(cloneTable);
      // 吸顶表头保留产品图片（不再删除），尺寸由 .pc-sticky-head .pc-product-image 缩小
      stickyHeadScroll.querySelectorAll('a,button,input,select,[tabindex]').forEach(function (control) { control.tabIndex = -1; });
      syncHorizontal(tableScroll);
      requestViewportUpdate();
    }
    function updateUrl() {
      var url = new URL(window.location.href);
      url.searchParams.set('compare', state.selected.join(','));
      window.history.replaceState({}, '', url.pathname + url.search + url.hash);
    }
    function updateCandidates() {
      if (!candidate) return;
      var oldValue = candidate.value;
      var availableProducts = products.filter(function (product) {
        return state.selected.indexOf(text(product.id)) === -1;
      });
      candidate.innerHTML = '';
      // 下拉框始终保留状态提示，避免产品选满或无候选项时出现没有文字的空白控件。
      var prompt = document.createElement('option');
      prompt.value = '';
      prompt.disabled = true;
      prompt.textContent = availableProducts.length ? '请选择要加入对比的产品' : '没有更多可添加的产品';
      candidate.appendChild(prompt);
      availableProducts.forEach(function (product) {
        var option = document.createElement('option');
        option.value = text(product.id);
        option.textContent = product.title + (product.category ? ' · ' + product.category : '');
        candidate.appendChild(option);
      });
      if (oldValue && Array.prototype.some.call(candidate.options, function (option) { return option.value === oldValue; })) candidate.value = oldValue;
      else candidate.value = '';
      candidate.disabled = !availableProducts.length;
      var add = root.querySelector('[data-pc-add]');
      if (add) add.disabled = candidate.disabled || !candidate.value;
      if (limit) limit.textContent = '已选择 ' + state.selected.length + ' / ' + totalProducts + ' 个产品';
    }
    function populateGroupFilter() { fillGroupFilter(groupFilter, payload); }
    function productButton(label, iconName, action, productId, disabled) {
      var button = el('button', 'pc-mini pc-icon-button');
      button.type = 'button';
      button.dataset.pcAction = action;
      button.dataset.productId = productId;
      button.disabled = !!disabled;
      setIconControl(button, iconName, label, false);
      return button;
    }
    function productLink(label, iconName, href) {
      var link = el('a', 'pc-mini pc-icon-button');
      link.href = safeHref(href);
      setIconControl(link, iconName, label, false);
      return link;
    }
    function renderHead(selectedProducts) {
      var visibleSlots = Math.max(selectedProducts.length, displaySlots);
      head.innerHTML = '';
      var row = document.createElement('tr');
      var corner = el('th', 'pc-param-head', '参数 / 产品');
      corner.scope = 'col';
      row.appendChild(corner);
      selectedProducts.forEach(function (product, index) {
        var cell = el('th', 'pc-product-head');
        cell.scope = 'col';
        var imageSrc = safeImage(product.image);
        if (payload.show_image && imageSrc) {
          var image = el('img', 'pc-product-image'); image.src = imageSrc; image.alt = product.title; image.loading = 'lazy'; cell.appendChild(image);
        }
        cell.appendChild(el('div', 'pc-product-title', product.title));
        if (payload.show_price && product.price) cell.appendChild(el('div', 'pc-product-price', product.price + (product.price_note ? ' ' + product.price_note : '')));
        var actions = el('div', 'pc-product-actions');
        actions.setAttribute('aria-label', product.title + ' 操作');
        actions.appendChild(productButton('左移', 'left', 'left', product.id, index === 0));
        actions.appendChild(productButton('右移', 'right', 'right', product.id, index === selectedProducts.length - 1));
        actions.appendChild(productButton('从对比中隐藏', 'eye', 'remove', product.id, selectedProducts.length <= 1));
        if (product.detail_url) actions.appendChild(productLink('查看详情', 'detail', product.detail_url));
        cell.appendChild(actions); row.appendChild(cell);
      });
      // 只补足视觉槽位，不改变真实产品总数，也不限制后续加入产品。
      for (var pad = selectedProducts.length; pad < visibleSlots; pad++) {
        var placeholder = el('th', 'pc-product-head pc-product-head--empty');
        placeholder.setAttribute('aria-hidden', 'true');
        row.appendChild(placeholder);
      }
      head.appendChild(row);
    }
    function renderBody(selectedProducts) {
      var visibleSlots = Math.max(selectedProducts.length, displaySlots);
      body.innerHTML = ''; if (groupsNav) groupsNav.innerHTML = '';
      var visibleRows = 0;
      (payload.groups || []).forEach(function (group, groupIndex) {
        var rows = (group.rows || []).filter(function (row) {
          var values = selectedProducts.map(function (product) { return text((product.values || {})[group.key + ':' + row.key]); });
          var haystack = (row.label + ' ' + values.join(' ')).toLowerCase();
          if (state.search && haystack.indexOf(state.search) === -1) return false;
          if (state.hideSame && values.length > 1 && values.every(function (value) { return value === values[0]; })) return false;
          return values.some(Boolean) || !state.search;
        });
        if (!rows.length) return;
        visibleRows += rows.length;
        var groupId = 'pc-group-' + groupIndex;
        var groupRow = document.createElement('tr'); groupRow.className = 'pc-group-row'; groupRow.id = groupId;
        // 组标题行横跨参数列 + 全部视觉槽位，背景铺满整行。
        var groupCell = el('th'); groupCell.colSpan = visibleSlots + 1; groupCell.scope = 'colgroup'; groupCell.appendChild(el('span', 'pc-group-title', group.title || '规格参数')); groupRow.appendChild(groupCell); body.appendChild(groupRow);
        if (groupsNav) { var navButton = el('button', 'pc-group-link', group.title || '规格参数'); navButton.type = 'button'; navButton.dataset.target = groupId; groupsNav.appendChild(navButton); }
        rows.forEach(function (rowData) {
          var row = document.createElement('tr');
          var label = el('th', 'pc-param-name', rowData.label || rowData.key); label.scope = 'row';
          if (rowData.unit) label.appendChild(el('span', 'pc-param-unit', '(' + rowData.unit + ')'));
          row.appendChild(label);
          selectedProducts.forEach(function (product) {
            var value = text((product.values || {})[group.key + ':' + rowData.key]) || payload.empty_text;
            row.appendChild(el('td', '', value));
          });
          // 每行同样补足空占位单元格，保持与表头一致的固定列数
          for (var padCell = selectedProducts.length; padCell < visibleSlots; padCell++) {
            row.appendChild(el('td', 'pc-cell--empty'));
          }
          body.appendChild(row);
        });
      });
      var firstGroup = groupsNav && groupsNav.querySelector('.pc-group-link');
      if (firstGroup) firstGroup.classList.add('active');
      if (empty) empty.hidden = visibleRows > 0;
    }
    function render() {
      var selectedProducts = currentProducts();
      renderHead(selectedProducts); renderBody(selectedProducts); updateCandidates(); updateUrl(); rebuildStickyHead();
    }

    root.addEventListener('click', function (event) {
      var action = event.target.closest('[data-pc-action]');
      if (action) {
        var id = action.dataset.productId; var index = state.selected.indexOf(id);
        if (action.dataset.pcAction === 'remove' && state.selected.length > 1) state.selected.splice(index, 1);
        if (action.dataset.pcAction === 'left' && index > 0) { state.selected.splice(index, 1); state.selected.splice(index - 1, 0, id); }
        if (action.dataset.pcAction === 'right' && index < state.selected.length - 1) { state.selected.splice(index, 1); state.selected.splice(index + 1, 0, id); }
        render(); return;
      }
      var groupLink = event.target.closest('.pc-group-link');
      if (groupLink) {
        groupsNav.querySelectorAll('.pc-group-link').forEach(function (button) { button.classList.toggle('active', button === groupLink); });
        var target = root.querySelector('#' + groupLink.dataset.target);
        if (target) target.scrollIntoView({behavior:'smooth', block:'start'});
        return;
      }
      if (event.target.closest('[data-pc-add]') && candidate && candidate.value && state.selected.length < totalProducts) { state.selected.push(candidate.value); render(); return; }
      var hideSame = event.target.closest('[data-pc-hide-same]');
      if (hideSame) {
        state.hideSame = !state.hideSame;
        hideSame.setAttribute('aria-pressed', state.hideSame ? 'true' : 'false');
        setIconControl(hideSame, state.hideSame ? 'eye' : 'eyeOff', state.hideSame ? '显示全部参数' : '隐藏相同项', false);
        render(); return;
      }
      if (event.target.closest('[data-pc-reset]')) {
        state.selected = defaultSelection(); state.hideSame = false; state.search = '';
        var search = root.querySelector('[data-pc-search]'); if (search) search.value = '';
        if (hideSameButton) { hideSameButton.setAttribute('aria-pressed', 'false'); setIconControl(hideSameButton, 'eyeOff', '隐藏相同项', false); }
        render(); return;
      }
      var share = event.target.closest('[data-pc-share]');
      if (share) {
        var copy = navigator.clipboard && navigator.clipboard.writeText ? navigator.clipboard.writeText(window.location.href) : Promise.reject();
        copy.then(function () {
          setIconControl(share, 'check', '链接已复制', false);
          setTimeout(function () { setIconControl(share, 'copy', '复制对比链接', false); }, 1500);
        }).catch(function () { window.prompt('复制此链接', window.location.href); });
      }
    });
    var searchInput = root.querySelector('[data-pc-search]');
    if (searchInput) searchInput.addEventListener('input', function () { state.search = searchInput.value.trim().toLowerCase(); renderBody(currentProducts()); });
    if (candidate) candidate.addEventListener('change', function () {
      var add = root.querySelector('[data-pc-add]');
      if (add) add.disabled = candidate.disabled || !candidate.value;
    });
    // 选择对比分类 → 跳转到对应对比页（不做当前页内过滤）
    if (groupFilter) groupFilter.addEventListener('change', function () {
      var url = groupFilter.value;
      if (url && url !== window.location.pathname) window.location.href = url;
    });
    tableScroll.addEventListener('scroll', function () { syncHorizontal(tableScroll); requestViewportUpdate(); }, {passive: true});
    floatingScroll.addEventListener('scroll', function () { syncHorizontal(floatingScroll); }, {passive: true});
    window.addEventListener('scroll', requestViewportUpdate, {passive: true});
    window.addEventListener('resize', function () { rebuildStickyHead(); requestViewportUpdate(); }, {passive: true});
    if (window.ResizeObserver) new ResizeObserver(requestViewportUpdate).observe(tableScroll);
    populateGroupFilter();
    render();
    window.setTimeout(rebuildStickyHead, 250);
  }

  function boot() { document.querySelectorAll('[data-product-comparison]').forEach(init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
}());
