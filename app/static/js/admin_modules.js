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
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c];
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

  function legacyRichEditorExec(editor, cmd, arg) {
    editor.focus();
    if (cmd === 'formatBlock') {
      var tag = String(arg || 'p').replace(/[<>]/g, '').toLowerCase();
      if (!/^(p|h1|h2|h3|h4|h5|h6|blockquote)$/.test(tag)) tag = 'p';
      document.execCommand('formatBlock', false, '<' + tag + '>');
      if (tag === 'p') {
        var sel = window.getSelection();
        var node = sel && sel.rangeCount ? sel.getRangeAt(0).commonAncestorContainer : null;
        var el = node && node.nodeType === 1 ? node : (node ? node.parentElement : null);
        var heading = el ? el.closest('h1,h2,h3,h4,h5,h6,blockquote') : null;
        if (heading && editor.contains(heading)) {
          var p = document.createElement('p');
          while (heading.firstChild) p.appendChild(heading.firstChild);
          heading.parentNode.replaceChild(p, heading);
        }
      }
      return;
    }
    document.execCommand(cmd, false, arg || null);
  }

  window._richEditorCommand = function(btn, event, cmd, arg) {
    if (event) event.preventDefault();
    var wrapper = btn && btn.closest ? btn.closest('.mb-2') : null;
    var editor = wrapper ? wrapper.querySelector('.rich-editor-body') : null;
    if (!editor) return false;
    legacyRichEditorExec(editor, cmd, arg);
    var textarea = editor.nextElementSibling;
    if (textarea) textarea.value = editor.innerHTML;
    return false;
  };

  window._richEditorSelectCommand = function(control, cmd, arg) {
    var wrapper = control && control.closest ? control.closest('.mb-2') : null;
    var editor = wrapper ? wrapper.querySelector('.rich-editor-body') : null;
    if (!editor) return false;
    legacyRichEditorExec(editor, cmd, arg);
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

  function richEditorHtml(name, value, compact) {
    var richProfile = typeof compact === 'string' ? compact : '';
    var currentType = (window._moduleCtx && window._moduleCtx.currentModuleType) || '';
    var moduleMatch = String(name || '').match(/^module_(\d+)_/);
    if (moduleMatch && typeof document !== 'undefined') {
      var moduleTypeInput = document.querySelector('[name="module_' + moduleMatch[1] + '_type"]');
      if (moduleTypeInput && moduleTypeInput.value) currentType = moduleTypeInput.value;
    }
    compact = !!((compact === true) || (
      (currentType === 'section_title' || currentType === 'highlight_card') &&
      /(^|_)desc(ription)?$/i.test(String(name || ''))
    ));
    if (!richProfile) richProfile = compact ? 'compact' : 'full';
    compact = richProfile === 'compact';
    var icons = {
      bold: '<svg viewBox="0 0 24 24"><path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/><path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/></svg>',
      italic: '<svg viewBox="0 0 24 24"><line x1="19" y1="4" x2="10" y2="4"/><line x1="14" y1="20" x2="5" y2="20"/><line x1="15" y1="4" x2="9" y2="20"/></svg>',
      underline: '<svg viewBox="0 0 24 24"><path d="M6 3v7a6 6 0 0 0 6 6 6 6 0 0 0 6-6V3"/><line x1="4" y1="21" x2="20" y2="21"/></svg>',
      strike: '<svg viewBox="0 0 24 24"><path d="M5 12h14"/><path d="M17 6.5A5 5 0 0 0 8 9c0 1 .3 1.8 1 2.4"/><path d="M9 17.5a5 5 0 0 0 7.7-2.2"/></svg>',
      alignLeft: '<svg viewBox="0 0 24 24"><line x1="17" y1="10" x2="3" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="17" y1="14" x2="3" y2="14"/><line x1="21" y1="18" x2="3" y2="18"/></svg>',
      alignCenter: '<svg viewBox="0 0 24 24"><line x1="18" y1="10" x2="6" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="18" y1="14" x2="6" y2="14"/><line x1="21" y1="18" x2="3" y2="18"/></svg>',
      alignRight: '<svg viewBox="0 0 24 24"><line x1="21" y1="10" x2="7" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="21" y1="14" x2="7" y2="14"/><line x1="21" y1="18" x2="3" y2="18"/></svg>',
      ul: '<svg viewBox="0 0 24 24"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>',
      ol: '<svg viewBox="0 0 24 24"><line x1="10" y1="6" x2="21" y2="6"/><line x1="10" y1="12" x2="21" y2="12"/><line x1="10" y1="18" x2="21" y2="18"/><path d="M4 6h1v4"/><path d="M3 10h2"/><path d="M4 18h1.5a1.5 1.5 0 1 0 0-3H4"/></svg>',
      indent: '<svg viewBox="0 0 24 24"><line x1="21" y1="6" x2="11" y2="6"/><line x1="21" y1="10" x2="11" y2="10"/><line x1="21" y1="14" x2="11" y2="14"/><line x1="21" y1="18" x2="11" y2="18"/><polyline points="7 8 3 12 7 16"/></svg>',
      outdent: '<svg viewBox="0 0 24 24"><line x1="21" y1="6" x2="11" y2="6"/><line x1="21" y1="10" x2="11" y2="10"/><line x1="21" y1="14" x2="11" y2="14"/><line x1="21" y1="18" x2="11" y2="18"/><polyline points="3 8 7 12 3 16"/></svg>',
      table: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>',
      link: '<svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
      imageUrl: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>',
      imageUpload: '<svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
      videoUrl: '<svg viewBox="0 0 24 24"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>',
      videoUpload: '<svg viewBox="0 0 24 24"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/><line x1="8" y1="13" x2="8" y2="19"/><polyline points="5 16 8 19 11 16"/></svg>',
      mediaLibrary: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>',
      blockquote: '<svg viewBox="0 0 24 24"><path d="M3 5v8h5.5L6 21"/><path d="M12 5v8h5.5L15 21"/></svg>',
      hr: '<svg viewBox="0 0 24 24"><line x1="4" y1="12" x2="20" y2="12"/><polyline points="8 8 4 12 8 16"/><polyline points="16 8 20 12 16 16"/></svg>',
      sub: '<svg viewBox="0 0 24 24"><text x="4" y="14" font-size="12" font-weight="bold" fill="currentColor">x</text><text x="14" y="22" font-size="9" font-weight="bold" fill="currentColor">2</text></svg>',
      sup: '<svg viewBox="0 0 24 24"><text x="4" y="12" font-size="12" font-weight="bold" fill="currentColor">x</text><text x="14" y="10" font-size="9" font-weight="bold" fill="currentColor">2</text></svg>',
      settings: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>',
      clear: '<svg viewBox="0 0 24 24"><line x1="10" y1="6" x2="17" y2="6"/><path d="M7.5 6L9 18h6l1.5-12"/><line x1="4.5" y1="6" x2="19.5" y2="6"/></svg>',
      undo: '<svg viewBox="0 0 24 24"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>',
      redo: '<svg viewBox="0 0 24 24"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>',
      code: '<svg viewBox="0 0 24 24"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>'
    };
    function btn(cmd, title, icon, extra) {
      var cls = 'btn btn-sm btn-light rte-btn ' + (extra || '');
      return '<button type="button" class="' + cls + '" data-cmd="' + cmd + '" title="' + title + '" aria-label="' + title + '">' + icon + '</button>';
    }
    function btnArg(cmd, arg, title, html, extra) {
      var cls = 'btn btn-sm btn-light rte-btn ' + (extra || '');
      return '<button type="button" class="' + cls + '" data-cmd="' + cmd + '" data-arg="' + arg + '" title="' + title + '" aria-label="' + title + '">' + html + '</button>';
    }
    // ----- 工具栏 HTML：按功能分组，rte-sep 竖线分隔 -----
    var tb = '<div class="rich-toolbar rte-toolbar" style="display:flex;gap:1px;flex-wrap:wrap;align-items:center">';
    // G1 内联格式
    tb += btn('bold', '加粗 (Ctrl+B)', icons.bold);
    tb += btn('italic', '斜体 (Ctrl+I)', icons.italic);
    tb += btn('underline', '下划线 (Ctrl+U)', icons.underline);
    tb += btn('strikeThrough', '删除线', icons.strike);
    tb += '<span class="rte-sep"></span>';
    if (richProfile === 'content') {
      tb += '<select class="rte-font-size-select" title="所选文字字号" aria-label="所选文字字号" style="width:76px;height:30px;font-size:13px">' +
        '<option value="">字号</option><option value="12">12px</option><option value="14">14px</option><option value="16">16px</option><option value="18">18px</option><option value="20">20px</option><option value="24">24px</option><option value="28">28px</option><option value="32">32px</option>' +
        '</select><span class="rte-sep"></span>';
    } else if (!compact) {
      // G2 标题（完整正文编辑器使用）
      tb += btnArg('formatBlock', 'h2', '二级标题', 'H2', 'rte-heading-btn');
      tb += btnArg('formatBlock', 'h3', '三级标题', 'H3', 'rte-heading-btn');
      tb += btnArg('formatBlock', 'h4', '四级标题', 'H4', 'rte-heading-btn');
      tb += btnArg('formatBlock', 'p', '正文段落', 'P', 'rte-heading-btn');
      tb += '<span class="rte-sep"></span>';
    }
    // G3 对齐
    tb += btn('justifyLeft', '左对齐', icons.alignLeft);
    tb += btn('justifyCenter', '居中', icons.alignCenter);
    tb += btn('justifyRight', '右对齐', icons.alignRight);
    tb += '<span class="rte-sep"></span>';
    if (!compact) {
      // G4 列表 & 缩进
      tb += btn('insertUnorderedList', '无序列表', icons.ul);
      tb += btn('insertOrderedList', '有序列表', icons.ol);
      tb += btn('indent', '增加缩进', icons.indent);
      tb += btn('outdent', '减少缩进', icons.outdent);
      tb += '<span class="rte-sep"></span>';
      // G5 插入元素（表格/链接/图片/视频）
      tb += '<button type="button" class="btn btn-sm btn-light rte-btn rte-table-btn" title="插入表格" aria-label="插入表格">' + icons.table + '</button>';
      tb += '<button type="button" class="btn btn-sm btn-light rte-btn rte-table-settings-btn" title="表格设置（修改列宽/边框）" aria-label="表格设置">' + icons.settings + '</button>';
      tb += '<span class="rte-sep rte-media-sep"></span>';
      tb += '<button type="button" class="btn btn-sm btn-light rte-btn rte-link-btn" title="插入链接 (Ctrl+K)" aria-label="插入链接">' + icons.link + '</button>';
      tb += '<button type="button" class="btn btn-sm btn-light rte-btn rte-image-btn" title="插入图片链接" aria-label="插入图片链接">' + icons.imageUrl + '</button>';
      tb += '<button type="button" class="btn btn-sm btn-light rte-btn rte-upload-image-btn" title="上传图片" aria-label="上传图片">' + icons.imageUpload + '</button>';
      tb += '<button type="button" class="btn btn-sm btn-light rte-btn rte-video-url-btn" title="插入视频链接" aria-label="插入视频链接">' + icons.videoUrl + '</button>';
      tb += '<button type="button" class="btn btn-sm btn-light rte-btn rte-upload-video-btn" title="上传视频" aria-label="上传视频">' + icons.videoUpload + '</button>';
      tb += '<button type="button" class="btn btn-sm btn-light rte-btn rte-media-library-btn" title="从媒体库选择" aria-label="从媒体库选择">' + icons.mediaLibrary + '</button>';
      tb += '<span class="rte-sep"></span>';
      // G6 结构元素
      tb += btnArg('formatBlock', '<blockquote>', '引用块', icons.blockquote, 'rte-structure-btn');
      tb += btn('insertHorizontalRule', '分割线', icons.hr);
      tb += '<span class="rte-sep"></span>';
      // G7 文字样式
      tb += btn('subscript', '下标', icons.sub);
      tb += btn('superscript', '上标', icons.sup);
    }
    tb += '<input type="color" class="rte-color-picker" value="#141413" title="文字颜色">';
    tb += '<span class="rte-sep"></span>';
    // G8 撤销/重做
    tb += btn('undo', '撤销', icons.undo);
    tb += btn('redo', '重做', icons.redo);
    tb += '<span class="rte-sep"></span>';
    // G9 HTML 源码切换（仅完整正文编辑器使用）
    if (!compact) {
      tb += '<button type="button" class="btn btn-sm btn-light rte-btn rte-source-btn" title="查看/编辑 HTML 源码" aria-label="查看源码">' + icons.code + '</button>';
    }
    tb += '</div>';
    if (richProfile === 'content' || richProfile === 'notice') {
      var removeSpecial = richProfile === 'content'
        ? ['rte-table-btn', 'rte-table-settings-btn', 'rte-image-btn', 'rte-upload-image-btn', 'rte-video-url-btn', 'rte-upload-video-btn', 'rte-media-library-btn', 'rte-source-btn']
        : ['rte-heading-btn', 'rte-structure-btn', 'rte-table-btn', 'rte-table-settings-btn', 'rte-image-btn', 'rte-upload-image-btn', 'rte-video-url-btn', 'rte-upload-video-btn', 'rte-media-library-btn', 'rte-source-btn'];
      removeSpecial.forEach(function(className) {
        tb = tb.replace(new RegExp('<button[^>]*\\b' + className + '\\b[^>]*>[\\s\\S]*?<\\/button>', 'g'), '');
      });
      if (richProfile === 'notice') {
        ['justifyLeft', 'justifyCenter', 'justifyRight', 'indent', 'outdent', 'insertHorizontalRule', 'subscript', 'superscript'].forEach(function(command) {
          tb = tb.replace(new RegExp('<button[^>]*data-cmd="' + command + '"[^>]*>[\\s\\S]*?<\\/button>', 'g'), '');
        });
        tb = tb.replace(/<input[^>]*class="rte-color-picker"[^>]*>/g, '');
        tb = tb.replace(/<span class="rte-sep(?: [^"]*)?"><\/span>/g, '');
      } else {
        tb = tb.replace(/(?:<span class="rte-sep(?: [^"]*)?"><\/span>\s*){2,}/g, '<span class="rte-sep"></span>');
      }
    }
    return '<div class="rte-wrapper rte-profile-' + richProfile + '">' +
      tb +
      '<div contenteditable="true" class="rich-editor-body form-control form-control-sm rte-editor" style="min-height:150px;max-height:400px;overflow-y:auto;line-height:1.7;font-size:14px;outline:none" data-placeholder="">' + (value || '') + '</div>' +
      '<textarea class="form-control form-control-sm d-none rte-source-ta" style="min-height:150px;max-height:400px;font-family:Consolas,Monaco,monospace;font-size:14px;line-height:1.5" spellcheck="false"></textarea>' +
      '<textarea class="form-control form-control-sm d-none" name="' + esc(name) + '">' + esc(value || '') + '</textarea>' +
      '</div>';
  }
  // 导出到 window：panel_page_edit.html / panel_data_list.html 的内联脚本需要直接调用
  window.richEditorHtml = richEditorHtml;

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
      '<select class="form-select form-select-sm unit-picker" style="width:40%" onchange="var i=this.parentElement.querySelector(\'[name=&quot;' + name + '&quot;]\');if(i){var v=i.value.replace(/(?:px|rem|%|vh|vw)$/i,\'\').trim();var u=this.value;if(v&&u)i.value=v+u;}">' +
      '<option value="">--</option>' + opts + '</select></div>';
  }

  function sel(name, ph, options, dv) {
    var segmented = segmentedControl(name, options, dv, esc);
    if (segmented) {
      return '<div class="label-radio-row"><label class="form-label small mb-1 text-muted">' + ph + '</label>' + segmented + '</div>';
    }
    var h = '<div class="label-radio-row"><label class="form-label small mb-1 text-muted">' + ph + '</label><select class="form-select form-select-sm" name="' + name + '">';
    options.forEach(function(o) {
      h += '<option value="' + esc(o.value) + '"' + (String(dv || '') === String(o.value) ? ' selected' : '') + '>' + esc(o.label) + '</option>';
    });
    return h + '</select></div>';
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
        var openItem = openPicker.closest('.module-item, .detail-feature-item');
        if (openItem) openItem.classList.remove('icon-picker-open');
      }
    });
    picker.classList.toggle('open');
    var item = picker.closest('.module-item, .detail-feature-item');
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
    var item = picker.closest('.module-item, .detail-feature-item');
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
      var item = picker.closest('.module-item, .detail-feature-item');
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
    function alignmentIcon(alignment) {
      var widths = [12, 8, 10];
      var positions = alignment === 'left'
        ? [2, 2, 2]
        : alignment === 'right'
          ? [2, 6, 4]
          : [2, 4, 3];
      return '<svg class="seg-radio-align-icon" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">' +
        widths.map(function(width, i) {
          return '<path d="M' + positions[i] + ' ' + (4 + i * 4) + 'h' + width + '" stroke="currentColor" stroke-width="1.5" stroke-linecap="square"/>';
        }).join('') +
      '</svg>';
    }
    var opts = (options || []).map(function(opt) {
      return {
        value: String(typeof opt === 'object' ? opt.value : opt),
        label: String(typeof opt === 'object' ? (opt.label || opt.text || opt.value) : opt)
      };
    });
    var alignValues = ['left', 'center', 'right'];
    var blankMeansCenter = opts.some(function(opt) {
      return opt.value === '' && /居中|center/i.test(opt.label);
    });
    var isAlignment = ['left', 'right'].every(function(alignment) {
      return opts.some(function(opt) { return opt.value === alignment; });
    }) && opts.some(function(opt) { return opt.value === 'center' || opt.value === ''; }) && opts.every(function(opt) {
      return opt.value === '' || alignValues.indexOf(opt.value) !== -1;
    });
    if (isAlignment) {
      opts = alignValues.map(function(alignment) {
        return {
          value: alignment,
          label: { left: '居左', center: '居中', right: '居右' }[alignment]
        };
      });
    }
    if (opts.length < 2 || opts.length > 3) return '';
    var current = String(value == null ? '' : value);
    if (isAlignment && blankMeansCenter && current === '') current = 'center';
    return '<div class="seg-radio' + (isAlignment ? ' seg-radio--align' : '') + '" role="radiogroup">' +
      opts.map(function(opt) {
        var active = current === opt.value;
        var id = (name + '_' + opt.value).replace(/[^a-zA-Z0-9_-]/g, '_');
        return '<label class="seg-radio-option' + (active ? ' active' : '') + '" role="radio" aria-checked="' + (active ? 'true' : 'false') + '" for="' + escFn(id) + '"' + (isAlignment ? ' title="' + escFn(opt.label) + '"' : '') + '>' +
          '<input type="radio" id="' + escFn(id) + '" name="' + escFn(name) + '" value="' + escFn(opt.value) + '"' + (active ? ' checked' : '') + ' onchange="var input=this;var g=input.closest(\'.seg-radio\');g.querySelectorAll(\'.seg-radio-option\').forEach(function(b){b.classList.toggle(\'active\', b.contains(input));b.setAttribute(\'aria-checked\', b.contains(input)?\'true\':\'false\');});">' +
          (isAlignment ? '' : '<span class="seg-radio-dot" aria-hidden="true"></span>') + '<span class="seg-radio-label">' +
            (isAlignment ? alignmentIcon(opt.value) + '<span class="visually-hidden">' + escFn(opt.label) + '</span>' : escFn(opt.label)) +
          '</span>' +
          '</label>';
      }).join('') +
      '</div>';
  }

  function isDescriptionKey(key) {
    return /(description|summary|excerpt|desc|intro|message)/i.test(String(key || ''));
  }

  function mediaUploadHtml(name, value, type, placeholder, altValue) {
    var isVideo = type === 'video';
    var isEmbed = type === 'embed' || type === 'package';
    var safeName = esc(name);
    var safeValue = esc(value || '');
    var safeAlt = esc(altValue || '');
    var accept = isEmbed ? '.zip' : (isVideo ? 'video/mp4,video/webm,video/ogg,video/quicktime' : 'image/*,.svg,.svgz');
    var icon = isEmbed
      ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>'
      : isVideo
        ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>'
        : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>';
    // embed 类型无法本地预览（zip 包），始终显示图标
    var preview = (value && !isEmbed)
      ? (isVideo ? '<video src="' + safeValue + '" muted></video>' : '<img src="' + safeValue + '" alt="">')
      : icon;
    var helpText = isEmbed
      ? '上传包含 index.html 的 zip 网页包，用于嵌入 iframe 展示。'
      : isVideo ? '支持 MP4/WebM/OGG/MOV。' : '默认转 WebP，取消勾选则保留原格式。';
    var altInput = (isVideo || isEmbed) ? '' :
      '<div class="module-media-alt-row mt-1">' +
        '<input type="text" class="form-control form-control-sm module-media-alt-input" name="' + safeName + '_alt" value="' + safeAlt + '" placeholder="图片 Alt：自动使用标题/产品名，可覆盖">' +
      '</div>';
    return '<div class="module-media-layout"><div class="module-media-tools">' +
        '<div class="module-media-picker' + (value ? ' has-media' : '') + '" role="button" tabindex="0" title="' + (isEmbed ? '上传网页包' : '点击上传') + '" onclick="openModuleMediaPicker(event,this)" onkeydown="openModuleMediaPicker(event,this)">' +
          preview +
          (value ? moduleMediaPreviewButton() : '') +
          '<input type="file" name="' + safeName + '_file" accept="' + accept + '" onchange="handleModuleImageUpload(this)" style="display:none">' +
          (value ? '<button type="button" class="module-media-clear" onclick="event.preventDefault();event.stopPropagation();clearModuleImage(this)" title="删除后重新上传"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>' : '') +
        '</div>' +
      '</div>' +
      '<div class="module-media-content"><div class="module-media-url-row">' +
        '<input type="text" class="form-control form-control-sm" name="' + safeName + '" value="' + safeValue + '" placeholder="' + esc(placeholder || '') + '" oninput="updateImagePreview(this)">' +
        '<button type="button" class="module-media-library-btn" onclick="openModuleMediaLibrary(this)" title="从媒体库选择"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg></button>' +
        (isVideo || isEmbed ? '' : '<input type="hidden" name="' + safeName + '_convert_webp" value="false"><label class="module-convert-check"><input type="checkbox" name="' + safeName + '_convert_webp" value="true" checked><span></span>WebP</label>') +
      '</div>' + altInput + '<div class="form-text">' + helpText + '</div></div></div>';
}

  function enhanceCompactSelects(root) {
    root = root || document;
    root.querySelectorAll('select.form-select').forEach(function(select) {
      if (select.dataset.segmentedEnhanced === '1') return;
      if (select.multiple || select.classList.contains('unit-picker') || select.classList.contains('rte-heading-select') || select.classList.contains('detail-content-layout-field') || select.dataset.noSegmented === '1') return;
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
      var segParent = select.parentNode;
      segParent.insertBefore(segmented, select);
      // label + seg-radio 同行排版
      segParent.classList.add('label-radio-row');
      var segLabel = segParent.querySelector('.form-label');
      if (segLabel) segLabel.classList.remove('mb-1');
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
      var isStyleSelect = def.control === 'select' || def.control === 'switch';
      var styleSegmented = isStyleSelect ? segmentedControl(name, def.options || [], val, schemaEsc) : null;
      html += '<div class="mb-2' + (isStyleSelect ? ' label-radio-row' : '') + '"><label class="form-label small mb-1 text-muted">' + schemaEsc(labelText({ key: token, label: def.label || token })) + '</label>';
      if (styleSegmented) {
        html += styleSegmented;
      } else if (def.control === 'select' || def.control === 'switch') {
        html += '<select class="form-select form-select-sm" name="' + schemaEsc(name) + '"><option value="">默认</option>';
        (def.options || []).forEach(function(o) {
          var ov = o.value, ol = o.text || o.value;
          html += '<option value="' + schemaEsc(ov) + '"' + (String(val) === String(ov) ? ' selected' : '') + '>' + schemaEsc(ol) + '</option>';
        });
        html += '</select>';
      } else if (def.control === 'color') {
        html += '<div class="input-group input-group-sm">' +
          '<input type="color" class="form-control form-control-color" value="' + schemaEsc(val || '#888888') + '" oninput="this.nextElementSibling.value=this.value">' +
          '<input type="text" class="form-control form-control-sm" name="' + schemaEsc(name) + '" value="' + schemaEsc(val) + '" placeholder="如 #f5f7fa"></div>';
      } else if (def.control === 'dimension') {
        var dimensionMatch = String(val || '').trim().match(/^(\d+(?:\.\d+)?)\s*(px|rem|vh|vw|%)?$/i);
        var dimensionValue = dimensionMatch ? dimensionMatch[1] : '';
        var dimensionUnit = dimensionMatch && dimensionMatch[2] ? dimensionMatch[2].toLowerCase() : (def.default_unit || 'px');
        var dimensionUnits = def.units || ['px', 'rem', 'vh', 'vw', '%'];
        html += '<div class="input-group input-group-sm">' +
          '<input type="number" min="0" step="any" class="form-control form-control-sm" value="' + schemaEsc(dimensionValue) + '" placeholder="如 500" oninput="var w=this.parentElement;w.querySelector(\'input[type=hidden]\').value=this.value?this.value+w.querySelector(\'select\').value:\'\'">' +
          '<select class="form-select form-select-sm" style="max-width:90px" onchange="var w=this.parentElement,n=w.querySelector(\'input[type=number]\');w.querySelector(\'input[type=hidden]\').value=n.value?n.value+this.value:\'\'">' +
          dimensionUnits.map(function(unit) { return '<option value="' + schemaEsc(unit) + '"' + (dimensionUnit === unit ? ' selected' : '') + '>' + schemaEsc(unit) + '</option>'; }).join('') +
          '</select><input type="hidden" name="' + schemaEsc(name) + '" value="' + schemaEsc(dimensionMatch ? dimensionValue + dimensionUnit : '') + '"></div>';
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
  window.toggleModuleVisibility = function(btn) {
    var item = btn && btn.closest('.module-item');
    if (!item) return;
    var input = item.querySelector('.module-root-hidden');
    if (!input) return;
    var visible = btn.getAttribute('data-visible') === 'true';
    var nextVisible = !visible;
    btn.setAttribute('data-visible', nextVisible ? 'true' : 'false');
    btn.innerHTML = nextVisible ? window.EYE_OPEN_SVG : window.EYE_OFF_SVG;
    btn.title = nextVisible ? '隐藏模块' : '显示模块';
    btn.setAttribute('aria-label', btn.title);
    input.value = nextVisible ? 'false' : 'true';
    input.dispatchEvent(new Event('change', {bubbles: true}));
  };
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

  function contactInfoEditor(prefix, values) {
    values = values || {};
    function toggle(key, label, fallback) {
      var value = values[key];
      if (value == null || value === '') value = fallback;
      return visToggle(prefix + key, label, String(value));
    }
    return '<div class="alert alert-info py-2 px-3 mb-3" style="font-size:14px;line-height:1.5">' +
        '<div class="fw-semibold mb-1">此模块数据来自网站设置</div>' +
        '<div>数据源：<code>settings:contact</code>，电话、手机、邮箱、地址和营业时间请在「网站设置」中修改。</div>' +
      '</div>' +
      '<div class="row g-2">' +
        '<div class="col-6"><label class="form-label small mb-1 text-muted">区块标题</label><input type="text" class="form-control form-control-sm" name="' + esc(prefix + 'title') + '" value="' + esc(values.title || '') + '"></div>' +
        '<div class="col-6"><label class="form-label small mb-1 text-muted">区块副标题</label><input type="text" class="form-control form-control-sm" name="' + esc(prefix + 'subtitle') + '" value="' + esc(values.subtitle || '') + '"></div>' +
      '</div>' +
      '<hr class="my-2">' +
      '<div class="small fw-semibold mb-2 text-muted">显示项目</div>' +
      '<div class="d-flex flex-wrap gap-2">' +
        toggle('show_phone', '电话', 'true') +
        toggle('show_mobile', '手机', 'true') +
        toggle('show_email', '邮箱', 'true') +
        toggle('show_address', '地址', 'true') +
        toggle('show_business_hours', '营业时间', 'false') +
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
      '<div class="detail-gallery-item-header d-flex justify-content-between align-items-center px-2 py-2" style="cursor:pointer;background:#f8fafc;border-radius:0" onclick="window._toggleDetailGalleryItem(this)">' +
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
    media_area: '媒体区域',
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
    if (raw && /[\u4e00-\u9fff]/.test(raw)) return raw;
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
    if (type === 'hidden') {
      return '<input type="hidden" name="' + prefix + key + '" value="' + esc(value || field.default || '') + '">';
    }
    var isBindingField = /(^|_)(field|source)(_|$)/i.test(key) || /_ratio$/i.test(key) || /_radius$/i.test(key);
    var isImage = type === 'image' || (
      /(^|_)(image|cover|background_image|photo|logo)(_|$)/i.test(key) &&
      !/(images?_per|image_position|media_type)/i.test(key) &&
      !isBindingField
    );
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
    var isSegmented = type === 'select' && segmentedControl(prefix + key, field.options || [], value, esc);
    if (type === 'select') {
      wrapperAttrs = wrapperAttrs.replace('module-field', 'module-field label-radio-row');
    }
    html += '<div' + wrapperAttrs + '><label class="form-label small mb-1 text-muted">' + esc(labelText(field)) + '</label>';
    if (isVisibilityField(field)) {
      html += visibilityEye(prefix + key, value);
    } else if (type === 'list' || type === 'grid') {
      html += schemaListEditor(prefix, field, value);
    } else if (type === 'video') {
      html += mediaUploadHtml(prefix + key, value || '', 'video', placeholder || '视频 URL');
    } else if (type === 'embed') {
      // 网页包上传：zip 文件 → 解压为 iframe 可嵌入页面
      html += mediaUploadHtml(prefix + key, value || '', 'embed', placeholder || '上传网页包 ZIP');
    } else if (isImage) {
      html += mediaUploadHtml(prefix + key, value || '', 'image', placeholder || '');
    } else if (type === 'richtext') {
      html += richEditorHtml(prefix + key, value || '');
    } else if (type === 'textarea' && isDescriptionKey(key)) {
      html += richEditorHtml(prefix + key, value || '');
    } else if (type === 'textarea') {
      html += '<textarea class="form-control form-control-sm" rows="4" name="' + prefix + key + '" placeholder="' + esc(placeholder || '') + '">' + esc(value || '') + '</textarea>';
    } else if (isSegmented) {
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
    } else if (type === 'color') {
      var colorVal = value && String(value).trim();
      var pickerVal = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(colorVal || '') ? colorVal : '#888888';
      html += '<div class="module-color-control">' +
        '<label class="module-color-swatch' + (colorVal ? '' : ' color-empty') + '" title="选择颜色" style="background:' + esc(pickerVal) + '">' +
          '<input type="color" value="' + esc(pickerVal) + '" oninput="var wrap=this.closest(\'.module-color-control\');var sw=this.closest(\'.module-color-swatch\');var text=wrap&&wrap.querySelector(\'input[type=text]\');if(sw){sw.style.background=this.value;sw.classList.remove(\'color-empty\');}if(text){text.value=this.value;text.dispatchEvent(new Event(\'input\',{bubbles:true}));}">' +
        '</label>' +
        '<input type="text" class="form-control form-control-sm" name="' + prefix + key + '" value="' + esc(colorVal || '') + '" placeholder="选择颜色" oninput="var wrap=this.closest(\'.module-color-control\');var sw=wrap&&wrap.querySelector(\'.module-color-swatch\');var c=wrap&&wrap.querySelector(\'input[type=color]\');var valid=/^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(this.value);if(sw){sw.classList.toggle(\'color-empty\', !this.value);if(valid)sw.style.background=this.value;}if(c&&valid)c.value=this.value;">' +
        '</div>';
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
    var children = (field.children || field.item_fields || []);
    if ((field.type === 'list' || field.type === 'grid') && children.length === 1) {
      var only = children[0] || {};
      var nested = only.children || only.item_fields || [];
      if ((only.type || '') === 'group' && nested.length) {
        children = nested;
      }
    }
    var normalized = children.map(function(child) {
      var copy = Object.assign({}, child);
      copy.key = copy.key || copy.name;
      return copy;
    }).filter(function(child) {
      return !!child.key;
    });
    /* 叶子图片可以用 data-href 指向同一条目的链接字段。链接不是独立 DOM
       节点，但仍必须在列表编辑器中提供输入框。 */
    var childKeys = normalized.map(function(child) { return child.key; });
    normalized.slice().forEach(function(child) {
      var hrefKey = child.href_field || '';
      if (hrefKey && childKeys.indexOf(hrefKey) === -1) {
        normalized.push({ key: hrefKey, name: hrefKey, type: 'url', label: '链接（可选）' });
        childKeys.push(hrefKey);
      }
    });
    return normalized;
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
    var itemLabel = field.item_label || '条目';
    var html = '<div class="schema-list-editor" data-list-base="' + attrEsc(base) + '" data-list-name="' + attrEsc(key) + '" data-children="' + attrEsc(JSON.stringify(children)) + '">';
    html += '<div class="d-flex justify-content-between align-items-center mb-2">' +
      '<div class="small fw-semibold text-primary">' + esc(labelText(field)) + '</div>' +
      '<button type="button" class="btn btn-sm btn-outline-primary" onclick="window.schemaListAdd(this)">+ 添加' + esc(itemLabel) + '</button>' +
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
        '<button type="button" class="btn btn-sm btn-outline-info fp-import-btn" onclick="event.stopPropagation();window.openFeaturedImport(0, this)" style="font-size:14px;margin-right:4px" title="从已有数据集选取条目，自动填入标题、图片、描述和链接">📜 从数据集导入</button>' +
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
      html += '<div class="alert alert-info py-2 px-3 mb-3" style="font-size:14px;line-height:1.5">' +
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
    // 整块显隐已移到模块标题栏，避免在配置区重复显示。
    return html;
  }

  function getMergedSchema(meta) {
    var schema = (meta && meta.schema) || {};
    var metaFields = (meta && meta.fields) || [];
    var metaFieldMap = {};
    metaFields.forEach(function(f) { metaFieldMap[f.key] = f; });
    var schemaFieldMap = {};
    function collectSchemaFields(fields) {
      (fields || []).forEach(function(sf) {
        if (!sf) return;
        var name = sf.name || sf.key;
        if (name) schemaFieldMap[name] = sf;
        collectSchemaFields(sf.children || sf.item_fields || []);
      });
    }
    collectSchemaFields(schema.fields || []);
    var conditionalControllerMap = {};
    metaFields.forEach(function(f) {
      if (f.show_if && f.show_if.field) conditionalControllerMap[f.show_if.field] = true;
    });

    function metaChildrenMap(mf) {
      var map = {};
      ((mf && (mf.children || mf.item_fields)) || []).forEach(function(child) {
        var childName = child && (child.name || child.key);
        if (childName) map[childName] = child;
      });
      return map;
    }

    function mergeField(sf, metaOverride) {
      var name = sf.name || sf.key;
      var mf = metaOverride || metaFieldMap[name];
      var childMetaMap = metaChildrenMap(mf);
      var children = (sf.children || sf.item_fields || []).map(function(child) {
        var childName = child && (child.name || child.key);
        return mergeField(child, childMetaMap[childName]);
      });
      var childNames = children.map(function(child) { return child.name || child.key; });
      ((mf && (mf.children || mf.item_fields)) || []).forEach(function(child) {
        var childName = child && (child.name || child.key);
        if (childName && childNames.indexOf(childName) === -1) {
          children.push(mergeField(child, child));
          childNames.push(childName);
        }
      });
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
        merged.item_label = mf.item_label || merged.item_label;
        merged.show_if = mf.show_if || merged.show_if;
        if ((mf.type === 'list' || mf.type === 'grid') && (mf.item_fields || mf.children || []).length && !children.length) {
          merged.children = (mf.item_fields || mf.children || []).map(function(child) { return mergeField(child); });
          merged.item_fields = merged.children;
        }
        if ((mf.children || mf.item_fields || []).length && !children.length) {
          merged.children = (mf.children || mf.item_fields || []).map(function(child) { return mergeField(child); });
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
      if (mf.type === 'list' || mf.type === 'grid') {
        mergedFields.push(metaToSchemaField(mf));
      }
    });

    var result = {
      root_type: schema.root_type,
      root_tag: schema.root_tag,
      hideable: schema.hideable,
      href_field: schema.href_field,
      style_tokens: schema.style_tokens || [],
      element_style_tokens: schema.element_style_tokens || [],
      from_source: schema.from_source,
      fields: mergedFields
    };
    // 第二个参数为 true 时跳过 schemaFieldToFormField 转换（兼容调用方自有的字段处理逻辑）
    if (arguments.length >= 2 && arguments[1] === true) return result;
    result.fields = mergedFields.map(schemaFieldToFormField);
    return result;
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
      '<div class="d-flex justify-content-between align-items-center schema-list-item-header" data-schema-list-toggle="1" style="cursor:pointer;user-select:none">' +
        '<span class="small fw-semibold d-flex align-items-center">' +
          '<svg class="schema-list-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:12px;height:12px;margin-right:4px;flex-shrink:0;color:#94a3b8;transition:transform 0.2s"><path d="M9 18l6-6-6-6"/></svg>' +
          '条目 ' + (index + 1) +
        '</span>' +
        '<button type="button" class="module-action-btn module-action-del schema-list-remove" title="删除" aria-label="删除条目">' + detailGalleryIcon('trash') + '</button>' +
      '</div>' +
      '<div class="schema-list-item-body" style="margin-top: 8px;">' + inner + '</div>' +
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
      var header = item.querySelector('.schema-list-item-header');
      if (header) header.classList.remove('mb-2');
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

  function stripSchemaListHeaderMargins(root) {
    (root || document).querySelectorAll('.schema-list-item-header.mb-2').forEach(function(header) {
      header.classList.remove('mb-2');
    });
  }

  stripSchemaListHeaderMargins(document);
  if (window.MutationObserver && !window.__schemaListHeaderMarginObserver) {
    window.__schemaListHeaderMarginObserver = new MutationObserver(function(mutations) {
      mutations.forEach(function(mutation) {
        Array.prototype.forEach.call(mutation.addedNodes || [], function(node) {
          if (!node || node.nodeType !== 1) return;
          if (node.matches && node.matches('.schema-list-item-header.mb-2')) node.classList.remove('mb-2');
          if (node.querySelectorAll) stripSchemaListHeaderMargins(node);
        });
      });
    });
    window.__schemaListHeaderMarginObserver.observe(document.body, { childList: true, subtree: true });
  }

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
            '<div onclick="window.selectFeaturedItem(' + i + ')" style="cursor:pointer;border:1px solid #e2e8f0;border-radius: 0;overflow:hidden;height:100%">' +
              (cover ? '<img src="' + esc(cover) + '" alt="" loading="lazy" style="width:100%;height:90px;object-fit:cover" onerror="this.style.display=\'none\'">' : '<div style="width:100%;height:90px;background:#f1f5f9;display:flex;align-items:center;justify-content:center;color:#94a3b8">无图</div>') +
              '<div style="padding:6px 8px"><div style="font-size:14px;font-weight:600;line-height:1.3;color:#1e293b">' + esc(item.title || item.name || item.slug || '') + '</div></div>' +
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

  function isDetailTemplateComponent(type) {
    return !!(window._moduleCtx && window._moduleCtx.isDetailTemplateMode) && /^detail_/.test(String(type || ''));
  }

  function isDetailAdvancedField(field) {
    var group = String((field && field.group) || '');
    if (group === '样式') return true;
    if (group === '内容' || group === '显示规则' || group === '表格') return false;
    var key = String((field && field.key) || '').toLowerCase();
    var label = String((field && field.label) || '').toLowerCase();
    var styleKeys = [
      'section_bg',
      'text_color',
      'link_color',
      'border_color',
      'image_radius',
      'image_ratio',
      'text_align',
      'layout',
      'style'
    ];
    if (styleKeys.indexOf(key) >= 0) return true;
    if (/(^|_)(color|bg|background|border|radius|ratio|align|layout|style)$/.test(key)) return true;
    return /(颜色|背景|边框|分隔线|圆角|比例|排版|布局|样式)/.test(label) &&
      !/(来源|最多|为空|空行|显示|隐藏|开启|关闭|链接为空)/.test(label);
  }

  function renderDetailTemplateComponentFields(prefix, fields, values) {
    values = values || {};
    var primary = [];
    var advanced = [];
    (fields || []).forEach(function(field) {
      (isDetailAdvancedField(field) ? advanced : primary).push(field);
    });
    function gridHtml(list, emptyText) {
      if (!list.length) return '<div class="text-muted small py-2">' + emptyText + '</div>';
      var out = '<div class="detail-template-field-grid">';
      list.forEach(function(field) {
        out += renderField(prefix, field, values[field.key] || field.default || '', '');
      });
      return out + '</div>';
    }
    var html = '<div class="d-flex mb-2 detail-template-tabs">' +
      '<button type="button" class="btn btn-sm btn-outline-secondary active content-style-tab flex-fill" data-tab="content" onclick="window._switchContentStyleTab(this, \'content\')">内容</button>' +
      '<button type="button" class="btn btn-sm btn-outline-secondary content-style-tab flex-fill" data-tab="style" onclick="window._switchContentStyleTab(this, \'style\')">样式</button>' +
      '</div>' +
      '<div class="content-style-panel panel-content detail-template-fields">' +
        gridHtml(primary, '此组件没有内容配置') +
      '</div>' +
      '<div class="content-style-panel panel-style detail-template-fields" style="display:none">' +
        gridHtml(advanced, '此组件没有样式配置') +
      '</div>';
    return html;
  }

  function findNamedInput(root, name) {
    var inputs = root.querySelectorAll('[name="' + name + '"]');
    if (!inputs.length) return null;
    // radio 按钮组需返回选中的那个，否则始终拿到第一个选项的值（如 media_type 永远 = image）
    if (inputs[0].type === 'radio') {
      for (var i = 0; i < inputs.length; i++) {
        if (inputs[i].checked) return inputs[i];
      }
      return inputs[0]; // 兜底：没有选中的就返回第一个
    }
    return inputs[0];
  }

  function updateConditionalFields(root) {
    root = root || document;
    root.querySelectorAll('.module-field[data-show-if-field]').forEach(function(fieldEl) {
      var fieldKey = fieldEl.getAttribute('data-field-key') || '';
      var depKey = fieldEl.getAttribute('data-show-if-field') || '';
      var expected = (fieldEl.getAttribute('data-show-if-value') || '').split(',').map(function(v) { return v.trim(); });
      // 搜值用 input（text/url/textarea/select/number/color），
      // 不能用裸 [name] —— 会匹配到 file input，其 name 后缀 _file 不匹配 fieldKey
      // 分段选择器会把 select 渲染成同名 radio；条件字段自身也可能是
      // hidden/radio，因此只排除 file，确保仍能从 name 推导当前组件前缀。
      var ownInput = fieldEl.querySelector('input[name]:not([type="file"]), textarea[name], select[name]');
      var prefix = '';
      if (ownInput && fieldKey && ownInput.name.slice(-fieldKey.length) === fieldKey) {
        prefix = ownInput.name.slice(0, -fieldKey.length);
      }
      var scope = fieldEl.closest('.device-config') || root;
      var depInput = fieldKey ? findNamedInput(scope, prefix + depKey) : null;
      var actual = depInput ? String(depInput.value || '') : '';
      if (!actual && depKey === 'media_type') actual = 'image';
      var shouldShow = expected.indexOf(actual) >= 0;
      // 详情模板网格使用 display:grid !important，单靠内联 display:none
      // 会被覆盖；同步切换专用 class，由 CSS 以同等级规则真正隐藏。
      fieldEl.classList.toggle('module-field-condition-hidden', !shouldShow);
      if (shouldShow) {
        fieldEl.style.removeProperty('display');
      } else {
        fieldEl.style.setProperty('display', 'none', 'important');
      }
    });
  }

  // 图片上传：选择文件后本地预览（全局函数，供动态生成的 onchange 调用
  function moduleMediaPlaceholderIcon(accept) {
    var isVideo = /video/i.test(accept || '');
    var isEmbed = /\.zip/i.test(accept || '');
    if (isEmbed) return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>';
    return isVideo
      ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>'
      : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>';
  }

  function moduleMediaPreviewButton() {
    return '<button type="button" class="module-media-preview-icon" onclick="event.preventDefault();event.stopPropagation();var media=this.closest(&quot;.module-media-picker&quot;).querySelector(&quot;img,video&quot;);if(media)enlargeImage(media)" title="预览" aria-label="预览"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg></button>';
  }

  window.openModuleMediaPicker = function(event, picker) {
    if (!event || !picker) return;
    if (event.type === 'keydown' && event.key !== 'Enter' && event.key !== ' ') return;
    if (event.target.closest('button,a,input')) return;
    event.preventDefault();
    var fileInput = picker.querySelector('input[type="file"]');
    if (fileInput) fileInput.click();
  };

  function renderModuleMediaPicker(picker, src, fileName, accept) {
    if (!picker) return;
    var existingFile = picker.querySelector('input[type=file]');
    // 保存旧文件引用——innerHTML 会销毁旧的 file input 及其已选文件
    var oldFiles = existingFile && existingFile.files && existingFile.files.length ? existingFile.files : null;
    fileName = fileName || (existingFile ? existingFile.name : '');
    accept = accept || (existingFile ? existingFile.getAttribute('accept') : 'image/*,.svg,.svgz') || 'image/*,.svg,.svgz';
    var safeSrc = src ? String(src).replace(/"/g, '&quot;') : '';
    var isVideo = /video/i.test(accept || '') || /\.(mp4|webm|ogg|mov)$/i.test(safeSrc);
    var isEmbed = /\.zip/i.test(accept || '');
    picker.classList.toggle('has-media', !!src);
    // embed 类型无需预览，始终显示图标
    if (isEmbed && src) {
      picker.innerHTML = moduleMediaPlaceholderIcon(accept) +
        '<input type="file" name="' + fileName + '" accept="' + accept + '" onchange="handleModuleImageUpload(this)" style="display:none">' +
        '<button type="button" class="module-media-clear" onclick="event.preventDefault();event.stopPropagation();clearModuleImage(this)" title="删除后重新上传"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>';
    } else {
      picker.innerHTML = src
        ? (isVideo ? '<video src="' + safeSrc + '" muted></video>' : '<img src="' + safeSrc + '" alt="">') +
          moduleMediaPreviewButton() +
          '<input type="file" name="' + fileName + '" accept="' + accept + '" onchange="handleModuleImageUpload(this)" style="display:none">' +
          '<button type="button" class="module-media-clear" onclick="event.preventDefault();event.stopPropagation();clearModuleImage(this)" title="删除后重新上传"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>'
        : moduleMediaPlaceholderIcon(accept) + '<input type="file" name="' + fileName + '" accept="' + accept + '" onchange="handleModuleImageUpload(this)" style="display:none">';
    }
    // innerHTML 替换会销毁旧的 file input，需把已选文件恢复到新 input 中
    if (oldFiles) {
      var newInput = picker.querySelector('input[type=file]');
      if (newInput) {
        try {
          var dt = new DataTransfer();
          for (var i = 0; i < oldFiles.length; i++) { dt.items.add(oldFiles[i]); }
          newInput.files = dt.files;
        } catch(e) { /* DataTransfer 不可用时静默跳过 */ }
      }
    }
  }

  function mediaAltFromFilename(file) {
    var name = file && file.name ? file.name : '';
    return name.replace(/\.[^.]+$/, '').replace(/[-_]+/g, ' ').trim();
  }

  function mediaAltFromForm(container, file) {
    var form = container && container.closest ? container.closest('form') : document;
    var candidates = ['title', 'name', 'label'];
    for (var i = 0; i < candidates.length; i++) {
      var input = form && form.querySelector('[name$="' + candidates[i] + '"]');
      if (input && String(input.value || '').trim()) return String(input.value).trim();
    }
    return mediaAltFromFilename(file);
  }

  function fillModuleMediaAlt(container, file) {
    if (!container) return;
    var altInput = container.querySelector('.module-media-alt-input');
    if (!altInput || String(altInput.value || '').trim()) return;
    altInput.value = mediaAltFromForm(container, file);
  }

  window.initModuleMediaAltInputs = function(root) {
    root = root || document;
    root.querySelectorAll('.module-media-alt-input').forEach(function(input) {
      if (String(input.value || '').trim()) return;
    var container = input.closest('.module-media-field') || input.closest('.hero-slide-body') || input.closest('.mb-2') || input.parentElement;
      input.value = mediaAltFromForm(container, null);
    });
  };
  window.setTimeout(function(){ window.initModuleMediaAltInputs && window.initModuleMediaAltInputs(document); }, 0);

  window.handleModuleImageUpload = function(fileInput) {
    var file = fileInput.files[0];
    var container = fileInput.closest('.module-media-field, .dataset-media-field') || fileInput.closest('.hero-slide-body') || fileInput.closest('.mb-2');
    var picker = container ? container.querySelector('.module-media-picker') : null;
    if (!file || !picker) return;
    fillModuleMediaAlt(container, file);
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
      lbImg.style.cssText = 'max-width:95vw;max-height:95vh;object-fit:contain;background-color:#fff;background-image:linear-gradient(45deg,#eef2f7 25%,transparent 25%),linear-gradient(-45deg,#eef2f7 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#eef2f7 75%),linear-gradient(-45deg,transparent 75%,#eef2f7 75%);background-position:0 0,0 8px,8px -8px,-8px 0;background-size:16px 16px;border-radius: 0;padding:12px;box-shadow:0 4px 30px rgba(0,0,0,.5)';
      overlay.appendChild(lbImg);
      document.body.appendChild(overlay);
    }
    overlay.querySelector('img').src = src;
    overlay.style.display = 'flex';
  };

  // 图片预览：删除按閽竻除图鐗?
  window.clearModuleImage = function(btn) {
    var container = btn.closest('.module-media-field, .dataset-media-field') || btn.closest('.hero-slide-body') || btn.closest('.mb-2');
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
    var container = urlInput.closest('.module-media-field, .dataset-media-field') || urlInput.closest('.hero-slide-body') || urlInput.closest('.mb-2');
    var picker = container ? container.querySelector('.module-media-picker') : null;
    if (!picker) return;
    var fileInput = picker.querySelector('input[type=file]');
    renderModuleMediaPicker(picker, urlInput.value.trim(), fileInput ? fileInput.name : '', fileInput ? fileInput.getAttribute('accept') : '');
  };

  window.openModuleMediaLibrary = function(btn) {
    var container = btn.closest('.module-media-field, .dataset-media-field') || btn.closest('.module-media-url-row') || btn.closest('.hero-slide-body') || btn.closest('.mb-2');
    var row = btn.closest('.module-media-url-row');
    var urlInput = row ? row.querySelector('input[type="hidden"][name], input[type="text"][name]') : null;
    if (!urlInput && container) {
      urlInput = container.querySelector('.module-media-url-row input[type="hidden"][name], .module-media-url-row input[type="text"][name], input[type="hidden"][name], input[type="text"][name]');
    }
    if (!urlInput) return;
    var overlay = document.getElementById('moduleMediaLibraryOverlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'moduleMediaLibraryOverlay';
      overlay.className = 'module-media-library-overlay';
      overlay.innerHTML = '<div class="module-media-library-dialog">' +
        '<div class="module-media-library-head"><strong>选择媒体</strong><button type="button" class="module-media-library-close" title="关闭"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button></div>' +
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
    var packageTarget = !!(
      (container && container.querySelector('input[type="file"][accept*=".zip"]')) ||
      (urlInput && urlInput.name === 'embed_url')
    );
    fetch('/media?_fragment=1' + (site ? '&site=' + encodeURIComponent(site) : ''))
      .then(function(r) { return r.text(); })
      .then(function(html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var cards = Array.prototype.slice.call(doc.querySelectorAll('.media-card[data-url]'));
        var items = cards.filter(function(card) {
          return packageTarget
            ? card.dataset.category === 'package'
            : ['image', 'video'].indexOf(card.dataset.category) >= 0;
        }).map(function(card) {
          var url = card.dataset.url || '';
          var name = card.dataset.displayName || url;
          var isImage = card.dataset.category === 'image';
          var isPackage = card.dataset.category === 'package';
          return '<button type="button" class="module-media-library-item" data-url="' + attrEsc(url) + '" title="' + attrEsc(name) + '">' +
            (isImage ? '<img src="' + attrEsc(url) + '" alt="" loading="lazy">' : '<span class="module-media-library-video">' + (isPackage ? 'ZIP' : '▶') + '</span>') +
            '<span>' + schemaEsc(name) + '</span></button>';
        }).join('');
        grid.innerHTML = items || '<div class="text-muted small p-3">' + (packageTarget ? '媒体库暂无网页包' : '媒体库暂无可选图片或视频') + '</div>';
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
      'data_list_showcase': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="5" rx="1"/><rect x="3" y="14" width="18" height="5" rx="1"/><path d="M8 5v5"/><path d="M8 14v5"/></svg>',
      'stat_counter': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></svg>',
      'contact_info': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 9h6"/><path d="M9 13h4"/><circle cx="8.5" cy="8.5" r="0.5" fill="currentColor"/><circle cx="8.5" cy="12.5" r="0.5" fill="currentColor"/></svg>',
      'contact_form': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6l5-3 8 3 5-3v15l-5 3-8-3-5 3z"/><path d="M8 3v15M16 6v15"/><path d="M12 10a2 2 0 1 1 4 0c0 2-2 4-2 4s-2-2-2-4z"/></svg>',
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

  function buildModuleHTML(type, idx, mdata, variant) {
    mdata = mdata || {};
    var meta = findBlockMeta(type);
    var fields = meta.fields || [];
    var displayName = meta.display_name || type.replace(/_/g, ' ');
    var isDataModule = (type === 'item_data');
    var isDetailTplComponent = isDetailTemplateComponent(type);
    var variantLabel = variant || mdata.variant || 'default';
    var d = mdata;
    var isDsMode = !!(window._moduleCtx && window._moduleCtx.isDatasetMode);

    // 动态字段 (根据 meta.yaml fields 生成)
    // 过滤掉由 specialEditor 自动渲染的字段（分页配置銆乧olumns 等），避免在通用表单区重复出鐜?
    var pagerKeys = ['show_pagination', 'pagination_style', 'items_per_page', 'pager_align', 'show_view_all', 'pager'];
    var desktopFieldList = fields.filter(function(f) {
      if (isDetailTplComponent) return true;
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
    var useDatasetSchemaEditor = schemaManaged && isDsMode;

    /* 兼容旧高级编辑器的字段命名；数据详情页的新表单与渲染器统一使用
       data-* 模板声明的 heading / subheading / style_*。 */
    if (useDatasetSchemaEditor) {
      d = Object.assign({}, d);
      var schemaFieldNames = (meta.schema.fields || []).map(function(field) { return field.name || field.key; });
      if (schemaFieldNames.indexOf('heading') >= 0 && !d.heading && d.title) d.heading = d.title;
      if (schemaFieldNames.indexOf('subheading') >= 0 && !d.subheading && d.subtitle) d.subheading = d.subtitle;
      var schemaStyleTokens = (meta.schema.style_tokens || []).concat(meta.schema.element_style_tokens || []);
      if (schemaStyleTokens.indexOf('cols') >= 0 && !d.style_cols && d.columns) d.style_cols = d.columns;
      if (schemaStyleTokens.indexOf('bg-color') >= 0 && !d['style_bg-color'] && d.section_bg) {
        d['style_bg-color'] = d.section_bg;
      }
      if (type === 'logo_cloud' && Array.isArray(d.logos)) {
        d.logos = d.logos.map(function(item) {
          item = Object.assign({}, item || {});
          if (!item.logo && item.image) item.logo = item.image;
          return item;
        });
      }
    }

    if (schemaManaged) {
      var mergedSchema = getMergedSchema(meta);
      if (type === 'featured_picks') {
        var featuredEditors = featuredPicksEditors('module_' + idx + '_data_', meta, d);
        specialEditor = featuredEditors.content;
        styleEditor = featuredEditors.style;
      } else if (type === 'contact_info') {
        specialEditor = contactInfoEditor('module_' + idx + '_data_', d);
        styleEditor = schemaStyleForm('module_' + idx + '_data_', mergedSchema, d);
      } else {
        var previousModuleType = window._moduleCtx && window._moduleCtx.currentModuleType;
        if (window._moduleCtx) window._moduleCtx.currentModuleType = type;
        specialEditor = renderSchemaForm('module_' + idx + '_data_', mergedSchema, d);
        styleEditor = schemaStyleForm('module_' + idx + '_data_', mergedSchema, d);
        if (window._moduleCtx) window._moduleCtx.currentModuleType = previousModuleType || '';
      }
    }

    /* ====== item_data (详情数据) 特殊处理 ====== */
    if (useDatasetSchemaEditor) {
      /* 数据详情页中的声明式模块完全以模板 schema 为准。
         保留上面生成的内容表单与样式令牌，不再被旧硬编码编辑器覆盖。 */
    } else if (isDataModule && window._moduleCtx && window._moduleCtx.isDetailTemplateMode) {
      specialEditor =
        '<div class="small fw-semibold mb-1 text-muted">细节图</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + sel('module_' + idx + '_data_show_detail_images', '显示细节图', [{value:'true',label:'显示'}, {value:'false',label:'隐藏'}], d.show_detail_images || 'true') + '</div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">最多显示几张</label><input type="number" min="0" max="30" class="form-control form-control-sm" name="module_' + idx + '_data_detail_images_max" value="' + esc(d.detail_images_max || '6') + '"></div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_show_arrows', '显示箭头', [{value:'true',label:'显示'}, {value:'false',label:'隐藏'}], d.show_arrows || 'true') + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_show_dots', '显示圆点', [{value:'true',label:'显示'}, {value:'false',label:'隐藏'}], d.show_dots || 'true') + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_auto_scroll', '自动滚动', [{value:'false',label:'关闭'}, {value:'true',label:'开启'}], d.auto_scroll || 'false') + '</div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">滚动间隔秒</label><input type="number" min="1" max="60" class="form-control form-control-sm" name="module_' + idx + '_data_scroll_interval" value="' + esc(d.scroll_interval || '3') + '"></div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">规格表</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + sel('module_' + idx + '_data_show_specs', '显示规格表', [{value:'true',label:'显示'}, {value:'false',label:'隐藏'}], d.show_specs || 'true') + '</div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">最多显示几行</label><input type="number" min="0" max="100" class="form-control form-control-sm" name="module_' + idx + '_data_specs_max_rows" value="' + esc(d.specs_max_rows || '8') + '"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">表格列数</label><input type="number" min="1" max="6" class="form-control form-control-sm" name="module_' + idx + '_data_specs_columns" value="' + esc(d.specs_columns || '2') + '"></div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_hide_empty_rows', '空行处理', [{value:'true',label:'隐藏空行'}, {value:'false',label:'保留'}], d.hide_empty_rows || 'true') + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">链接</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + sel('module_' + idx + '_data_show_link', '显示链接', [{value:'true',label:'有链接时显示'}, {value:'false',label:'隐藏'}], d.show_link || 'true') + '</div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">默认链接文字</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_link_text" value="' + esc(d.link_text || '了解更多') + '"></div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">自动生成</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + sel('module_' + idx + '_data_auto_category', '分类', [{value:'inherit',label:'继承列表/手动覆盖'}, {value:'manual',label:'只手动'}], d.auto_category || 'inherit') + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_auto_tags', '标签', [{value:'suggest',label:'建议生成'}, {value:'manual',label:'只手动'}], d.auto_tags || 'suggest') + '</div>' +
        '</div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">颜色</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_text_color', '普通文字颜色', d.text_color || '#333333') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_link_color', '链接文字颜色', d.link_color || '#0f66d0') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_title_color', '标题颜色', d.title_color || '') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', '背景颜色', d.section_bg || '') + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">尺寸</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_image_radius', '图片圆角', ['px','rem','%'], d.image_radius || '') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_block_gap', '模块间距', ['px','rem'], d.block_gap || '') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_content_width', '内容宽度', ['px','%','rem'], d.content_width || '') + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_text_align', '对齐方式', [{value:'left',label:'左对齐'}, {value:'center',label:'居中'}, {value:'right',label:'右对齐'}], d.text_align || 'left') + '</div>' +
        '</div>';
    } else if (isDataModule) {
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
      var mediaType = item.media_type || (item.embed_url ? 'embed' : (item.video ? 'video' : 'image'));
      var mediaFields =
        renderField('', {key:'media_type', label:'媒体类型', type:'select', options:[{value:'image', label:'图片'}, {value:'video', label:'视频'}, {value:'embed', label:'嵌入页面'}]}, mediaType, '') +
        renderField('', {key:'cover', label:'图片', type:'image', show_if:{field:'media_type', value:'image'}}, coverVal, '图片 URL 或上传') +
        renderField('', {key:'video', label:'视频', type:'video', show_if:{field:'media_type', value:'video'}}, item.video || '', '视频 URL 或上传') +
        renderField('', {key:'embed_url', label:'嵌入页面', type:'embed', show_if:{field:'media_type', value:'embed'}}, item.embed_url || '', '上传网页包 ZIP');
      styleEditor = schemaStyleForm('module_' + idx + '_data_', meta.schema || {}, item);
      specialEditor =
        '<div class="small fw-semibold mb-1 text-muted">基础字段</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">slug <span class="text-danger">*</span></label><input type="text" class="form-control form-control-sm font-monospace" name="slug" value="' + esc(item.slug || '') + '" required minlength="3" maxlength="30" pattern="[a-z0-9][a-z0-9-]{1,28}[a-z0-9]" title="只能用小写字母、数字、连字符，3-30 字符，不能以连字符开头或结尾" placeholder="如 my-post"><div class="form-text">英文+数字+连字符，唯一标识</div></div>' +
        /* ==== 封面图：位于日期上方，只显示在数据集列表缩略图，不在详情页展示 ==== */
        mediaFields +
        detailGalleryHtml +
        '<hr class="my-2">' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">日期</label><input type="date" class="form-control form-control-sm" name="date" value="' + esc(item.date || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">名称</label><input type="text" class="form-control form-control-sm" name="name" value="' + esc(item.name || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">分类</label><input type="text" class="form-control form-control-sm" name="category" value="' + esc(item.category || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标题</label><input type="text" class="form-control form-control-sm" name="title" value="' + esc(item.title || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">简介</label>' + richEditorHtml('description', item.description || item.excerpt || item.summary || '') + '</div>' +
        '<div class="mb-2"><div class="d-flex align-items-center gap-2 mb-1"><label class="form-label small mb-0 text-muted">标签</label>' + visibilityEye('tags_visible', tagsVisible ? 'true' : 'false') + '</div><input type="text" class="form-control form-control-sm" name="tags" value="' + esc(tagsVal) + '" placeholder="多个标签用逗号分隔"><div class="form-text">例如：LED, 展示道具, 近期项目</div></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">价格</label><input type="text" class="form-control form-control-sm" name="price" value="' + esc(item.price || '') + '" placeholder="例如 ¥199 / $3/million"></div>' +
        '<hr class="my-2">' +
        /* 富文本编辑器（详细介绍）——与其他模块统一使用 richEditorHtml */
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">详细介绍</label>' +
        richEditorHtml('body', item.body || item.content || '') +
        '<input type="hidden" name="rte_clicked_editor_idx" value="">' +
        '<div class="form-text">支持加粗、斜体、标题、列表、引用、分割线、链接、图片、文字颜色</div>' +
        '<hr class="my-2">';
      // 动态剩余字段
      var skipKeys = ['id','slug','date','title','description','excerpt','summary','cover','image','photo','logo','media_type','video','embed_url','tags','tags_visible','detail_gallery','detail_images','body','content','modules','csrf_token','name','category','price','specs','section_bg','inner_width','style_bg-color'];
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
    if (schemaManaged) {
      /* 声明式模块保留 schema 生成的内容与样式面板，跳过整条旧模块编辑器分支。 */
    } else if (type === 'hero_banner') {
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
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪左>' +
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
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">描述文字</label>' + richEditorHtml('module_' + idx + '_data_desc', d.desc || '', true) + '</div>' +
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
          '<div class="col-6">' + un('module_' + idx + '_data_style_min-height', '最小高度', ['px','rem','vh'], d['style_min-height']) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_top" value="' + esc(d.margin_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_right" value="' + esc(d.margin_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_bottom" value="' + esc(d.margin_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_left" value="' + esc(d.margin_left) + '" placeholder="↪左>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top || '1rem') + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom || '1rem') + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪左>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 text-muted mt-2">内容层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内容层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪左>' +
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
      specialEditor = dataGridEditors(idx, d).specialEditor;
      // 每行个数与每页数量同属显示数量配置，统一放在内容页；样式页只保留视觉样式。
      var dataGridStyleSchema = Object.assign({}, getMergedSchema(meta));
      dataGridStyleSchema.style_tokens = (dataGridStyleSchema.style_tokens || []).filter(function(token) { return token !== 'cols'; });
      dataGridStyleSchema.element_style_tokens = (dataGridStyleSchema.element_style_tokens || []).filter(function(token) { return token !== 'cols'; });
      styleEditor = schemaStyleForm('module_' + idx + '_data_', dataGridStyleSchema, d);

    } else if (type === 'data_list_showcase') {
      specialEditor = dataListShowcaseEditors(idx, d).specialEditor;

    /* ====== feature_grid ====== */
    } else if (type === 'feature_grid' && !schemaManaged) {
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
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_top" value="' + esc(d.margin_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_right" value="' + esc(d.margin_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_bottom" value="' + esc(d.margin_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_left" value="' + esc(d.margin_left) + '" placeholder="↪左>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top || '1rem') + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom || '1rem') + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪左>' +
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
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">标题区边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_margin_top" value="' + esc(d.header_margin_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_margin_right" value="' + esc(d.header_margin_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_margin_bottom" value="' + esc(d.header_margin_bottom || '4rem') + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_margin_left" value="' + esc(d.header_margin_left) + '" placeholder="↪左>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">标题区内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_padding_top" value="' + esc(d.header_padding_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_padding_right" value="' + esc(d.header_padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_padding_bottom" value="' + esc(d.header_padding_bottom || '2rem') + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_padding_left" value="' + esc(d.header_padding_left) + '" placeholder="↪左>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">主标题?/div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_title_size', '标题字号', ['px','rem'], d.title_size || '2.25rem') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_title_color', '标题颜色', d.title_color || '#1e293b') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_title_margin_bottom', '标题下边距', ['px','rem'], d.title_margin_bottom || '0.5rem') + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">副标题</div>' +
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
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">卡片内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_padding_top" value="' + esc(d.card_padding_top || '2rem') + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_padding_right" value="' + esc(d.card_padding_right || '1.5rem') + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_padding_bottom" value="' + esc(d.card_padding_bottom || '2rem') + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_padding_left" value="' + esc(d.card_padding_left || '1.5rem') + '" placeholder="↪左>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">卡片圆角</div>' +
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
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">卡片标题</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_card_title_size', '标题字号', ['px','rem'], d.card_title_size || '1rem') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_card_title_color', '标题颜色', d.card_title_color || '#1e293b') + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_card_title_weight', '标题字重', [{value:'',label:'默认'},{value:'400',label:'400'},{value:'500',label:'500'},{value:'600',label:'600'},{value:'700',label:'700'}], d.card_title_weight || '600') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_card_title_margin_bottom', '标题下边距', ['px','rem'], d.card_title_margin_bottom || '0.5rem') + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">卡片描述</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_card_desc_size', '描述字号', ['px','rem'], d.card_desc_size || '0.875rem') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_card_desc_color', '描述颜色', d.card_desc_color || '#64748b') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_card_desc_line_height', '描述行高', ['rem',''], d.card_desc_line_height || '1.6') + '</div>' +
        '</div>';
      // 功能网格只开放模板声明的样式令牌（当前为每行列数）。
      // 上面的旧字段仅用于兼容已有数据，不再作为可编辑样式展示。
      styleEditor = schemaStyleForm('module_' + idx + '_data_', getMergedSchema(meta), d);

    /* ====== highlight_card ====== */
    } else if (type === 'highlight_card') {
      specialEditor =
        '<hr class="my-2">' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标签文字</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_tag" value="' + esc(d.tag || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">描述</label>' + richEditorHtml('module_' + idx + '_data_desc', d.desc || '', true) + '</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">图片</label>' + mediaUploadHtml('module_' + idx + '_data_image', d.image || '', 'image', '图片 URL', d.image_alt || d.alt || '') + '</div>' +
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
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_top" value="' + esc(d.margin_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_bottom" value="' + esc(d.margin_bottom) + '" placeholder="↪下>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">内容层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内容层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_border_radius', '圆角', ['px','rem','%'], d.border_radius) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪左>' +
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
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_top" value="' + esc(d.margin_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_right" value="' + esc(d.margin_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_bottom" value="' + esc(d.margin_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_left" value="' + esc(d.margin_left) + '" placeholder="↪左>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪左>' +
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
          return '<div class="border rounded p-2 mb-2 id-spec-item" data-spec-index="' + si + '"><div class="d-flex justify-content-between align-items-center mb-2"><span class="small fw-semibold">规格 ' + (si + 1) + '</span><button type="button" class="btn btn-sm btn-outline-danger" onclick="event.stopPropagation();this.closest(\'.id-spec-item\').remove();window._reindexIdSpecs(' + idx + ')">删除</button></div><div class="row g-2"><div class="col-6"><label class="form-label small mb-1 text-muted">参数名</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_specs_' + si + '_name" value="' + esc(name) + '"></div><div class="col-6"><label class="form-label small mb-1 text-muted">参数值?</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_specs_' + si + '_value" value="' + esc(value) + '"></div></div></div>';
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
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪左>' +
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
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪左>' +
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
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪左>' +
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
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪左>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>';

    /* ====== contact_form ====== */
    } else if (type === '__legacy_contact_form_editor') {
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
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="↪左>' +
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
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">表单内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_padding_top" value="' + esc(d.form_padding_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_padding_right" value="' + esc(d.form_padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_padding_bottom" value="' + esc(d.form_padding_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_padding_left" value="' + esc(d.form_padding_left) + '" placeholder="↪左>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">表单外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_margin_top" value="' + esc(d.form_margin_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_margin_right" value="' + esc(d.form_margin_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_margin_bottom" value="' + esc(d.form_margin_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_margin_left" value="' + esc(d.form_margin_left) + '" placeholder="↪左>' +
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
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">按钮内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_padding_top" value="' + esc(d.btn_padding_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_padding_right" value="' + esc(d.btn_padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_padding_bottom" value="' + esc(d.btn_padding_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_padding_left" value="' + esc(d.btn_padding_left) + '" placeholder="↪左>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">按钮外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_margin_top" value="' + esc(d.btn_margin_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_margin_right" value="' + esc(d.btn_margin_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_margin_bottom" value="' + esc(d.btn_margin_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_margin_left" value="' + esc(d.btn_margin_left) + '" placeholder="↪左>' +
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
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">地图外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_margin_top" value="' + esc(d.map_margin_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_margin_right" value="' + esc(d.map_margin_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_margin_bottom" value="' + esc(d.map_margin_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_margin_left" value="' + esc(d.map_margin_left) + '" placeholder="↪左>' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:12px">地图内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_padding_top" value="' + esc(d.map_padding_top) + '" placeholder="↪上>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_padding_right" value="' + esc(d.map_padding_right) + '" placeholder="↪右>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_padding_bottom" value="' + esc(d.map_padding_bottom) + '" placeholder="↪下>' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_padding_left" value="' + esc(d.map_padding_left) + '" placeholder="↪左>' +
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
        '<span class="module-title-group ' + titleColor + '"><span class="module-drag-handle" title="拖动排序" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="9" cy="7" r="1"/><circle cx="15" cy="7" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="9" cy="17" r="1"/><circle cx="15" cy="17" r="1"/></svg></span><svg class="module-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg><span class="module-order">' + (idx + 1) + '</span><span class="module-title-stack">' +
          '<span class="module-title-main">' + getBlockIconHTML(type) + ' ' + esc(displayName) + '</span>' +
          '<span class="module-title-meta">' + esc(variantLabel) + '</span>' +
        '</span></span>' +
        '<div class="d-flex gap-1 flex-shrink-0 flex-nowrap">' +
          '<button type="button" class="module-action-btn module-visibility-action" data-visible="' + ((d._hidden === true || String(d._hidden).toLowerCase() === 'true') ? 'false' : 'true') + '" title="' + ((d._hidden === true || String(d._hidden).toLowerCase() === 'true') ? '显示模块' : '隐藏模块') + '" aria-label="' + ((d._hidden === true || String(d._hidden).toLowerCase() === 'true') ? '显示模块' : '隐藏模块') + '" onclick="event.stopPropagation();window.toggleModuleVisibility(this)">' + ((d._hidden === true || String(d._hidden).toLowerCase() === 'true') ? window.EYE_OFF_SVG : window.EYE_OPEN_SVG) + '</button>' +
          '<button type="button" class="module-action-btn module-action-del" title="删除" onclick="event.stopPropagation();this.closest(\'.module-item\').remove();window._reindexModules()">' + detailGalleryIcon('trash') + '</button>' +
        '</div>' +
      '</div>' +
      '<input type="hidden" name="module_' + idx + '_type" value="' + esc(type) + '">' +
      '<input type="hidden" name="module_' + idx + '_variant" value="' + esc(variantLabel) + '">' +
      '<input type="hidden" name="module_' + idx + '_order" value="' + (idx + 1) + '">' +
      '<input type="hidden" class="module-root-hidden" name="module_' + idx + '_data__hidden" value="' + ((d._hidden === true || String(d._hidden).toLowerCase() === 'true') ? 'true' : 'false') + '">' +
      '<div class="module-config p-2 border-top" style="display:block">';

    if (isDetailTplComponent) {
      html += '<div class="device-config device-desktop detail-template-component-config">' +
        renderDetailTemplateComponentFields('module_' + idx + '_data_', desktopFieldList, d) +
      '</div>';
    } else if (!isDataModule) {
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
    if (!isDataModule && !isDetailTplComponent) {
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


  // data_grid 共享编辑器：页面编辑器和数据集编辑面板共用同一份表单 HTML
  function dataGridEditors(idx, d) {
    var datasetNames = (window._moduleCtx && window._moduleCtx.datasetNames) || [];
    var dsOptionsHtml = '';
    datasetNames.forEach(function(ds) {
      dsOptionsHtml += '<option value="' + esc(ds.target) + '"' + (d.dataset === ds.target ? ' selected' : '') + '>' + esc(ds.label) + ' (' + esc(ds.target) + ')</option>';
    });
    var specialEditor =
      // 区块标题/副标题——放在最上面，店主优先看到
      '<div class="mb-2"><label class="form-label small mb-1 text-muted">区块标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>' +
      '<div class="mb-2"><label class="form-label small mb-1 text-muted">副标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_subtitle" value="' + esc(d.subtitle || '') + '"></div>' +
      '<hr class="my-2">' +
      '<div class="small fw-semibold mb-1 text-muted">数据</div>' +
      '<div class="mb-2"><label class="form-label small mb-1 text-muted">数据来源</label>' +
        '<select class="form-select form-select-sm" data-no-segmented="1" name="module_' + idx + '_data_dataset">' +
        (dsOptionsHtml || '<option value="">暂无数据源</option>') +
        '</select></div>' +
      '<div class="mb-2"><label class="form-label small mb-1 text-muted">卡片布局</label>' +
        '<select class="form-select form-select-sm" name="module_' + idx + '_data_card_layout"><option value="image_top"' + (d.card_layout !== 'image_left' && d.card_layout !== 'image_right' ? ' selected' : '') + '>上图下文</option><option value="image_left"' + (d.card_layout === 'image_left' ? ' selected' : '') + '>左图右文</option><option value="image_right"' + (d.card_layout === 'image_right' ? ' selected' : '') + '>左文右图</option></select></div>' +
      '<div class="form-check form-switch mb-2">' +
        '<input class="form-check-input" type="checkbox" role="switch" id="module_' + idx + '_card_show_border"' +
        (d.card_show_border === 'false' ? '' : ' checked') +
        ' onchange="this.nextElementSibling.nextElementSibling.value=this.checked?\'true\':\'false\'">' +
        '<label class="form-check-label small" for="module_' + idx + '_card_show_border">显示卡片边框</label>' +
        '<input type="hidden" name="module_' + idx + '_data_card_show_border" value="' + (d.card_show_border === 'false' ? 'false' : 'true') + '">' +
      '</div>' +
      '<div class="form-check form-switch mb-2">' +
        '<input class="form-check-input" type="checkbox" role="switch" id="module_' + idx + '_show_detail_btn"' +
        (d.show_detail_btn === true || d.show_detail_btn === 'true' ? ' checked' : '') +
        ' onchange="this.nextElementSibling.nextElementSibling.value=this.checked?\'true\':\'false\'">' +
        '<label class="form-check-label small" for="module_' + idx + '_show_detail_btn">显示卡片按钮</label>' +
        '<input type="hidden" name="module_' + idx + '_data_show_detail_btn" value="' + (d.show_detail_btn === true || d.show_detail_btn === 'true' ? 'true' : 'false') + '">' +
      '</div>' +
      '<hr class="my-2">' +
      '<div class="small fw-semibold mb-1 text-muted">筛选</div>' +
      '<div class="form-check form-switch mb-2">' +
        '<input class="form-check-input" type="checkbox" role="switch" id="module_' + idx + '_show_filters"' +
        (d.show_filters === false || d.show_filters === 'false' ? '' : ' checked') +
        ' onchange="this.nextElementSibling.nextElementSibling.value=this.checked?\'true\':\'false\'">' +
        '<label class="form-check-label small" for="module_' + idx + '_show_filters">显示筛选</label>' +
        '<input type="hidden" name="module_' + idx + '_data_show_filters" value="' + (d.show_filters === false || d.show_filters === 'false' ? 'false' : 'true') + '">' +
      '</div>' +
      '<div class="form-check form-switch mb-2">' +
        '<input class="form-check-input" type="checkbox" role="switch" id="module_' + idx + '_show_search"' +
        (d.show_search === true || d.show_search === 'true' ? ' checked' : '') +
        ' onchange="this.nextElementSibling.nextElementSibling.value=this.checked?\'true\':\'false\'">' +
        '<label class="form-check-label small" for="module_' + idx + '_show_search">显示搜索框</label>' +
        '<input type="hidden" name="module_' + idx + '_data_show_search" value="' + (d.show_search === true || d.show_search === 'true' ? 'true' : 'false') + '">' +
      '</div>' +
      '<hr class="my-2">' +
      '<div class="small fw-semibold mb-1 text-muted">分页</div>' +
      '<div class="form-check form-switch mb-3">' +
        '<input class="form-check-input" type="checkbox" role="switch" id="module_' + idx + '_show_pagination"' +
        (d.show_pagination !== 'false' ? ' checked' : '') +
        ' onchange="this.nextElementSibling.nextElementSibling.value=this.checked?\'true\':\'false\'">' +
        '<label class="form-check-label small" for="module_' + idx + '_show_pagination">显示分页</label>' +
        '<input type="hidden" name="module_' + idx + '_data_show_pagination" value="' + (d.show_pagination !== 'false' ? 'true' : 'false') + '">' +
      '</div>' +
      '<div class="mb-2">' +
        '<label class="form-label small mb-1 text-muted">分页样式</label>' +
        '<select class="form-select form-select-sm" name="module_' + idx + '_data_pagination_style">' +
          '<option value="load_more"' + (d.pagination_style !== 'page_numbers' ? ' selected' : '') + '>加载更多</option>' +
          '<option value="page_numbers"' + (d.pagination_style === 'page_numbers' ? ' selected' : '') + '>页码导航</option>' +
        '</select></div>' +
      '<div class="row g-2 mb-2">' +
        '<div class="col-6"><label class="form-label small mb-1 text-muted">每页显示数量</label>' +
          '<input type="number" min="1" step="1" inputmode="numeric" class="form-control form-control-sm" name="module_' + idx + '_data_items_per_page" value="' + esc(d.items_per_page || '6') + '"></div>' +
        '<div class="col-6"><label class="form-label small mb-1 text-muted">每行个数</label>' +
          '<input type="number" min="1" step="1" inputmode="numeric" class="form-control form-control-sm" name="module_' + idx + '_data_style_cols" value="' + esc(d.style_cols || '3') + '"></div>' +
      '</div>' +
      '<div class="mb-2">' +
        '<label class="form-label small mb-1 text-muted">分页对齐</label>' +
        segmentedControl('module_' + idx + '_data_pager_align', [
          { value: 'left', label: '居左' },
          { value: 'center', label: '居中' },
          { value: 'right', label: '居右' }
        ], d.pager_align || 'center', esc) +
      '</div>';
    return { specialEditor: specialEditor };
  }

  /* ====== 对外暴露 ====== */
  function dataListShowcaseEditors(idx, d) {
    var datasetNames = (window._moduleCtx && window._moduleCtx.datasetNames) || [];
    var dsOptionsHtml = '';
    datasetNames.forEach(function(ds) {
      dsOptionsHtml += '<option value="' + esc(ds.target) + '"' + (d.dataset === ds.target ? ' selected' : '') + '>' + esc(ds.label) + ' (' + esc(ds.target) + ')</option>';
    });
    if (!d.dataset && datasetNames.length) {
      dsOptionsHtml = dsOptionsHtml.replace('<option value="' + esc(datasetNames[0].target) + '"', '<option value="' + esc(datasetNames[0].target) + '" selected');
    }
    function sw(key, label, defaultOn) {
      var checked = d[key] === undefined ? defaultOn : d[key] !== 'false';
      return '<div class="form-check form-switch mb-2">' +
        '<input class="form-check-input" type="checkbox" role="switch" id="module_' + idx + '_' + key + '"' +
        (checked ? ' checked' : '') +
        ' onchange="this.nextElementSibling.nextElementSibling.value=this.checked?\'true\':\'false\'">' +
        '<label class="form-check-label small" for="module_' + idx + '_' + key + '">' + label + '</label>' +
        '<input type="hidden" name="module_' + idx + '_data_' + key + '" value="' + (checked ? 'true' : 'false') + '">' +
      '</div>';
    }
    var specialEditor =
      '<div class="small fw-semibold mb-1 text-muted">数据</div>' +
      '<div class="mb-2"><label class="form-label small mb-1 text-muted">数据来源</label>' +
        '<select class="form-select form-select-sm" data-no-segmented="1" name="module_' + idx + '_data_dataset">' +
        (dsOptionsHtml || '<option value="">暂无数据源</option>') +
        '</select></div>' +
      '<div class="mb-2"><label class="form-label small mb-1 text-muted">最大显示数量</label>' +
        '<input type="number" min="1" class="form-control form-control-sm" name="module_' + idx + '_data_max_items" value="' + esc(d.max_items || '12') + '">' +
      '</div>' +
      '<hr class="my-2">' +
      '<div class="small fw-semibold mb-1 text-muted">搜索与筛选</div>' +
      sw('show_search', '显示搜索', true) +
      sw('show_filters', '显示筛选', true) +
      '<hr class="my-2">' +
      '<div class="small fw-semibold mb-1 text-muted">分页</div>' +
      sw('show_pagination', '显示分页', true) +
      '<div class="mb-2">' +
        '<label class="form-label small mb-1 text-muted">分页样式</label>' +
        '<select class="form-select form-select-sm" name="module_' + idx + '_data_pagination_style">' +
          '<option value="page_numbers"' + (d.pagination_style !== 'load_more' ? ' selected' : '') + '>页码导航</option>' +
          '<option value="load_more"' + (d.pagination_style === 'load_more' ? ' selected' : '') + '>加载更多</option>' +
        '</select></div>' +
      '<div class="mb-2">' +
        '<label class="form-label small mb-1 text-muted">每页显示数量</label>' +
        '<select class="form-select form-select-sm" name="module_' + idx + '_data_items_per_page">' +
          ['3','4','6','8','10','12'].map(function(n) { return '<option value="' + n + '"' + ((d.items_per_page || '6') === n ? ' selected' : '') + '>' + n + ' 条/页</option>'; }).join('') +
        '</select></div>' +
      '<div class="mb-2">' +
        '<label class="form-label small mb-1 text-muted">分页对齐</label>' +
        segmentedControl('module_' + idx + '_data_pager_align', [
          { value: 'left', label: '居左' },
          { value: 'center', label: '居中' },
          { value: 'right', label: '居右' }
        ], d.pager_align || 'center', esc) +
      '</div>' +
      sw('show_view_all', '显示查看全部', false) +
      sw('show_detail_btn', '显示"了解详情"按钮', true);
    return { specialEditor: specialEditor };
  }

  window._buildModuleHTML = buildModuleHTML;
  window.getMergedSchema = getMergedSchema;
  window._dataGridEditors = dataGridEditors;
  window._dataListShowcaseEditors = dataListShowcaseEditors;
  window._featuredPicksEditors = function(prefix, values) {
    return featuredPicksEditors(prefix, findBlockMeta('featured_picks'), values || {});
  };
  window._toggleModuleAccordion = toggleModuleAccordion;
  window.toggleModuleAccordion = toggleModuleAccordion;  // server 绔?onclick 引用此名
  window._updateModuleConditionalFields = updateConditionalFields;

  document.addEventListener('change', function(e) {
    if (!e.target || !e.target.name || e.target.name.indexOf('module_') !== 0) return;
    var scope = e.target.closest('.device-config') || e.target.closest('.module-item') || document;
    if (e.target.name.slice(-10) === 'media_type') enhanceCompactSelects(scope);
    updateConditionalFields(scope);
  });

  document.addEventListener('DOMContentLoaded', function() {
    enhanceCompactSelects(document);
    updateConditionalFields(document);
  });

  /* ====== 富文本编辑器 (RTE) ======
   * 核心策略：?
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

  function normalizeRteBlockArg(arg) {
    var tag = String(arg || 'p').replace(/[<>]/g, '').toLowerCase();
    if (!/^(p|h1|h2|h3|h4|h5|h6|blockquote)$/.test(tag)) tag = 'p';
    return '<' + tag + '>';
  }

  function replaceRteElementTag(el, tagName) {
    if (!el || !el.parentNode) return null;
    var next = document.createElement(tagName);
    while (el.firstChild) next.appendChild(el.firstChild);
    Array.prototype.slice.call(el.attributes || []).forEach(function(attr) {
      if (attr.name !== 'style' && attr.name !== 'class') next.setAttribute(attr.name, attr.value);
    });
    el.parentNode.replaceChild(next, el);
    return next;
  }

  function forceRteParagraph(rte) {
    var sel = window.getSelection();
    if (!rte || !sel || !sel.rangeCount) return;
    var range = sel.getRangeAt(0);
    var blocks = [];
    rte.querySelectorAll('h1,h2,h3,h4,h5,h6,blockquote').forEach(function(block) {
      if (range.intersectsNode && range.intersectsNode(block)) blocks.push(block);
    });
    if (!blocks.length) {
      var node = range.commonAncestorContainer;
      var el = node.nodeType === 1 ? node : node.parentElement;
      var block = el ? el.closest('h1,h2,h3,h4,h5,h6,blockquote') : null;
      if (block && rte.contains(block)) blocks.push(block);
    }
    blocks.forEach(function(block) {
      replaceRteElementTag(block, 'p');
    });
  }

  function runRteCommand(rte, cmd, arg) {
    if (cmd === 'formatBlock') {
      var blockArg = normalizeRteBlockArg(arg);
      document.execCommand('formatBlock', false, blockArg);
      if (blockArg === '<p>') forceRteParagraph(rte);
      return;
    }
    document.execCommand(cmd, false, arg);
  }

  function applyRteFontSize(rte, size) {
    if (!rte || !/^(12|14|16|18|20|24|28|32)$/.test(String(size || ''))) return;
    restoreRteSelection(rte, savedRangeInRte(rte));
    document.execCommand('fontSize', false, '7');
    rte.querySelectorAll('font[size="7"]').forEach(function(font) {
      font.removeAttribute('size');
      font.style.fontSize = size + 'px';
    });
    saveRteSelection(rte);
    syncRteBody(rte);
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

  function getRteTableRowCount(table) {
    return table ? table.querySelectorAll('tbody tr, tr').length : 0;
  }

  function ensureRteTableBody(table) {
    if (!table) return null;
    var tbody = table.querySelector('tbody');
    if (tbody) return tbody;
    tbody = document.createElement('tbody');
    Array.prototype.slice.call(table.querySelectorAll(':scope > tr')).forEach(function(row) {
      tbody.appendChild(row);
    });
    table.appendChild(tbody);
    return tbody;
  }

  function createRteTableCell(width) {
    var td = document.createElement('td');
    if (width) td.style.width = width;
    td.innerHTML = '<br>';
    return td;
  }

  function resizeRteTable(table, targetRows, targetCols) {
    if (!table) return;
    targetRows = Math.max(1, Math.min(parseInt(targetRows, 10) || 1, 50));
    targetCols = Math.max(1, Math.min(parseInt(targetCols, 10) || 1, 20));
    var tbody = ensureRteTableBody(table);
    if (!tbody) return;
    var widths = getRteTableWidths(table).split(',').filter(Boolean);
    while (tbody.children.length < targetRows) {
      var newRow = document.createElement('tr');
      for (var c = 0; c < targetCols; c++) newRow.appendChild(createRteTableCell(widths[c] || ''));
      tbody.appendChild(newRow);
    }
    while (tbody.children.length > targetRows) tbody.removeChild(tbody.lastElementChild);
    Array.prototype.forEach.call(tbody.querySelectorAll('tr'), function(row) {
      while (row.children.length < targetCols) row.appendChild(createRteTableCell(widths[row.children.length] || ''));
      while (row.children.length > targetCols) row.removeChild(row.lastElementChild);
    });
    var oldColgroup = table.querySelector('colgroup');
    if (oldColgroup) {
      while (oldColgroup.children.length < targetCols) oldColgroup.appendChild(document.createElement('col'));
      while (oldColgroup.children.length > targetCols) oldColgroup.removeChild(oldColgroup.lastElementChild);
    }
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

  // 直接插入指定行列的表格（默认等宽、有边框），由可视化网格选择器调用
  function insertRteTableGrid(rte, rows, cols) {
    rows = Math.max(1, Math.min(rows || 2, 20));
    cols = Math.max(1, Math.min(cols || 2, 10));
    restoreRteSelection(rte);
    var w = Math.round(100 / cols);
    var widths = [];
    for (var i = 0; i < cols; i++) widths.push(w + '%');
    var html = '<table style="width:100%;table-layout:fixed;border-collapse:collapse" data-rte-border="1" data-rte-widths="1">';
    html += buildRteColgroup(widths) + '<tbody>';
    for (var r = 0; r < rows; r++) {
      html += '<tr>';
      for (var c = 0; c < cols; c++) {
        html += '<td style="width:' + widths[c] + '"><br></td>';
      }
      html += '</tr>';
    }
    html += '</tbody></table><p><br></p>';
    document.execCommand('insertHTML', false, html);
    syncRteBody(rte);
  }

  // 显示可视化表格网格选择器（替代多次 prompt）
  function showTableGridPicker(rte, btn) {
    var wrapper = rte.closest('.rte-wrapper');
    if (!wrapper) return;
    // 如果已存在则先移除
    var existing = wrapper.querySelector('.rte-table-grid-popover');
    if (existing) { existing.remove(); return; }
    var MAX_COLS = 10, MAX_ROWS = 8;
    var popover = document.createElement('div');
    popover.className = 'rte-table-grid-popover';
    popover.style.cssText = 'position:absolute;z-index:99999;background:#fff;border:1px solid #dee2e6;border-radius: 0;box-shadow:0 6px 20px rgba(0,0,0,.15);padding:8px';
    var header = document.createElement('div');
    header.className = 'rte-table-grid-header';
    header.style.cssText = 'text-align:center;font-size:14px;color:#6c757d;margin-bottom:6px;font-weight:500';
    header.textContent = '拖选表格大小';
    popover.appendChild(header);
    var grid = document.createElement('div');
    grid.className = 'rte-table-grid';
    grid.style.cssText = 'display:grid;grid-template-columns:repeat(' + MAX_COLS + ', 22px);gap:2px';
    for (var r = 1; r <= MAX_ROWS; r++) {
      for (var c = 1; c <= MAX_COLS; c++) {
        var cell = document.createElement('div');
        cell.className = 'rte-table-grid-cell';
        cell.style.cssText = 'width:22px;height:22px;border:1px solid #e0e0e0;border-radius: 0;cursor:pointer;transition:background .08s';
        cell.dataset.row = r;
        cell.dataset.col = c;
        grid.appendChild(cell);
      }
    }
    popover.appendChild(grid);
    wrapper.appendChild(popover);
    // 定位在按钮下方
    if (window.getComputedStyle(wrapper).position === 'static') wrapper.style.position = 'relative';
    var btnRect = btn.getBoundingClientRect();
    var wrapperRect = wrapper.getBoundingClientRect();
    var popoverWidth = popover.offsetWidth || 248;
    var left = btnRect.left - wrapperRect.left;
    var maxLeft = Math.max(0, wrapper.clientWidth - popoverWidth - 8);
    left = Math.max(0, Math.min(left, maxLeft));
    popover.style.left = left + 'px';
    popover.style.top = (btnRect.bottom - wrapperRect.top + 4) + 'px';
    // hover highlight
    var hoverRow = 0, hoverCol = 0;
    function highlight() {
      grid.querySelectorAll('.rte-table-grid-cell').forEach(function(c) {
        var cr = parseInt(c.dataset.row), cc = parseInt(c.dataset.col);
        if (cr <= hoverRow && cc <= hoverCol) {
          c.style.background = 'var(--bs-primary, #0d6efd)';
          c.style.borderColor = 'var(--bs-primary, #0d6efd)';
        } else {
          c.style.background = '';
          c.style.borderColor = '#e0e0e0';
        }
      });
      header.textContent = hoverRow > 0 ? (hoverRow + '×' + hoverCol + ' 表格') : '拖选表格大小';
    }
    grid.addEventListener('mouseover', function(e) {
      var cell = e.target.closest('.rte-table-grid-cell');
      if (!cell) return;
      hoverRow = parseInt(cell.dataset.row);
      hoverCol = parseInt(cell.dataset.col);
      highlight();
    });
    grid.addEventListener('mouseleave', function() {
      hoverRow = 0; hoverCol = 0;
      highlight();
    });
    grid.addEventListener('click', function(e) {
      var cell = e.target.closest('.rte-table-grid-cell');
      if (!cell) return;
      popover.remove();
      insertRteTableGrid(rte, parseInt(cell.dataset.row), parseInt(cell.dataset.col));
    });
    // 点击外部关闭
    setTimeout(function() {
      var closeHandler = function(ev) {
        if (!popover.parentNode) { document.removeEventListener('click', closeHandler); return; }
        if (!popover.contains(ev.target) && ev.target !== btn) {
          popover.remove();
          document.removeEventListener('click', closeHandler);
        }
      };
      document.addEventListener('click', closeHandler);
    }, 50);
  }

  // 单个弹框编辑表格（列宽 + 边框），替代两次 prompt
  function editRteTable(rte) {
    restoreRteSelection(rte);
    var table = getRteTableAtSelection(rte);
    if (!table) {
      window.alert('请先将光标置于表格内');
      return;
    }
    var wrapper = rte.closest('.rte-wrapper');
    var overlay = ensureRteUrlOverlay(wrapper);
    if (!overlay) return;
    var rows = getRteTableRowCount(table);
    var cols = getRteTableColumnCount(table);
    var currentWidths = getRteTableWidths(table);
    var currentBorder = table.getAttribute('data-rte-border') !== '0';
    var titleEl = overlay.querySelector('.rte-url-dialog-title');
    var inputEl = overlay.querySelector('.rte-url-dialog-input');
    var confirmEl = overlay.querySelector('.rte-url-dialog-confirm');
    var dialog = overlay.querySelector('.rte-url-dialog');
    titleEl.textContent = '表格设置（' + rows + '×' + cols + '）';
    inputEl.value = currentWidths || '';
    inputEl.placeholder = '列宽，如 50,50，留空则等宽';
    confirmEl.textContent = '应用';

    var sizeRow = dialog.querySelector('.rte-table-dialog-size-row');
    if (!sizeRow) {
      sizeRow = document.createElement('div');
      sizeRow.className = 'rte-table-dialog-size-row d-flex align-items-center gap-2 mb-2';
      sizeRow.innerHTML =
        '<label style="font-size:14px;margin:0;flex:1">行数<input type="number" min="1" max="50" class="form-control form-control-sm rte-table-dialog-rows" style="margin-top:4px"></label>' +
        '<label style="font-size:14px;margin:0;flex:1">列数<input type="number" min="1" max="20" class="form-control form-control-sm rte-table-dialog-cols" style="margin-top:4px"></label>';
      inputEl.parentNode.insertBefore(sizeRow, inputEl);
    }
    sizeRow.style.display = '';
    var rowsInput = dialog.querySelector('.rte-table-dialog-rows');
    var colsInput = dialog.querySelector('.rte-table-dialog-cols');
    if (rowsInput) rowsInput.value = rows;
    if (colsInput) colsInput.value = cols;

    var borderRow = dialog.querySelector('.rte-table-dialog-border-row');
    if (!borderRow) {
      borderRow = document.createElement('div');
      borderRow.className = 'rte-table-dialog-border-row d-flex align-items-center gap-2 mt-2';
      borderRow.innerHTML = '<label style="font-size:14px;white-space:nowrap;margin:0"><input type="checkbox" class="rte-table-dialog-border-cb"> 显示表格边框</label>';
      inputEl.parentNode.insertBefore(borderRow, inputEl.nextSibling);
    }
    borderRow.style.display = '';
    var borderCb = dialog.querySelector('.rte-table-dialog-border-cb');
    if (borderCb) borderCb.checked = currentBorder;
    overlay.style.display = 'flex';
    overlay.dataset.rteMode = 'table';
    overlay.dataset.rteTableRows = rows;
    overlay.dataset.rteTableCols = cols;
    _rteDialogState = { rte: rte, mode: 'table', existingLink: null, range: savedRangeInRte(rte) };
    setTimeout(function() { if (rowsInput) rowsInput.focus(); }, 50);
  }
  function makeRteToolbarButton(className, label, title, html) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-sm btn-light rte-btn ' + className;
    btn.style.cssText = 'font-size:14px;line-height:1';
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
    // data-cmd 按钮的默认 tooltip
    var cmdTitles = {
      bold: '加粗 (Ctrl+B)', italic: '斜体 (Ctrl+I)', underline: '下划线 (Ctrl+U)', strikeThrough: '删除线',
      justifyLeft: '左对齐', justifyCenter: '居中', justifyRight: '右对齐',
      insertUnorderedList: '无序列表', insertOrderedList: '有序列表',
      indent: '增加缩进', outdent: '减少缩进',
      insertHorizontalRule: '分割线',
      subscript: '下标', superscript: '上标',
      removeFormat: '清除格式', undo: '撤销', redo: '重做'
    };
    toolbar.querySelectorAll('.rte-btn[data-cmd]').forEach(function(btn) {
      var title = null;
      // formatBlock 按钮根据 data-arg 决定 tooltip
      if (btn.dataset.cmd === 'formatBlock') {
        var arg = btn.dataset.arg || '';
        if (arg === 'h2') title = '二级标题';
        else if (arg === 'h3') title = '三级标题';
        else if (arg === 'h4') title = '四级标题';
        else if (arg === 'p') title = '正文段落';
        else if (arg === '<blockquote>') title = '引用块';
      } else {
        title = cmdTitles[btn.dataset.cmd];
      }
      if (title) {
        btn.title = title;
        btn.setAttribute('aria-label', title);
      }
    });
    var color = toolbar.querySelector('.rte-color-picker');
    if (color) color.title = '文字颜色';
    // 特定 class 按钮的 tooltip（无 data-cmd 的按钮）
    [
      ['.rte-table-btn', '插入表格（拖选大小）'],
      ['.rte-table-settings-btn', '表格设置（修改列宽/边框）'],
      ['.rte-link-btn', '插入链接 (Ctrl+K)'],
      ['.rte-image-btn', '插入图片链接'],
      ['.rte-upload-image-btn', '上传图片'],
      ['.rte-video-url-btn', '插入视频链接'],
      ['.rte-upload-video-btn', '上传视频'],
      ['.rte-media-library-btn', '从媒体库选择'],
      ['.rte-source-btn', '查看/编辑 HTML 源码']
    ].forEach(function(item) {
      var btn = toolbar.querySelector(item[0]);
      if (!btn) return;
      btn.title = item[1];
      btn.setAttribute('aria-label', item[1]);
    });
  }

  // 工具栏按钮已在 richEditorHtml 中完整生成，此处只做 tooltip 规范化
  function finalizeRteToolbar(wrapper, toolbar) {
    if (toolbar) normalizeRteToolbar(toolbar);
  }

  // 确保 RTE wrapper 有文件 input + 上传状态（工具栏按钮已在 richEditorHtml 中生成）
  function ensureRteUploadControls(rte) {
    var wrapper = rte && rte.closest('.rte-wrapper');
    if (!wrapper) return;
    var toolbar = wrapper.querySelector('.rte-toolbar');
    if (toolbar) normalizeRteToolbar(toolbar);  // 统一更新 tooltip

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
    if (!wrapper.querySelector('.rte-upload-status')) {
      var status = document.createElement('div');
      status.className = 'rte-upload-status small text-muted mb-1';
      status.style.display = 'none';
      wrapper.insertBefore(status, rte);
    }
  }

  function insertRteImage(rte, url) {
    restoreRteSelection(rte);
    var safeUrl = String(url || '').replace(/"/g, '&quot;');
    if (!safeUrl) return;
    document.execCommand('insertHTML', false, '<img src="' + safeUrl + '" style="max-width:100%;border-radius:0">');
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
      'border-radius: 0;font-size:14px;color:#888';
    toolbar.innerHTML = '<span>馃幀 视频</span>';

    var delBtn = document.createElement('button');
    delBtn.type = 'button';
    delBtn.className = 'rte-media-del';
    delBtn.setAttribute('contenteditable', 'false');
    delBtn.textContent = '✕?删除';
    delBtn.style.cssText = 'border:1px solid #ddd;background:#fff;color:#e74c3c;' +
      'border-radius: 0;cursor:pointer;font-size:14px;padding:1px 8px;line-height:1.6';
    toolbar.appendChild(delBtn);
    wrapper.appendChild(toolbar);

    var video = document.createElement('video');
    video.src = safeUrl;
    video.setAttribute('controls', '');
    video.setAttribute('playsinline', '');
    video.setAttribute('preload', 'metadata');
    video.style.cssText = 'max-width:100%;display:block;border-radius:0';
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

  /* 网页包：直接插入 iframe，不用包裹层 —— 预览/前端不残留编辑态 HTML */
  function insertRtePackage(rte, url, name) {
    restoreRteSelection(rte);
    var safeUrl = String(url || '').replace(/"/g, '&quot;');
    if (!safeUrl) return;

    var iframe = document.createElement('iframe');
    iframe.src = safeUrl;
    iframe.setAttribute('frameborder', '0');
    iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin');
    iframe.setAttribute('allowfullscreen', '');
    iframe.style.cssText = 'width:100%;aspect-ratio:16/9;display:block;border:none;border-radius: 0;margin:1rem 0';

    var sel = window.getSelection();
    if (sel.rangeCount) {
      var range = sel.getRangeAt(0);
      if (rte.contains(range.commonAncestorContainer)) {
        range.insertNode(iframe);
        range.setStartAfter(iframe);
        range.collapse(true);
        sel.removeAllRanges();
        sel.addRange(range);
      }
    }
    syncRteBody(rte);
  }

  function insertRteMediaFromLibrary(rte, url, category, name, range) {
    if (!rte || !url) return;
    restoreRteSelection(rte, range);
    var safeUrl = String(url || '').replace(/"/g, '&quot;');
    var safeName = String(name || url || 'media').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    if (category === 'image') {
      document.execCommand('insertHTML', false, '<img src="' + safeUrl + '" alt="' + safeName + '" style="max-width:100%;border-radius:0">');
    } else if (category === 'video') {
      insertRteVideo(rte, url);
      return;
    } else if (category === 'package') {
      insertRtePackage(rte, url, safeName);
      return;
    } else {
      document.execCommand('insertHTML', false, '<a href="' + safeUrl + '" target="_blank" rel="noopener">' + safeName + '</a>');
    }
    syncRteBody(rte);
  }


  // 注册鍦?document 上用事件委托，因涓wrapper 鏄姩鎬?DOM 节点銆?
  function openRteMediaLibrary(btn, rte) {
    if (!rte) return;
    saveRteSelection(rte);
    var overlay = document.getElementById('moduleMediaLibraryOverlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'moduleMediaLibraryOverlay';
      overlay.className = 'module-media-library-overlay';
      overlay.innerHTML = '<div class="module-media-library-dialog">' +
        '<div class="module-media-library-head"><strong>选择媒体</strong><button type="button" class="module-media-library-close" title="关闭"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button></div>' +
        '<div class="module-media-library-grid"><div class="text-muted small p-3">加载中...</div></div>' +
        '</div>';
      document.body.appendChild(overlay);
      overlay.addEventListener('click', function(e) {
        if (e.target === overlay || e.target.closest('.module-media-library-close')) {
          overlay.classList.remove('show');
        }
      });
    }
    overlay._targetInput = null;
    overlay._rteTarget = rte;
    overlay._rteRange = savedRangeInRte(rte);
    overlay.classList.add('show');
    var grid = overlay.querySelector('.module-media-library-grid');
    grid.innerHTML = '<div class="text-muted small p-3">加载中...</div>';
    var site = (typeof currentSiteParam === 'function' && currentSiteParam()) || new URLSearchParams(window.location.search).get('site') || '';
    fetch('/media?_fragment=1' + (site ? '&site=' + encodeURIComponent(site) : ''))
      .then(function(r) { return r.text(); })
      .then(function(html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var cards = Array.prototype.slice.call(doc.querySelectorAll('.media-card[data-url]'));
        var items = cards.map(function(card) {
          var url = card.dataset.url || '';
          var name = card.dataset.displayName || card.dataset.name || url;
          var category = card.dataset.category || 'other';
          var isImage = category === 'image';
          var isVideo = category === 'video';
          var icon = isVideo ? '▶' : (category === 'document' ? 'DOC' : (category === 'package' ? 'ZIP' : 'FILE'));
          return '<button type="button" class="module-media-library-item" data-url="' + attrEsc(url) + '" data-category="' + attrEsc(category) + '" data-name="' + attrEsc(name) + '" title="' + attrEsc(name) + '">' +
            (isImage ? '<img src="' + attrEsc(url) + '" alt="" loading="lazy">' : '<span class="module-media-library-video">' + icon + '</span>') +
            '<span>' + schemaEsc(name) + '</span></button>';
        }).join('');
        grid.innerHTML = items || '<div class="text-muted small p-3">媒体库暂无文件</div>';
      })
      .catch(function() {
        grid.innerHTML = '<div class="text-danger small p-3">媒体库加载失败</div>';
      });
  }

  document.addEventListener('click', function(e) {
    var item = e.target.closest('#moduleMediaLibraryOverlay .module-media-library-item');
    if (!item) return;
    var overlay = item.closest('#moduleMediaLibraryOverlay');
    if (!overlay || !overlay._rteTarget) return;
    e.preventDefault();
    e.stopPropagation();
    insertRteMediaFromLibrary(
      overlay._rteTarget,
      item.dataset.url || '',
      item.dataset.category || '',
      item.dataset.name || item.getAttribute('title') || '',
      overlay._rteRange
    );
    overlay._rteTarget = null;
    overlay._rteRange = null;
    overlay.classList.remove('show');
  }, true);
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
  // rte-toolbar 内的按钮点击 preventDefault，阻止编辑器失焦
  document.addEventListener('mousedown', function(e) {
    if (e.target.closest('.rte-toolbar .rte-btn, .rte-toolbar .rte-color-picker')) {
      e.preventDefault();
      return;
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
    } else if (btn.classList.contains('rte-media-library-btn')) {
      openRteMediaLibrary(btn, rte);
    } else if (btn.classList.contains('rte-table-btn')) {
      showTableGridPicker(rte, btn);
    } else if (btn.classList.contains('rte-table-settings-btn')) {
      editRteTable(rte);
    } else if (btn.classList.contains('rte-link-btn')) {
      openRtePopover(rte, 'link');
    } else if (btn.classList.contains('rte-image-btn')) {
      openRtePopover(rte, 'image');
    } else if (btn.classList.contains('rte-video-url-btn')) {
      openRtePopover(rte, 'video');
    } else if (btn.classList.contains('rte-source-btn')) {
      toggleRteSource(rte);
    } else {
      rte.focus();
      runRteCommand(rte, cmd, arg);
      syncRteBody(rte);
    }
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
      status.textContent = '视频上传中...';
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
          catch (err) { throw new Error('视频上传失败 (HTTP ' + r.status + ')'); }
          return { ok: r.ok, data: data };
        });
      })
      .then(function(result) {
        if (!result.ok || !result.data || !result.data.url) {
          throw new Error((result.data && result.data.error) || '视频上传失败');
        }
        insertRteVideo(rte, result.data.url);
        if (status) {
          status.textContent = '视频已插入';
          status.className = 'rte-upload-status small text-success mb-1';
          setTimeout(function() { status.style.display = 'none'; }, 1800);
        }
      })
      .catch(function(err) {
        if (status) {
          status.textContent = err.message || '视频上传失败';
          status.className = 'rte-upload-status small text-danger mb-1';
          status.style.display = '';
        } else {
          alert(err.message || '视频上传失败');
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

  document.addEventListener('change', function(e) {
    if (!e.target.classList.contains('rte-font-size-select')) return;
    var rte = e.target.closest('.rte-wrapper').querySelector('.rte-editor');
    if (!rte) rte = _lastRteEditor;
    if (!rte || !e.target.value) return;
    applyRteFontSize(rte, e.target.value);
    e.target.value = '';
  });

  // 编辑器内容变更 -> 同步到隐藏 textarea
  document.addEventListener('input', function(e) {
    var rte = e.target.closest('.rte-editor');
    if (rte) {
      saveRteSelection(rte);
      syncRteBody(rte);
    }
    // 源码视图 textarea 编辑时同步回提交表单
    var sourceTa = e.target.closest('.rte-source-ta');
    if (sourceTa) {
      var wrapper = sourceTa.closest('.rte-wrapper');
      var formTa = wrapper ? wrapper.querySelector('textarea[name]:not(.rte-source-ta)') : null;
      if (formTa) formTa.value = sourceTa.value;
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
      status.textContent = '图片上传中...';
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
            if (r.status === 401) throw new Error('请重新登录');
            if (r.status === 404) throw new Error('上传接口未找到，请重启 Flask 服务器并刷新管理页面');
            throw new Error('上传失败 (HTTP ' + r.status + ')，请刷新页面后重试');
          }
          return { ok: r.ok, data: data };
        });
      })
      .then(function(result) {
        if (!result.ok || !result.data || !result.data.url) {
          throw new Error((result.data && result.data.error) || '上传失败');
        }
        insertRteImage(rte, result.data.url);
        if (status) {
          status.textContent = '图片已插入';
          status.className = 'rte-upload-status small text-success mb-1';
          setTimeout(function() { status.style.display = 'none'; }, 1800);
        }
      })
      .catch(function(err) {
        if (status) {
          status.textContent = err.message || '上传失败';
          status.className = 'rte-upload-status small text-danger mb-1';
          status.style.display = '';
        } else {
          alert(err.message || '上传失败');
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
    // 弹窗含三标签页（外部链接 / 本站页面 / 媒体文件）+ 共用 URL 预览栏
    overlay.innerHTML =
      '<div class="rte-url-dialog" style="background:#fff;border-radius: 0;box-shadow:0 8px 32px rgba(0,0,0,.18);padding:20px;width:520px;max-width:92vw;max-height:85vh;display:flex;flex-direction:column">' +
        '<div class="rte-url-dialog-title small fw-semibold mb-3" style="font-size:14px;color:#343a40;flex-shrink:0"></div>' +
        // 标签页（仅 link 模式可见）
        '<div class="rte-url-tabs" style="display:none;flex-shrink:0;border-bottom:2px solid #e9ecef;margin-bottom:12px">' +
          '<button type="button" class="rte-url-tab active" data-rte-tab="url">外部链接</button>' +
          '<button type="button" class="rte-url-tab" data-rte-tab="pages">本站页面</button>' +
          '<button type="button" class="rte-url-tab" data-rte-tab="media">媒体文件</button>' +
        '</div>' +
        // 标签页内容区（可滚动）
        '<div class="rte-url-tab-body" style="flex:1;overflow-y:auto;min-height:0">' +
          '<div class="rte-url-tab-panel" data-rte-tab-panel="url">' +
            '<input type="text" class="form-control form-control-sm rte-url-dialog-input" placeholder="https://example.com">' +
          '</div>' +
          '<div class="rte-url-tab-panel" data-rte-tab-panel="pages" style="display:none">' +
            '<div class="rte-pages-list text-muted small py-4 text-center">加载中...</div>' +
          '</div>' +
          '<div class="rte-url-tab-panel" data-rte-tab-panel="media" style="display:none">' +
            '<div class="rte-media-picker-grid text-muted small py-4 text-center">加载中...</div>' +
          '</div>' +
        '</div>' +
        // URL 预览栏（三标签共用）：页面/媒体选中后自动填入，也可手动编辑
        '<div style="flex-shrink:0;margin-top:12px">' +
          '<label class="form-label small mb-1 text-muted" style="font-size:12px">目标地址</label>' +
          '<input type="text" class="form-control form-control-sm rte-url-dialog-input-preview" placeholder="选择页面或媒体后自动填入，也可手动输入" style="font-size:14px">' +
        '</div>' +
        '<div class="d-flex gap-2 mt-3 justify-content-end" style="flex-shrink:0">' +
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

    // 重置可能被表格设置修改的弹框状态
    delete overlay.dataset.rteMode;
    var sizeRow = overlay.querySelector('.rte-table-dialog-size-row');
    if (sizeRow) sizeRow.style.display = 'none';
    var borderRow = overlay.querySelector('.rte-table-dialog-border-row');
    if (borderRow) borderRow.style.display = 'none';

    var titleEl   = overlay.querySelector('.rte-url-dialog-title');
    // 外部链接标签页内的输入框（直接输入 URL）
    var urlInput  = overlay.querySelector('.rte-url-dialog-input');
    // 底部共用预览输入框（三标签共用，页面/媒体选中后自动填入）
    var previewInput = overlay.querySelector('.rte-url-dialog-input-preview');
    var confirmEl = overlay.querySelector('.rte-url-dialog-confirm');
    var tabsRow   = overlay.querySelector('.rte-url-tabs');

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
      : (mode === 'video' ? '插入视频链接' : '插入图片');

    // 标签页仅 link 模式显示
    if (mode === 'link' && tabsRow) {
      tabsRow.style.display = '';
      // 默认切到外部链接标签
      selectRteLinkTab(overlay, 'url');
    } else if (tabsRow) {
      tabsRow.style.display = 'none';
      // 非 link 模式：隐藏标签，直接显示输入区
      var allPanels = overlay.querySelectorAll('.rte-url-tab-panel');
      allPanels.forEach(function(p) { p.style.display = 'none'; });
      var urlPanel = overlay.querySelector('[data-rte-tab-panel="url"]');
      if (urlPanel) urlPanel.style.display = '';
    }

    // 共同预览输入框填入当前 URL
    if (urlInput) urlInput.value = currentUrl;
    if (previewInput) previewInput.value = currentUrl;
    if (mode === 'video') {
      if (urlInput) urlInput.placeholder = 'https://example.com/video.mp4';
      if (previewInput) previewInput.placeholder = 'https://example.com/video.mp4';
    } else {
      if (urlInput) urlInput.placeholder = mode === 'link' ? 'https://example.com' : 'https://example.com/pic.webp';
      if (previewInput) previewInput.placeholder = mode === 'link' ? '选择页面或媒体后自动填入，也可手动输入' : 'https://example.com/pic.webp';
    }
    confirmEl.textContent = mode === 'link' && existing ? '更新' : '确认';
    overlay.style.display = 'flex';

    // 焦点：link 模式放到外部链接输入框，其他模式放到通用输入框
    setTimeout(function() {
      var target = (mode === 'link' && urlInput) ? urlInput : (previewInput || urlInput);
      if (target) { target.focus(); target.select(); }
    }, 50);
  }

  // 切换链接弹窗的标签页（模块级函数，供 document 委托事件调用）
  function selectRteLinkTab(overlay, tabName) {
    // 更新标签高亮
    overlay.querySelectorAll('.rte-url-tab').forEach(function(t) {
      t.classList.toggle('active', t.dataset.rteTab === tabName);
    });
    // 切换面板
    overlay.querySelectorAll('.rte-url-tab-panel').forEach(function(p) {
      p.style.display = (p.dataset.rteTabPanel === tabName) ? '' : 'none';
    });
    // 外部链接标签：同步输入框 → 预览栏
    if (tabName === 'url') {
      var urlInput = overlay.querySelector('.rte-url-dialog-input');
      var previewInput = overlay.querySelector('.rte-url-dialog-input-preview');
      if (urlInput) {
        urlInput.addEventListener('input', function() {
          if (previewInput) previewInput.value = urlInput.value;
        });
        if (previewInput && !previewInput.value && urlInput.value) previewInput.value = urlInput.value;
      }
    }
    // 按需懒加载
    if (tabName === 'pages') loadRtePages(overlay);
    if (tabName === 'media') loadRteMedia(overlay);
  }

  // 加载本站页面列表到链接弹窗
  function loadRtePages(overlay) {
    if (overlay.dataset.rtePagesLoaded === '1') return;
    overlay.dataset.rtePagesLoaded = '1';
    var listEl = overlay.querySelector('.rte-pages-list');
    if (!listEl) return;
    listEl.innerHTML = '<span class="text-muted">加载中...</span>';
    var site = (typeof currentSiteParam === 'function' && currentSiteParam()) || new URLSearchParams(window.location.search).get('site') || '';
    fetch('/api/site/pages?site=' + encodeURIComponent(site))
      .then(function(r) { return r.json().then(function(d) { return { ok: r.ok, data: d }; }); })
      .then(function(result) {
        if (!result.ok || !result.data.pages || !result.data.pages.length) {
          listEl.innerHTML = '<span class="text-muted">暂无页面</span>';
          return;
        }
        var typeLabels = { home: '首页', page: '页面', list: '列表' };
        var items = result.data.pages.map(function(p) {
          return '<button type="button" class="rte-page-item" data-url="' + attrEsc(p.url) + '" title="' + attrEsc(p.label + ' — ' + p.url) + '">' +
            '<span class="rte-page-item-label">' + schemaEsc(p.label) + '</span>' +
            '<span class="rte-page-item-meta">' + (typeLabels[p.type] || p.type) + ' · ' + schemaEsc(p.url) + '</span>' +
          '</button>';
        }).join('');
        listEl.innerHTML = items;
      })
      .catch(function() {
        listEl.innerHTML = '<span class="text-danger">页面加载失败</span>';
      });
  }

  // 加载媒体文件网格到链接弹窗
  function loadRteMedia(overlay) {
    if (overlay.dataset.rteMediaLoaded === '1') return;
    overlay.dataset.rteMediaLoaded = '1';
    var gridEl = overlay.querySelector('.rte-media-picker-grid');
    if (!gridEl) return;
    gridEl.innerHTML = '<span class="text-muted">加载中...</span>';
    var site = (typeof currentSiteParam === 'function' && currentSiteParam()) || new URLSearchParams(window.location.search).get('site') || '';
    fetch('/media?_fragment=1' + (site ? '&site=' + encodeURIComponent(site) : ''))
      .then(function(r) { return r.text(); })
      .then(function(html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var cards = Array.prototype.slice.call(doc.querySelectorAll('.media-card[data-url]'));
        var items = cards.map(function(card) {
          var url = card.dataset.url || '';
          var name = card.dataset.displayName || card.dataset.name || url;
          var category = card.dataset.category || 'other';
          var icon = category === 'image' ? 'IMG' : (category === 'video' ? 'VID' : (category === 'document' ? 'DOC' : (category === 'package' ? 'ZIP' : 'FILE')));
          return '<button type="button" class="rte-media-picker-item" data-url="' + attrEsc(url) + '" title="' + attrEsc(name) + '">' +
            '<span class="rte-media-picker-badge">' + icon + '</span>' +
            '<span class="rte-media-picker-name">' + schemaEsc(name) + '</span>' +
          '</button>';
        }).join('');
        gridEl.innerHTML = items || '<span class="text-muted">媒体库暂无文件</span>';
      })
      .catch(function() {
        gridEl.innerHTML = '<span class="text-danger">媒体库加载失败</span>';
      });
  }

  // 确认（加锁防重复触发）
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.rte-url-dialog-confirm')) return;
    var overlay = e.target.closest('.rte-url-overlay');
    if (!overlay || overlay.style.display === 'none') return;
    var state = _rteDialogState;
    if (!state.rte) return;
    // 取底部预览输入框的值（link 模式三标签共用），兜底取外部链接输入框
    var previewInput = overlay.querySelector('.rte-url-dialog-input-preview');
    var urlInputEl = overlay.querySelector('.rte-url-dialog-input');
    var url = (previewInput ? previewInput.value : (urlInputEl ? urlInputEl.value : '')).trim();
    var rte = state.rte;
    // 先清除 state + 隐藏 overlay，再操作 DOM，防止任何重入
    _rteDialogState = { rte: null, mode: '', existingLink: null, range: null };
    overlay.style.display = 'none';

    restoreRteSelection(rte, state.range);

    if (state.mode === 'table') {
      var table = getRteTableAtSelection(rte);
      if (table) {
        var dialog = overlay.querySelector('.rte-url-dialog');
        var cb = dialog ? dialog.querySelector('.rte-table-dialog-border-cb') : null;
        var showBorder = cb ? cb.checked : true;
        var rowsInput = dialog ? dialog.querySelector('.rte-table-dialog-rows') : null;
        var colsInput = dialog ? dialog.querySelector('.rte-table-dialog-cols') : null;
        var rows = rowsInput ? rowsInput.value : overlay.dataset.rteTableRows;
        var cols = colsInput ? colsInput.value : overlay.dataset.rteTableCols;
        resizeRteTable(table, rows, cols);
        cols = getRteTableColumnCount(table);
        var widths = parseRteColumnWidths(url, cols);
        applyRteTableSettings(table, widths, showBorder);
      }
    } else if (state.mode === 'link') {
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
      // execCommand('insertImage') 行为不可靠（选区/浏览器差异会自动重复插入）
      // 改用 insertHTML 注入 <img> 标签，一次精确插入
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

  // 链接弹窗内标签页切换（委托）
  document.addEventListener('click', function(e) {
    var tabBtn = e.target.closest('.rte-url-tab');
    if (!tabBtn) return;
    var overlay = tabBtn.closest('.rte-url-overlay');
    if (!overlay) return;
    var tabName = tabBtn.dataset.rteTab;
    if (tabName) selectRteLinkTab(overlay, tabName);
  });

  // 链接弹窗内页面项点击 → 填入预览输入框
  document.addEventListener('click', function(e) {
    var item = e.target.closest('.rte-page-item');
    if (!item) return;
    var overlay = item.closest('.rte-url-overlay');
    if (!overlay) return;
    var previewInput = overlay.querySelector('.rte-url-dialog-input-preview');
    if (previewInput) previewInput.value = item.dataset.url || '';
    // 选中高亮
    overlay.querySelectorAll('.rte-page-item.selected').forEach(function(s) { s.classList.remove('selected'); });
    item.classList.add('selected');
  });

  // 链接弹窗内媒体项点击 → 填入预览输入框
  document.addEventListener('click', function(e) {
    var item = e.target.closest('.rte-media-picker-item');
    if (!item) return;
    var overlay = item.closest('.rte-url-overlay');
    if (!overlay) return;
    var previewInput = overlay.querySelector('.rte-url-dialog-input-preview');
    if (previewInput) previewInput.value = item.dataset.url || '';
    // 选中高亮
    overlay.querySelectorAll('.rte-media-picker-item.selected').forEach(function(s) { s.classList.remove('selected'); });
    item.classList.add('selected');
  });

  // Enter 确认（同时监听外部链接输入框和底部预览输入框）
  document.addEventListener('keydown', function(e) {
    if (e.key !== 'Enter') return;
    var input = e.target.closest('.rte-url-dialog-input') || e.target.closest('.rte-url-dialog-input-preview');
    if (!input) return;
    e.preventDefault();
    var overlay = input.closest('.rte-url-overlay');
    var confirm = overlay ? overlay.querySelector('.rte-url-dialog-confirm') : null;
    if (confirm) confirm.click();
  });

  // HTML 源码切换：在 contenteditable 与 textarea 之间切换
  function initModuleDragSort(container) {
    if (!container || container.dataset.moduleDragSortReady === '1') return;
    container.dataset.moduleDragSortReady = '1';
    var dragged = null;
    var suppressClick = false;
    container.addEventListener('click', function(event) {
      if (!suppressClick || !event.target.closest('.module-header')) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      suppressClick = false;
    }, true);
    container.addEventListener('pointerdown', function(event) {
      var header = event.target.closest('.module-header');
      if (!header || event.target.closest('button,a,input,select,textarea,label')) return;
      var item = header.closest('.module-item');
      if (item) item.draggable = true;
    });
    container.addEventListener('dragstart', function(event) {
      var item = event.target.closest('.module-item');
      if (!item || !item.draggable) { event.preventDefault(); return; }
      dragged = item;
      suppressClick = true;
      container.classList.add('module-list-sorting');
      item.classList.add('is-dragging');
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', item.dataset.moduleIndex || item.dataset.index || '');
    });
    container.addEventListener('dragover', function(event) {
      if (!dragged) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = 'move';
      var siblings = Array.prototype.slice.call(container.querySelectorAll(':scope > .module-item:not(.is-dragging)'));
      var next = siblings.find(function(item) {
        var rect = item.getBoundingClientRect();
        return event.clientY < rect.top + rect.height / 2;
      });
      container.insertBefore(dragged, next || null);
    });
    function finish() {
      if (!dragged) return;
      dragged.classList.remove('is-dragging');
      dragged.draggable = false;
      dragged = null;
      container.classList.remove('module-list-sorting');
      if (container.id === 'selectedModules' && typeof window.reindexModules === 'function') window.reindexModules();
      if (container.id === 'selectedModulesDs' && typeof window._reindexModules === 'function') window._reindexModules();
      window.setTimeout(function() { suppressClick = false; }, 180);
    }
    container.addEventListener('drop', function(event) { event.preventDefault(); finish(); });
    container.addEventListener('dragend', finish);
    document.addEventListener('pointerup', function() {
      container.querySelectorAll(':scope > .module-item[draggable="true"]:not(.is-dragging)').forEach(function(item) { item.draggable = false; });
    });
  }
  initModuleDragSort(document.getElementById('selectedModules'));
  initModuleDragSort(document.getElementById('selectedModulesDs'));

  function toggleRteSource(rte) {
    if (!rte) return;
    var wrapper = rte.closest('.rte-wrapper');
    if (!wrapper) return;
    var sourceTa = wrapper.querySelector('.rte-source-ta');
    if (!sourceTa) return;
    var formTa = wrapper.querySelector('textarea[name]:not(.rte-source-ta)');
    var isSource = !sourceTa.classList.contains('d-none') && window.getComputedStyle(sourceTa).display !== 'none';
    if (isSource) {
      rte.innerHTML = sourceTa.value;
      sourceTa.classList.add('d-none');
      rte.classList.remove('d-none');
      if (formTa) formTa.value = sourceTa.value;
    } else {
      sourceTa.value = rte.innerHTML;
      sourceTa.classList.remove('d-none');
      rte.classList.add('d-none');
      if (formTa) formTa.value = sourceTa.value;
      sourceTa.focus();
    }
    rte.style.display = '';
    sourceTa.style.display = '';
  }
  function syncRteBody(rte) {
    var wrapper = rte.closest('.rte-wrapper') || rte.parentElement;
    var ta = wrapper ? wrapper.querySelector('textarea[name]:not(.rte-source-ta)') : null;
    if (ta) ta.value = rte.innerHTML;
  }

  }
})();
