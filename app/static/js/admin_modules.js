/* admin_modules.js — 共享模块表单渲染
 *
 * 页面编辑器 (panel_page_edit.html) 和数据集编辑面板 (panel_data_list.html)
 * 共用此文件。每个模板在使用前定义好:
 *   window._moduleCtx.blockLibrary — 模块库列表
 *   window._moduleCtx.datasetNames — 数据集选项 (可选)
 *   window._moduleCtx.editItem   — 当前编辑条目 (item_data 模式, 可选)
 *   window._moduleCtx.isDatasetMode — 是否为数据集编辑模式
 *
 * 然后调用 window._buildModuleHTML(type, idx, mdata) 生成模块 HTML。
 * 返回值: { html, borderStyle, headerBg }
 *   - html: 模块内部 HTML (不含 .module-item 外框)
 *   - borderStyle / headerBg: 外框和内标题栏样式
 */

;(function() {
  'use strict';

  /* ====== 工具函数 ====== */

  function esc(s) {
    return String(s || '').replace(/[&<>'"]/g, function(c) {
      return { '&': '&', '<': '<', '>': '>', "'": '&#39;', '"': '"' }[c];
    });
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
      '<option value="">—</option>' + opts + '</select></div>';
  }

  function sel(name, ph, options, dv) {
    var h = '<label class="form-label small mb-1 text-muted">' + ph + '</label><select class="form-select form-select-sm" name="' + name + '">';
    options.forEach(function(o) {
      h += '<option value="' + esc(o.value) + '"' + (String(dv || '') === String(o.value) ? ' selected' : '') + '>' + esc(o.label) + '</option>';
    });
    return h + '</select>';
  }

  function schemaEsc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

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
      html += '<div class="mb-2"><label class="form-label small mb-1 text-muted">' + schemaEsc(def.label || token) + '</label>';
      if (def.control === 'select' || def.control === 'switch') {
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
      } else if (def.control === 'image') {
        html += '<input type="text" class="form-control form-control-sm" name="' + schemaEsc(name) + '" value="' + schemaEsc(val) + '" placeholder="背景图 URL" oninput="updateImagePreview(this)">' +
          '<label class="d-flex align-items-center gap-2 px-3 py-2 mt-1 rounded-2" style="border:1px dashed #cbd5e1;background:#f8fafc;cursor:pointer;font-size:12px;color:#64748b;transition:border-color .15s,background .15s" onmouseenter="this.style.borderColor=\'#94a3b8\';this.style.background=\'#f1f5f9\'" onmouseleave="this.style.borderColor=\'#cbd5e1\';this.style.background=\'#f8fafc\'">' +
          '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>上传背景图' +
          '<input type="file" name="' + schemaEsc(name) + '_file" accept="image/*" onchange="handleModuleImageUpload(this)" style="display:none"></label>';
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

  function renderField(prefix, field, value, placeholder) {
    var key = field.key, type = (field.type || 'text').toLowerCase(), html = '';
    var isImage = /(image|cover|background|media|photo|logo)/i.test(key);
    html += '<div class="mb-2"><label class="form-label small mb-1 text-muted">' + esc(field.label || key) + '</label>';
    if (isImage) {
      // 图片字段：URL 输入框 + 上传 UI + 预览
      html += '<input type="text" class="form-control form-control-sm" name="' + prefix + key + '" value="' + esc(value || '') + '" placeholder="' + esc(placeholder || '') + '" oninput="updateImagePreview(this)">';
      html += '<label class="d-flex align-items-center gap-2 mt-1 px-3 py-2 rounded-2" style="border:1px dashed #cbd5e1;background:#f8fafc;cursor:pointer;font-size:12px;color:#64748b;transition:border-color .15s,background .15s" onmouseenter="this.style.borderColor=\'#94a3b8\';this.style.background=\'#f1f5f9\'" onmouseleave="this.style.borderColor=\'#cbd5e1\';this.style.background=\'#f8fafc\'"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>上传图片<input type="file" name="' + prefix + key + '_file" accept="image/*" onchange="handleModuleImageUpload(this)" style="display:none"></label>';
      html += '<div class="form-text mt-1">支持 JPG/PNG/GIF/WebP，最大 12MB，上传后自动转 WebP</div>';
      html += '<div class="module-image-url-text mt-1" style="font-size:11px;color:#94a3b8;word-break:break-all;display:none"></div>';
      html += '<div class="mt-2 module-image-preview" style="display:none"><div style="position:relative;display:inline-block"><img src="" style="max-width:120px;max-height:90px;border-radius:4px;border:1px solid #dee2e6;cursor:pointer" onclick="enlargeImage(this)" onerror="this.parentElement.parentElement.style.display=\'none\'"><button type="button" class="btn btn-sm" onclick="clearModuleImage(this)" style="position:absolute;top:-8px;right:-8px;width:22px;height:22px;border-radius:50%;background:#dc3545;color:#fff;font-size:12px;line-height:1;padding:0;display:flex;align-items:center;justify-content:center" title="移除图片">&times;</button></div></div>';
    } else if (type === 'textarea') {
      html += '<textarea class="form-control form-control-sm" rows="4" name="' + prefix + key + '" placeholder="' + esc(placeholder || '') + '">' + esc(value || '') + '</textarea>';
    } else if (type === 'select') {
      html += '<select class="form-select form-select-sm" name="' + prefix + key + '"><option value="">请选择</option>';
      (field.options || []).forEach(function(opt) {
        var ov = typeof opt === 'object' ? opt.value : opt;
        var ol = typeof opt === 'object' ? (opt.label || opt.value) : opt;
        html += '<option value="' + esc(ov) + '"' + (String(value || '') === String(ov) ? ' selected' : '') + '>' + esc(ol) + '</option>';
      });
      html += '</select>';
    } else if (type === 'number') {
      html += '<input type="number" class="form-control form-control-sm" name="' + prefix + key + '" value="' + esc(value || '') + '" placeholder="' + esc(placeholder || '') + '">';
    } else {
      html += '<input type="text" class="form-control form-control-sm" name="' + prefix + key + '" value="' + esc(value || '') + '" placeholder="' + esc(placeholder || '') + '">';
    }
    return html + '</div>';
  }

  // 图片上传：选择文件后本地预览（全局函数，供动态生成的 onchange 调用）
  window.handleModuleImageUpload = function(fileInput) {
    var file = fileInput.files[0];
    var container = fileInput.closest('.hero-slide-body') || fileInput.closest('.mb-2');
    var preview = container ? container.querySelector('.module-image-preview') : null;
    var img = preview ? preview.querySelector('img') : null;
    var urlText = container ? container.querySelector('.module-image-url-text') : null;
    if (!file || !preview || !img) return;
    if (file.type.startsWith('image/')) {
      img.src = URL.createObjectURL(file);
      preview.style.display = '';
    }
    if (urlText) { urlText.textContent = file.name; urlText.style.display = ''; }
    img.onerror = function() { preview.style.display = 'none'; };
  };

  // 图片预览：点击放大
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
      lbImg.style.cssText = 'max-width:95vw;max-height:95vh;border-radius:6px;box-shadow:0 4px 30px rgba(0,0,0,.5)';
      overlay.appendChild(lbImg);
      document.body.appendChild(overlay);
    }
    overlay.querySelector('img').src = src;
    overlay.style.display = 'flex';
  };

  // 图片预览：删除按钮清除图片
  window.clearModuleImage = function(btn) {
    var container = btn.closest('.hero-slide-body') || btn.closest('.mb-2');
    if (!container) return;
    var urlInput = container.querySelector('input[type="hidden"]') || container.querySelector('input[type="text"]');
    var fileInput = container.querySelector('input[type="file"]');
    var urlText = container.querySelector('.module-image-url-text');
    var preview = container.querySelector('.module-image-preview');
    var img = preview ? preview.querySelector('img') : null;
    if (urlInput) urlInput.value = '';
    if (fileInput) fileInput.value = '';
    if (urlText) { urlText.textContent = ''; urlText.style.display = 'none'; }
    if (img) img.src = '';
    if (preview) preview.style.display = 'none';
  };

  // 图片预览：URL 输入框变化时更新预览
  window.updateImagePreview = function(urlInput) {
    var container = urlInput.closest('.hero-slide-body') || urlInput.closest('.mb-2');
    var preview = container ? container.querySelector('.module-image-preview') : null;
    var img = preview ? preview.querySelector('img') : null;
    if (!preview || !img) return;
    var url = urlInput.value.trim();
    if (url) {
      img.src = url;
      preview.style.display = '';
    } else {
      preview.style.display = 'none';
      img.src = '';
    }
  };

  /* ====== 对外暴露 ====== */
  window._cn = cn;
  window._un = un;
  window._esc = esc;
  window._renderField = renderField;

  // 模块图标映射 — 与 _block_icons.html 中 block_icon 宏保持一致
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
      'item_detail': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="18" rx="1"/><rect x="13" y="3" width="8" height="8" rx="1"/><path d="M13 15h4"/><path d="M13 19h6"/></svg>'
    };
    return icons[type] || '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M12 8v8"/><path d="M8 12h8"/></svg>';
  }

  /* ====== findBlockMeta ====== */

  function findBlockMeta(type) {
    var lib = (window._moduleCtx && window._moduleCtx.blockLibrary) || [];
    return lib.find(function(b) { return b.name === type; }) || {
      name: type, display_name: type.replace(/_/g, ' '), fields: [], variants: [{key:'default',label:'默认'}]
    };
  }

  /* ====== 主函数: buildModuleHTML ======
   * type:   模块类型名
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
    var needsResp = (type !== 'section_title' && type !== 'hero_banner' && type !== 'highlight_card' && type !== 'item_detail' && type !== 'text_content');
    var d = mdata;
    var isDsMode = !!(window._moduleCtx && window._moduleCtx.isDatasetMode);

    // 动态字段 (根据 meta.yaml fields 生成)
    var desktopFields = fields.map(function(f) { return renderField('module_' + idx + '_data_', f, d[f.key] || f.default || '', ''); }).join('');
    var tabletFields  = fields.map(function(f) { return renderField('module_' + idx + '_resp_tablet_data_', f, '', '继承电脑端'); }).join('');
    var mobileFields  = fields.map(function(f) { return renderField('module_' + idx + '_resp_mobile_data_', f, '', '继承电脑端'); }).join('');

    // 数据集来源选项
    var datasetNames = (window._moduleCtx && window._moduleCtx.datasetNames) || [];

    var specialEditor = '';
    var styleEditor = '';
    var borderStyle = '';
    var headerBg = '';
    var titleColor = '';

    /* ====== item_data (详情数据) 特殊处理 ====== */
    if (isDataModule) {
      var item = (window._moduleCtx && window._moduleCtx.editItem) || mdata || {};
      var tagsVal = (item.tags && Array.isArray(item.tags)) ? item.tags.join(', ') : (item.tags || '');
      styleEditor = schemaStyleForm('module_' + idx + '_data_', meta.schema || {}, item);
      specialEditor =
        '<div class="small fw-semibold mb-1 text-muted">内容字段</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">slug <span class="text-danger">*</span></label><input type="text" class="form-control form-control-sm font-monospace" name="slug" value="' + esc(item.slug || '') + '" required pattern="[a-z0-9][a-z0-9-]*[a-z0-9]" placeholder="如 my-post"><div class="form-text">英文+数字+连字符，唯一标识</div></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">日期</label><input type="date" class="form-control form-control-sm" name="date" value="' + esc(item.date || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标题</label><input type="text" class="form-control form-control-sm" name="title" value="' + esc(item.title || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">简述</label><textarea class="form-control form-control-sm" name="description" rows="2">' + esc(item.description || item.excerpt || item.summary || '') + '</textarea></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">预览图</label><input type="text" class="form-control form-control-sm" name="image" value="' + esc(item.image || item.cover || item.photo || '') + '" placeholder="图片 URL 或上传"><input type="file" class="form-control form-control-sm mt-1" name="image" accept="image/*"><div class="form-text">可粘贴 URL 或上传图片（自动转 WebP）</div></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标签</label><input type="text" class="form-control form-control-sm" name="tags" value="' + esc(tagsVal) + '" placeholder="多个用逗号或空格分隔"><div class="form-text">如：LED, 展示道具, 近期项目</div></div>' +
        '<hr class="my-2">' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">详细介绍</label><textarea class="form-control form-control-sm" name="body" rows="10" style="min-height:200px;font-family:monospace;white-space:pre-wrap;" placeholder="支持 Markdown 格式">' + esc(item.body || item.content || '') + '</textarea></div>';
      // 动态剩余字段
      var skipKeys = ['id','slug','date','title','description','excerpt','summary','cover','image','photo','logo','tags','body','content','modules','section_bg','inner_width','title_color','title_size','desc_color','desc_size','tag_color','tag_size','tag_bg','tag_radius','style_bg-color'];
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
    if (type === 'hero_banner') {
      specialEditor =
        '<hr class="my-2">' +
        '<div class="hero-slides-editor" data-module-index="' + idx + '"><div class="d-flex justify-content-between align-items-center mb-2"><div class="small fw-semibold text-primary">轮播媒体项</div><button type="button" class="btn btn-sm btn-outline-primary" onclick="window._addHeroSlide(' + idx + ')">+ 添加媒体项</button></div><input type="hidden" name="module_' + idx + '_slide_count" class="hero-slide-count" value="' + (d.slide_count || '1') + '"><div class="hero-slide-list">' + (window._heroSlideHtml ? window._heroSlideHtml(idx, 0, d) : '') + '</div></div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2 mb-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_hero_width', 'Banner 外层宽度', ['px','%','vw','rem'], d.hero_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_hero_height', 'Banner 高度', ['px','vh','rem','%'], d.hero_height) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_content_width', '内容区宽度', ['px','%','vw','rem'], d.content_width) + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_banner_align', 'Banner 文字排版', [{value:'',label:'默认（全宽）'},{value:'center',label:'居中'},{value:'left',label:'居左'},{value:'right',label:'居右'}], d.banner_align) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});">' +
            '<option value="px">px</option>' +
            '<option value="rem">rem</option>' +
          '</select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">遮罩层</div>' +
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
          '<div class="col-6">' + un('module_' + idx + '_data_subtitle_font_size', '副标题字体大小', ['px','rem'], d.subtitle_font_size) + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_subtitle_color', '副标题颜色', d.subtitle_color || '#cccccc') + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_btn_font_size', '按钮字体大小', ['px','rem'], d.btn_font_size) + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_text_color', '按钮文字颜色', d.btn_text_color || '#ffffff') + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_bg', '按钮背景色', d.btn_bg || '#067a7a') + '</div>' +
        '</div>';

    /* ====== section_title ====== */
    } else if (type === 'section_title') {
      specialEditor =
        '<div class="small fw-semibold mb-1 text-muted">内容</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标签文字</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_tag" value="' + esc(d.tag || '') + '" placeholder="模块上方小标签"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">描述文字</label><textarea class="form-control form-control-sm" rows="3" name="module_' + idx + '_data_desc">' + esc(d.desc || '') + '</textarea></div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">按钮</div>' +
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">按钮文字</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_btn_text" value="' + esc(d.btn_text || '') + '"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">按钮链接</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_btn_url" value="' + esc(d.btn_url || '') + '"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">打开方式</label><select class="form-select form-select-sm" name="module_' + idx + '_data_btn_target"><option value=""' + (d.btn_target !== '_blank' ? ' selected' : '') + '>当前窗口</option><option value="_blank"' + (d.btn_target === '_blank' ? ' selected' : '') + '>新窗口</option></select></div>' +
        '</div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', '外层背景色', d.section_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_top" value="' + esc(d.margin_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_right" value="' + esc(d.margin_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_bottom" value="' + esc(d.margin_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_left" value="' + esc(d.margin_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top || '1rem') + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom || '1rem') + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 text-muted mt-2">内层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="← 左">' +
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
          '<div class="col-6">' + cn('module_' + idx + '_data_tag_bg', '标签背景色', d.tag_bg || '#067a7a') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_tag_color', '标签字体色', d.tag_color || '#ffffff') + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">按钮颜色</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_bg', '按钮背景色', d.btn_bg || '#067a7a') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_color', '按钮文字色', d.btn_color || '#ffffff') + '</div>' +
        '</div>';

    /* ====== data_grid ====== */
    } else if (type === 'data_grid') {
      var dsOptionsHtml = '';
      datasetNames.forEach(function(ds) {
        dsOptionsHtml += '<option value="' + esc(ds.target) + '"' + (d.dataset === ds.target ? ' selected' : '') + '>' + esc(ds.label) + '（' + esc(ds.target) + '）</option>';
      });
      specialEditor =
        '<div class="small fw-semibold mb-1 text-muted">数据</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">数据来源</label>' +
          '<select class="form-select form-select-sm" name="module_' + idx + '_data_dataset">' +
          (dsOptionsHtml || '<option value="">暂无数据源</option>') +
          '</select></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">卡片布局</label>' +
          '<select class="form-select form-select-sm" name="module_' + idx + '_data_card_layout"><option value="image_top"' + (d.card_layout !== 'image_left' ? ' selected' : '') + '>上图下文</option><option value="image_left"' + (d.card_layout === 'image_left' ? ' selected' : '') + '>左图右文</option></select></div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">分页</div>' +
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">显示分页</label>' +
            '<select class="form-select form-select-sm" name="module_' + idx + '_data_show_pagination"><option value="true"' + (d.show_pagination !== 'false' ? ' selected' : '') + '>显示</option><option value="false"' + (d.show_pagination === 'false' ? ' selected' : '') + '>隐藏</option></select></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">分页样式</label>' +
            '<select class="form-select form-select-sm" name="module_' + idx + '_data_pagination_style"><option value="load_more"' + (d.pagination_style !== 'page_numbers' ? ' selected' : '') + '>加载更多</option><option value="page_numbers"' + (d.pagination_style === 'page_numbers' ? ' selected' : '') + '>页码导航</option></select></div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">每页显示数量</label><input type="number" class="form-control form-control-sm" name="module_' + idx + '_data_items_per_page" value="' + esc(d.items_per_page || '6') + '"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">分页对齐</label>' +
            '<select class="form-select form-select-sm" name="module_' + idx + '_data_pager_align"><option value="center"' + (d.pager_align === 'center' || !d.pager_align ? ' selected' : '') + '>居中</option><option value="left"' + (d.pager_align === 'left' ? ' selected' : '') + '>居左</option><option value="right"' + (d.pager_align === 'right' ? ' selected' : '') + '>居右</option></select></div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">内容</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">区块标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', '外层背景色', d.section_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_top" value="' + esc(d.margin_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_right" value="' + esc(d.margin_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_bottom" value="' + esc(d.margin_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_left" value="' + esc(d.margin_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>';

    /* ====== product_grid ====== */
    } else if (type === 'product_grid') {
      specialEditor =
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">最大显示数量</label><input type="number" class="form-control form-control-sm" name="module_' + idx + '_data_max_items" value="' + esc(d.max_items || '6') + '"></div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">区块标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', '外层背景色', d.section_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>';

    /* ====== feature_grid ====== */
    } else if (type === 'feature_grid') {
      var featCount = d.feature_count || '1';
      specialEditor =
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">区块标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title) + '" placeholder="如 产品特点"></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">区块副标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_subtitle" value="' + esc(d.subtitle) + '" placeholder="如 为什么选择我们"></div>' +
        '<div class="feature-items-editor" data-module-index="' + idx + '"><div class="d-flex justify-content-between align-items-center mb-2"><div class="small fw-semibold text-primary">功能卡片</div><button type="button" class="btn btn-sm btn-outline-primary" onclick="window._addFeatureItem(' + idx + ')">+ 添加功能卡片</button></div><input type="hidden" name="module_' + idx + '_feature_count" class="feature-item-count" value="' + featCount + '"><div class="feature-item-list">' + (window._featureItemHtml ? window._featureItemHtml(idx, 0, d) : '') + '</div></div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted mt-2">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', '外层背景色', d.section_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_top" value="' + esc(d.margin_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_right" value="' + esc(d.margin_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_bottom" value="' + esc(d.margin_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_left" value="' + esc(d.margin_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top || '1rem') + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom || '1rem') + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 text-muted mt-2">内层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 text-muted mt-2">标题区样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_header_bg', '标题区背景色', d.header_bg) + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_header_align', '标题区文字排版', [{value:'',label:'默认'},{value:'left',label:'左对齐'},{value:'center',label:'居中'},{value:'right',label:'右对齐'}], d.header_align || 'center') + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">标题区外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_margin_top" value="' + esc(d.header_margin_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_margin_right" value="' + esc(d.header_margin_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_margin_bottom" value="' + esc(d.header_margin_bottom || '4rem') + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_margin_left" value="' + esc(d.header_margin_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">标题区内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_padding_top" value="' + esc(d.header_padding_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_padding_right" value="' + esc(d.header_padding_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_padding_bottom" value="' + esc(d.header_padding_bottom || '2rem') + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_header_padding_left" value="' + esc(d.header_padding_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">主标题</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_title_size', '标题字号', ['px','rem'], d.title_size || '2.25rem') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_title_color', '标题颜色', d.title_color || '#1e293b') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_title_margin_bottom', '标题下外边距', ['px','rem'], d.title_margin_bottom || '0.5rem') + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">副标题</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_subtitle_size', '副标题字号', ['px','rem'], d.subtitle_size || '1.125rem') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_subtitle_color', '副标题颜色', d.subtitle_color || '#64748b') + '</div>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 text-muted mt-2">网格样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_grid_gap', '卡片间距', ['px','rem'], d.grid_gap || '2rem') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_grid_row_gap', '行间距', ['px','rem'], d.grid_row_gap) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_grid_column_gap', '列间距', ['px','rem'], d.grid_column_gap) + '</div>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 text-muted mt-2">卡片样式</div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">显示边框</label><select class="form-select form-select-sm" name="module_' + idx + '_data_card_show_border"><option value=""' + (d.card_show_border !== '0' ? ' selected' : '') + '>默认（显示）</option><option value="0"' + (d.card_show_border === '0' ? ' selected' : '') + '>隐藏边框</option></select></div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">卡片内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_padding_top" value="' + esc(d.card_padding_top || '2rem') + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_padding_right" value="' + esc(d.card_padding_right || '1.5rem') + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_padding_bottom" value="' + esc(d.card_padding_bottom || '2rem') + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_padding_left" value="' + esc(d.card_padding_left || '1.5rem') + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">卡片圆角</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_radius_top_left" value="' + esc(d.card_radius_top_left || '12px') + '" placeholder="↖ 左上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_radius_top_right" value="' + esc(d.card_radius_top_right || '12px') + '" placeholder="↗ 右上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_radius_bottom_right" value="' + esc(d.card_radius_bottom_right || '12px') + '" placeholder="↘ 右下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_radius_bottom_left" value="' + esc(d.card_radius_bottom_left || '12px') + '" placeholder="↙ 左下">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option><option value=\"%\">%</option></select>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 text-muted mt-2">图标样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_icon_size', '图标大小', ['px','rem'], d.icon_size || '56px') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_icon_color', '图标颜色', d.icon_color || '#067a7a') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_icon_bg', '图标背景色', d.icon_bg) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_icon_width', '图标区宽度', ['px','rem'], d.icon_width || '56px') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_icon_height', '图标区高度', ['px','rem'], d.icon_height || '56px') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_icon_radius', '图标圆角', ['px','%'], d.icon_radius || '8px') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_icon_margin_right', '图标右外边距', ['px','rem'], d.icon_margin_right) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_icon_margin_bottom', '图标下外边距', ['px','rem'], d.icon_margin_bottom || '0.25rem') + '</div>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 text-muted mt-2">卡片文字样式</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">卡片标题</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_card_title_size', '标题字号', ['px','rem'], d.card_title_size || '1rem') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_card_title_color', '标题颜色', d.card_title_color || '#1e293b') + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_card_title_weight', '标题字重', [{value:'',label:'默认'},{value:'400',label:'400'},{value:'500',label:'500'},{value:'600',label:'600'},{value:'700',label:'700'}], d.card_title_weight || '600') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_card_title_margin_bottom', '标题下外边距', ['px','rem'], d.card_title_margin_bottom || '0.5rem') + '</div>' +
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
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">描述</label><textarea class="form-control form-control-sm" rows="3" name="module_' + idx + '_data_desc">' + esc(d.desc || '') + '</textarea></div>' +
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">图片</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_image" value="' + esc(d.image || '') + '" placeholder="图片 URL"><input type="file" class="form-control form-control-sm mt-1" name="module_' + idx + '_data_image_file" accept="image/*"><div class="form-text">上传后自动转 WebP 并覆盖该字段</div></div>' +
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">主按钮文字</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_primaryBtn" value="' + esc(d.primaryBtn || '') + '"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">主按钮链接</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_primaryLink" value="' + esc(d.primaryLink || '') + '"></div>' +
        '</div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', '外层背景色', d.section_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_top" value="' + esc(d.margin_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_bottom" value="' + esc(d.margin_bottom) + '" placeholder="↓ 下">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">内层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_border_radius', '圆角', ['px','rem','%'], d.border_radius) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="← 左">' +
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
          '<div class="col-6">' + cn('module_' + idx + '_data_tag_bg', '标签背景色', d.tag_bg || '#067a7a') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_tag_color', '标签字体色', d.tag_color || '#ffffff') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_bg', '按钮背景色', d.btn_bg || '#067a7a') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_color', '按钮字体色', d.btn_color || '#ffffff') + '</div>' +
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
          '<button type="button" class="btn btn-sm btn-outline-secondary py-1 px-2" onmousedown="var u=prompt(\'链接地址\');if(u){document.execCommand(\'createLink\',false,u)};event.preventDefault()" title="插入链接" style="font-size:12px;line-height:1">🔗</button>' +
        '</div>' +
        '<div contenteditable="true" class="rich-editor-body form-control form-control-sm" style="border-radius:0 0 4px 4px;min-height:150px;max-height:400px;overflow-y:auto" oninput="this.nextElementSibling.value=this.innerHTML">' + (d.body || '') + '</div>' +
        '<textarea class="form-control form-control-sm d-none" name="module_' + idx + '_data_body">' + esc(d.body || '') + '</textarea></div>';
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
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', '外层背景色', d.section_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_top" value="' + esc(d.margin_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_right" value="' + esc(d.margin_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_bottom" value="' + esc(d.margin_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_margin_left" value="' + esc(d.margin_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="← 左">' +
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
        '<div class="mb-2"><label class="form-label small mb-1 text-muted">描述</label><textarea class="form-control form-control-sm" rows="3" name="module_' + idx + '_data_desc">' + esc(d.desc || d.description || '') + '</textarea></div>' +
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
          return '<div class="border rounded p-2 mb-2 id-spec-item" data-spec-index="' + si + '"><div class="d-flex justify-content-between align-items-center mb-2"><span class="small fw-semibold">规格 ' + (si + 1) + '</span><button type="button" class="btn btn-sm btn-outline-danger" onclick="event.stopPropagation();this.closest(\'.id-spec-item\').remove();window._reindexIdSpecs(' + idx + ')">删除</button></div><div class="row g-2"><div class="col-6"><label class="form-label small mb-1 text-muted">参数名</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_specs_' + si + '_name" value="' + esc(name) + '"></div><div class="col-6"><label class="form-label small mb-1 text-muted">参数值</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_specs_' + si + '_value" value="' + esc(value) + '"></div></div></div>';
        }).join('') +
        '</div></div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', '外层背景色', d.section_bg || '#ffffff') + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">内层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_inner_bg', '内层背景色', d.inner_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="← 左">' +
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
          '<div class="col-6">' + cn('module_' + idx + '_data_tag_bg', '标签背景色', d.tag_bg || '#067a7a') + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_tag_color', '标签字体色', d.tag_color || '#ffffff') + '</div>' +
        '</div>';

    /* ====== stat_counter ====== */
    } else if (type === 'stat_counter') {
      specialEditor =
        '<div class="stat-items-editor" data-module-index="' + idx + '"><div class="d-flex justify-content-between align-items-center mb-2"><div class="small fw-semibold text-primary">统计项</div><button type="button" class="btn btn-sm btn-outline-primary" onclick="window._addStatItem(' + idx + ')">+ 添加统计项</button></div><input type="hidden" name="module_' + idx + '_stat_count" class="stat-item-count" value="' + (d.stat_count || '1') + '"><div class="stat-item-list">' + (window._statItemHtml ? window._statItemHtml(idx, 0, d) : '') + '</div></div>' +
        '<hr class="my-2">' +
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">区块标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_title" value="' + esc(d.title || '') + '"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">区块副标题</label><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_subtitle" value="' + esc(d.subtitle || '') + '"></div>' +
        '</div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', '外层背景色', d.section_bg || '#f5f7fa') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="row g-2">' +
          '<div class="col-6">' + sel('module_' + idx + '_data_columns', '每行列数', [{value:'4',label:'四列'},{value:'3',label:'三列'},{value:'6',label:'六列'}], d.columns || '4') + '</div>' +
        '</div>';

    /* ====== logo_cloud ====== */
    } else if (type === 'logo_cloud') {
      specialEditor =
        '<div class="logo-items-editor" data-module-index="' + idx + '"><div class="d-flex justify-content-between align-items-center mb-2"><div class="small fw-semibold text-primary">Logo 列表</div><button type="button" class="btn btn-sm btn-outline-primary" onclick="window._addLogoItem(' + idx + ')">+ 添加 Logo</button></div><input type="hidden" name="module_' + idx + '_logo_count" class="logo-item-count" value="' + (d.logo_count || '1') + '"><div class="logo-item-list">' + (window._logoItemHtml ? window._logoItemHtml(idx, 0, d) : '') + '</div></div>' +
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
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', '外层背景色', d.section_bg || '#f5f7fa') + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">内层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_inner_bg', '内层背景色', d.inner_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option><option value="%">%</option></select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">Logo 卡片样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_logo_bg', '卡片背景色', d.logo_bg || '#ffffff') + '</div>' +
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
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', '外层背景色', d.section_bg || '#f5f7fa') + '</div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">内层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_inner_bg', '内层背景色', d.inner_bg || '#ffffff') + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_outer_width', '外层宽度', ['px','%','rem'], d.outer_width) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="← 左">' +
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
          '<div class="col-6">' + cn('module_' + idx + '_data_number_bg', '序号背景色', d.number_bg || '#067a7a') + '</div>' +
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
        '<hr class="my-2">' +
        '<div class="row g-2">' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">每行列数</label><input type="number" class="form-control form-control-sm" name="module_' + idx + '_resp_columns" value="' + esc(d.columns || '') + '" placeholder="默认" min="1" max="6"></div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">每页显示数量</label><input type="number" class="form-control form-control-sm" name="module_' + idx + '_resp_items_per_page" value="' + esc(d.items_per_page || '') + '" placeholder="默认"></div>' +
        '</div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', '外层背景色', d.section_bg) + '</div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">外层宽度 <span class="text-muted" style="font-weight:normal;">（留空使用全局宽度）</span></label><div class="input-group input-group-sm"><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_outer_width" value="' + esc(d.outer_width || '') + '" placeholder="如 1200px" style="width:60%"><select class="form-select form-select-sm" style="width:40%" onchange="var inp=this.parentElement.querySelector(\'[name=&quot;module_' + idx + '_data_outer_width&quot;]\');if(inp){var v=inp.value.replace(/px|rem|%$/i,\'\').trim();var u=this.value;if(v&&u)inp.value=v+u;}"><option value="">—</option><option value="px">px</option><option value="%">%</option><option value="rem">rem</option></select></div></div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">内层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="← 左">' +
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
          '<div class="col-12"><label class="form-label small mb-1 text-muted">表单提交地址</label><input type="url" class="form-control form-control-sm" name="module_' + idx + '_data_form_action" value="' + esc(d.form_action || '') + '" placeholder="如 https://formspree.io/f/your-form-id"></div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-2 text-muted">表单字段</div>' +
        '<div class="d-flex flex-wrap gap-2">' +
          visToggle('module_' + idx + '_data_show_name', '姓名', (d.show_name || 'true')) +
          visToggle('module_' + idx + '_data_show_email', '邮箱', (d.show_email || 'true')) +
          visToggle('module_' + idx + '_data_show_phone', '电话', (d.show_phone || 'true')) +
          visToggle('module_' + idx + '_data_show_company', '公司', (d.show_company || 'false')) +
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
          '<div class="col-12"><label class="form-label small mb-1 text-muted">地图嵌入地址</label><input type="url" class="form-control form-control-sm" name="module_' + idx + '_data_map_src" value="' + esc(d.map_src || '') + '" placeholder="从高德/Google 地图获取的嵌入链接（iframe src）"></div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + sel('module_' + idx + '_data_layout', '排版方式', [{value:'form_left',label:'表单左 地图右'},{value:'form_right',label:'地图左 表单右'}], d.layout || 'form_left') + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_map_width_ratio', '地图占比', [{value:'30',label:'30%'},{value:'35',label:'35%'},{value:'40',label:'40%'},{value:'45',label:'45%'},{value:'50',label:'50%'},{value:'60',label:'60%'},{value:'70',label:'70%'},{value:'100',label:'100%'}], d.map_width_ratio || '40') + '</div>' +
        '</div>';
      styleEditor =
        '<div class="small fw-semibold mb-1 text-muted">外层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_section_bg', '外层背景色', d.section_bg) + '</div>' +
          '<div class="col-6"><label class="form-label small mb-1 text-muted">外层宽度</label><div class="input-group input-group-sm"><input type="text" class="form-control form-control-sm" name="module_' + idx + '_data_outer_width" value="' + esc(d.outer_width || '') + '" placeholder="如 1200px" style="width:60%"><select class="form-select form-select-sm" style="width:40%" onchange="var inp=this.parentElement.querySelector(\'[name=&quot;module_' + idx + '_data_outer_width&quot;]\');if(inp){var v=inp.value.replace(/px|rem|%$/i,\'\').trim();var u=this.value;if(v&&u)inp.value=v+u;}"><option value="">—</option><option value="px">px</option><option value="%">%</option><option value="rem">rem</option></select></div></div>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">内层样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_inner_width', '内层宽度', ['px','%','rem'], d.inner_width) + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_top" value="' + esc(d.padding_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_right" value="' + esc(d.padding_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_bottom" value="' + esc(d.padding_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_padding_left" value="' + esc(d.padding_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">表单样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_form_bg', '表单背景色', d.form_bg) + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_input_bg', '输入框背景色', d.input_bg) + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_input_border', '输入框边框色', d.input_border) + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_text_color', '文字颜色', d.text_color) + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_input_radius', '输入框圆角', ['px','rem','%'], d.input_radius) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_form_radius', '表单圆角', ['px','rem','%'], d.form_radius) + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_title_size', '标题字号', ['px','rem','em'], d.title_size) + '</div>' +
          '<div class="col-6">' + un('module_' + idx + '_data_input_height', '输入框高度', ['px','rem'], d.input_height) + '</div>' +
        '</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + un('module_' + idx + '_data_field_gap', '字段间距', ['px','rem'], d.field_gap) + '</div>' +
          '<div class="col-6">' + sel('module_' + idx + '_data_label_style', '标签排版', [{value:'top',label:'标签在上'},{value:'left',label:'标签在左'},{value:'hidden',label:'隐藏标签'}], d.label_style || 'top') + '</div>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">表单内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_padding_top" value="' + esc(d.form_padding_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_padding_right" value="' + esc(d.form_padding_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_padding_bottom" value="' + esc(d.form_padding_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_padding_left" value="' + esc(d.form_padding_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">表单外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_margin_top" value="' + esc(d.form_margin_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_margin_right" value="' + esc(d.form_margin_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_margin_bottom" value="' + esc(d.form_margin_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_form_margin_left" value="' + esc(d.form_margin_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<hr class="my-2">' +
        '<div class="small fw-semibold mb-1 text-muted">按钮样式</div>' +
        '<div class="row g-2">' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_bg', '按钮背景色', d.btn_bg) + '</div>' +
          '<div class="col-6">' + cn('module_' + idx + '_data_btn_color', '按钮文字色', d.btn_color) + '</div>' +
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
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_padding_top" value="' + esc(d.btn_padding_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_padding_right" value="' + esc(d.btn_padding_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_padding_bottom" value="' + esc(d.btn_padding_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_padding_left" value="' + esc(d.btn_padding_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">按钮外边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_margin_top" value="' + esc(d.btn_margin_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_margin_right" value="' + esc(d.btn_margin_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_margin_bottom" value="' + esc(d.btn_margin_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_btn_margin_left" value="' + esc(d.btn_margin_left) + '" placeholder="← 左">' +
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
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_margin_top" value="' + esc(d.map_margin_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_margin_right" value="' + esc(d.map_margin_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_margin_bottom" value="' + esc(d.map_margin_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_margin_left" value="' + esc(d.map_margin_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small text-muted mt-2 mb-1" style="font-size:11px">地图内边距</div>' +
        '<div class="input-group input-group-sm">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_padding_top" value="' + esc(d.map_padding_top) + '" placeholder="↑ 上">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_padding_right" value="' + esc(d.map_padding_right) + '" placeholder="→ 右">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_padding_bottom" value="' + esc(d.map_padding_bottom) + '" placeholder="↓ 下">' +
          '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_map_padding_left" value="' + esc(d.map_padding_left) + '" placeholder="← 左">' +
          '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>' +
        '</div>' +
        '<div class="small fw-semibold mb-1 mt-2 text-muted">表单显隐</div>' +
        '<div class="d-flex flex-wrap gap-2">' +
          visToggle('module_' + idx + '_data_show_form', '显示表单', (d.show_form || 'true')) +
        '</div>';
    }

    /* ====== responsive 控件 ====== */
    var respCountField = 'items_per_page';
    var respCountLabel = '每页显示数量';
    var respCountPlaceholder = (type === 'data_grid') ? '默认' : '0=全部';

    /* ====== 构建 HTML (结构与 Jinja 模板对齐) ====== */
    var html =
      '<div class="d-flex align-items-center justify-content-between p-2 module-header" style="' + headerBg + 'cursor:pointer">' +
        '<span class="small fw-semibold d-flex align-items-center gap-1 ' + titleColor + '">' + getBlockIconHTML(type) + ' ' + esc(displayName) + '</span>' +
        '<div class="d-flex gap-1 flex-shrink-0 flex-nowrap">' +
          '<button type="button" class="module-action-btn" title="上移" onclick="event.stopPropagation();window._moveModule(this, -1)">↑</button>' +
          '<button type="button" class="module-action-btn" title="下移" onclick="event.stopPropagation();window._moveModule(this, 1)">↓</button>' +
          '<button type="button" class="module-action-btn module-action-del" title="删除" onclick="event.stopPropagation();this.closest(\'.module-item\').remove();window._reindexModules()">✕</button>' +
        '</div>' +
      '</div>' +
      '<input type="hidden" name="module_' + idx + '_type" value="' + esc(type) + '">' +
      '<input type="hidden" name="module_' + idx + '_order" value="' + (idx + 1) + '">' +
      '<div class="module-config p-2 border-top" style="display:block">';

    if (!isDataModule) {
      // 电脑端：tab 按钮 + 两个面板（结构与 Jinja 模板一致）
      html += '<div class="device-config device-desktop">' +
        '<div class="d-flex mb-2">' +
          '<button type="button" class="btn btn-sm btn-outline-secondary active content-style-tab flex-fill" data-tab="content" onclick="window._switchContentStyleTab(this, \'content\')">内容</button>' +
          '<button type="button" class="btn btn-sm btn-outline-secondary content-style-tab flex-fill" data-tab="style" onclick="window._switchContentStyleTab(this, \'style\')">样式</button>' +
        '</div>' +
        '<div class="content-style-panel panel-content">' +
          (specialEditor || desktopFields) +
          (needsResp ?
            '<hr class="my-2"><div class="row g-2">' +
              '<div class="col-6"><label class="form-label small mb-1 text-muted">每行列数</label><input type="number" class="form-control form-control-sm" name="module_' + idx + '_resp_columns" value="' + esc(d.columns || '') + '" placeholder="默认" min="1" max="6"></div>' +
              (type !== 'data_grid' ? '<div class="col-6"><label class="form-label small mb-1 text-muted">' + respCountLabel + '</label><input type="number" class="form-control form-control-sm" name="module_' + idx + '_resp_' + respCountField + '" value="' + esc(d[respCountField] || '') + '" placeholder="' + respCountPlaceholder + '"></div>' : '') +
            '</div>' : '') +
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

    // 平板端 / 手机端（结构与 Jinja 模板一致，与 .device-desktop 同级）
    if (!isDataModule) {
      html +=
        '<div class="device-config device-tablet" style="display:none">' +
          tabletFields +
          (needsResp ?
            '<hr class="my-2"><div class="row g-2">' +
              '<div class="col-6"><label class="form-label small mb-1 text-muted">每行列数</label><input type="number" class="form-control form-control-sm" name="module_' + idx + '_resp_tablet_columns" placeholder="继承电脑端" min="1" max="6"></div>' +
              (type !== 'data_grid' ? '<div class="col-6"><label class="form-label small mb-1 text-muted">' + respCountLabel + '</label><input type="number" class="form-control form-control-sm" name="module_' + idx + '_resp_tablet_' + respCountField + '" placeholder="继承电脑端"></div>' : '') +
            '</div>' : '') +
          '<div class="mb-2 mt-2"><label class="form-check-label small"><input type="checkbox" class="form-check-input" name="module_' + idx + '_resp_tablet_hidden" value="1"> 平板端隐藏此模块</label></div>' +
        '</div>' +
        '<div class="device-config device-mobile" style="display:none">' +
          mobileFields +
          (needsResp ?
            '<hr class="my-2"><div class="row g-2">' +
              '<div class="col-6"><label class="form-label small mb-1 text-muted">每行列数</label><input type="number" class="form-control form-control-sm" name="module_' + idx + '_resp_mobile_columns" placeholder="继承电脑端" min="1" max="6"></div>' +
              (type !== 'data_grid' ? '<div class="col-6"><label class="form-label small mb-1 text-muted">' + respCountLabel + '</label><input type="number" class="form-control form-control-sm" name="module_' + idx + '_resp_mobile_' + respCountField + '" placeholder="继承电脑端"></div>' : '') +
            '</div>' : '') +
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

    return { html: html, borderStyle: borderStyle, headerBg: headerBg };
  }

  /* ====== 手风琴展开/收缩 (供模板 addEventListener 调用) ======
   * 除了依赖 CSS !important 规则驱动 .module-config 显隐外，
   * 额外显式操作 .content-style-panel 的 display，确保即便
   * DOM 结构异常，面板也能正确切换。 */
  function toggleModuleAccordion(moduleItem) {
    var wasExpanded = moduleItem.classList.contains('expanded');
    // 收缩同容器内所有模块：移除 expanded + 显式隐藏面板
    var container = moduleItem.parentElement;
    if (container) {
      container.querySelectorAll('.module-item').forEach(function(item) {
        item.classList.remove('expanded');
        item.querySelectorAll('.content-style-panel').forEach(function(p) {
          p.style.display = 'none';
        });
      });
    }
    // 如果之前未展开，则展开当前模块：恢复 active tab 对应的面板
    if (!wasExpanded) {
      moduleItem.classList.add('expanded');
      var activeTab = moduleItem.querySelector('.content-style-tab.active');
      var tabName = activeTab ? activeTab.dataset.tab : 'content';
      var target = moduleItem.querySelector('.panel-' + tabName);
      if (target) target.style.display = '';
    }
  }

  /* ====== 对外暴露 ====== */
  window._buildModuleHTML = buildModuleHTML;
  window._toggleModuleAccordion = toggleModuleAccordion;

})();
