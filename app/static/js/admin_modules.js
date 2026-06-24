/* admin_modules.js —共享模块表单渲染
 *
 * 页面编辑器(panel_page_edit.html) 和数数据集编辑面板 (panel_data_list.html)
 * 共用此文件。每个模板在使用前定义好:
 *   window._moduleCtx.blockLibrary —模块库列表
 *   window._moduleCtx.datasetNames —数据集选项 (可选?
 *   window._moduleCtx.editItem   —当前编辑条目 (item_data 模式, 可选?
 *   window._moduleCtx.isDatasetMode —是否为数据集编辑模式
 *
 * 然后调用 window._buildModuleHTML(type, idx, mdata) 生成模块 HTML。
 * 返回值 { html, borderStyle, headerBg }
 *   - html: 模块内部 HTML (不含 .module-item 外层)
 *   - borderStyle / headerBg: 外层和内标题栏样式
 */

;(function() {
  'use strict';

  /* ====== 工具函数 ====== */

  function esc(s) {
    return String(s || '').replace(/[&<>'"]/g, function(c) {
      return { '&': '&', '<': '<', '>': '>', "'": '&#39;', '"': '"' }[c];
    });
  }

  window._insertRichEditorLink = function(btn, event) {
    if (event) event.preventDefault();
    var wrapper = btn && btn.closest ? btn.closest('.mb-2') : null;
    var editor = wrapper ? wrapper.querySelector('.rich-editor-body') : null;
    if (!editor) return false;
    var sel = window.getSelection();
    var range = null;
    if (sel && sel.rangeCount && editor.contains(sel.getRangeAt(0).commonAncestorContainer)) {
      range = sel.getRangeAt(0).cloneRange();
    }
    var url = window.prompt('链接地址');
    if (!url) return false;
    editor.focus();
    var link = document.createElement('a');
    link.href = url;
    link.target = '_blank';
    link.rel = 'noopener';
    if (range && !range.collapsed) {
      try {
        range.surroundContents(link);
      } catch (err) {
        var fragment = range.extractContents();
        link.appendChild(fragment);
        range.insertNode(link);
      }
    } else {
      link.textContent = url;
      if (!range) {
        range = document.createRange();
        range.selectNodeContents(editor);
        range.collapse(false);
      }
      range.insertNode(link);
    }
    var textarea = editor.nextElementSibling;
    if (textarea) textarea.value = editor.innerHTML;
    return false;
  };

  window._richEditorCommand = function(btn, event, cmd, arg) {
    if (event) event.preventDefault();
    var wrapper = btn && btn.closest ? btn.closest('.mb-2') : null;
    var editor = wrapper ? wrapper.querySelector('.rich-editor-body') : null;
    if (!editor) return false;
    editor.focus();
    document.execCommand(cmd, false, arg || null);
    var textarea = editor.nextElementSibling;
    if (textarea) textarea.value = editor.innerHTML;
    return false;
  };

  window._richEditorSelectCommand = function(control, cmd, arg) {
    var wrapper = control && control.closest ? control.closest('.mb-2') : null;
    var editor = wrapper ? wrapper.querySelector('.rich-editor-body') : null;
    if (!editor) return false;
    editor.focus();
    document.execCommand(cmd, false, arg || null);
    var textarea = editor.nextElementSibling;
    if (textarea) textarea.value = editor.innerHTML;
    return false;
  };

  window._insertRichEditorTable = function(btn, event) {
    if (event) event.preventDefault();
    var wrapper = btn && btn.closest ? btn.closest('.mb-2') : null;
    var editor = wrapper ? wrapper.querySelector('.rich-editor-body') : null;
    if (!editor) return false;
    var size = window.prompt('表格行列，例濡?3x3', '3x3');
    if (size === null) return false;
    var match = String(size || '').toLowerCase().match(/^\s*(\d+)\s*[x*,\x2c ]\s*(\d+)\s*$/);
    var rows = match ? parseInt(match[1], 10) : 3;
    var cols = match ? parseInt(match[2], 10) : 3;
    rows = Math.max(1, Math.min(rows || 3, 20));
    cols = Math.max(1, Math.min(cols || 3, 10));
    editor.focus();
    var html = '<table><tbody>';
    for (var r = 0; r < rows; r++) {
      html += '<tr>';
      for (var c = 0; c < cols; c++) html += '<td><br></td>';
      html += '</tr>';
    }
    html += '</tbody></table><p><br></p>';
    document.execCommand('insertHTML', false, html);
    var textarea = editor.nextElementSibling;
    if (textarea) textarea.value = editor.innerHTML;
    return false;
  };

  function richEditorHtml(name, value) {
    return '<div class="rte-wrapper">' +
      '<div class="rich-toolbar rte-toolbar" style="display:flex;gap:1px;margin-bottom:3px;flex-wrap:wrap;align-items:center">' +
      /* 格式按钮 */
      '<button type="button" class="btn btn-sm btn-light rte-btn" data-cmd="bold" title="加粗"><b>B</b></button>' +
      '<button type="button" class="btn btn-sm btn-light rte-btn" data-cmd="italic" title="斜体"><i>I</i></button>' +
      '<button type="button" class="btn btn-sm btn-light rte-btn" data-cmd="underline" title="下划线"><u>U</u></button>' +
      '<button type="button" class="btn btn-sm btn-light rte-btn" data-cmd="strikeThrough" title="删除线"><s>S</s></button>' +
      '<span class="rte-sep"></span>' +
      /* 标题下拉 */
      '<select class="form-select form-select-sm rte-heading-select" style="width:auto;font-size:12px" title="标题">' +
        '<option value="">正文</option><option value="h1">H1</option><option value="h2">H2</option><option value="h3">H3</option><option value="h4">H4</option>' +
      '</select>' +
      '<span class="rte-sep"></span>' +
      /* 对齐 */
      '<button type="button" class="btn btn-sm btn-light rte-btn" data-cmd="justifyLeft" title="左对齐">≡</button>' +
      '<button type="button" class="btn btn-sm btn-light rte-btn" data-cmd="justifyCenter" title="居中">≡</button>' +
      '<button type="button" class="btn btn-sm btn-light rte-btn" data-cmd="justifyRight" title="右对齐">≡</button>' +
      '<span class="rte-sep"></span>' +
      /* 列表 */
      '<button type="button" class="btn btn-sm btn-light rte-btn" data-cmd="insertUnorderedList" title="无序列表">•≡</button>' +
      '<button type="button" class="btn btn-sm btn-light rte-btn" data-cmd="insertOrderedList" title="有序列表">1.</button>' +
      '<button type="button" class="btn btn-sm btn-light rte-btn rte-table-btn" title="插入表格">⊞</button>' +
      '<button type="button" class="btn btn-sm btn-light rte-btn rte-table-settings-btn" title="表格设置">⚙</button>' +
      '<span class="rte-sep"></span>' +
      /* 链接/图片 */
      '<button type="button" class="btn btn-sm btn-light rte-btn rte-link-btn" title="插入链接">🔗</button>' +
      '<span class="rte-sep"></span>' +
      /* 块级 */
      '<button type="button" class="btn btn-sm btn-light rte-btn" data-cmd="formatBlock" data-arg="blockquote" title="引用块">❝</button>' +
      '<button type="button" class="btn btn-sm btn-light rte-btn" data-cmd="insertHorizontalRule" title="分割线">—</button>' +
      '<span class="rte-sep"></span>' +
      /* 文字颜色 */
      '<input type="color" class="rte-color-picker" value="#141413" style="width:28px;height:28px;border:1px solid #dee2e6;border-radius:4px;padding:2px;cursor:pointer" title="文字颜色">' +
      '<span class="rte-sep"></span>' +
      /* 清除格式 + 撤销/重做 */
      '<button type="button" class="btn btn-sm btn-light rte-btn" data-cmd="removeFormat" title="清除格式">✕</button>' +
      '<button type="button" class="btn btn-sm btn-light rte-btn" data-cmd="undo" title="撤销">↩</button>' +
      '<button type="button" class="btn btn-sm btn-light rte-btn" data-cmd="redo" title="重做">↪</button>' +
      '</div>' +
      '<div contenteditable="true" class="rich-editor-body form-control form-control-sm rte-editor" style="min-height:150px;max-height:400px;overflow-y:auto;line-height:1.7;font-size:13px;outline:none" data-placeholder="">' + (value || '') + '</div>' +
      '<textarea class="form-control form-control-sm d-none" name="' + esc(name) + '">' + esc(value || '') + '</textarea>' +
      '</div>';
  }

  function cn(name, ph, dv) {
    var hasVal = dv && String(dv).trim();
    var color = hasVal ? dv : '#888888';
    return '<label class="form-label small mb-1 text-muted">' + ph + '</label>' +
      '<div class="input-group input-group-sm">' +
      '<input type="color" class="form-control form-control-color" value="' + esc(color) + '" oninput="this.parentElement.querySelector(\'input[type=text]\').value=this.value">' +
      '<input type="text" class="form-control form-control-sm" name="' + name + '" value="' + esc(hasVal ? dv : '') + '" placeholder="' + esc(ph) + '" oninput="this.parentElement.querySelector(\'input[type=color]\').value=this.value">' +
      '</div>';
  }

  function un(name, ph, units, dv) {
    var opts = (units || []).map(function(u) { return '<option value="' + u + '">' + u + '</option>'; }).join('');
    return '<label class="form-label small mb-1 text-muted">' + ph + '</label>' +
      '<div class="input-group input-group-sm">' +
      '<input type="text" class="form-control form-control-sm" name="' + name + '" value="' + esc(dv || '') + '" placeholder="' + esc(ph) + '" style="width:60%">' +
      '<select class="form-select form-select-sm unit-picker" style="width:40%" onchange="var i=this.parentElement.querySelector(\'[name=&quot;' + name + '&quot;]\');if(i){var v=i.value.replace(/px|rem|%$/i,\'\').trim();var u=this.value;if(v&&u)i.value=v+u;}">' +
      '<option value="">--</option>' + opts + '</select></div>';
  }

  function sel(name, ph, options, dv) {
    var segmented = segmentedControl(name, options, dv, esc);
    if (segmented) {
      return '<label class="form-label small mb-1 text-muted">' + ph + '</label>' + segmented;
    }
    var h = '<label class="form-label small mb-1 text-muted">' + ph + '</label><select class="form-select form-select-sm" name="' + name + '">';
    options.forEach(function(o) {
      h += '<option value="' + esc(o.value) + '"' + (String(dv || '') === String(o.value) ? ' selected' : '') + '>' + esc(o.label) + '</option>';
    });
    return h + '</select>';
  }

  function iconRegistry() {
    return (window._moduleCtx && window._moduleCtx.iconRegistry) || window.iconRegistry || {};
  }

  function iconNames() {
    var names = [];
    if (typeof iconList !== 'undefined' && Array.isArray(iconList)) names = iconList.slice();
    if (!names.length) names = Object.keys(iconRegistry());
    return names.filter(function(name, idx) {
      return name && names.indexOf(name) === idx;
    }).sort();
  }

  function iconSvg(name) {
    return iconRegistry()[String(name || '')] || '';
  }

  function iconPickerHtml(name, value) {
    var current = String(value || '');
    var currentLabel = current || '(none)';
    var html = '<div class="icon-picker" data-value="' + esc(current) + '">' +
      '<input type="hidden" name="' + esc(name) + '" value="' + esc(current) + '">' +
      '<button type="button" class="icon-picker-trigger" onclick="window._toggleIconPicker(this,event)">' +
        '<span class="icon-picker-preview">' + (current ? iconSvg(current) : '') + '</span>' +
        '<span class="icon-picker-label">' + esc(currentLabel) + '</span>' +
        '<span class="icon-picker-caret">▾</span>' +
      '</button>' +
      '<div class="icon-picker-menu" onclick="event.stopPropagation()">' +
        '<input type="text" class="form-control form-control-sm icon-picker-search" placeholder="搜索图标" oninput="window._filterIconPicker(this)">' +
        '<div class="icon-picker-options">' +
          '<button type="button" class="icon-picker-option' + (!current ? ' active' : '') + '" data-value="" onclick="window._selectIconPicker(this,event)">' +
            '<span class="icon-picker-option-preview"></span><span class="icon-picker-option-label">（无图标）</span>' +
          '</button>';
    iconNames().forEach(function(iconName) {
      var active = current === String(iconName);
      html += '<button type="button" class="icon-picker-option' + (active ? ' active' : '') + '" data-value="' + esc(iconName) + '" data-label="' + esc(iconName).toLowerCase() + '" onclick="window._selectIconPicker(this,event)">' +
        '<span class="icon-picker-option-preview">' + iconSvg(iconName) + '</span>' +
        '<span class="icon-picker-option-label">' + esc(iconName) + '</span>' +
      '</button>';
    });
    html += '</div></div></div>';
    return html;
  }

  window._iconPickerHtml = iconPickerHtml;

  window._toggleIconPicker = function(trigger, event) {
    if (event) event.stopPropagation();
    var picker = trigger && trigger.closest ? trigger.closest('.icon-picker') : null;
    if (!picker) return;
    document.querySelectorAll('.icon-picker.open').forEach(function(openPicker) {
      if (openPicker !== picker) {
        openPicker.classList.remove('open');
        var openItem = openPicker.closest('.module-item');
        if (openItem) openItem.classList.remove('icon-picker-open');
      }
    });
    picker.classList.toggle('open');
    var item = picker.closest('.module-item');
    if (item) item.classList.toggle('icon-picker-open', picker.classList.contains('open'));
    if (picker.classList.contains('open')) {
      var search = picker.querySelector('.icon-picker-search');
      if (search) {
        search.value = '';
        window._filterIconPicker(search);
        setTimeout(function() { search.focus(); }, 0);
      }
    }
  };

  window._selectIconPicker = function(option, event) {
    if (event) event.stopPropagation();
    var picker = option && option.closest ? option.closest('.icon-picker') : null;
    if (!picker) return;
    var value = option.getAttribute('data-value') || '';
    var input = picker.querySelector('input[type="hidden"]');
    var preview = picker.querySelector('.icon-picker-preview');
    var label = picker.querySelector('.icon-picker-label');
    if (input) {
      input.value = value;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
    if (preview) preview.innerHTML = value ? iconSvg(value) : '';
    if (label) label.textContent = value || '(none)';
    picker.dataset.value = value;
    picker.querySelectorAll('.icon-picker-option').forEach(function(btn) {
      btn.classList.toggle('active', (btn.getAttribute('data-value') || '') === value);
    });
    picker.classList.remove('open');
    var item = picker.closest('.module-item');
    if (item) item.classList.remove('icon-picker-open');
  };

  window._filterIconPicker = function(input) {
    var picker = input && input.closest ? input.closest('.icon-picker') : null;
    if (!picker) return;
    var q = String(input.value || '').trim().toLowerCase();
    picker.querySelectorAll('.icon-picker-option').forEach(function(option) {
      var label = option.getAttribute('data-label') || option.textContent.toLowerCase();
      option.style.display = !q || label.indexOf(q) >= 0 ? '' : 'none';
    });
  };

  document.addEventListener('click', function() {
    document.querySelectorAll('.icon-picker.open').forEach(function(picker) {
      picker.classList.remove('open');
      var item = picker.closest('.module-item');
      if (item) item.classList.remove('icon-picker-open');
    });
  });

  function schemaEsc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function attrEsc(s) {
    return schemaEsc(s).replace(/'/g, '&#39;');
  }

  function segmentedControl(name, options, value, escapeFn) {
    var escFn = escapeFn || esc;
    var opts = (options || []).map(function(opt) {
      return {
        value: String(typeof opt === 'object' ? opt.value : opt),
        label: String(typeof opt === 'object' ? (opt.label || opt.text || opt.value) : opt)
      };
    });
    if (opts.length < 2 || opts.length > 3) return '';
    var current = String(value == null ? '' : value);
    return '<div class="seg-radio" role="radiogroup">' +
      opts.map(function(opt) {
        var active = current === opt.value;
        var id = (name + '_' + opt.value).replace(/[^a-zA-Z0-9_-]/g, '_');
        return '<label class="seg-radio-option' + (active ? ' active' : '') + '" role="radio" aria-checked="' + (active ? 'true' : 'false') + '" for="' + escFn(id) + '">' +
          '<input type="radio" id="' + escFn(id) + '" name="' + escFn(name) + '" value="' + escFn(opt.value) + '"' + (active ? ' checked' : '') + ' onchange="var input=this;var g=input.closest(\'.seg-radio\');g.querySelectorAll(\'.seg-radio-option\').forEach(function(b){b.classList.toggle(\'active\', b.contains(input));b.setAttribute(\'aria-checked\', b.contains(input)?\'true\':\'false\');});">' +
          '<span class="seg-radio-dot" aria-hidden="true"></span><span class="seg-radio-label">' + escFn(opt.label) + '</span>' +
          '</label>';
      }).join('') +
      '</div>';
  }

  function isDescriptionKey(key) {
    return /(description|summary|excerpt|desc|intro|message)/i.test(String(key || ''));
  }

  function mediaUploadHtml(name, value, type, placeholder) {
    var isVideo = type === 'video';
    var safeName = esc(name);
    var safeValue = esc(value || '');
    var accept = isVideo ? 'video/mp4,video/webm,video/ogg,video/quicktime' : 'image/*,.svg,.svgz';
    var icon = isVideo
      ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>'
      : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>';
    var preview = value
      ? (isVideo ? '<video src="' + safeValue + '" muted></video>' : '<img src="' + safeValue + '" alt="">')
      : icon;
    return '<div class="module-media-tools mt-1">' +
        '<label class="module-media-picker' + (value ? ' has-media' : '') + '" title="点击上传">' +
          preview +
          (value ? '<span class="module-media-preview-icon" aria-hidden="true"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg></span>' : '') +
          '<input type="file" name="' + safeName + '_file" accept="' + accept + '" onchange="handleModuleImageUpload(this)" style="display:none">' +
          (value ? '<button type="button" class="module-media-clear" onclick="event.preventDefault();event.stopPropagation();clearModuleImage(this)" title="删除后重新上传">×</button>' : '') +
        '</label>' +
      '</div>' +
      '<div class="form-text mt-1">' + (isVideo ? '支持 MP4/WebM/OGG/MOV。' : '默认转 WebP，取消勾选则保留原格式。') + '</div>' +
      '<div class="module-media-url-row">' +
        '<input type="text" class="form-control form-control-sm" name="' + safeName + '" value="' + safeValue + '" placeholder="' + esc(placeholder || '') + '" oninput="updateImagePreview(this)">' +
        '<button type="button" class="module-media-library-btn" onclick="openModuleMediaLibrary(this)" title="从媒体库选择"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg></button>' +
        (isVideo ? '' : '<input type="hidden" name="' + safeName + '_convert_webp" value="false"><label class="module-convert-check"><input type="checkbox" name="' + safeName + '_convert_webp" value="true" checked><span></span>WebP</label>') +
      '</div>';
}

  function enhanceCompactSelects(root) {
    root = root || document;
    root.querySelectorAll('select.form-select').forEach(function(select) {
      if (select.dataset.segmentedEnhanced === '1') return;
      if (select.multiple || select.classList.contains('unit-picker') || select.classList.contains('rte-heading-select') || select.dataset.noSegmented === '1') return;
      if (select.closest('.input-group')) return;
      var options = Array.prototype.slice.call(select.options || []).filter(function(opt) {
        return opt.value !== '';
      });
      if (options.length < 2 || options.length > 3) return;
      select.dataset.segmentedEnhanced = '1';
      var wrapper = document.createElement('div');
      wrapper.innerHTML = segmentedControl(select.name, options.map(function(opt) {
        return { value: opt.value, label: opt.textContent };
      }), select.value, esc);
      var segmented = wrapper.firstElementChild;
      select.parentNode.insertBefore(segmented, select);
      select.remove();
    });
  }

  window.enhanceCompactSelects = enhanceCompactSelects;

  function schemaStyleForm(prefix, schema, mdata) {
    mdata = mdata || {};
    var registry = (window._moduleCtx && window._moduleCtx.styleRegistry) || {};
    var tokens = [];
    ((schema && schema.style_tokens) || []).concat((schema && schema.element_style_tokens) || []).forEach(function(token) {
      if (tokens.indexOf(token) === -1) tokens.push(token);
    });
    if (!tokens.length) return '<div class="small text-muted">该模块无可调样式</div>';
    var html = '';
    tokens.forEach(function(token) {
      var def = registry[token];
      if (!def) return;
      var name = prefix + 'style_' + token;
      var val = (mdata && mdata['style_' + token] != null) ? mdata['style_' + token] : '';
      html += '<div class="mb-2"><label class="form-label small mb-1 text-muted">' + schemaEsc(labelText({ key: token, label: def.label || token })) + '</label>';
      if (def.control === 'select' || def.control === 'switch') {
        var segmented = segmentedControl(name, def.options || [], val, schemaEsc);
        if (segmented) {
          html += segmented;
        } else {
          html += '<select class="form-select form-select-sm" name="' + schemaEsc(name) + '"><option value="">默认</option>';
          (def.options || []).forEach(function(o) {
            var ov = o.value, ol = o.text || o.value;
            html += '<option value="' + schemaEsc(ov) + '"' + (String(val) === String(ov) ? ' selected' : '') + '>' + schemaEsc(ol) + '</option>';
          });
          html += '</select>';
        }
      } else if (def.control === 'color') {
        html += '<div class="input-group input-group-sm">' +
          '<input type="color" class="form-control form-control-color" value="' + schemaEsc(val || '#888888') + '" oninput="this.nextElementSibling.value=this.value">' +
          '<input type="text" class="form-control form-control-sm" name="' + schemaEsc(name) + '" value="' + schemaEsc(val) + '" placeholder="如 #f5f7fa"></div>';
      } else if (def.control === 'image') {
        html += mediaUploadHtml(name, val || '', 'image', '背景鍥?URL');
      } else {
        html += '<input type="text" class="form-control form-control-sm" name="' + schemaEsc(name) + '" value="' + schemaEsc(val) + '">';
      }
      html += '</div>';
    });
    return html || '<div class="small text-muted">该模块无可调样式</div>';
  }

  // 眼睛切换按钮（显隐控制），与 panel_page_edit.html 中 toggleVisibilityEye 配合
  var EYE_OPEN = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
  var EYE_OFF = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72 1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
  window.EYE_OPEN_SVG = window.EYE_OPEN_SVG || EYE_OPEN;
  window.EYE_OFF_SVG = window.EYE_OFF_SVG || EYE_OFF;
  if (typeof window.toggleVisibilityEye !== 'function') {
    window.toggleVisibilityEye = function(btn) {
      var isVisible = btn.getAttribute('data-visible') === 'true';
      var newVisible = !isVisible;
      btn.setAttribute('data-visible', newVisible ? 'true' : 'false');
      var hiddenInput = btn.parentElement.querySelector('input[type="hidden"]');
      if (hiddenInput) hiddenInput.value = newVisible ? 'true' : 'false';
      btn.innerHTML = newVisible ? window.EYE_OPEN_SVG : window.EYE_OFF_SVG;
      btn.title = newVisible ? '点击隐藏' : '点击显示';
    };
  }
  function isVisibilityField(field) {
    var key = String(field.key || field.name || '');
    var opts = field.options || [];
    var values = opts.map(function(opt) { return String(typeof opt === 'object' ? opt.value : opt); });
    var hasTrueFalse = values.indexOf('true') >= 0 && values.indexOf('false') >= 0;
    return hasTrueFalse && (/^show_/i.test(key) || /_show_/i.test(key) || /visible/i.test(key));
  }
  function visibilityEye(name, value) {
    var visible = value === '' || value == null ? true : (String(value) === 'true' || value === true);
    return '<button type="button" class="eye-toggle-btn" data-visible="' + (visible ? 'true' : 'false') + '" onclick="toggleVisibilityEye(this)" title="' + (visible ? '点击隐藏' : '点击显示') + '">' +
      (visible ? EYE_OPEN : EYE_OFF) +
      '</button>' +
      '<input type="hidden" name="' + esc(name) + '" value="' + (visible ? 'true' : 'false') + '">';
  }
  function visToggle(name, label, dv) {
    var visible = dv === 'true';
    return '<div class="visibility-item">' +
      '<button type="button" class="eye-toggle-btn" data-target="' + name + '" data-visible="' + dv + '" onclick="toggleVisibilityEye(this)" title="' + (visible ? '点击隐藏' : '点击显示') + '">' +
      (visible ? EYE_OPEN : EYE_OFF) +
      '</button>' +
      '<span class="vis-label">' + label + '</span>' +
      '<input type="hidden" name="' + name + '" value="' + dv + '">' +
      '</div>';
  }

  function detailGalleryIcon(name) {
    var icons = {
      up: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg>',
      down: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>',
      trash: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
      chevron: '<svg class="detail-gallery-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="transition:transform .15s"><path d="m6 9 6 6 6-6"/></svg>'
    };
    return icons[name] || '';
  }

  function detailGalleryItemHtml(index, url, collapsed) {
    var hasUrl = !!url;
    return '<div class="border rounded mb-2 detail-gallery-item' + (collapsed ? ' collapsed' : '') + '" data-image-index="' + index + '">' +
      '<div class="detail-gallery-item-header d-flex justify-content-between align-items-center px-2 py-2" style="cursor:pointer;background:#f8fafc;border-radius:4px 4px 0 0" onclick="window._toggleDetailGalleryItem(this)">' +
        '<div class="d-flex align-items-center gap-2">' +
          detailGalleryIcon('chevron') +
          '<span class="small fw-semibold">图片 ' + (index + 1) + '</span>' +
        '</div>' +
        '<div class="d-flex align-items-center gap-1">' +
          '<button type="button" class="module-action-btn" onclick="event.stopPropagation();window._moveDetailGalleryImage(this,-1)" title="上移" aria-label="上移">' + detailGalleryIcon('up') + '</button>' +
          '<button type="button" class="module-action-btn" onclick="event.stopPropagation();window._moveDetailGalleryImage(this,1)" title="下移" aria-label="下移">' + detailGalleryIcon('down') + '</button>' +
          '<button type="button" class="module-action-btn module-action-del" onclick="event.stopPropagation();this.closest(\'.detail-gallery-item\').remove();window._reindexDetailGalleryImages()" title="删除" aria-label="删除">' + detailGalleryIcon('trash') + '</button>' +
        '</div>' +
      '</div>' +
      '<div class="detail-gallery-item-body p-2" style="' + (collapsed ? 'display:none;' : '') + '">' +
        mediaUploadHtml('detail_gallery_' + index + '_url', url || '', 'image', '图片 URL 或上传') +
      '</div>' +
    '</div>';
  }

  window._toggleDetailGalleryItem = function(header) {
    var item = header && header.closest ? header.closest('.detail-gallery-item') : null;
    if (!item) return;
    var body = item.querySelector('.detail-gallery-item-body');
    var isCollapsed = item.classList.toggle('collapsed');
    if (body) body.style.display = isCollapsed ? 'none' : '';
    var chevron = item.querySelector('.detail-gallery-chevron');
    if (chevron) chevron.style.transform = isCollapsed ? 'rotate(-90deg)' : '';
  };

  window._moveDetailGalleryImage = function(btn, dir) {
    var item = btn && btn.closest ? btn.closest('.detail-gallery-item') : null;
    var list = item && item.parentElement;
    if (!item || !list) return;
    if (dir < 0 && item.previousElementSibling) {
      list.insertBefore(item, item.previousElementSibling);
    } else if (dir > 0 && item.nextElementSibling) {
      list.insertBefore(item.nextElementSibling, item);
    }
    window._reindexDetailGalleryImages();
  };

  window._syncDetailGalleryPreview = function(input) {
    var item = input && input.closest ? input.closest('.detail-gallery-item') : null;
    if (!item) return;
    var preview = item.querySelector('.detail-gallery-preview');
    var img = preview ? preview.querySelector('img') : null;
    var url = input.value || '';
    if (!preview || !img) return;
    if (url) {
      img.src = url;
      preview.style.display = '';
    } else {
      img.removeAttribute('src');
      preview.style.display = 'none';
    }
  };

  window._previewDetailGalleryFile = function(input) {
    var file = input && input.files ? input.files[0] : null;
    var item = input && input.closest ? input.closest('.detail-gallery-item') : null;
    var preview = item ? item.querySelector('.detail-gallery-preview') : null;
    var img = preview ? preview.querySelector('img') : null;
    if (!file || !preview || !img) return;
    var reader = new FileReader();
    reader.onload = function(e) {
      img.src = e.target.result;
      preview.style.display = '';
    };
    reader.readAsDataURL(file);
  };

  window._addDetailGalleryImage = function() {
    var editor = document.querySelector('.detail-gallery-editor');
    if (!editor) return;
    var countEl = editor.querySelector('.detail-gallery-count');
    var list = editor.querySelector('.detail-gallery-list');
    var next = parseInt(countEl.value || '0', 10);
    list.insertAdjacentHTML('beforeend', detailGalleryItemHtml(next, '', false));
    countEl.value = next + 1;
    window._reindexDetailGalleryImages();
  };

  window._reindexDetailGalleryImages = function() {
    var editor = document.querySelector('.detail-gallery-editor');
    if (!editor) return;
    var items = editor.querySelectorAll('.detail-gallery-item');
    var countEl = editor.querySelector('.detail-gallery-count');
    if (countEl) countEl.value = items.length;
    items.forEach(function(item, i) {
      item.dataset.imageIndex = i;
      var title = item.querySelector('.small.fw-semibold');
      if (title) title.textContent = '图片 ' + (i + 1);
      item.querySelectorAll('input[name]').forEach(function(el) {
        el.name = el.name.replace(/detail_gallery_\d+_/, 'detail_gallery_' + i + '_');
      });
      var chevron = item.querySelector('.detail-gallery-chevron');
      if (chevron) chevron.style.transform = item.classList.contains('collapsed') ? 'rotate(-90deg)' : '';
    });
  };

  function statItemData(mdata, statIndex) {
    var stats = mdata && Array.isArray(mdata.stats) ? mdata.stats : [];
    return stats[statIndex] || {};
  }

  window._statItemHtml = function(moduleIndex, statIndex, mdata) {
    var p = 'module_' + moduleIndex + '_stats_' + statIndex + '_';
    var item = statItemData(mdata, statIndex);
    return '<div class="border rounded p-2 mb-2 list-item" data-item-index="' + statIndex + '">' +
      '<div class="d-flex justify-content-between align-items-center mb-2 list-item-header" style="cursor:pointer; user-select:none;" onclick="this.closest(\'.list-item\').classList.toggle(\'collapsed\')">' +
        '<span class="small fw-semibold">统计项' + (statIndex + 1) + '</span>' +
        '<button type="button" class="btn btn-sm btn-outline-danger" onclick="event.stopPropagation();this.closest(\'.list-item\').remove();window._reindexStatItems(' + moduleIndex + ')" title="删除"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg></button>' +
      '</div>' +
      '<div class="list-item-body">' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">图标</label>' + iconPickerHtml(p + 'icon', item.icon || '') + '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">数字</label><input type="number" class="form-control form-control-sm" name="' + p + 'number" value="' + esc(item.number || '') + '" placeholder="濡?500"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">后缀</label><input type="text" class="form-control form-control-sm" name="' + p + 'suffix" value="' + esc(item.suffix || '') + '" placeholder="濡?+"></div>' +
        '</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标签</label><input type="text" class="form-control form-control-sm" name="' + p + 'label" value="' + esc(item.label || '') + '" placeholder="濡?服务客户"></div>' +
      '</div>' +
    '</div>';
  };

  window._addStatItem = function(moduleIndex) {
    var editor = document.querySelector('.stat-items-editor[data-module-index="' + moduleIndex + '"]');
    if (!editor) return;
    var count = editor.querySelector('.stat-item-count');
    var list = editor.querySelector('.stat-item-list');
    var next = parseInt(count.value || '0', 10);
    list.insertAdjacentHTML('beforeend', window._statItemHtml(moduleIndex, next, {}));
    count.value = next + 1;
  };

  window._reindexStatItems = function(moduleIndex) {
    var editor = document.querySelector('.stat-items-editor[data-module-index="' + moduleIndex + '"]');
    if (!editor) return;
    var items = editor.querySelectorAll('.list-item');
    var count = editor.querySelector('.stat-item-count');
    if (count) count.value = items.length;
    items.forEach(function(item, idx) {
      item.dataset.itemIndex = idx;
      var label = item.querySelector('.small.fw-semibold');
      if (label) label.textContent = '统计项' + (idx + 1);
      item.querySelectorAll('input[name], select[name], textarea[name]').forEach(function(el) {
        el.name = el.name.replace(/module_\d+_stats_\d+_/, 'module_' + moduleIndex + '_stats_' + idx + '_');
      });
    });
  };

  var FIELD_LABEL_MAP = {
    title: 'Title', subtitle: 'Subtitle', desc: 'Description', description: 'Description', excerpt: 'Excerpt', summary: 'Summary',
    body: 'Body', content: 'Content', tag: 'Tag', tags: 'Tags', name: 'Name', category: 'Category', price: 'Price', date: 'Date', slug: 'Slug',
    image: 'Image', cover: 'Cover', photo: 'Photo', logo: 'Logo', icon: 'Icon', video: 'Video', media: 'Media', media_type: 'Media type',
    embed_url: 'Embed URL', link: 'Link', url: 'URL', href: 'Link', alt: 'Alt text', dataset: 'Dataset', columns: 'Columns', rows: 'Rows',
    items: 'Items', list: 'List', grid: 'Grid', layout: 'Layout', align: 'Align', visible: 'Visible', hidden: 'Hidden'
  };

  function normalizeLabelKey(value) {
    return String(value || '')
      .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
      .replace(/[\s-]+/g, '_')
      .replace(/__+/g, '_')
      .replace(/^_+|_+$/g, '')
      .toLowerCase();
  }

  function labelText(field) {
    var key = String(field.key || field.name || '');
    var raw = String(field.label || '');
    var normalizedKey = normalizeLabelKey(key);
    var normalizedRaw = normalizeLabelKey(raw);
    return FIELD_LABEL_MAP[normalizedKey] || FIELD_LABEL_MAP[normalizedRaw] || translateLabel(raw || key);
  }

  function translateLabel(label) {
    var text = String(label || '').trim();
    if (!text || /[\u4e00-\u9fff]/.test(text)) return text;
    var normalized = normalizeLabelKey(text);
    if (FIELD_LABEL_MAP[normalized]) return FIELD_LABEL_MAP[normalized];
    var tokenMap = {
      show: 'Show', hide: 'Hide', enable: 'Enable', enabled: 'Enabled', visible: 'Visible', primary: 'Primary', secondary: 'Secondary',
      button: 'Button', btn: 'Button', cta: 'CTA', link: 'Link', url: 'URL', href: 'Link', text: 'Text', title: 'Title', heading: 'Heading',
      subtitle: 'Subtitle', subheading: 'Subheading', desc: 'Description', description: 'Description', summary: 'Summary', image: 'Image', cover: 'Cover',
      background: 'Background', bg: 'Background', color: 'Color', badge: 'Badge', label: 'Label', icon: 'Icon', media: 'Media', video: 'Video',
      desktop: 'Desktop', tablet: 'Tablet', mobile: 'Mobile', width: 'Width', height: 'Height', size: 'Size', align: 'Align', layout: 'Layout'
    };
    return normalized.split('_').filter(Boolean).map(function(part) {
      return tokenMap[part] || part;
    }).join('') || text;
  }

  function isHalfField(field) {
    var key = String(field.key || field.name || '').toLowerCase();
    var type = String(field.type || 'text').toLowerCase();
    var label = String(field.label || '').toLowerCase();
    if (isVisibilityField(field)) return true;
    if (field.show_if && field.show_if.field) return false;
    if (/^(group|list|grid|textarea|richtext|image|video|embed|audio|file)$/i.test(type)) return false;
    if (/(url|src|href|link|action|address|description|summary|excerpt|content|body|message|image|cover|photo|logo|media|video)/i.test(key)) return false;
    if (/(_text|_title|title|subtitle|desc)$/i.test(key)) return false;
    if (/^(show_|hide_|enable_|enabled_|visible|is_)/i.test(key) || /(_show_|_visible|_enabled)$/i.test(key)) return true;
    if (/(align|layout|style|columns|items_per_page|max_items|count|number|ratio|category|date|price|name)$/i.test(key)) return true;
    if (/(color|bg|border|radius|width|height|size|gap|margin|padding|opacity|weight)$/i.test(key)) return true;
    if (/(显示|隐藏|颜色|宽度|高度|字号|圆角|间距|对齐|排版|列数|数量|分类|日期|价格|名称)/.test(label)) return true;
    return false;
  }

  function renderField(prefix, field, value, placeholder) {
    var key = field.key, type = (field.type || 'text').toLowerCase(), html = '';
    var isImage = /(image|cover|background|media|photo|logo)/i.test(key);
    var showIf = field.show_if || null;
    var wrapperAttrs = ' class="mb-2 module-field" data-field-key="' + esc(key) + '"';
    if (showIf && showIf.field) {
      wrapperAttrs += ' data-show-if-field="' + esc(showIf.field) + '" data-show-if-value="' + esc(showIf.value || '') + '"';
    }
    if (isVisibilityField(field)) {
      wrapperAttrs = wrapperAttrs.replace('module-field', 'module-field module-visibility-field');
    }
    if (isHalfField(field)) {
      wrapperAttrs = wrapperAttrs.replace('module-field', 'module-field module-field-half');
    }
    html += '<div' + wrapperAttrs + '><label class="form-label small mb-1 text-muted">' + esc(labelText(field)) + '</label>';
    if (isVisibilityField(field)) {
      html += visibilityEye(prefix + key, value);
    } else if (type === 'list' || type === 'grid') {
      html += schemaListEditor(prefix, field, value);
    } else if (type === 'video') {
      html += mediaUploadHtml(prefix + key, value || '', 'video', placeholder || '视频 URL');
    } else if (isImage) {
      html += mediaUploadHtml(prefix + key, value || '', 'image', placeholder || '');
    } else if (type === 'richtext') {
      html += richEditorHtml(prefix + key, value || '');
    } else if (type === 'textarea' && isDescriptionKey(key)) {
      html += richEditorHtml(prefix + key, value || '');
    } else if (type === 'textarea') {
      html += '<textarea class="form-control form-control-sm" rows="4" name="' + prefix + key + '" placeholder="' + esc(placeholder || '') + '">' + esc(value || '') + '</textarea>';
    } else if (type === 'select' && segmentedControl(prefix + key, field.options || [], value, esc)) {
      html += segmentedControl(prefix + key, field.options || [], value, esc);
    } else if (type === 'select') {
      html += '<select class="form-select form-select-sm" name="' + prefix + key + '"><option value="">请选择</option>';
      (field.options || []).forEach(function(opt) {
        var ov = typeof opt === 'object' ? opt.value : opt;
        var ol = typeof opt === 'object' ? (opt.label || opt.value) : opt;
        html += '<option value="' + esc(ov) + '"' + (String(value || '') === String(ov) ? ' selected' : '') + '>' + esc(ol) + '</option>';
      });
      html += '</select>';
    } else if (type === 'icon') {
      html += iconPickerHtml(prefix + key, value);
    } else if (type === 'number') {
      html += '<input type="number" class="form-control form-control-sm" name="' + prefix + key + '" value="' + esc(value || '') + '" placeholder="' + esc(placeholder || '') + '">';
    } else if (type === 'radio') {
      (field.options || []).forEach(function(opt, oi) {
        var ov = typeof opt === 'object' ? opt.value : opt;
        var ol = typeof opt === 'object' ? (opt.label || opt.value) : opt;
        html += '<div class="form-check form-check-inline">' +
          '<input class="form-check-input" type="radio" name="' + prefix + key + '" value="' + esc(ov) + '" id="' + prefix + key + '_' + oi + '"' +
          (String(value || '') === String(ov) ? ' checked' : '') + '>' +
          '<label class="form-check-label" for="' + prefix + key + '_' + oi + '">' + esc(ol) + '</label>' +
          '</div>';
      });
    } else if (type === 'switch') {
      // switch 开关控件（true/false），对齐 panel_page_edit.html 鐨?switch 渲染
      var checked = String(value || field.default || 'true') !== 'false';
      html += '<div class="form-check form-switch mb-0">' +
        '<input class="form-check-input" type="checkbox" role="switch" ' + (checked ? 'checked' : '') +
        ' onchange="var h=this.parentElement.querySelector(\'input[type=hidden]\');if(h)h.value=this.checked?\'true\':\'false\'">' +
        '</div>' +
        '<input type="hidden" name="' + prefix + key + '" value="' + (checked ? 'true' : 'false') + '">';
    } else {
      html += '<input type="text" class="form-control form-control-sm" name="' + prefix + key + '" value="' + esc(value || '') + '" placeholder="' + esc(placeholder || '') + '">';
    }
    return html + '</div>';
  }

  function fieldChildren(field) {
    return (field.children || field.item_fields || []).map(function(child) {
      var copy = Object.assign({}, child);
      copy.key = copy.key || copy.name;
      return copy;
    }).filter(function(child) {
      return !!child.key;
    });
  }

  function schemaFieldToFormField(field) {
    var copy = Object.assign({}, field || {});
    copy.key = copy.key || copy.name;
    copy.label = copy.label || copy.key;
    copy.children = (copy.children || copy.item_fields || []).map(schemaFieldToFormField).filter(function(child) {
      return !!child.key;
    });
    copy.item_fields = copy.children;
    return copy;
  }

  function schemaInlineHalfChild(field) {
    if (!field || field.type !== 'group' || field.hideable) return null;
    var children = fieldChildren(field);
    if (children.length !== 1) return null;
    return isHalfField(children[0]) ? children[0] : null;
  }

  function schemaHideToggle(name, label, hiddenVal) {
    var checked = hiddenVal !== 'true';
    return '<div class="form-check form-switch">' +
      '<input class="form-check-input" type="checkbox" role="switch" ' + (checked ? 'checked' : '') +
      ' onchange="this.parentElement.querySelector(\'input[type=hidden]\').value=this.checked?\'false\':\'true\'">' +
      '<label class="form-check-label small">' + esc(label) + '</label>' +
      '<input type="hidden" name="' + esc(name) + '" value="' + esc(hiddenVal || 'false') + '">' +
      '</div>';
  }

  function schemaDatasetField(prefix, field, mdata) {
    var key = field.key || field.name;
    if (field.source) {
      return '<div class="small text-muted mb-2">' + esc(labelText(field)) + ' comes from <b>' + esc(field.source) + '</b>.</div>';
    }
    var datasets = (window._moduleCtx && window._moduleCtx.datasetNames) || window.datasetNames || [];
    var val = (mdata && mdata.dataset != null) ? mdata.dataset : '';
    var html = '<div class="mb-2"><label class="form-label small mb-1 text-muted">Dataset: ' + esc(labelText(field)) + '</label>' +
      '<select class="form-select form-select-sm" data-no-segmented="1" name="' + esc(prefix + 'dataset') + '">' +
      '<option value="">Select dataset</option>';
    datasets.forEach(function(ds) {
      var target = ds.target || ds.value || ds.key || '';
      html += '<option value="' + esc(target) + '"' + (String(val) === String(target) ? ' selected' : '') + '>' + esc(ds.label || target) + '</option>';
    });
    html += '</select></div>';
    return html;
  }

  function schemaListEditor(prefix, field, value, mdata) {
    var key = field.key || field.name;
    if (field.source != null) {
      return schemaDatasetField(prefix, field, mdata || {});
    }
    var items = Array.isArray(value) ? value : ((mdata && Array.isArray(mdata[key])) ? mdata[key] : []);
    var children = fieldChildren(field);
    var base = prefix.replace(/data_$/, '');
    var html = '<div class="schema-list-editor" data-list-base="' + attrEsc(base) + '" data-list-name="' + attrEsc(key) + '" data-children="' + attrEsc(JSON.stringify(children)) + '">';
    html += '<div class="d-flex justify-content-between align-items-center mb-2">' +
      '<div class="small fw-semibold text-primary">' + esc(labelText(field)) + '</div>' +
      '<button type="button" class="btn btn-sm btn-outline-primary" onclick="window.schemaListAdd(this)">+ 添加条目</button>' +
      '</div>';
    html += '<input type="hidden" class="schema-list-count" name="' + attrEsc(base + key + '_count') + '" value="' + items.length + '">';
    html += '<div class="schema-list-items">';
    items.forEach(function(item, i) {
      html += schemaListItemHtml(base, key, i, children, item || {});
    });
    html += '</div></div>';
    if (key === 'items' && window._moduleCtx && window._moduleCtx.currentModuleType === 'featured_picks') {
      html = html.replace(
        '<button type="button" class="btn btn-sm btn-outline-primary" onclick="window.schemaListAdd(this)">+ 添加条目</button>',
        '<button type="button" class="btn btn-sm btn-outline-info fp-import-btn" onclick="event.stopPropagation();window.openFeaturedImport(0, this)" style="font-size:11px;margin-right:4px" title="从已有数据集选取条目，自动填入标题、图片、描述和链接">📜 从数据集导入</button>' +
        '<button type="button" class="btn btn-sm btn-outline-primary" onclick="window.schemaListAdd(this)">+ 添加条目</button>'
      );
    }
    return html;
  }

  function renderSchemaGroup(prefix, field, values) {
    values = values || {};
    var key = field.key || field.name || '';
    var children = fieldChildren(field);
    var html = '';
    if (children.length) {
      if (field.hideable) {
        html += '<div class="mb-2 pb-2" style="border-bottom:1px solid #e2e8f0">' +
          '<div class="d-flex align-items-center justify-content-between">' +
          '<label class="form-label small mb-0 text-muted fw-semibold">' + esc(labelText(field)) + '</label>' +
          '<div>' + schemaHideToggle(prefix + '_hidden_' + key, '显示', values['_hidden_' + key] || 'false') + '</div>' +
          '</div></div>';
      }
      html += '<div class="mb-2">';
      children.forEach(function(child) {
        if (child.type === 'group') {
          html += renderSchemaGroup(prefix, child, values);
        } else if (child.type === 'list' || child.type === 'grid') {
          html += schemaListEditor(prefix, child, values[child.key], values);
        } else {
          html += renderField(prefix, child, values[child.key] || child.default || '', '');
        }
      });
      html += '</div>';
    } else if (field.hideable) {
      html += '<div class="d-flex align-items-center gap-2 mb-2" style="white-space:nowrap">' +
        '<span class="small">' + esc(labelText(field)) + '</span>' +
        schemaHideToggle(prefix + '_hidden_' + key, '显示', values['_hidden_' + key] || 'false') +
        '</div>';
    }
    return html;
  }

  function renderSchemaForm(prefix, schema, values) {
    values = values || {};
    var html = '';
    if (schema && schema.from_source) {
      html += '<div class="alert alert-info py-2 px-3 mb-3" style="font-size:12px;line-height:1.5">' +
        '<div class="fw-semibold mb-1">此模块数据来自网站设置/div>' +
        '<div>数据源：<code>' + esc(schema.from_source) + '</code>，请在「网站设置」中修改。</div>' +
        '</div>';
    }
    var pendingHalf = [];
    function flushPendingHalf() {
      if (!pendingHalf.length) return;
      html += '<div class="module-field-row">';
      pendingHalf.forEach(function(field) {
        html += renderField(prefix, field, values[field.key] || field.default || '', '');
      });
      html += '</div>';
      pendingHalf = [];
    }
    ((schema && schema.fields) || []).forEach(function(field) {
      if (field.type === 'list' || field.type === 'grid') {
        flushPendingHalf();
        html += schemaListEditor(prefix, field, values[field.key], values);
      } else if (field.type === 'group') {
        var inlineChild = schemaInlineHalfChild(field);
        if (inlineChild) {
          pendingHalf.push(inlineChild);
        } else {
          flushPendingHalf();
          html += renderSchemaGroup(prefix, field, values);
        }
      } else if (isHalfField(field)) {
        pendingHalf.push(field);
      } else {
        flushPendingHalf();
        html += renderField(prefix, field, values[field.key] || field.default || '', '');
      }
    });
    flushPendingHalf();
    if (schema && schema.hideable) {
      var hiddenVal = values._hidden === true || values._hidden === 'true' ? 'true' : 'false';
      html += '<div class="mt-2 pt-2 border-top">' + schemaHideToggle(prefix + '_hidden', '整块显示', hiddenVal) + '</div>';
    }
    return html;
  }

  function getMergedSchema(meta) {
    var schema = (meta && meta.schema) || {};
    var metaFields = (meta && meta.fields) || [];
    var metaFieldMap = {};
    metaFields.forEach(function(f) { metaFieldMap[f.key] = f; });
    var schemaFieldMap = {};
    (schema.fields || []).forEach(function(sf) { schemaFieldMap[sf.name || sf.key] = sf; });
    var conditionalControllerMap = {};
    metaFields.forEach(function(f) {
      if (f.show_if && f.show_if.field) conditionalControllerMap[f.show_if.field] = true;
    });

    function mergeField(sf) {
      var name = sf.name || sf.key;
      var mf = metaFieldMap[name];
      var children = (sf.children || sf.item_fields || []).map(mergeField);
      var merged = Object.assign({}, sf, {
        name: name,
        key: name,
        children: children,
        item_fields: children
      });
      if (mf) {
        merged.type = mf.type || merged.type;
        merged.options = mf.options || merged.options;
        merged.label = mf.label || merged.label;
        merged.show_if = mf.show_if || merged.show_if;
        if ((mf.children || mf.item_fields || []).length && !children.length) {
          merged.children = (mf.children || mf.item_fields || []).map(mergeField);
          merged.item_fields = merged.children;
        }
      }
      merged.label = merged.label || name;
      return merged;
    }

    function metaToSchemaField(mf) {
      return mergeField({
        name: mf.key,
        key: mf.key,
        type: mf.type || 'text',
        label: mf.label || mf.key,
        children: mf.item_fields || mf.children || []
      });
    }

    var mergedFields = [];
    metaFields.forEach(function(mf) {
      if (!conditionalControllerMap[mf.key]) return;
      if (schemaFieldMap[mf.key]) return;
      mergedFields.push(metaToSchemaField(mf));
    });
    (schema.fields || []).forEach(function(sf) {
      mergedFields.push(mergeField(sf));
    });
    metaFields.forEach(function(mf) {
      if (schemaFieldMap[mf.key]) return;
      if (mf.type === 'list' || mf.type === 'grid') mergedFields.push(metaToSchemaField(mf));
    });

    return {
      root_type: schema.root_type,
      root_tag: schema.root_tag,
      hideable: schema.hideable,
      href_field: schema.href_field,
      style_tokens: schema.style_tokens || [],
      element_style_tokens: schema.element_style_tokens || [],
      from_source: schema.from_source,
      fields: mergedFields.map(schemaFieldToFormField)
    };
  }

  function featuredPicksEditors(prefix, meta, values) {
    meta = meta || findBlockMeta('featured_picks');
    values = values || {};
    var mergedSchema = getMergedSchema(meta);
    if (window._moduleCtx) window._moduleCtx.currentModuleType = 'featured_picks';
    var content = renderSchemaForm(prefix, mergedSchema, values);
    if (window._moduleCtx) window._moduleCtx.currentModuleType = '';
    return {
      content: content,
      style: schemaStyleForm(prefix, mergedSchema, values)
    };
  }

  function schemaListItemHtml(base, listName, index, children, itemData) {
    var itemPrefix = base + listName + '_' + index + '_';
    var inner = '';
    (children || []).forEach(function(child) {
      inner += renderField(itemPrefix, child, itemData ? itemData[child.key] : '', '');
    });
    return '<div class="border rounded p-2 mb-2 schema-list-item collapsed" data-item-index="' + index + '">' +
      '<div class="d-flex justify-content-between align-items-center mb-2 schema-list-item-header" data-schema-list-toggle="1" style="cursor:pointer;user-select:none">' +
        '<span class="small fw-semibold d-flex align-items-center">' +
          '<svg class="schema-list-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:12px;height:12px;margin-right:4px;flex-shrink:0;color:#94a3b8;transition:transform 0.2s"><path d="M9 18l6-6-6-6"/></svg>' +
          '条目 ' + (index + 1) +
        '</span>' +
        '<button type="button" class="module-action-btn module-action-del schema-list-remove" title="删除" aria-label="删除条目">✕</button>' +
      '</div>' +
      '<div class="schema-list-item-body">' + inner + '</div>' +
    '</div>';
  }

  function schemaListReindex(editor) {
    var base = editor.dataset.listBase || '';
    var listName = editor.dataset.listName || '';
    var prefixStr = base + listName + '_';
    var re = new RegExp('^(' + prefixStr.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')\\d+_');
    var items = editor.querySelectorAll('.schema-list-item');
    var count = editor.querySelector('.schema-list-count');
    if (count) count.value = items.length;
    items.forEach(function(item, i) {
      item.dataset.itemIndex = i;
      var label = item.querySelector('.schema-list-item-header .small.fw-semibold');
      if (label) {
        var svg = label.querySelector('svg');
        label.textContent = '条目 ' + (i + 1);
        if (svg) label.insertBefore(svg, label.firstChild);
      }
      item.querySelectorAll('[name]').forEach(function(el) {
        el.name = el.name.replace(re, function(_, prefix) { return prefix + i + '_'; });
      });
    });
  }

  window.schemaListAdd = function(btn) {
    var editor = btn.closest('.schema-list-editor');
    if (!editor) return;
    var base = editor.dataset.listBase || '';
    var listName = editor.dataset.listName || '';
    var children = [];
    try { children = JSON.parse(editor.dataset.children || '[]'); } catch (err) { children = []; }
    var list = editor.querySelector('.schema-list-items');
    var index = list ? list.querySelectorAll('.schema-list-item').length : 0;
    if (list) list.insertAdjacentHTML('beforeend', schemaListItemHtml(base, listName, index, children, {}));
    schemaListReindex(editor);
    updateConditionalFields(editor);
  };
  window._schemaListItemHtml = schemaListItemHtml;
  window._schemaListReindex = schemaListReindex;

  if (!window.__adminModulesSchemaListEventsBound) {
    window.__adminModulesSchemaListEventsBound = true;
    document.addEventListener('click', function(event) {
      var removeBtn = event.target.closest && event.target.closest('.schema-list-remove');
      if (removeBtn) {
        event.preventDefault();
        event.stopPropagation();
        var editor = removeBtn.closest('.schema-list-editor');
        var item = removeBtn.closest('.schema-list-item');
        if (item) item.remove();
        if (editor) schemaListReindex(editor);
        return;
      }
      var header = event.target.closest && event.target.closest('.schema-list-item-header[data-schema-list-toggle]');
      if (header && !event.target.closest('button,a,input,select,textarea,label')) {
        event.preventDefault();
        event.stopPropagation();
        var row = header.closest('.schema-list-item');
        if (row) row.classList.toggle('collapsed');
      }
    }, true);
  }

  window.openFeaturedImport = window.openFeaturedImport || function(moduleIdx, btn) {
    var datasets = (window._moduleCtx && window._moduleCtx.datasetNames) || window.datasetNames || [];
    var select = document.getElementById('dsPickerDataset');
    var items = document.getElementById('dsPickerItems');
    if (!select || !items) {
      window.alert('当前面板缺少数据集选择器，请刷新后台后重试');
      return;
    }
    window._featuredImportButton = btn;
    select.innerHTML = '<option value="">-- 请选择数据集--</option>';
    // 构建 target ↪完整菜单璺緞映射（含父级 group target锛?
    window._datasetPathMap = {};
    datasets.forEach(function(ds) {
      var target = ds.target || ds.value || ds.key || '';
      window._datasetPathMap[target] = ds.path || target;
      select.innerHTML += '<option value="' + esc(target) + '">' + esc(ds.label || ds.target || ds.value || ds.key || '') + '</option>';
    });
    items.innerHTML = '<div class="col-12 text-muted small text-center py-4">请先在上方选择一个数据集</div>';
    var modalEl = document.getElementById('datasetPickerModal');
    if (window.bootstrap && modalEl) {
      window.bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }
  };

  window.loadPickerDatasetItems = window.loadPickerDatasetItems || function(datasetName) {
    var itemsEl = document.getElementById('dsPickerItems');
    if (!itemsEl) return;
    if (!datasetName) {
      itemsEl.innerHTML = '<div class="col-12 text-muted small text-center py-4">请先在上方选择一个数据集</div>';
      window._featuredPickerCache = [];
      return;
    }
    var siteId = (window._moduleCtx && window._moduleCtx.siteId) || new URLSearchParams(window.location.search).get('site') || '';
    itemsEl.innerHTML = '<div class="col-12 text-muted small text-center py-4">加载中..</div>';
    fetch('/api/site/' + encodeURIComponent(siteId) + '/dataset/' + encodeURIComponent(datasetName) + '/items')
      .then(function(resp) {
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        return resp.json();
      })
      .then(function(data) {
        var items = data.items || [];
        window._featuredPickerCache = items;
        if (!items.length) {
          itemsEl.innerHTML = '<div class="col-12 text-muted small text-center py-4">该数据集暂无条目</div>';
          return;
        }
        itemsEl.innerHTML = items.map(function(item, i) {
          var cover = item.cover || item.image || item.photo || '';
          return '<div class="col-4 col-md-3 mb-2">' +
            '<div onclick="window.selectFeaturedItem(' + i + ')" style="cursor:pointer;border:1px solid #e2e8f0;border-radius:6px;overflow:hidden;height:100%">' +
              (cover ? '<img src="' + esc(cover) + '" alt="" loading="lazy" style="width:100%;height:90px;object-fit:cover" onerror="this.style.display=\'none\'">' : '<div style="width:100%;height:90px;background:#f1f5f9;display:flex;align-items:center;justify-content:center;color:#94a3b8">无图</div>') +
              '<div style="padding:6px 8px"><div style="font-size:11px;font-weight:600;line-height:1.3;color:#1e293b">' + esc(item.title || item.name || item.slug || '') + '</div></div>' +
            '</div></div>';
        }).join('');
      })
      .catch(function(err) {
        itemsEl.innerHTML = '<div class="col-12 text-danger small text-center py-4">加载失败: ' + esc(err.message || '未知错误') + '</div>';
      });
  };

  window.selectFeaturedItem = window.selectFeaturedItem || function(index) {
    var cache = window._featuredPickerCache || [];
    var item = cache[index];
    var btn = window._featuredImportButton;
    if (!item || !btn) return;
    var editor = btn.closest('.schema-list-editor');
    if (!editor) return;
    var base = editor.dataset.listBase || '';
    var listName = editor.dataset.listName || '';
    var children = [];
    try { children = JSON.parse(editor.dataset.children || '[]'); } catch (err) { children = []; }
    var dsName = (document.getElementById('dsPickerDataset') || {}).value || '';
    var siteId = (window._moduleCtx && window._moduleCtx.siteId) || new URLSearchParams(window.location.search).get('site') || '';
    var lang = (window._moduleCtx && window._moduleCtx.currentLang) || new URLSearchParams(window.location.search).get('lang') || '';
    // 用完整菜单路径（含父级group target）生成链鎺?
    var dsPath = (window._datasetPathMap && window._datasetPathMap[dsName]) || dsName;
    var link = item.slug && dsName && siteId ? ('/preview/' + siteId + '/' + (lang ? lang + '/' : '') + dsPath + '/' + item.slug + '/') : '';
    var itemData = {};
    children.forEach(function(child) {
      var name = child.key || child.name;
      if (name === 'image') itemData[name] = item.cover || item.image || item.photo || '';
      else if (name === 'title') itemData[name] = item.title || item.name || '';
      else if (name === 'desc') itemData[name] = item.summary || item.excerpt || item.description || '';
      else if (name === 'link') itemData[name] = link;
    });
    var list = editor.querySelector('.schema-list-items');
    var next = list ? list.querySelectorAll('.schema-list-item').length : 0;
    if (list) list.insertAdjacentHTML('beforeend', schemaListItemHtml(base, listName, next, children, itemData));
    schemaListReindex(editor);
    var added = list ? list.querySelector('.schema-list-item:last-child') : null;
    if (added) {
      added.classList.remove('collapsed');
      var imgInput = added.querySelector('[name$="_image"]');
      if (imgInput && typeof updateImagePreview === 'function') updateImagePreview(imgInput);
    }
    var modalEl = document.getElementById('datasetPickerModal');
    if (window.bootstrap && modalEl) {
      var modal = window.bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
    }
  };

  function renderFieldsGrouped(prefix, fields, values, placeholder) {
    values = values || {};
    var html = '';
    var pendingHalf = [];
    function flushPendingHalf() {
      if (!pendingHalf.length) return;
      html += '<div class="module-field-row">';
      pendingHalf.forEach(function(f) {
        html += renderField(prefix, f, values[f.key] || f.default || '', placeholder || '');
      });
      html += '</div>';
      pendingHalf = [];
    }
    (fields || []).forEach(function(field) {
      if (isHalfField(field)) {
        pendingHalf.push(field);
      } else {
        flushPendingHalf();
        html += renderField(prefix, field, values[field.key] || field.default || '', placeholder || '');
      }
    });
    flushPendingHalf();
    return html;
  }

  function findNamedInput(root, name) {
    var inputs = root.querySelectorAll('[name]');
    for (var i = 0; i < inputs.length; i++) {
      if (inputs[i].name === name) return inputs[i];
    }
    return null;
  }

  function updateConditionalFields(root) {
    root = root || document;
    root.querySelectorAll('.module-field[data-show-if-field]').forEach(function(fieldEl) {
      var fieldKey = fieldEl.getAttribute('data-field-key') || '';
      var depKey = fieldEl.getAttribute('data-show-if-field') || '';
      var expected = (fieldEl.getAttribute('data-show-if-value') || '').split(',').map(function(v) { return v.trim(); });
      var ownInput = fieldEl.querySelector('[name]');
      var prefix = '';
      if (ownInput && fieldKey && ownInput.name.slice(-fieldKey.length) === fieldKey) {
        prefix = ownInput.name.slice(0, -fieldKey.length);
      }
      var scope = fieldEl.closest('.device-config') || root;
      var depInput = prefix ? findNamedInput(scope, prefix + depKey) : null;
      var actual = depInput ? String(depInput.value || '') : '';
      if (!actual && depKey === 'media_type') actual = 'image';
      fieldEl.style.display = expected.indexOf(actual) >= 0 ? '' : 'none';
    });
  }

  // 图片上传：选择文件后本地预览（全局函数，供动态生成的 onchange 调用
  function moduleMediaPlaceholderIcon(accept) {
    var isVideo = /video/i.test(accept || '');
    return isVideo
      ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>'
      : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>';
  }

  function renderModuleMediaPicker(picker, src, fileName, accept) {
    if (!picker) return;
    var existingFile = picker.querySelector('input[type=file]');
    fileName = fileName || (existingFile ? existingFile.name : '');
    accept = accept || (existingFile ? existingFile.getAttribute('accept') : 'image/*,.svg,.svgz') || 'image/*,.svg,.svgz';
    var safeSrc = src ? String(src).replace(/"/g, '&quot;') : '';
    var isVideo = /video/i.test(accept || '') || /\.(mp4|webm|ogg|mov)$/i.test(safeSrc);
    picker.classList.toggle('has-media', !!src);
    picker.innerHTML = src
      ? (isVideo ? '<video src="' + safeSrc + '" muted></video>' : '<img src="' + safeSrc + '" alt="">') +
        '<span class="module-media-preview-icon" aria-hidden="true"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg></span>' +
        '<input type="file" name="' + fileName + '" accept="' + accept + '" onchange="handleModuleImageUpload(this)" style="display:none">' +
        '<button type="button" class="module-media-clear" onclick="event.preventDefault();event.stopPropagation();clearModuleImage(this)" title="删除后重新上传">×</button>'
      : moduleMediaPlaceholderIcon(accept) + '<input type="file" name="' + fileName + '" accept="' + accept + '" onchange="handleModuleImageUpload(this)" style="display:none">';
  }
  window.handleModuleImageUpload = function(fileInput) {
    var file = fileInput.files[0];
    var container = fileInput.closest('.hero-slide-body') || fileInput.closest('.mb-2');
    var picker = container ? container.querySelector('.module-media-picker') : null;
    if (!file || !picker) return;
    renderModuleMediaPicker(picker, URL.createObjectURL(file), fileInput.name, fileInput.getAttribute('accept') || '');
  };

  // 图片预览：点击放澶?
  window.enlargeImage = function(img) {
    var src = img.src;
    if (!src) return;
    var overlay = document.getElementById('imgLightbox');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'imgLightbox';
      overlay.style.cssText = 'position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.85);display:flex;align-items:center;justify-content:center;cursor:pointer';
      overlay.onclick = function() { overlay.style.display = 'none'; };
      var lbImg = document.createElement('img');
      lbImg.style.cssText = 'max-width:95vw;max-height:95vh;object-fit:contain;background-color:#fff;background-image:linear-gradient(45deg,#eef2f7 25%,transparent 25%),linear-gradient(-45deg,#eef2f7 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#eef2f7 75%),linear-gradient(-45deg,transparent 75%,#eef2f7 75%);background-position:0 0,0 8px,8px -8px,-8px 0;background-size:16px 16px;border-radius:6px;padding:12px;box-shadow:0 4px 30px rgba(0,0,0,.5)';
      overlay.appendChild(lbImg);
      document.body.appendChild(overlay);
    }
    overlay.querySelector('img').src = src;
    overlay.style.display = 'flex';
  };

  // 图片预览：删除按閽竻除图鐗?
  window.clearModuleImage = function(btn) {
    var container = btn.closest('.hero-slide-body') || btn.closest('.mb-2');
    if (!container) return;
    var urlInput = container.querySelector('input[type="text"][name]') || container.querySelector('input[type="hidden"][name]:not([name$="_convert_webp"])');
    var fileInput = container.querySelector('input[type="file"]');
    var picker = container.querySelector('.module-media-picker');
    if (urlInput) urlInput.value = '';
    if (fileInput) fileInput.value = '';
    renderModuleMediaPicker(picker, '', fileInput ? fileInput.name : '', fileInput ? fileInput.getAttribute('accept') : '');
  };

  // 图片预览锛歎RL 输入框变化时更新预览
  window.updateImagePreview = function(urlInput) {
    var container = urlInput.closest('.hero-slide-body') || urlInput.closest('.mb-2');
    var picker = container ? container.querySelector('.module-media-picker') : null;
    if (!picker) return;
    var fileInput = picker.querySelector('input[type=file]');
    renderModuleMediaPicker(picker, urlInput.value.trim(), fileInput ? fileInput.name : '', fileInput ? fileInput.getAttribute('accept') : '');
  };

  window.openModuleMediaLibrary = function(btn) {
    var container = btn.closest('.hero-slide-body') || btn.closest('.mb-2');
    var urlInput = container ? (container.querySelector('input[type="hidden"][name], input[type="text"][name]')) : null;
    if (!urlInput) return;
    var overlay = document.getElementById('moduleMediaLibraryOverlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'moduleMediaLibraryOverlay';
      overlay.className = 'module-media-library-overlay';
      overlay.innerHTML = '<div class="module-media-library-dialog">' +
        '<div class="module-media-library-head"><strong>选择媒体</strong><button type="button" class="module-media-library-close" title="关闭">×</button></div>' +
        '<div class="module-media-library-grid"><div class="text-muted small p-3">加载中..</div></div>' +
        '</div>';
      document.body.appendChild(overlay);
      overlay.addEventListener('click', function(e) {
        if (e.target === overlay || e.target.closest('.module-media-library-close')) {
          overlay.classList.remove('show');
        }
      });
    }
    overlay._targetInput = urlInput;
    overlay.classList.add('show');
    var grid = overlay.querySelector('.module-media-library-grid');
    grid.innerHTML = '<div class="text-muted small p-3">加载中..</div>';
    var site = (typeof currentSiteParam === 'function' && currentSiteParam()) || new URLSearchParams(window.location.search).get('site') || '';
    fetch('/media?_fragment=1' + (site ? '&site=' + encodeURIComponent(site) : ''))
      .then(function(r) { return r.text(); })
      .then(function(html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var cards = Array.prototype.slice.call(doc.querySelectorAll('.media-card[data-url]'));
        var items = cards.filter(function(card) {
          return ['image', 'video'].indexOf(card.dataset.category) >= 0;
        }).map(function(card) {
          var url = card.dataset.url || '';
          var name = card.dataset.displayName || url;
          var isImage = card.dataset.category === 'image';
          return '<button type="button" class="module-media-library-item" data-url="' + attrEsc(url) + '" title="' + attrEsc(name) + '">' +
            (isImage ? '<img src="' + attrEsc(url) + '" alt="" loading="lazy">' : '<span class="module-media-library-video">▶</span>') +
            '<span>' + schemaEsc(name) + '</span></button>';
        }).join('');
        grid.innerHTML = items || '<div class="text-muted small p-3">媒体库暂无可选图片或视频</div>';
      })
      .catch(function() {
        grid.innerHTML = '<div class="text-danger small p-3">媒体库加载失败/div>';
      });
  };

  document.addEventListener('click', function(e) {
    var item = e.target.closest('.module-media-library-item');
    if (!item) return;
    var overlay = item.closest('#moduleMediaLibraryOverlay');
    var input = overlay && overlay._targetInput;
    if (!input) return;
    input.value = item.dataset.url || '';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    overlay.classList.remove('show');
  });

  /* ====== 对外暴露 ====== */
  window._cn = cn;
  window._un = un;
  window._esc = esc;
  window._renderField = renderField;

  // 模块图标映射 —涓_block_icons.html 涓block_icon 宏保持一自动?
  function getBlockIconHTML(type) {
    var icons = {
      'hero_banner': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="14" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>',
      'section_title': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16"/><path d="M4 10h12"/><path d="M4 15h8"/><path d="M4 20h4"/></svg>',
      'text_content': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/></svg>',
      'highlight_card': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="8" height="16" rx="1"/><path d="M10 9h12v-2a1 1 0 0 0-1-1H10z"/><path d="M10 14h9"/><path d="M10 18h6"/></svg>',
      'feature_grid': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
      'data_grid': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M3 15h18"/><path d="M9 3v18"/></svg>',
      'stat_counter': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>',
      'contact_info': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 9h6"/><path d="M9 13h4"/><circle cx="8.5" cy="8.5" r="0.5" fill="currentColor"/><circle cx="8.5" cy="12.5" r="0.5" fill="currentColor"/></svg>',
      'contact_form': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 9h6"/><path d="M9 13h4"/><path d="M17 17l2 2"/><path d="M19 15a4 4 0 1 0-8 0"/></svg>',
      'process_steps': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="12" r="3"/><circle cx="12" cy="12" r="3"/><circle cx="19" cy="12" r="3"/><path d="M8 12h1"/><path d="M15 12h1"/></svg>',
      'logo_cloud': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="6" r="2"/><circle cx="16" cy="6" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="8" cy="18" r="2"/><circle cx="16" cy="18" r="2"/></svg>',
      'item_detail': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="18" rx="1"/><rect x="13" y="3" width="8" height="8" rx="1"/><path d="M13 15h4"/><path d="M13 19h6"/></svg>',
      'image_carousel': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="5" width="7" height="13" rx="1"/><rect x="13" y="5" width="7" height="13" rx="1"/><path d="m1 10 2 2-2 2"/><path d="m23 14-2-2 2-2"/></svg>',
      'featured_picks': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><path d="M17.5 14l1.2 2.5 2.7.4-2 2 .5 2.7-2.4-1.3-2.4 1.3.5-2.7-2-2 2.7-.4z"/></svg>'
    };
    return icons[type] || '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M12 8v8"/><path d="M8 12h8"/></svg>';
  }

  /* ====== findBlockMeta ====== */

  function findBlockMeta(type) {
    var lib = (window._moduleCtx && window._moduleCtx.blockLibrary) || [];
    return lib.find(function(b) { return b.name === type; }) || {
      name: type, display_name: type.replace(/_/g, ' '), fields: [], variants: []
    };
  }

  /* ====== 主函鏁? buildModuleHTML ======
   * type:   模块类型鍚
   * idx:    模块序号 (0-based)
   * mdata:  已保存的模块数据 (新模块传 {})
   * 返回:   { html, borderStyle, headerBg }
   */

  function buildModuleHTML(type, idx, mdata) {
    mdata = mdata || {};
    var meta = findBlockMeta(type);
    var fields = meta.fields || [];
    var displayName = meta.display_name || type.replace(/_/g, ' ');
    var isDataModule = (type === 'item_data');
    var d = mdata;
    var isDsMode = !!(window._moduleCtx && window._moduleCtx.isDatasetMode);

    // 动态字段 (根据 meta.yaml fields 生成)
    // 过滤掉由 specialEditor 自动渲染的字段（分页配置銆乧olumns 等），避免在通用表单区重复出鐜?
    var pagerKeys = ['show_pagination', 'pagination_style', 'items_per_page', 'pager_align', 'show_view_all', 'pager'];
    var desktopFieldList = fields.filter(function(f) {
      return ['columns', 'max_items'].concat(pagerKeys).indexOf(f.key) === -1;
    });
    var desktopFields = renderFieldsGrouped('module_' + idx + '_data_', desktopFieldList, d, '');
    var tabletFieldList = fields.filter(function(f) {
      return ['columns', 'max_items', 'items_per_page', 'show_pagination', 'pagination_style', 'pager_align', 'pager'].indexOf(f.key) === -1;
    });
    var tabletFields = renderFieldsGrouped('module_' + idx + '_resp_tablet_data_', tabletFieldList, {}, 'Desktop default');
    var mobileFieldList = fields.filter(function(f) {
      return ['columns', 'max_items', 'items_per_page', 'show_pagination', 'pagination_style', 'pager_align', 'pager'].indexOf(f.key) === -1;
    });
    var mobileFields = renderFieldsGrouped('module_' + idx + '_resp_mobile_data_', mobileFieldList, {}, 'Desktop default');

    // 数据集来源选项
    var datasetNames = (window._moduleCtx && window._moduleCtx.datasetNames) || [];

    var specialEditor = '';
    var styleEditor = '';
    var borderStyle = '';
    var headerBg = '';
    var titleColor = '';
    var schemaManaged = !!(!isDataModule && meta.is_data_attr && meta.schema);

    if (schemaManaged) {
      var mergedSchema = getMergedSchema(meta);
      if (type === 'featured_picks') {
        var featuredEditors = featuredPicksEditors('module_' + idx + '_data_', meta, d);
        specialEditor = featuredEditors.content;
        styleEditor = featuredEditors.style;
      } else {
        specialEditor = renderSchemaForm('module_' + idx + '_data_', mergedSchema, d);
        styleEditor = schemaStyleForm('module_' + idx + '_data_', mergedSchema, d);
      }
    }

    /* ====== item_data (详情数据) 特殊处理 ====== */
    if (isDataModule) {
      var item = (window._moduleCtx && window._moduleCtx.editItem) || mdata || {};
      var tagsVal = (item.tags && Array.isArray(item.tags)) ? item.tags.join(', ') : (item.tags || '');
      var tagsVisible = !(item.tags_visible === false || String(item.tags_visible) === 'false');
      var detailGallery = (item.detail_gallery && typeof item.detail_gallery === 'object') ? item.detail_gallery : {};
      var detailGalleryVisible = !(detailGallery.visible === false || String(detailGallery.visible) === 'false');
      var detailImages = Array.isArray(detailGallery.images) ? detailGallery.images : [];
      var detailGalleryHtml =
        '<div class="detail-gallery-editor" data-module-index="' + idx + '">' +
          '<div class="d-flex justify-content-between align-items-center mb-2">' +
            '<div class="d-flex align-items-center gap-2">' +
              '<div class="small fw-semibold text-primary">细节图库</div>' +
              visibilityEye('detail_gallery_visible', detailGalleryVisible ? 'true' : 'false') +
            '</div>' +
            '<button type="button" class="btn btn-sm btn-outline-primary" onclick="window._addDetailGalleryImage()">+ 添加图片</button>' +
          '</div>' +
          '<input type="hidden" name="detail_gallery_count" class="detail-gallery-count" value="' + detailImages.length + '">' +
          '<div class="detail-gallery-list">' +
            detailImages.map(function(img, ii) {
              var url = (typeof img === 'object' ? (img.url || '') : (img || ''));
              return detailGalleryItemHtml(ii, url, ii > 0);
            }).join('') +
          '</div>' +
        '</div>';
      /* 封面图：取 item 顶层字段，与列表页缩略图自动匹配（cover / image / photo 依次回退）*/
      var coverVal = item.cover || item.image || item.photo || '';
      styleEditor = schemaStyleForm('module_' + idx + '_data_', meta.schema || {}, item);
      specialEditor =
        '<div class="small fw-semibold mb-1 text-muted">基础字段</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">slug <span class="text-danger">*</span></label><input type="text" class="form-control form-control-sm font-monospace" name="slug" value="' + esc(item.slug || '') + '" required pattern="[a-z0-9][a-z0-9-]*[a-z0-9]" placeholder="濡?my-post"><div class="form-text">英文+数字+连字符，鍞竴标识</div></div>' +
        /* ==== 封面图：位于日期上方，只显示在数据集列表缩略图，不在详情页展示 ==== */
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">封面图</label>' +
        mediaUploadHtml('cover', coverVal, 'image', '图片 URL 或上传') +
        '<div class="form-text">仅显示在数据集列表中作为封面缩略图</div>' +
        detailGalleryHtml +
        '<hr class="my-2">' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">日期</label><input type="date" class="form-control form-control-sm" name="date" value="' + esc(item.date || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">名称</label><input type="text" class="form-control form-control-sm" name="name" value="' + esc(item.name || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">分类</label><input type="text" class="form-control form-control-sm" name="category" value="' + esc(item.category || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标题</label><input type="text" class="form-control form-control-sm" name="title" value="' + esc(item.title || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">简介</label>' + richEditorHtml('description', item.description || item.excerpt || item.summary || '') + '</div>' +
        '<div class="mb-2"><div class="d-flex align-items-center gap-2 mb-1"><label class="form-label small mb-0 text-muted">标签</label>' + visibilityEye('tags_visible', tagsVisible ? 'true' : 'false') + '</div><input type="text" class="form-control form-control-sm" name="tags" value="' + esc(tagsVal) + '" placeholder="多个用逗号或空格分隔"><div class="form-text">例如：LED, 展示道具, 近期项目</div></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">价格</label><input type="text" class="form-control form-control-sm" name="price" value="' + esc(item.price || '') + '" placeholder="例如 ¥199 / $3/million"></div>' +
        '<hr class="my-2">' +
        /* 富文本编辑器（详细介绍）——与其他模块统一使用 richEditorHtml */
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">详细介绍</label>' +
        richEditorHtml('body', item.body || item.content || '') +
        '<input type="hidden" name="rte_clicked_editor_idx" value="">' +
        '<div class="form-text">支持加粗、斜体、标题、列表、引用、分割线、链接、图片、文字颜色</div>' +
        '<hr class="my-2">';
      // 动态剩余字段
      var skipKeys = ['id','slug','date','title','description','excerpt','summary','cover','image','photo','logo','tags','tags_visible','detail_gallery','detail_images','body','content','modules','csrf_token','name','category','price','specs','section_bg','inner_width','style_bg-color'];
      Object.keys(item).forEach(function(k) {
        if (skipKeys.indexOf(k) >= 0 || /^module_/.test(k)) return;
        var v = item[k];
        specialEditor += '<div class="mb-2"><label class="form-label small mb-1 text-muted">' + esc(k) + '</label>';
        if (k === 'cover' || k === 'photo' || k === 'logo') {
          specialEditor += '<input type="text" class="form-control form-control-sm" name="' + esc(k) + '" value="' + esc(v || '') + '"><input type="file" class="form-control form-control-sm mt-1" name="' + esc(k) + '" accept="image/*">';
        } else if (typeof v === 'string' && v.length > 80) {
          specialEditor += '<textarea class="form-control form-control-sm" name="' + esc(k) + '" rows="3">' + esc(v) + '</textarea>';
        } else {
          specialEditor += '<input type="text" class="form-control form-control-sm" name="' + esc(k) + '" value="' + esc(v || '') + '">';
        }
        specialEditor += '</div>';
      });
    }

    /* ====== hero_banner ====== */
    if (!schemaManaged && type === 'hero_banner') {
      specialEditor =
        '<hr class="my-2">' +
        '<div class="hero-slides-editor" data-module-index="' + idx + '"><div class="d-flex justify-content-between align-items-center mb-2"><div class="small fw-semibold text-primary">轮播媒体项</div><button type="button" class="btn btn-sm btn-outline-primary" onclick="window._addHeroSlide(' + idx + ')">+ 添加媒体椤</button></div><input type="hidden" name="module_' + idx + '_slide_count" class="hero-slide-count" value="' + (d.slide_count || '1') + '"><div class="hero-slide-list">' + (window._heroSlideHtml ? window._heroSlideHtml(idx, 0, d) : '') + '</div></div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2 mb-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_hero_width', '模块外层宽度', ['px','%','vw','rem'], d.hero_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_hero_height', '横幅高度', ['px','vh','rem','%'], d.hero_height) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_content_width', 'Size', ['px','%','vw','rem'], d.content_width) + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_banner_align', '模块文字排版', [{value:'',label:'默认（全宽）'},{value:'center',label:'居中'},{value:'left',label:'居左'},{value:'right',label:'居右'}], d.banner_align) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});">' +
            '<option value="px">px</option>' +
            '<option value="rem">rem</option>' +
          '</select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">遮罩层/div>' +
        '<div class="row g-2 mb-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">启用遮罩</label><select class="form-select form-select-sm" name="module_' + idx + '_data_overlay_enabled"><option value="true"' + (d.overlay_enabled !== 'false' ? ' selected' : '') + '>启用</option><option value="false"' + (d.overlay_enabled === 'false' ? ' selected' : '') + '>不启用</option></select></div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">配色</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_title_font_size', '标题字体大小', ['px','rem'], d.title_font_size) + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_title_color', '标题颜色', d.title_color || '#ffffff') + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_subtitle_font_size', 'Size', ['px','rem'], d.subtitle_font_size) + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_subtitle_color', 'Color', d.subtitle_color || '#cccccc') + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_btn_font_size', '按钮字体大小', ['px','rem'], d.btn_font_size) + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_text_color', '按钮文字颜色', d.btn_text_color || '#ffffff') + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_bg', 'Color', d.btn_bg || '#067a7a') + '</div>' +
        '</div>';

    /* ====== section_title ====== */
    } else if (type === 'section_title') {
      specialEditor =
        '<div class="small fw-semibold mb-1 text-muted">内容</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标签文字</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_tag" value="' + esc(d.tag || '') + '" placeholder="模块上方小标绛?></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">描述文字</label>' + richEditorHtml('module_' + idx + '_data_desc', d.desc || '') + '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">按钮</div>' +
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">按钮文字</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_btn_text" value="' + esc(d.btn_text || '') + '"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">按钮链接</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_btn_url" value="' + esc(d.btn_url || '') + '"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">打开方式</label><select class="form-select form-select-sm" name="module_' + idx + '_data_btn_target"><option value=""' + (d.btn_target !== '_blank' ? ' selected' : '') + '>当前窗口</option><option value="_blank"' + (d.btn_target === '_blank' ? ' selected' : '') + '>新窗鍙?/option></select></div>' +
        '</div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', 'Color', d.section_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_top" value="' + esc(d.margin_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_right" value="' + esc(d.margin_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_bottom" value="' + esc(d.margin_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_left" value="' + esc(d.margin_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top || '1rem') + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom || '1rem') + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 text-muted mt-2">内容层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内容层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">文字排版</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + sel('module_' + idx + '_data_text_align', '对齐方式', [{value:'center',label:'居中'},{value:'left',label:'居左'},{value:'right',label:'居右'}], d.text_align || 'center') + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">字体样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_title_color', '标题颜色', d.title_color || '#1e293b') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_title_size', '标题字号', ['px','rem'], d.title_size) + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_desc_color', '描述颜色', d.desc_color || '#64748b') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_desc_size', '描述字号', ['px','rem'], d.desc_size) + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_tag_bg', 'Color', d.tag_bg || '#067a7a') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_tag_color', 'Color', d.tag_color || '#ffffff') + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">按钮颜色</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_bg', 'Color', d.btn_bg || '#067a7a') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_color', 'Color', d.btn_color || '#ffffff') + '</div>' +
        '</div>';

    /* ====== data_grid ====== */
    } else if (type === 'data_grid') {
      var dsOptionsHtml = '';
      datasetNames.forEach(function(ds) {
        dsOptionsHtml += '<option value="' + esc(ds.target) + '"' + (d.dataset === ds.target ? ' selected' : '') + '>' + esc(ds.label) + ' (' + esc(ds.target) + ')</option>';
      });
      specialEditor =
        '<div class="small fw-semibold mb-1 text-muted">数据</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">数据来源</label>' +
          '<select class="form-select form-select-sm" data-no-segmented="1" name="module_' + idx + '_data_dataset">' +
          (dsOptionsHtml || '<option value="">暂无数据源/option>') +
          '</select></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">卡片布局</label>' +
          '<select class="form-select form-select-sm" name="module_' + idx + '_data_card_layout"><option value="image_top"' + (d.card_layout !== 'image_left' ? ' selected' : '') + '>上图下文</option><option value="image_left"' + (d.card_layout === 'image_left' ? ' selected' : '') + '>左图右文</option></select></div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">分页</div>' +
        // Row 1: 显示分页 —toggle 开关
        '<div class="form-check form-switch mb-3">' +
          '<input class="form-check-input" type="checkbox" role="switch" id="module_' + idx + '_show_pagination"' +
          (d.show_pagination !== 'false' ? ' checked' : '') +
          ' onchange="this.nextElementSibling.nextElementSibling.value=this.checked?\'true\':\'false\'">' +
          '<label class="form-check-label small" for="module_' + idx + '_show_pagination">显示分页</label>' +
          '<input type="hidden" name="module_' + idx + '_data_show_pagination" value="' + (d.show_pagination !== 'false' ? 'true' : 'false') + '">' +
        '</div>' +
        // Row 2: 分页样式 —下拉选择
        '<div class="mb-2">' +
          '<label class="form-label small mb-1 text-muted">分页样式</label>' +
          '<select class="form-select form-select-sm" name="module_' + idx + '_data_pagination_style">' +
            '<option value="load_more"' + (d.pagination_style !== 'page_numbers' ? ' selected' : '') + '>加载更多</option>' +
            '<option value="page_numbers"' + (d.pagination_style === 'page_numbers' ? ' selected' : '') + '>页码导航</option>' +
          '</select></div>' +
        // Row 3: 每页显示数量 —下拉选择
        '<div class="mb-2">' +
          '<label class="form-label small mb-1 text-muted">每页显示数量</label>' +
          '<select class="form-select form-select-sm" name="module_' + idx + '_data_items_per_page">' +
            ['3','4','6','8','10','12','18','24'].map(function(n) { return '<option value="' + n + '"' + ((d.items_per_page || '6') === n ? ' selected' : '') + '>' + n + ' 条/页</option>'; }).join('') +
          '</select></div>' +
        // Row 4: 分页对齐 —下拉选择
        '<div class="mb-2">' +
          '<label class="form-label small mb-1 text-muted">分页对齐</label>' +
          '<select class="form-select form-select-sm" name="module_' + idx + '_data_pager_align">' +
            '<option value="center"' + (d.pager_align === 'center' || !d.pager_align ? ' selected' : '') + '>居中</option>' +
            '<option value="left"' + (d.pager_align === 'left' ? ' selected' : '') + '>居左</option>' +
            '<option value="right"' + (d.pager_align === 'right' ? ' selected' : '') + '>居右</option>' +
          '</select></div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">内容</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">区块标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', 'Color', d.section_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内容层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_top" value="' + esc(d.margin_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_right" value="' + esc(d.margin_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_bottom" value="' + esc(d.margin_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_left" value="' + esc(d.margin_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>';

    /* ====== feature_grid ====== */
    } else if (type === 'feature_grid') {
      var featCount = d.feature_count || '1';
      specialEditor =
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">区块标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title) + '" placeholder="濡?产品特点"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">区块副标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_subtitle" value="' + esc(d.subtitle) + '" placeholder="如：为什么选择我们"></div>' +
        '<div class="feature-items-editor" data-module-index="' + idx + '"><div class="d-flex justify-content-between align-items-center mb-2"><div class="small fw-semibold text-primary">功能卡片</div><button type="button" class="btn btn-sm btn-outline-primary" onclick="window._addFeatureItem(' + idx + ')">+ 添加功能卡片</button></div><input type="hidden" name="module_' + idx + '_feature_count" class="feature-item-count" value="' + featCount + '"><div class="feature-item-list">' + (window._featureItemHtml ? window._featureItemHtml(idx, 0, d) : '') + '</div></div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted mt-2">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', 'Color', d.section_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_top" value="' + esc(d.margin_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_right" value="' + esc(d.margin_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_bottom" value="' + esc(d.margin_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_left" value="' + esc(d.margin_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top || '1rem') + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom || '1rem') + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 text-muted mt-2">内容层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内容层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 text-muted mt-2">标题区样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_header_bg', '标题区背景色', d.header_bg) + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_header_align', 'Option', [{value:'',label:'Default'},{value:'left',label:'Left'},{value:'center',label:'Center'},{value:'right',label:'Right'}], d.header_align || 'center') + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">标题区边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_margin_top" value="' + esc(d.header_margin_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_margin_right" value="' + esc(d.header_margin_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_margin_bottom" value="' + esc(d.header_margin_bottom || '4rem') + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_margin_left" value="' + esc(d.header_margin_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">标题区内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_padding_top" value="' + esc(d.header_padding_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_padding_right" value="' + esc(d.header_padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_padding_bottom" value="' + esc(d.header_padding_bottom || '2rem') + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_padding_left" value="' + esc(d.header_padding_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">主标棰?/div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_title_size', '标题字号', ['px','rem'], d.title_size || '2.25rem') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_title_color', '标题颜色', d.title_color || '#1e293b') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_title_margin_bottom', '标题下边距', ['px','rem'], d.title_margin_bottom || '0.5rem') + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">副标题</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_subtitle_size', 'Size', ['px','rem'], d.subtitle_size || '1.125rem') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_subtitle_color', 'Color', d.subtitle_color || '#64748b') + '</div>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 text-muted mt-2">网格样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_grid_gap', '卡片间距', ['px','rem'], d.grid_gap || '2rem') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_grid_row_gap', 'Size', ['px','rem'], d.grid_row_gap) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_grid_column_gap', 'Size', ['px','rem'], d.grid_column_gap) + '</div>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 text-muted mt-2">卡片样式</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">显示边框</label><select class="form-select form-select-sm" name="module_' + idx + '_data_card_show_border"><option value=""' + (d.card_show_border !== '0' ? ' selected' : '') + '>默认（显示）</option><option value="0"' + (d.card_show_border === '0' ? ' selected' : '') + '>隐藏边框</option></select></div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">卡片内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_padding_top" value="' + esc(d.card_padding_top || '2rem') + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_padding_right" value="' + esc(d.card_padding_right || '1.5rem') + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_padding_bottom" value="' + esc(d.card_padding_bottom || '2rem') + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_padding_left" value="' + esc(d.card_padding_left || '1.5rem') + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">卡片圆角</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_radius_top_left" value="' + esc(d.card_radius_top_left || '12px') + '" placeholder="↪左上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_radius_top_right" value="' + esc(d.card_radius_top_right || '12px') + '" placeholder="↪右上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_radius_bottom_right" value="' + esc(d.card_radius_bottom_right || '12px') + '" placeholder="↪右下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_radius_bottom_left" value="' + esc(d.card_radius_bottom_left || '12px') + '" placeholder="↪左下">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option><option value=\"%\">%</option></select>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 text-muted mt-2">图标样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_icon_size', '图标大小', ['px','rem'], d.icon_size || '56px') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_icon_color', '图标颜色', d.icon_color || '#067a7a') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_icon_bg', 'Color', d.icon_bg) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_icon_width', 'Size', ['px','rem'], d.icon_width || '56px') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_icon_height', 'Size', ['px','rem'], d.icon_height || '56px') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_icon_radius', '图标圆角', ['px','%'], d.icon_radius || '8px') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_icon_margin_right', '图标右边距', ['px','rem'], d.icon_margin_right) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_icon_margin_bottom', '图标下边距', ['px','rem'], d.icon_margin_bottom || '0.25rem') + '</div>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 text-muted mt-2">卡片文字样式</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">卡片标题</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_card_title_size', '标题字号', ['px','rem'], d.card_title_size || '1rem') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_card_title_color', '标题颜色', d.card_title_color || '#1e293b') + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_card_title_weight', '标题字重', [{value:'',label:'默认'},{value:'400',label:'400'},{value:'500',label:'500'},{value:'600',label:'600'},{value:'700',label:'700'}], d.card_title_weight || '600') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_card_title_margin_bottom', '标题下边距', ['px','rem'], d.card_title_margin_bottom || '0.5rem') + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">卡片描述</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_card_desc_size', '描述字号', ['px','rem'], d.card_desc_size || '0.875rem') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_card_desc_color', '描述颜色', d.card_desc_color || '#64748b') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_card_desc_line_height', '描述行高', ['rem',''], d.card_desc_line_height || '1.6') + '</div>' +
        '</div>';

    /* ====== highlight_card ====== */
    } else if (type === 'highlight_card') {
      specialEditor =
        '<hr class="my-2">' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标签文字</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_tag" value="' + esc(d.tag || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">描述</label>' + richEditorHtml('module_' + idx + '_data_desc', d.desc || '') + '</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">图片</label>' + mediaUploadHtml('module_' + idx + '_data_image', d.image || '', 'image', '图片 URL') + '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">主按閽枃瀛?</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_primaryBtn" value="' + esc(d.primaryBtn || '') + '"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">主按閽摼鎺?</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_primaryLink" value="' + esc(d.primaryLink || '') + '"></div>' +
        '</div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', 'Color', d.section_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_top" value="' + esc(d.margin_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_bottom" value="' + esc(d.margin_bottom) + '" placeholder="↪涓>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">内容层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内容层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_border_radius', '圆角', ['px','rem','%'], d.border_radius) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">图文布局</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + sel('module_' + idx + '_data_image_position', '图文左右位置', [{value:'left',label:'图左文右'},{value:'right',label:'文左图右'}], d.image_position || 'left') + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">配色</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_text_bg', '文本区背景色', d.text_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_text_color', '文本区字体色', d.text_color || '#333333') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_tag_bg', 'Color', d.tag_bg || '#067a7a') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_tag_color', 'Color', d.tag_color || '#ffffff') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_bg', 'Color', d.btn_bg || '#067a7a') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_color', 'Color', d.btn_color || '#ffffff') + '</div>' +
        '</div>';

    /* ====== text_content ====== */
    } else if (type === 'text_content') {
      specialEditor =
        '<div class="small fw-semibold mb-1 text-muted">内容</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">正文</label>' +
        '<div class="rich-toolbar" style="border:1px solid #dee2e6;border-bottom:none;border-radius:4px 4px 0 0;padding:3px 4px;background:#f8f9fa;display:flex;gap:1px;flex-wrap:wrap">' +
          '<button type="button" class="btn btn-sm btn-outline-secondary py-1 px-2" onmousedown="document.execCommand(\'bold\',false,null);event.preventDefault()" title="加粗" style="font-size:12px;line-height:1"><b>B</b></button>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary py-1 px-2" onmousedown="document.execCommand(\'italic\',false,null);event.preventDefault()" title="斜体" style="font-size:12px;line-height:1"><i>I</i></button>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary py-1 px-2" onmousedown="document.execCommand(\'underline\',false,null);event.preventDefault()" title="下划线" style="font-size:12px;line-height:1"><u>U</u></button>' +
          '<span style="border-left:1px solid #dee2e6;margin:0 3px"></span>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary py-1 px-2" onmousedown="document.execCommand(\'formatBlock\',false,\'h2\');event.preventDefault()" title="大标题" style="font-size:12px;line-height:1">H2</button>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary py-1 px-2" onmousedown="document.execCommand(\'formatBlock\',false,\'h3\');event.preventDefault()" title="小标题" style="font-size:12px;line-height:1">H3</button>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary py-1 px-2" onmousedown="document.execCommand(\'formatBlock\',false,\'p\');event.preventDefault()" title="正文段落" style="font-size:12px;line-height:1">P</button>' +
          '<span style="border-left:1px solid #dee2e6;margin:0 3px"></span>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary py-1 px-2" onmousedown="return window._richEditorCommand(this,event,\'justifyLeft\')" title="左对齐" style="font-size:12px;line-height:1">≡</button>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary py-1 px-2" onmousedown="return window._richEditorCommand(this,event,\'justifyCenter\')" title="居中" style="font-size:12px;line-height:1">≡</button>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary py-1 px-2" onmousedown="return window._richEditorCommand(this,event,\'justifyRight\')" title="右对齐" style="font-size:12px;line-height:1">≡</button>' +
          '<span style="border-left:1px solid #dee2e6;margin:0 3px"></span>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary py-1 px-2" onmousedown="return window._richEditorCommand(this,event,\'insertUnorderedList\')" title="无序列表" style="font-size:12px;line-height:1">•≡</button>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary py-1 px-2" onmousedown="return window._richEditorCommand(this,event,\'insertOrderedList\')" title="有序列表" style="font-size:12px;line-height:1">OL</button>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary py-1 px-2" onmousedown="return window._insertRichEditorTable(this,event)" title="插入表格" style="font-size:12px;line-height:1">TB</button>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary py-1 px-2" onmousedown="return window._insertRichEditorLink(this,event)" title="插入链接" style="font-size:12px;line-height:1">🔗</button>' +
        '</div>' +
        '<div contenteditable="true" class="rich-editor-body form-control form-control-sm" style="border-radius:0 0 4px 4px;min-height:150px;max-height:400px;overflow-y:auto" oninput="this.nextElementSibling.value=this.innerHTML">' + (d.body || '') + '</div>' +
        '<textarea class="form-control form-control-sm d-none" name="module_' + idx + '_data_body">' + esc(d.body || '') + '</textarea></div>';
      specialEditor =
        '<div class="small fw-semibold mb-1 text-muted">内容</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">正文</label>' +
        richEditorHtml('module_' + idx + '_data_body', d.body || '') +
        '</div>';
      styleEditor =
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">文字排版</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + sel('module_' + idx + '_data_text_align', '对齐方式', [{value:'left',label:'居左'},{value:'center',label:'居中'},{value:'right',label:'居右'}], d.text_align || 'left') + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_columns', '分栏', [{value:'1',label:'单栏'},{value:'2',label:'双栏'}], d.columns || '1') + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', 'Color', d.section_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内容层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_top" value="' + esc(d.margin_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_right" value="' + esc(d.margin_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_bottom" value="' + esc(d.margin_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_left" value="' + esc(d.margin_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">文字样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_title_color', '标题颜色', d.title_color || '#1e293b') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_body_color', '正文颜色', d.body_color || '#475569') + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_title_size', '标题字号', ['px','rem'], d.title_size) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_body_size', '正文字号', ['px','rem'], d.body_size) + '</div>' +
        '</div>';

    /* ====== item_detail ====== */
    } else if (type === 'item_detail') {
      var imgList = Array.isArray(d.images) ? d.images : [];
      var specList = Array.isArray(d.specs) ? d.specs : [];
      specialEditor =
        '<div class="small fw-semibold mb-1 text-muted">内容</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">描述</label>' + richEditorHtml('module_' + idx + '_data_desc', d.desc || d.description || '') + '</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标签（逗号分隔）</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_tags" value="' + esc(Array.isArray(d.tags) ? d.tags.join(', ') : (d.tags || '')) + '"></div>' +
        '<hr class="my-2">' +
        '<div class="id-images-editor" data-module-index="' + idx + '"><div class="d-flex justify-content-between align-items-center mb-2"><div class="small fw-semibold text-primary">图片列表</div><button type="button" class="btn btn-sm btn-outline-primary" onclick="window._addIdImage(' + idx + ')">+ 添加图片</button></div><input type="hidden" name="module_' + idx + '_data_images_count" class="id-image-count" value="' + imgList.length + '"><div class="id-image-list">' +
        imgList.map(function(img, ii) {
          var url = (typeof img === 'object' ? (img.url || '') : (img || ''));
          return '<div class="border rounded p-2 mb-2 id-image-item" data-image-index="' + ii + '"><div class="d-flex justify-content-between align-items-center mb-2"><span class="small fw-semibold">图片 ' + (ii + 1) + '</span><button type="button" class="btn btn-sm btn-outline-danger" onclick="event.stopPropagation();this.closest(\'.id-image-item\').remove();window._reindexIdImages(' + idx + ')">删除</button></div><div class="mb-2"><label class="form-label small mb-1 text-muted">图片 URL</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_images_' + ii + '_url" value="' + esc(url) + '"><input type="file" class="form-control form-control-sm mt-1" name="module_' + idx + '_data_images_' + ii + '_url_file" accept="image/*"><div class="form-text">上传后自动转 WebP 并覆盖 URL</div></div></div>';
        }).join('') +
        '</div></div><hr class="my-2">' +
        '<div class="id-specs-editor" data-module-index="' + idx + '"><div class="d-flex justify-content-between align-items-center mb-2"><div class="small fw-semibold text-primary">规格参数</div><button type="button" class="btn btn-sm btn-outline-primary" onclick="window._addIdSpec(' + idx + ')">+ 添加规格</button></div><input type="hidden" name="module_' + idx + '_data_specs_count" class="id-spec-count" value="' + specList.length + '"><div class="id-spec-list">' +
        specList.map(function(spec, si) {
          var name = (typeof spec === 'object' ? (spec.name || spec.label || spec.key || '') : '');
          var value = (typeof spec === 'object' ? (spec.value || '') : '');
          return '<div class="border rounded p-2 mb-2 id-spec-item" data-spec-index="' + si + '"><div class="d-flex justify-content-between align-items-center mb-2"><span class="small fw-semibold">规格 ' + (si + 1) + '</span><button type="button" class="btn btn-sm btn-outline-danger" onclick="event.stopPropagation();this.closest(\'.id-spec-item\').remove();window._reindexIdSpecs(' + idx + ')">删除</button></div><div class="row g-2"><div class="col-6"><label class="form-label small mb-1 text-muted">参数鍚</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_specs_' + si + '_name" value="' + esc(name) + '"></div><div class="col-6"><label class="form-label small mb-1 text-muted">参数鍊?</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_specs_' + si + '_value" value="' + esc(value) + '"></div></div></div>';
        }).join('') +
        '</div></div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', 'Color', d.section_bg || '#ffffff') + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">内容层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_inner_bg', 'Color', d.inner_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内容层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">图片样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_img_border_radius', '图片圆角', ['px','rem','%'], d.img_border_radius) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_img_height', '图片高度', ['px','rem','%'], d.img_height) + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">配色</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_text_bg', '文本区背景色', d.text_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_text_color', '文本区字体色', d.text_color || '#333333') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_tag_bg', 'Color', d.tag_bg || '#067a7a') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_tag_color', 'Color', d.tag_color || '#ffffff') + '</div>' +
        '</div>';

    /* ====== stat_counter ====== */
    } else if (type === 'stat_counter') {
      var statItems = Array.isArray(d.stats) && d.stats.length ? d.stats : [{}];
      specialEditor =
        '<div class="stat-items-editor" data-module-index="' + idx + '"><div class="d-flex justify-content-between align-items-center mb-2"><div class="small fw-semibold text-primary">统计项/div><button type="button" class="btn btn-sm btn-outline-primary" onclick="window._addStatItem(' + idx + ')">+ 添加统计项</button></div><input type="hidden" name="module_' + idx + '_stats_count" class="stat-item-count" value="' + statItems.length + '"><div class="stat-item-list">' + statItems.map(function(_, si) { return window._statItemHtml(idx, si, d); }).join('') + '</div></div>' +
        '<hr class="my-2">' +
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">区块标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">区块副标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_subtitle" value="' + esc(d.subtitle || '') + '"></div>' +
        '</div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', 'Color', d.section_bg || '#f5f7fa') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内容层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="row g-2">' +
          '<div class="col-6">' + sel('module_' + idx + '_data_columns', '每行列数', [{value:'4',label:'四列'},{value:'3',label:'三列'},{value:'6',label:'六列'}], d.columns || '4') + '</div>' +
        '</div>';

    /* ====== logo_cloud ====== */
    } else if (type === 'logo_cloud') {
      specialEditor =
        '<div class="logo-items-editor" data-module-index="' + idx + '"><div class="d-flex justify-content-between align-items-center mb-2"><div class="small fw-semibold text-primary">标志列表</div><button type="button" class="btn btn-sm btn-outline-primary" onclick="window._addLogoItem(' + idx + ')">+ 添加标志</button></div><input type="hidden" name="module_' + idx + '_logo_count" class="logo-item-count" value="' + (d.logo_count || '1') + '"><div class="logo-item-list">' + (window._logoItemHtml ? window._logoItemHtml(idx, 0, d) : '') + '</div></div>' +
        '<hr class="my-2">' +
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">区块标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">区块副标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_subtitle" value="' + esc(d.subtitle || '') + '"></div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + sel('module_' + idx + '_data_columns', '每行列数', [{value:'4',label:'四列'},{value:'5',label:'五列'},{value:'6',label:'六列'}], d.columns || '4') + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_grayscale', '灰度滤镜', [{value:'true',label:'开启（hover时恢复彩色）'},{value:'false',label:'关闭（保持原色）'}], d.grayscale || 'true') + '</div>' +
        '</div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', 'Color', d.section_bg || '#f5f7fa') + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">内容层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_inner_bg', 'Color', d.inner_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内容层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option><option value="%">%</option></select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">标志卡片样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_logo_bg', 'Color', d.logo_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_logo_border', '边框大小', ['px','rem'], d.logo_border) + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_logo_border_color', '边框颜色', d.logo_border_color || '#e5e7eb') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_logo_radius', '圆角', ['px','rem','%'], d.logo_radius) + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_logo_width', '卡片宽度', ['px','rem','%'], d.logo_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_logo_height', '卡片高度', ['px','rem','%'], d.logo_height) + '</div>' +
        '</div>';

    /* ====== process_steps ====== */
    } else if (type === 'process_steps') {
      specialEditor =
        '<div class="step-items-editor" data-module-index="' + idx + '"><div class="d-flex justify-content-between align-items-center mb-2"><div class="small fw-semibold text-primary">步骤列表</div><button type="button" class="btn btn-sm btn-outline-primary" onclick="window._addStepItem(' + idx + ')">+ 添加步骤</button></div><input type="hidden" name="module_' + idx + '_step_count" class="step-item-count" value="' + (d.step_count || '1') + '"><div class="step-item-list">' + (window._stepItemHtml ? window._stepItemHtml(idx, 0, d) : '') + '</div></div>' +
        '<hr class="my-2">' +
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">区块标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">区块副标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_subtitle" value="' + esc(d.subtitle || '') + '"></div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + sel('module_' + idx + '_data_direction', '排列方向', [{value:'horizontal',label:'横向'},{value:'vertical',label:'纵向'}], d.direction || 'horizontal') + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_step_style', '步骤样式', [{value:'number',label:'数字序号'},{value:'icon',label:'图标'}], d.step_style || 'number') + '</div>' +
        '</div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', 'Color', d.section_bg || '#f5f7fa') + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">内容层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_inner_bg', 'Color', d.inner_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内容层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">配色</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_title_font_size', '标题字体大小', ['px','rem'], d.title_font_size) + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_title_color', '标题颜色', d.title_color || '#1a1a1a') + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_desc_font_size', '描述字体大小', ['px','rem'], d.desc_font_size) + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_desc_color', '描述颜色', d.desc_color || '#666666') + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_icon_color', '图标颜色', d.icon_color || '#067a7a') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_number_bg', 'Color', d.number_bg || '#067a7a') + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_number_font_size', '序号字体大小', ['px','rem'], d.number_font_size) + '</div>' +
        '</div>';
    /* ====== contact_info ====== */
    } else if (type === 'contact_info') {
      specialEditor =
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">区块标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">区块副标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_subtitle" value="' + esc(d.subtitle || '') + '"></div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-2 text-muted">显示控制（数据来自网站设置中的联系方式）</div>' +
        '<div class="d-flex flex-wrap gap-2">' +
          visToggle('module_' + idx + '_data_show_phone', '电话', (d.show_phone || 'true')) +
          visToggle('module_' + idx + '_data_show_mobile', '手机', (d.show_mobile || 'true')) +
          visToggle('module_' + idx + '_data_show_email', '邮箱', (d.show_email || 'true')) +
          visToggle('module_' + idx + '_data_show_address', '地址', (d.show_address || 'true')) +
          visToggle('module_' + idx + '_data_show_business_hours', '营业时间', (d.show_business_hours || 'false')) +
        '</div>' +
        '';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', 'Color', d.section_bg) + '</div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">外层宽度 <span class="text-muted" style="font-weight:normal;">（留空不限制宽度锛?</span></label><div class="input-group input-group-sm"><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_outer_width" value="' + esc(d.outer_width || '') + '" placeholder="濡?1200px" style="width:60%"><select class="form-select form-select-sm" style="width:40%" onchange="var inp=this.parentElement.querySelector(\'[name=&quot;module_' + idx + '_data_outer_width&quot;]\');if(inp){var v=inp.value.replace(/px|rem|%$/i,\'\').trim();var u=this.value;if(v&&u)inp.value=v+u;}"><option value="">--</option><option value="px">px</option><option value="%">%</option><option value="rem">rem</option></select></div></div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">内容层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内容层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>';

    /* ====== contact_form ====== */
    } else if (type === 'contact_form') {
      specialEditor =
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">区块标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">区块副标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_subtitle" value="' + esc(d.subtitle || '') + '"></div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-12"><label class="form-label small mb-1 text-muted">表单提交地址</label><input type="url" class="form-control form-control-sm" name="module_' + idx + '_data_form_action" value="' + esc(d.form_action || '') + '" placeholder="留空则使用平台内置留言，或填入外部服务地址"></div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-2 text-muted">表单瀛楁</div>' +
        '<div class="d-flex flex-wrap gap-2">' +
          visToggle('module_' + idx + '_data_show_name', '姓名', (d.show_name || 'true')) +
          visToggle('module_' + idx + '_data_show_email', '邮箱', (d.show_email || 'true')) +
          visToggle('module_' + idx + '_data_show_phone', '电话', (d.show_phone || 'true')) +
          visToggle('module_' + idx + '_data_show_company', '鍏徃', (d.show_company || 'false')) +
          visToggle('module_' + idx + '_data_show_message', '留言', (d.show_message || 'true')) +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">提交按钮文字</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_submit_text" value="' + esc(d.submit_text || '') + '" placeholder="发送留言"></div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-2 text-muted">地图（高德/Google 嵌入）</div>' +
        '<div class="d-flex flex-wrap gap-2">' +
          visToggle('module_' + idx + '_data_show_map', '显示地图', (d.show_map || 'false')) +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-12"><label class="form-label small mb-1 text-muted">地图嵌入地址</label><input type="url" class="form-control form-control-sm" name="module_' + idx + '_data_map_src" value="' + esc(d.map_src || '') + '" placeholder="从高寰Google 地图获取的嵌入链接（iframe src锛?></div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + sel('module_' + idx + '_data_layout', 'Layout', [{value:'form_left',label:'Form left / map right'},{value:'form_right',label:'Map left / form right'}], d.layout || 'form_left') + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_map_width_ratio', '地图占比', [{value:'30',label:'30%'},{value:'35',label:'35%'},{value:'40',label:'40%'},{value:'45',label:'45%'},{value:'50',label:'50%'},{value:'60',label:'60%'},{value:'70',label:'70%'},{value:'100',label:'100%'}], d.map_width_ratio || '40') + '</div>' +
        '</div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', 'Color', d.section_bg) + '</div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">外层宽度</label><div class="input-group input-group-sm"><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_outer_width" value="' + esc(d.outer_width || '') + '" placeholder="濡?1200px" style="width:60%"><select class="form-select form-select-sm" style="width:40%" onchange="var inp=this.parentElement.querySelector(\'[name=&quot;module_' + idx + '_data_outer_width&quot;]\');if(inp){var v=inp.value.replace(/px|rem|%$/i,\'\').trim();var u=this.value;if(v&&u)inp.value=v+u;}"><option value="">--</option><option value="px">px</option><option value="%">%</option><option value="rem">rem</option></select></div></div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">内容层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内容层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">表单样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_form_bg', 'Color', d.form_bg) + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_input_bg', '输入框背景色', d.input_bg) + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_input_border', '输入框边框色', d.input_border) + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_text_color', '文字颜色', d.text_color) + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_input_radius', 'Size', ['px','rem','%'], d.input_radius) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_form_radius', '表单圆角', ['px','rem','%'], d.form_radius) + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_title_size', '标题字号', ['px','rem','em'], d.title_size) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_input_height', 'Size', ['px','rem'], d.input_height) + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_field_gap', '字段间距', ['px','rem'], d.field_gap) + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_label_style', '标签排版', [{value:'top',label:'标签在上'},{value:'left',label:'标签在左'},{value:'hidden',label:'隐藏标签'}], d.label_style || 'top') + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">表单内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_padding_top" value="' + esc(d.form_padding_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_padding_right" value="' + esc(d.form_padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_padding_bottom" value="' + esc(d.form_padding_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_padding_left" value="' + esc(d.form_padding_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">表单外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_margin_top" value="' + esc(d.form_margin_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_margin_right" value="' + esc(d.form_margin_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_margin_bottom" value="' + esc(d.form_margin_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_margin_left" value="' + esc(d.form_margin_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">按钮样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_bg', 'Color', d.btn_bg) + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_color', 'Color', d.btn_color) + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_btn_size', '按钮文字大小', ['px','rem','em'], d.btn_size) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_btn_radius', '按钮圆角', ['px','rem','%'], d.btn_radius) + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + sel('module_' + idx + '_data_btn_align', '按钮位置', [{value:'left',label:'靠左'},{value:'center',label:'居中'},{value:'right',label:'靠右'}], d.btn_align || 'left') + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">按钮内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_padding_top" value="' + esc(d.btn_padding_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_padding_right" value="' + esc(d.btn_padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_padding_bottom" value="' + esc(d.btn_padding_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_padding_left" value="' + esc(d.btn_padding_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">按钮外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_margin_top" value="' + esc(d.btn_margin_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_margin_right" value="' + esc(d.btn_margin_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_margin_bottom" value="' + esc(d.btn_margin_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_margin_left" value="' + esc(d.btn_margin_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">地图样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_map_height', '地图高度', ['px','rem','vh'], d.map_height) + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_map_radius', '地图圆角', ['px','rem','%'], d.map_radius) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">地图外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_margin_top" value="' + esc(d.map_margin_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_margin_right" value="' + esc(d.map_margin_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_margin_bottom" value="' + esc(d.map_margin_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_margin_left" value="' + esc(d.map_margin_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">地图内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_padding_top" value="' + esc(d.map_padding_top) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_padding_right" value="' + esc(d.map_padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_padding_bottom" value="' + esc(d.map_padding_bottom) + '" placeholder="↪涓>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_padding_left" value="' + esc(d.map_padding_left) + '" placeholder="↪宸>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 mt-2 text-muted">表单显隐</div>' +
        '<div class="d-flex flex-wrap gap-2">' +
          visToggle('module_' + idx + '_data_show_form', '显示表单', (d.show_form || 'true')) +
        '</div>';
    }

    /* ====== 构建 HTML (结构涓Jinja 模板对齐) ====== */
    var html =
      '<div class="d-flex align-items-center justify-content-between p-2 module-header" style="' + headerBg + 'cursor:pointer">' +
        '<span class="small fw-semibold d-flex align-items-center gap-1 ' + titleColor + '">' + getBlockIconHTML(type) + ' ' + esc(displayName) + '</span>' +
        '<div class="d-flex gap-1 flex-shrink-0 flex-nowrap">' +
          '<button type="button" class="module-action-btn" title="上移" onclick="event.stopPropagation();window._moveModule(this, -1)">' + detailGalleryIcon('up') + '</button>' +
          '<button type="button" class="module-action-btn" title="下移" onclick="event.stopPropagation();window._moveModule(this, 1)">' + detailGalleryIcon('down') + '</button>' +
          '<button type="button" class="module-action-btn module-action-del" title="删除" onclick="event.stopPropagation();this.closest(\'.module-item\').remove();window._reindexModules()">✕</button>' +
        '</div>' +
      '</div>' +
      '<input type="hidden" name="module_' + idx + '_type" value="' + esc(type) + '">' +
      '<input type="hidden" name="module_' + idx + '_order" value="' + (idx + 1) + '">' +
      '<div class="module-config p-2 border-top" style="display:block">';

    if (!isDataModule) {
      // 电脑绔細tab 按钮 + 两个面板（结构与 Jinja 模板涓自动达級
      html += '<div class="device-config device-desktop">' +
        '<div class="d-flex mb-2">' +
          '<button type="button" class="btn btn-sm btn-outline-secondary active content-style-tab flex-fill" data-tab="content" onclick="window._switchContentStyleTab(this, \'content\')">内容</button>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary content-style-tab flex-fill" data-tab="style" onclick="window._switchContentStyleTab(this, \'style\')">样式</button>' +
        '</div>' +
        '<div class="content-style-panel panel-content">' +
          (specialEditor || desktopFields) +
        '</div>' +
        '<div class="content-style-panel panel-style" style="display:none">' +
          (styleEditor || '') +
        '</div>' +
      '</div>';
    }

    if (isDataModule) {
      html += '<div class="device-config device-desktop">' +
        '<div class="d-flex mb-2">' +
          '<button type="button" class="btn btn-sm btn-outline-secondary active content-style-tab flex-fill" data-tab="content" onclick="window._switchContentStyleTab(this, \'content\')">内容</button>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary content-style-tab flex-fill" data-tab="style" onclick="window._switchContentStyleTab(this, \'style\')">样式</button>' +
        '</div>' +
        '<div class="content-style-panel panel-content">' + specialEditor + '</div>' +
        '<div class="content-style-panel panel-style" style="display:none">' + styleEditor + '</div>' +
      '</div>';
    }

    // 平板端?/ 手机绔紙结构涓Jinja 模板涓自动达紝涓.device-desktop 同级锛?
    if (!isDataModule) {
      html +=
        '<div class="device-config device-tablet" style="display:none">' +
          tabletFields +
          '<div class="mb-2 mt-2"><label class="form-check-label small"><input type="checkbox" class="form-check-input" name="module_' + idx + '_resp_tablet_hidden" value="1"> 平板端隐藏此模块</label></div>' +
        '</div>' +
        '<div class="device-config device-mobile" style="display:none">' +
          mobileFields +
          '<div class="mb-2 mt-2"><label class="form-check-label small"><input type="checkbox" class="form-check-input" name="module_' + idx + '_resp_mobile_hidden" value="1"> 手机端隐藏此模块</label></div>' +
        '</div>';
    }

    if (isDataModule) {
      html +=
        '<div class="device-config device-tablet" style="display:none">' +
          tabletFields +
        '</div>' +
        '<div class="device-config device-mobile" style="display:none">' +
          mobileFields +
        '</div>';
    }

    html += '</div>';

    setTimeout(function() {
      enhanceCompactSelects(document);
      updateConditionalFields(document);
    }, 0);
    return { html: html, borderStyle: borderStyle, headerBg: headerBg };
  }

  /* ====== 手风琴展开/收缩 ======
   *
   * server 绔覆染的模块头使鐢?onclick="toggleModuleAccordion(...)" 调用此函数，
   * 鍥犳必须同时暴露涓window.toggleModuleAccordion（不带下划线）。?
   *
   * 鍏煎 page editor 鍜?dataset editor 两种面板上下文：
   *   - 显式控制 .module-config 鐨?display锛坧age editor 鐢紝不走 CSS !important锛?
   *   - 显式控制 .content-style-panel 鐨?display（两种面板都鐢級
   *   - 有条件调鐢?selectModuleInPreview锛堜粎 page editor 鏈夐瑙?iframe锛?
   */
  function toggleModuleAccordion(moduleItem) {
    var wasExpanded = moduleItem.classList.contains('expanded');
    // 收缩同容器内所有模块：移除 expanded + 显式隐藏面板
    var container = moduleItem.parentElement;
    if (container) {
      container.querySelectorAll('.module-item').forEach(function(item) {
        item.classList.remove('expanded');
        // 隐藏 .module-config锛坧age editor 面板鐢級
        var cfg = item.querySelector('.module-config');
        if (cfg) cfg.style.display = 'none';
        // 隐藏所有?content-style 面板
        item.querySelectorAll('.content-style-panel').forEach(function(p) {
          p.style.display = 'none';
        });
      });
    }
    // 如果之前未展开，则展开当前模块
    if (!wasExpanded) {
      moduleItem.classList.add('expanded');
      // 展开 .module-config
      var cfg = moduleItem.querySelector('.module-config');
      if (cfg) cfg.style.display = 'block';
      // 恢复 active tab 对应的内容面鏉?
      var activeTab = moduleItem.querySelector('.content-style-tab.active');
      var tabName = activeTab ? activeTab.dataset.tab : 'content';
      var target = moduleItem.querySelector('.panel-' + tabName);
      if (target) target.style.display = '';
      // 联动涓棿预览 iframe锛堜粎 page editor 鐜鏈夎函数锛?
      if (typeof selectModuleInPreview === 'function') {
        selectModuleInPreview(moduleItem.dataset.moduleIndex);
      }
    }
  }

  /* ====== 对外暴露 ====== */
  window._buildModuleHTML = buildModuleHTML;
  window._featuredPicksEditors = function(prefix, values) {
    return featuredPicksEditors(prefix, findBlockMeta('featured_picks'), values || {});
  };
  window._toggleModuleAccordion = toggleModuleAccordion;
  window.toggleModuleAccordion = toggleModuleAccordion;  // server 绔?onclick 引用此名
  window._updateModuleConditionalFields = updateConditionalFields;

  document.addEventListener('change', function(e) {
    if (!e.target || !e.target.name || e.target.name.slice(-10) !== 'media_type') return;
    enhanceCompactSelects(e.target.closest('.device-config') || document);
    updateConditionalFields(e.target.closest('.device-config') || document);
  });

  document.addEventListener('DOMContentLoaded', function() {
    enhanceCompactSelects(document);
    updateConditionalFields(document);
  });

  /* ====== 富文鏈紪辑器 (RTE) ======
   * 核心策略锛?
   *   1. 委托 mousedown 鍦?.rte-toolbar 涓preventDefault，阻止按閽偣鍑诲自动寸紪辑器失焦
   *   2. 委托 click 执行 execCommand，通过 _lastRteEditor 找到对应的编辑器
   *   3. 颜色选择器和标题下拉鐢?change/input 事件
   */
  if (!window.__adminModulesRteBound) {
  window.__adminModulesRteBound = true;
  var _lastRteEditor = null;
  var _rteSavedRange = null;

  function saveRteSelection(rte) {
    var sel = window.getSelection();
    if (!rte || !sel || !sel.rangeCount) return null;
    var range = sel.getRangeAt(0);
    if (rte.contains(range.commonAncestorContainer)) {
      _rteSavedRange = range.cloneRange();
      return _rteSavedRange.cloneRange();
    }
    return null;
  }

  function restoreRteSelection(rte, range) {
    // 先捕获 range，再 focus —— rte.focus() 会同步触发 focusin 事件处理器，
    // 后者调用?saveRteSelection() 鎶?_rteSavedRange 覆盖为编辑器开头位置0锛夛紝
    // 如果鍏?focus 再取值会导致视频/图片/链接始终插在顶部而非光标位置銆?
    var targetRange = range || _rteSavedRange;
    rte.focus();
    if (!targetRange) return;
    var sel = window.getSelection();
    try {
      sel.removeAllRanges();
      sel.addRange(targetRange);
    } catch (err) {
      _rteSavedRange = null;
    }
  }

  function savedRangeInRte(rte) {
    if (!_rteSavedRange || !rte) return null;
    var node = _rteSavedRange.commonAncestorContainer;
    var el = node.nodeType === 1 ? node : (node.parentElement || node.parentNode);
    return el && rte.contains(el) ? _rteSavedRange.cloneRange() : null;
  }

  function setRteLinkAttrs(link, url) {
    link.setAttribute('href', url);
    link.setAttribute('target', '_blank');
    link.setAttribute('rel', 'noopener');
  }

  function insertRteLink(rte, url, savedRange) {
    if (!url) return;
    var range = savedRange || savedRangeInRte(rte);
    restoreRteSelection(rte, range);

    var link = document.createElement('a');
    setRteLinkAttrs(link, url);

    if (!range || range.collapsed) {
      link.textContent = url;
      var sel = window.getSelection();
      if (sel && sel.rangeCount) {
        range = sel.getRangeAt(0);
      } else {
        range = document.createRange();
        range.selectNodeContents(rte);
        range.collapse(false);
      }
      range.insertNode(link);
    } else {
      try {
        range.surroundContents(link);
      } catch (err) {
        var fragment = range.extractContents();
        link.appendChild(fragment);
        range.insertNode(link);
      }
    }

    var after = document.createRange();
    after.setStartAfter(link);
    after.collapse(true);
    var selection = window.getSelection();
    if (selection) {
      selection.removeAllRanges();
      selection.addRange(after);
      _rteSavedRange = after.cloneRange();
    }
  }

  function insertRteTable(rte) {
    var size = window.prompt('表格行列，例濡?3x3', '3x3');
    if (size === null) return;
    var match = String(size || '').toLowerCase().match(/^\s*(\d+)\s*[x*,\x2c ]\s*(\d+)\s*$/);
    var rows = match ? parseInt(match[1], 10) : 3;
    var cols = match ? parseInt(match[2], 10) : 3;
    rows = Math.max(1, Math.min(rows || 3, 20));
    cols = Math.max(1, Math.min(cols || 3, 10));
    restoreRteSelection(rte);

    var html = '<table><tbody>';
    for (var r = 0; r < rows; r++) {
      html += '<tr>';
      for (var c = 0; c < cols; c++) {
        html += '<td><br></td>';
      }
      html += '</tr>';
    }
    html += '</tbody></table><p><br></p>';
    document.execCommand('insertHTML', false, html);
    syncRteBody(rte);
  }

  function parseRteColumnWidths(input, cols) {
    var raw = String(input || '').trim();
    if (!raw) return [];
    var parts = raw.split(/[,\s]+/).filter(Boolean);
    var widths = [];
    for (var i = 0; i < Math.min(parts.length, cols); i++) {
      var part = parts[i].trim();
      if (!part) continue;
      if (/^\d+(\.\d+)?$/.test(part)) part += '%';
      if (/^\d+(\.\d+)?%$/.test(part) || /^\d+(\.\d+)?px$/.test(part) || /^\d+(\.\d+)?rem$/.test(part)) {
        widths[i] = part;
      }
    }
    return widths;
  }

  function buildRteColgroup(widths) {
    if (!widths || !widths.length) return '';
    var html = '<colgroup>';
    widths.forEach(function(width) {
      html += '<col' + (width ? ' style="width:' + width + '"' : '') + '>';
    });
    return html + '</colgroup>';
  }

  function getRteTableAtSelection(rte) {
    var sel = window.getSelection();
    var node = null;
    if (sel && sel.rangeCount) node = sel.getRangeAt(0).commonAncestorContainer;
    var el = node ? (node.nodeType === 1 ? node : node.parentElement) : null;
    var table = el && el.closest ? el.closest('table') : null;
    return table && rte.contains(table) ? table : null;
  }

  function getRteTableColumnCount(table) {
    var row = table ? table.querySelector('tr') : null;
    return row ? row.children.length : 0;
  }

  function getRteTableWidths(table) {
    var row = table ? table.querySelector('tr') : null;
    if (!row) return '';
    return Array.prototype.map.call(row.children, function(cell) {
      return (cell.style.width || '').trim();
    }).join(',');
  }

  function applyRteTableSettings(table, widths, showBorder) {
    if (!table) return;
    table.style.width = '100%';
    table.style.tableLayout = 'fixed';
    table.style.borderCollapse = 'collapse';
    table.setAttribute('data-rte-border', showBorder ? '1' : '0');
    table.setAttribute('data-rte-widths', widths && widths.length ? '1' : '0');

    var oldColgroup = table.querySelector('colgroup');
    if (oldColgroup) oldColgroup.remove();
    if (widths && widths.length) {
      table.insertAdjacentHTML('afterbegin', buildRteColgroup(widths));
    }

    table.querySelectorAll('tr').forEach(function(row) {
      Array.prototype.forEach.call(row.children, function(cell, index) {
        if (widths && widths[index]) {
          cell.style.width = widths[index];
        } else {
          cell.style.removeProperty('width');
        }
        if (showBorder) {
          cell.style.removeProperty('border');
        } else {
          cell.style.border = 'none';
        }
      });
    });
  }

  function insertRteTableConfigured(rte) {
    var size = window.prompt('Table size, for example 2x2', '2x2');
    if (size === null) return;
    var match = String(size || '').toLowerCase().match(/^\s*(\d+)\s*[x*,\x2c ]\s*(\d+)\s*$/);
    var rows = match ? parseInt(match[1], 10) : 2;
    var cols = match ? parseInt(match[2], 10) : 2;
    rows = Math.max(1, Math.min(rows || 2, 20));
    cols = Math.max(1, Math.min(cols || 2, 10));

    var defaults = [];
    for (var i = 0; i < cols; i++) defaults.push(Math.round(100 / cols));
    var widthsInput = window.prompt('Column widths, for example 50,50. Leave blank for equal widths.', defaults.join(','));
    if (widthsInput === null) return;
    var borderInput = window.prompt('Show table borders? y/n', 'y');
    if (borderInput === null) return;
    var widths = parseRteColumnWidths(widthsInput, cols);
    var showBorder = !/^n(o)?|0|false$/i.test(String(borderInput || '').trim());

    restoreRteSelection(rte);
    var html = '<table style="width:100%;table-layout:fixed;border-collapse:collapse" data-rte-border="' + (showBorder ? '1' : '0') + '" data-rte-widths="' + (widths && widths.length ? '1' : '0') + '">';
    html += buildRteColgroup(widths) + '<tbody>';
    for (var r = 0; r < rows; r++) {
      html += '<tr>';
      for (var c = 0; c < cols; c++) {
        var cellStyle = '';
        if (widths[c]) cellStyle += 'width:' + widths[c] + ';';
        if (!showBorder) cellStyle += 'border:none;';
        html += '<td' + (cellStyle ? ' style="' + cellStyle + '"' : '') + '><br></td>';
      }
      html += '</tr>';
    }
    html += '</tbody></table><p><br></p>';
    document.execCommand('insertHTML', false, html);
    syncRteBody(rte);
  }

  function editRteTable(rte) {
    restoreRteSelection(rte);
    var table = getRteTableAtSelection(rte);
    if (!table) {
      window.alert('Place the cursor inside a table first.');
      return;
    }
    var cols = getRteTableColumnCount(table);
    var widthsInput = window.prompt('Column widths, for example 50,50. Leave blank to clear custom widths.', getRteTableWidths(table));
    if (widthsInput === null) return;
    var currentBorder = table.getAttribute('data-rte-border') !== '0';
    var borderInput = window.prompt('Show table borders? y/n', currentBorder ? 'y' : 'n');
    if (borderInput === null) return;
    var widths = parseRteColumnWidths(widthsInput, cols);
    var showBorder = !/^n(o)?|0|false$/i.test(String(borderInput || '').trim());
    applyRteTableSettings(table, widths, showBorder);
    syncRteBody(rte);
  }

  function makeRteToolbarButton(className, label, title, html) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-sm btn-light rte-btn ' + className;
    btn.title = title;
    btn.setAttribute('aria-label', title);
    if (html) btn.innerHTML = html;
    else btn.textContent = label;
    return btn;
  }

  function ensureRteToolbarButton(wrapper, className, label, title, html) {
    var btn = wrapper.querySelector('.' + className);
    if (!btn) btn = makeRteToolbarButton(className, label, title, html);
    btn.title = title;
    btn.setAttribute('aria-label', title);
    return btn;
  }

  function placeRteToolbarGroup(toolbar, anchor, nodes) {
    if (!toolbar || !anchor) return;
    var ref = anchor.nextSibling;
    nodes.forEach(function(node) {
      if (!node) return;
      toolbar.insertBefore(node, ref);
      ref = node.nextSibling;
    });
  }

  function normalizeRteToolbar(toolbar) {
    if (!toolbar) return;
    var cmdTitles = {
      bold: 'Bold', italic: 'Italic', underline: 'Underline', strikeThrough: 'Strike', justifyLeft: 'Align left', justifyCenter: 'Align center', justifyRight: 'Align right',
      insertUnorderedList: 'Bullet list', insertOrderedList: 'Numbered list', formatBlock: 'Quote', insertHorizontalRule: 'Horizontal rule', removeFormat: 'Clear format', undo: 'Undo', redo: 'Redo'
    };
    toolbar.querySelectorAll('.rte-btn[data-cmd]').forEach(function(btn) {
      var title = cmdTitles[btn.dataset.cmd];
      if (!title) return;
      btn.title = title;
      btn.setAttribute('aria-label', title);
    });
    var heading = toolbar.querySelector('.rte-heading-select');
    if (heading) heading.title = '标题样式';
    var color = toolbar.querySelector('.rte-color-picker');
    if (color) color.title = '文字颜色';
    [
      ['.rte-table-btn', '插入表格'],
      ['.rte-table-settings-btn', '表格设置'],
      ['.rte-link-btn', '插入链接'],
      ['.rte-image-btn', '插入图片链接'],
      ['.rte-upload-image-btn', 'Upload image'],
      ['.rte-video-url-btn', '插入视频链接'],
      ['.rte-upload-video-btn', 'Upload video']
    ].forEach(function(item) {
      var btn = toolbar.querySelector(item[0]);
      if (!btn) return;
      btn.title = item[1];
      btn.setAttribute('aria-label', item[1]);
    });
  }

  function finalizeRteToolbar(wrapper, toolbar) {
    if (!wrapper || !toolbar) return;
    var tableInsertBtn = toolbar.querySelector('.rte-table-btn');
    var tableSettingsBtn = ensureRteToolbarButton(wrapper, 'rte-table-settings-btn', 'T', 'Table settings');
    if (tableInsertBtn) placeRteToolbarGroup(toolbar, tableInsertBtn, [tableSettingsBtn]);

    var mediaSep = wrapper.querySelector('.rte-media-sep');
    if (!mediaSep) {
      mediaSep = document.createElement('span');
      mediaSep.className = 'rte-sep rte-media-sep';
    }
    var linkBtn = ensureRteToolbarButton(wrapper, 'rte-link-btn', 'L', 'Insert link');
    var imageUrlBtn = ensureRteToolbarButton(wrapper, 'rte-image-btn', 'P', 'Insert image URL');
    var imageUploadBtn = ensureRteToolbarButton(wrapper, 'rte-upload-image-btn', 'I', 'Upload image');
    var videoUrlBtn = ensureRteToolbarButton(wrapper, 'rte-video-url-btn', 'V', 'Insert video URL');
    var videoUploadBtn = ensureRteToolbarButton(wrapper, 'rte-upload-video-btn', 'V', 'Upload video');
    var mediaAnchor = tableSettingsBtn || tableInsertBtn;
    if (mediaAnchor) {
      placeRteToolbarGroup(toolbar, mediaAnchor, [mediaSep, linkBtn, imageUrlBtn, imageUploadBtn, videoUrlBtn, videoUploadBtn]);
    }
    normalizeRteToolbar(toolbar);
  }

  function ensureRteUploadControls(rte) {
    var wrapper = rte && rte.closest('.rte-wrapper');
    if (!wrapper) return;
    var toolbar = wrapper.querySelector('.rte-toolbar');
    if (!toolbar) return;
    if (!wrapper.querySelector('.rte-table-settings-btn')) {
      var tableBtn = document.createElement('button');
      tableBtn.type = 'button';
      tableBtn.className = 'btn btn-sm btn-light rte-btn rte-table-settings-btn';
      tableBtn.title = 'Table settings';
      tableBtn.textContent = 'T';
      toolbar.appendChild(tableBtn);
    }
    var mediaSep = wrapper.querySelector('.rte-media-sep');
    if (!mediaSep) {
      mediaSep = document.createElement('span');
      mediaSep.className = 'rte-sep rte-media-sep';
      toolbar.appendChild(mediaSep);
    }
    if (!wrapper.querySelector('.rte-upload-image-btn')) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn btn-sm btn-light rte-btn rte-upload-image-btn';
      btn.title = 'Upload and insert image';
      btn.setAttribute('aria-label', 'Upload image');
      btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><path d="M17 8l-5-5-5 5"></path><path d="M12 3v12"></path></svg>';
      toolbar.appendChild(btn);
    }
    if (!wrapper.querySelector('.rte-video-url-btn')) {
      var videoUrlBtn = document.createElement('button');
      videoUrlBtn.type = 'button';
      videoUrlBtn.className = 'btn btn-sm btn-light rte-btn rte-video-url-btn';
      videoUrlBtn.title = 'Insert video URL';
      videoUrlBtn.setAttribute('aria-label', 'Insert video URL');
      videoUrlBtn.textContent = 'VID';
      toolbar.appendChild(videoUrlBtn);
    }
    if (!wrapper.querySelector('.rte-upload-video-btn')) {
      var videoBtn = document.createElement('button');
      videoBtn.type = 'button';
      videoBtn.className = 'btn btn-sm btn-light rte-btn rte-upload-video-btn';
      videoBtn.title = 'Upload and insert video';
      videoBtn.setAttribute('aria-label', 'Upload video');
      videoBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>';
      toolbar.appendChild(videoBtn);
    }

    finalizeRteToolbar(wrapper, toolbar);

    if (!wrapper.querySelector('.rte-image-upload-input')) {
      var input = document.createElement('input');
      input.type = 'file';
      input.className = 'rte-image-upload-input';
      input.accept = 'image/*';
      input.style.display = 'none';
      wrapper.insertBefore(input, rte);
    }
    if (!wrapper.querySelector('.rte-video-upload-input')) {
      var videoInput = document.createElement('input');
      videoInput.type = 'file';
      videoInput.className = 'rte-video-upload-input';
      videoInput.accept = 'video/mp4,video/webm,video/ogg,video/quicktime';
      videoInput.style.display = 'none';
      wrapper.insertBefore(videoInput, rte);
    }

    var status = document.createElement('div');
    status.className = 'rte-upload-status small text-muted mb-1';
    status.style.display = 'none';
    wrapper.insertBefore(status, rte);
  }

  function insertRteImage(rte, url) {
    restoreRteSelection(rte);
    var safeUrl = String(url || '').replace(/"/g, '&quot;');
    if (!safeUrl) return;
    document.execCommand('insertHTML', false, '<img src="' + safeUrl + '" style="max-width:100%;border-radius:6px">');
    syncRteBody(rte);
  }

  function insertRteVideo(rte, url) {
    restoreRteSelection(rte);
    var safeUrl = String(url || '').replace(/"/g, '&quot;');
    if (!safeUrl) return;
    // 鐢?contenteditable="false" 包裹视频为不可编辑原子单鍏冦€?
    // 删除按钮放在视频上方的小工具栏中，避免被浏览器原生控件遮挡。
    var wrapper = document.createElement('div');
    wrapper.setAttribute('contenteditable', 'false');
    wrapper.className = 'rte-media-wrapper';
    wrapper.style.cssText = 'display:inline-block;max-width:100%;margin:8px 0;user-select:none;vertical-align:top';

    // 视频上方的小工具栏
    var toolbar = document.createElement('div');
    toolbar.className = 'rte-media-toolbar';
    toolbar.style.cssText = 'display:flex;align-items:center;justify-content:space-between;' +
      'padding:3px 6px;background:#f5f5f5;border:1px solid #e0e0e0;border-bottom:none;' +
      'border-radius:6px 6px 0 0;font-size:11px;color:#888';
    toolbar.innerHTML = '<span>馃幀 视频</span>';

    var delBtn = document.createElement('button');
    delBtn.type = 'button';
    delBtn.className = 'rte-media-del';
    delBtn.setAttribute('contenteditable', 'false');
    delBtn.textContent = '✕?删除';
    delBtn.style.cssText = 'border:1px solid #ddd;background:#fff;color:#e74c3c;' +
      'border-radius:3px;cursor:pointer;font-size:11px;padding:1px 8px;line-height:1.6';
    toolbar.appendChild(delBtn);
    wrapper.appendChild(toolbar);

    var video = document.createElement('video');
    video.src = safeUrl;
    video.setAttribute('controls', '');
    video.setAttribute('playsinline', '');
    video.setAttribute('preload', 'metadata');
    video.style.cssText = 'max-width:100%;display:block;border-radius:0 0 6px 6px';
    wrapper.appendChild(video);

    // 鐢?Range.insertNode 直接插入 DOM 节点，避鍏?execCommand insertHTML
    // 琚祻览器 sanitize 鎺?contenteditable 属性自动?wrapper 退化为可编辑元绱犮€?
    var sel = window.getSelection();
    if (sel.rangeCount) {
      var range = sel.getRangeAt(0);
      if (rte.contains(range.commonAncestorContainer)) {
        range.insertNode(wrapper);
        range.setStartAfter(wrapper);
        range.collapse(true);
        sel.removeAllRanges();
        sel.addRange(range);
      }
    }
    syncRteBody(rte);
  }


  // 注册鍦?document 上用事件委托，因涓wrapper 鏄姩鎬?DOM 节点銆?
  document.addEventListener('click', function(e) {
    var delBtn = e.target.closest('.rte-media-del');
    if (!delBtn) return;
    e.preventDefault();
    e.stopPropagation();
    var wrapper = delBtn.closest('.rte-media-wrapper');
    if (!wrapper) return;
    var rte = wrapper.closest('.rte-editor');
    wrapper.remove();
    if (rte) syncRteBody(rte);
  });

  function ensureAllRteUploadControls() {
    document.querySelectorAll('.rte-editor').forEach(ensureRteUploadControls);
  }
  setTimeout(ensureAllRteUploadControls, 0);
  if (window.MutationObserver) {
    new MutationObserver(function(mutations) {
      var shouldScan = mutations.some(function(m) {
        return Array.prototype.some.call(m.addedNodes || [], function(node) {
          return node.nodeType === 1 && (
            (node.matches && node.matches('.rte-editor, .rte-wrapper')) ||
            (node.querySelector && node.querySelector('.rte-editor'))
          );
        });
      });
      if (shouldScan) ensureAllRteUploadControls();
    }).observe(document.body, { childList: true, subtree: true });
  }

  function triggerRteImageUpload(btn) {
    var wrapper = btn.closest('.rte-wrapper');
    var rte = wrapper ? wrapper.querySelector('.rte-editor') : _lastRteEditor;
    if (!rte) return;
    ensureRteUploadControls(rte);
    saveRteSelection(rte);
    var uploadInput = wrapper.querySelector('.rte-image-upload-input');
    if (uploadInput) {
      uploadInput.value = '';
      uploadInput.click();
    }
  }

  function getCsrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.getAttribute('content')) return meta.getAttribute('content');
    var input = document.querySelector('input[name="csrf_token"]');
    return input ? input.value : '';
  }

  function richtextUploadUrl() {
    var site = '';
    if (typeof currentSiteParam === 'function') site = currentSiteParam();
    if (!site) site = new URLSearchParams(window.location.search).get('site') || '';
    return '/api/richtext/upload-image' + (site ? '?site=' + encodeURIComponent(site) : '');
  }

  function richtextVideoUploadUrl() {
    var site = '';
    if (typeof currentSiteParam === 'function') site = currentSiteParam();
    if (!site) site = new URLSearchParams(window.location.search).get('site') || '';
    return '/api/richtext/upload-video' + (site ? '?site=' + encodeURIComponent(site) : '');
  }

  document.addEventListener('focusin', function(e) {
    var rte = e.target.closest('.rte-editor');
    if (rte) {
      _lastRteEditor = rte;
      ensureRteUploadControls(rte);
      saveRteSelection(rte);
    }
  });

  // 鈹€鈹€ 工具鏍mousedown：阻止按閽伔走焦鐐?鈹€鈹€
  document.addEventListener('mousedown', function(e) {
    if (e.target.closest('.rte-toolbar .rte-btn')) {
      e.preventDefault();
      return;
    }
    var headingSelect = e.target.closest('.rte-heading-select');
    if (headingSelect) {
      var wrapper = headingSelect.closest('.rte-wrapper');
      var rte = wrapper ? wrapper.querySelector('.rte-editor') : _lastRteEditor;
      if (rte) {
        _lastRteEditor = rte;
        saveRteSelection(rte);
      }
    }
  });

  // 鈹€鈹€ 工具鏍click：执行命浠?鈹€鈹€
  document.addEventListener('click', function(e) {
    var btn = e.target.closest('.rte-btn');
    if (!btn) return;
    var rte = btn.closest('.rte-wrapper').querySelector('.rte-editor');
    if (!rte) rte = _lastRteEditor;
    if (!rte) return;

    // 先用 preventDefault 过的 mousedown 保住了光标在此
    var cmd = btn.dataset.cmd;
    var arg = btn.dataset.arg || null;

    saveRteSelection(rte);

    if (btn.classList.contains('rte-upload-image-btn')) {
      triggerRteImageUpload(btn);
    } else if (btn.classList.contains('rte-upload-video-btn')) {
      triggerRteVideoUpload(btn);
    } else if (btn.classList.contains('rte-table-btn')) {
      insertRteTableConfigured(rte);
    } else if (btn.classList.contains('rte-table-settings-btn')) {
      editRteTable(rte);
    } else if (btn.classList.contains('rte-link-btn')) {
      openRtePopover(rte, 'link');
    } else if (btn.classList.contains('rte-image-btn')) {
      openRtePopover(rte, 'image');
    } else if (btn.classList.contains('rte-video-url-btn')) {
      openRtePopover(rte, 'video');
    } else {
      rte.focus();
      document.execCommand(cmd, false, arg);
      syncRteBody(rte);
    }
  });

  // 鈹€鈹€ 标题下拉 鈹€鈹€
  document.addEventListener('change', function(e) {
    if (!e.target.classList.contains('rte-heading-select')) return;
    var rte = e.target.closest('.rte-wrapper').querySelector('.rte-editor');
    if (!rte) rte = _lastRteEditor;
    if (!rte) return;
    restoreRteSelection(rte);
    var tag = e.target.value;
    document.execCommand('formatBlock', false, tag ? '<' + tag + '>' : '<p>');
    syncRteBody(rte);
    saveRteSelection(rte);
    e.target.value = '';
  });

  function triggerRteVideoUpload(btn) {
    var wrapper = btn.closest('.rte-wrapper');
    var rte = wrapper ? wrapper.querySelector('.rte-editor') : _lastRteEditor;
    if (!rte) return;
    ensureRteUploadControls(rte);
    saveRteSelection(rte);
    var uploadInput = wrapper.querySelector('.rte-video-upload-input');
    if (uploadInput) {
      uploadInput.value = '';
      uploadInput.click();
    }
  }

  document.addEventListener('change', function(e) {
    if (!e.target.classList.contains('rte-video-upload-input')) return;
    var input = e.target;
    var wrapper = input.closest('.rte-wrapper');
    var rte = wrapper ? wrapper.querySelector('.rte-editor') : _lastRteEditor;
    var status = wrapper ? wrapper.querySelector('.rte-upload-status') : null;
    var file = input.files && input.files[0];
    if (!rte || !file) return;

    var fd = new FormData();
    fd.append('video', file);
    var csrfToken = getCsrfToken();
    if (csrfToken) fd.append('csrf_token', csrfToken);
    if (status) {
      status.textContent = 'Uploading video...';
      status.className = 'rte-upload-status small text-muted mb-1';
      status.style.display = '';
    }

    fetch(richtextVideoUploadUrl(), {
      method: 'POST',
      body: fd,
      headers: csrfToken ? { 'X-CSRFToken': csrfToken } : {}
    })
      .then(function(r) {
        return r.text().then(function(text) {
          var data = null;
          try { data = text ? JSON.parse(text) : {}; }
          catch (err) { throw new Error('Video upload failed (HTTP ' + r.status + ').'); }
          return { ok: r.ok, data: data };
        });
      })
      .then(function(result) {
        if (!result.ok || !result.data || !result.data.url) {
          throw new Error((result.data && result.data.error) || 'Video upload failed');
        }
        insertRteVideo(rte, result.data.url);
        if (status) {
          status.textContent = 'Video inserted.';
          status.className = 'rte-upload-status small text-success mb-1';
          setTimeout(function() { status.style.display = 'none'; }, 1800);
        }
      })
      .catch(function(err) {
        if (status) {
          status.textContent = err.message || 'Video upload failed';
          status.className = 'rte-upload-status small text-danger mb-1';
          status.style.display = '';
        } else {
          alert(err.message || 'Video upload failed');
        }
      });
  });

  // 鈹€鈹€ 颜色选择鍣?鈹€鈹€
  document.addEventListener('input', function(e) {
    if (!e.target.classList.contains('rte-color-picker')) return;
    var rte = e.target.closest('.rte-wrapper').querySelector('.rte-editor');
    if (!rte) rte = _lastRteEditor;
    if (!rte) return;
    rte.focus();
    document.execCommand('foreColor', false, e.target.value);
    syncRteBody(rte);
  });

  // 鈹€鈹€ 编辑器内容变鏇?↪鍚屾 textarea 鈹€鈹€
  document.addEventListener('input', function(e) {
    var rte = e.target.closest('.rte-editor');
    if (rte) {
      saveRteSelection(rte);
      syncRteBody(rte);
    }
  });

  document.addEventListener('keyup', function(e) {
    var rte = e.target.closest('.rte-editor');
    if (rte) saveRteSelection(rte);
  });

  document.addEventListener('mouseup', function(e) {
    var rte = e.target.closest('.rte-editor');
    if (rte) saveRteSelection(rte);
  });

  document.addEventListener('keydown', function(e) {
    var rte = e.target.closest('.rte-editor');
    if (!rte) return;
    var key = e.key ? e.key.toLowerCase() : '';
    if ((e.ctrlKey || e.metaKey) && key === 'k') {
      e.preventDefault();
      _lastRteEditor = rte;
      saveRteSelection(rte);
      openRtePopover(rte, 'link');
    }
  });

  document.addEventListener('change', function(e) {
    if (!e.target.classList.contains('rte-image-upload-input')) return;
    var input = e.target;
    var wrapper = input.closest('.rte-wrapper');
    var rte = wrapper ? wrapper.querySelector('.rte-editor') : _lastRteEditor;
    var status = wrapper ? wrapper.querySelector('.rte-upload-status') : null;
    var file = input.files && input.files[0];
    if (!rte || !file) return;

    var fd = new FormData();
    fd.append('image', file);
    var csrfToken = getCsrfToken();
    if (csrfToken) fd.append('csrf_token', csrfToken);
    if (status) {
      status.textContent = 'Uploading image...';
      status.className = 'rte-upload-status small text-muted mb-1';
      status.style.display = '';
    }

    fetch(richtextUploadUrl(), {
      method: 'POST',
      body: fd,
      headers: csrfToken ? { 'X-CSRFToken': csrfToken } : {}
    })
      .then(function(r) {
        return r.text().then(function(text) {
          var data = null;
          try {
            data = text ? JSON.parse(text) : {};
          } catch (err) {
            if (r.status === 401) throw new Error('Please log in again.');
            if (r.status === 404) throw new Error('Upload API not found. Please restart the Flask server and refresh the admin page.');
            throw new Error('Upload failed (HTTP ' + r.status + '). Please refresh the page and try again.');
          }
          return { ok: r.ok, data: data };
        });
      })
      .then(function(result) {
        if (!result.ok || !result.data || !result.data.url) {
          throw new Error((result.data && result.data.error) || 'Upload failed');
        }
        insertRteImage(rte, result.data.url);
        if (status) {
          status.textContent = 'Image inserted.';
          status.className = 'rte-upload-status small text-success mb-1';
          setTimeout(function() { status.style.display = 'none'; }, 1800);
        }
      })
      .catch(function(err) {
        if (status) {
          status.textContent = err.message || 'Upload failed';
          status.className = 'rte-upload-status small text-danger mb-1';
          status.style.display = '';
        } else {
          alert(err.message || 'Upload failed');
        }
      });
  });

  // 鈹€鈹€ 粘贴清理格式 鈹€鈹€
  document.addEventListener('paste', function(e) {
    var rte = e.target.closest('.rte-editor');
    if (!rte) return;
    e.preventDefault();
    var text = (e.clipboardData || window.clipboardData).getData('text/plain');
    var html = text.split(/\n\n+/).map(function(p) {
      return '<p>' + p.replace(/\n/g, '<br>') + '</p>';
    }).join('');
    document.execCommand('insertHTML', false, html);
    syncRteBody(rte);
  });

  /* ==== URL 对齐弹框（链接 / 图片共用，页面居中遮罩） ==== */
  var _rteDialogState = { rte: null, mode: '', existingLink: null, range: null };

  function ensureRteUrlOverlay(wrapper) {
    if (!wrapper) return null;
    var overlay = wrapper.querySelector('.rte-url-overlay');
    if (overlay) return overlay;
    overlay = document.createElement('div');
    overlay.className = 'rte-url-overlay';
    overlay.style.cssText = 'display:none;position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.35);align-items:center;justify-content:center';
    overlay.innerHTML =
      '<div class="rte-url-dialog" style="background:#fff;border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,.18);padding:20px;width:420px;max-width:90vw">' +
        '<div class="rte-url-dialog-title small fw-semibold mb-3" style="font-size:13px;color:#343a40"></div>' +
        '<input type="text" class="form-control form-control-sm rte-url-dialog-input" placeholder="https://">' +
        '<div class="d-flex gap-2 mt-3 justify-content-end">' +
          '<button type="button" class="btn btn-sm btn-outline-secondary rte-url-dialog-cancel">取消</button>' +
          '<button type="button" class="btn btn-sm btn-primary rte-url-dialog-confirm">确认</button>' +
        '</div>' +
      '</div>';
    wrapper.appendChild(overlay);
    return overlay;
  }

  function openRtePopover(rte, mode) {
    var wrapper = rte.closest('.rte-wrapper');
    var overlay = ensureRteUrlOverlay(wrapper);
    if (!overlay) return;

    var titleEl   = overlay.querySelector('.rte-url-dialog-title');
    var inputEl   = overlay.querySelector('.rte-url-dialog-input');
    var confirmEl = overlay.querySelector('.rte-url-dialog-confirm');

    var existing = null;
    var rangeSnapshot = savedRangeInRte(rte);
    var currentUrl = '';
    if (mode === 'link') {
      var sel = window.getSelection();
      if (sel.rangeCount) {
        var currentRange = sel.getRangeAt(0);
        if (rte.contains(currentRange.commonAncestorContainer)) {
          rangeSnapshot = currentRange.cloneRange();
          _rteSavedRange = rangeSnapshot.cloneRange();
        }
      }
      if (rangeSnapshot) {
        var node = rangeSnapshot.commonAncestorContainer;
        var el = node.nodeType === 1 ? node : (node.parentElement || node.parentNode);
        existing = el && el.closest ? el.closest('a') : null;
      }
      currentUrl = existing ? (existing.getAttribute('href') || '') : '';
    }

    _rteDialogState = { rte: rte, mode: mode, existingLink: existing, range: rangeSnapshot };

    titleEl.textContent = mode === 'link'
      ? (existing ? '编辑链接' : '插入链接')
      : '插入图片';
    inputEl.value = currentUrl;
    if (mode === 'video') {
      titleEl.textContent = '插入视频链接';
      inputEl.placeholder = 'https://example.com/video.mp4';
    } else {
      inputEl.placeholder = mode === 'link' ? 'https://example.com' : 'https://example.com/pic.webp';
    }
    confirmEl.textContent = mode === 'link' && existing ? '更新' : '确认';
    overlay.style.display = 'flex';
    setTimeout(function(){ inputEl.focus(); inputEl.select(); }, 50);
  }

  // 确认（加锁防閲嶅触发锛?
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.rte-url-dialog-confirm')) return;
    var overlay = e.target.closest('.rte-url-overlay');
    if (!overlay || overlay.style.display === 'none') return;
    var state = _rteDialogState;
    if (!state.rte) return;
    var url = overlay.querySelector('.rte-url-dialog-input').value.trim();
    var rte = state.rte;
    // 先消璐?state + 隐藏 overlay，再操作 DOM锛岄槻姝换何重鍏?
    _rteDialogState = { rte: null, mode: '', existingLink: null, range: null };
    overlay.style.display = 'none';

    restoreRteSelection(rte, state.range);

    if (state.mode === 'link') {
      if (state.existingLink) {
        if (url) {
          setRteLinkAttrs(state.existingLink, url);
        } else {
          var txt = document.createTextNode(state.existingLink.textContent);
          state.existingLink.parentNode.replaceChild(txt, state.existingLink);
        }
      } else if (url) {
        insertRteLink(rte, url, state.range);
      }
    } else if (state.mode === 'image' && url) {
      // execCommand('insertImage') 行为不可靠（选区/娴忚器差寮傚自动撮噸复插入）銆?
      // 改用 insertHTML 注入 <img> 标签，一次精确插入。
      insertRteImage(rte, url);
    } else if (state.mode === 'video' && url) {
      insertRteVideo(rte, url);
    }
    syncRteBody(rte);
  });

  // 取消 / 点击遮罩关闭
  // 鐢?closest 匹配取消按钮锛堝彲鑳借点击的是按钮内的文本节点锛?
  document.addEventListener('click', function(e) {
    if (e.target.closest('.rte-url-dialog-cancel')) {
      var overlay = e.target.closest('.rte-url-overlay');
      if (overlay) overlay.style.display = 'none';
      _rteDialogState = { rte: null, mode: '', existingLink: null, range: null };
      return;
    }
    // 点击 overlay 自动韩（遮罩空鐧藉锛夊叧闂?
    if (e.target.classList.contains('rte-url-overlay')) {
      e.target.style.display = 'none';
      _rteDialogState = { rte: null, mode: '', existingLink: null, range: null };
    }
  });

  // Enter 确认
  document.addEventListener('keydown', function(e) {
    if (e.key !== 'Enter') return;
    var input = e.target.closest('.rte-url-dialog-input');
    if (!input) return;
    e.preventDefault();
    var overlay = input.closest('.rte-url-overlay');
    var confirm = overlay ? overlay.querySelector('.rte-url-dialog-confirm') : null;
    if (confirm) confirm.click();
  });

  function syncRteBody(rte) {
    var wrapper = rte.closest('.rte-wrapper') || rte.parentElement;
    var ta = wrapper ? (wrapper.querySelector('textarea[hidden], textarea.d-none, textarea[name="body"]')) : null;
    if (ta) ta.value = rte.innerHTML;
  }

  }
})();