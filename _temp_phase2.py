"""Phase 2: Upgrade renderDynamicField + add grouping/list functions to panel_page_edit.html"""

with open(r'f:\dengtec\mycompany.website\app\templates\dashboard\panel_page_edit.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ===== Change 1: Upgrade renderDynamicField to handle new types =====
# Find the old renderDynamicField function and replace it
old_rdf_start = """function renderDynamicField(prefix, field, value, placeholder) {
  var key = field.key;
  var type = field.type || 'text';
  var label = field.label || key;
  var lowerKey = key.toLowerCase();
  var html = '<div class=\"mb-2\"><label class=\"form-label small mb-1 text-muted\">' + escapeHtml(label) + '</label>';

  // 颜色字段: color / bg / text_ → 颜色选择器+文本
  var isColor = /color|_bg$|^bg$/i.test(lowerKey) && !/image|cover|background_image|section_bg|background|media/i.test(lowerKey);
  // 需要单位的字段
  var needsSizeUnit = /size|font/i.test(lowerKey);
  var needsWidthUnit = /width/i.test(lowerKey);
  var needsRadiusUnit = /radius/i.test(lowerKey);
  var needsSpacingUnit = /margin|padding/i.test(lowerKey);
  var needsUnit = needsSizeUnit || needsWidthUnit || needsRadiusUnit || needsSpacingUnit;

  if (type === 'textarea') {
    html += '<textarea class=\"form-control form-control-sm\" rows=\"4\" name=\"' + prefix + key + '\" placeholder=\"' + escapeHtml(placeholder || '') + '\">' + escapeHtml(value || '') + '</textarea>';
  } else if (type === 'select') {
    html += '<select class=\"form-select form-select-sm\" name=\"' + prefix + key + '\"><option value=\"\">请选择</option>';
    (field.options || []).forEach(function(opt) {
      var optValue = typeof opt === 'object' ? opt.value : opt;
      var optLabel = typeof opt === 'object' ? (opt.label || opt.value) : opt;
      html += '<option value=\"' + escapeHtml(optValue) + '\"' + (String(value || '') === String(optValue) ? ' selected' : '') + '>' + escapeHtml(optLabel) + '</option>';
    });
    html += '</select>';
  } else if (type === 'number') {
    html += '<input type=\"number\" class=\"form-control form-control-sm\" name=\"' + prefix + key + '\" value=\"' + escapeHtml(value || '') + '\" placeholder=\"' + escapeHtml(placeholder || '') + '\">';
  } else if (isColor) {
    html += '<div class=\"input-group input-group-sm\"><input type=\"color\" class=\"form-control form-control-color\" value=\"' + escapeHtml(value || '#888888') + '\" oninput=\"this.parentElement.querySelector(\\'input[type=text]\\').value=this.value\"><input type=\"text\" class=\"form-control form-control-sm\" name=\"' + prefix + key + '\" value=\"' + escapeHtml(value || '') + '\" placeholder=\"' + escapeHtml(placeholder || '') + '\" oninput=\"this.parentElement.querySelector(\\'input[type=color]\\').value=this.value\"></div>';
  } else if (needsUnit) {
    var unitOptions = '';
    if (needsSizeUnit) unitOptions = '<option value=\"\">—</option><option value=\"px\">px</option><option value=\"rem\">rem</option>';
    else if (needsWidthUnit) unitOptions = '<option value=\"\">—</option><option value=\"px\">px</option><option value=\"%\">%</option><option value=\"rem\">rem</option>';
    else if (needsRadiusUnit) unitOptions = '<option value=\"\">—</option><option value=\"px\">px</option><option value=\"rem\">rem</option><option value=\"%\">%</option>';
    else if (needsSpacingUnit) unitOptions = '<option value=\"\">—</option><option value=\"px\">px</option><option value=\"rem\">rem</option>';
    html += '<div class=\"input-group input-group-sm\"><input type=\"text\" class=\"form-control form-control-sm\" name=\"' + prefix + key + '\" value=\"' + escapeHtml(value || '') + '\" placeholder=\"' + escapeHtml(placeholder || '') + '\" style=\"width:60%\"><select class=\"form-select form-select-sm unit-picker\" data-target=\"' + prefix + key + '\" style=\"width:40%\" onchange=\"var inp=this.parentElement.querySelector(\\'[name=\"' + prefix + key + '\"]\\');if(inp){var v=inp.value.replace(/px|rem|%$/i,\\'\\').trim();var u=this.value;if(v&&u)inp.value=v+u;}\">' + unitOptions + '</select></div>';
  } else {
    html += '<input type=\"text\" class=\"form-control form-control-sm\" name=\"' + prefix + key + '\" value=\"' + escapeHtml(value || '') + '\" placeholder=\"' + escapeHtml(placeholder || '') + '\">';
  }
  if (/(image|cover|background|media|photo|logo)/i.test(key)) {
    html += '<input type=\"file\" class=\"form-control form-control-sm mt-1\" name=\"' + prefix + key + '_file\" accept=\"image/*\">';
    html += '<div class=\"form-text\">可上传图片；视频请填写 URL。</div>';
  }
  return html + '</div>';
}"""

new_rdf = """function renderDynamicField(prefix, field, value, placeholder) {
  var key = field.key;
  var type = field.type || 'text';
  var label = field.label || key;
  var lowerKey = key.toLowerCase();
  var html = '<div class=\"mb-2\"><label class=\"form-label small mb-1 text-muted\">' + escapeHtml(label) + '</label>';

  // 颜色字段: color / bg / text_ → 颜色选择器+文本 (regex fallback, type:color 优先级更高)
  var isColorByKey = /color|_bg$|^bg$/i.test(lowerKey) && !/image|cover|background_image|section_bg|background|media/i.test(lowerKey);
  // 需要单位的字段
  var needsSizeUnit = /size|font/i.test(lowerKey);
  var needsWidthUnit = /width/i.test(lowerKey);
  var needsRadiusUnit = /radius/i.test(lowerKey);
  var needsSpacingUnit = /margin|padding/i.test(lowerKey);
  var needsUnit = needsSizeUnit || needsWidthUnit || needsRadiusUnit || needsSpacingUnit;

  if (type === 'richtext') {
    // 富文本编辑器：contenteditable div + 工具栏 + 隐藏 textarea
    html += '<div class=\"rich-toolbar\" style=\"border:1px solid #dee2e6;border-bottom:none;border-radius:4px 4px 0 0;padding:3px 4px;background:#f8f9fa;display:flex;gap:1px;flex-wrap:wrap\">' +
      '<button type=\"button\" class=\"btn btn-sm btn-outline-secondary py-1 px-2\" onmousedown=\"document.execCommand(\\'bold\\',false,null);event.preventDefault()\" title=\"加粗\" style=\"font-size:12px;line-height:1\"><b>B</b></button>' +
      '<button type=\"button\" class=\"btn btn-sm btn-outline-secondary py-1 px-2\" onmousedown=\"document.execCommand(\\'italic\\',false,null);event.preventDefault()\" title=\"斜体\" style=\"font-size:12px;line-height:1\"><i>I</i></button>' +
      '<button type=\"button\" class=\"btn btn-sm btn-outline-secondary py-1 px-2\" onmousedown=\"document.execCommand(\\'underline\\',false,null);event.preventDefault()\" title=\"下划线\" style=\"font-size:12px;line-height:1\"><u>U</u></button>' +
      '<span style=\"border-left:1px solid #dee2e6;margin:0 3px\"></span>' +
      '<button type=\"button\" class=\"btn btn-sm btn-outline-secondary py-1 px-2\" onmousedown=\"document.execCommand(\\'formatBlock\\',false,\\'h2\\');event.preventDefault()\" title=\"大标题\" style=\"font-size:12px;line-height:1\">H2</button>' +
      '<button type=\"button\" class=\"btn btn-sm btn-outline-secondary py-1 px-2\" onmousedown=\"document.execCommand(\\'formatBlock\\',false,\\'h3\\');event.preventDefault()\" title=\"小标题\" style=\"font-size:12px;line-height:1\">H3</button>' +
      '<button type=\"button\" class=\"btn btn-sm btn-outline-secondary py-1 px-2\" onmousedown=\"document.execCommand(\\'formatBlock\\',false,\\'p\\');event.preventDefault()\" title=\"正文段落\" style=\"font-size:12px;line-height:1\">P</button>' +
      '<span style=\"border-left:1px solid #dee2e6;margin:0 3px\"></span>' +
      '<button type=\"button\" class=\"btn btn-sm btn-outline-secondary py-1 px-2\" onmousedown=\"var u=prompt(\\'链接地址\\');if(u){document.execCommand(\\'createLink\\',false,u)};event.preventDefault()\" title=\"插入链接\" style=\"font-size:12px;line-height:1\">🔗</button>' +
    '</div>' +
    '<div contenteditable=\"true\" class=\"rich-editor-body form-control form-control-sm\" style=\"border-radius:0 0 4px 4px;min-height:150px;max-height:400px;overflow-y:auto\" oninput=\"this.nextElementSibling.value=this.innerHTML\">' + (value || '') + '</div>' +
    '<textarea class=\"form-control form-control-sm d-none\" name=\"' + prefix + key + '\">' + escapeHtml(value || '') + '</textarea>';
  } else if (type === 'textarea') {
    html += '<textarea class=\"form-control form-control-sm\" rows=\"4\" name=\"' + prefix + key + '\" placeholder=\"' + escapeHtml(placeholder || '') + '\">' + escapeHtml(value || '') + '</textarea>';
  } else if (type === 'select' || type === 'icon') {
    // icon 类型也是下拉选择，用 options 列表
    var selOptions = field.options || [];
    if (type === 'icon' && selOptions.length === 0) {
      // 图标默认列表
      selOptions = [
        {value: 'star', label: '⭐ 星形'},{value: 'heart', label: '❤️ 心形'},{value: 'check', label: '✓ 对勾'},
        {value: 'gear', label: '⚙ 齿轮'},{value: 'globe', label: '🌐 地球'},{value: 'bulb', label: '💡 灯泡'},
        {value: 'rocket', label: '🚀 火箭'},{value: 'shield', label: '🛡 盾牌'},{value: 'trophy', label: '🏆 奖杯'},
        {value: 'chart', label: '📊 图表'},{value: 'clock', label: '🕐 时钟'},{value: 'users', label: '👥 用户'},
        {value: 'phone', label: '📞 电话'},{value: 'mail', label: '✉️ 邮件'},{value: 'pin', label: '📍 定位'},
        {value: 'tag', label: '🏷 标签'},{value: 'wrench', label: '🔧 扳手'},{value: 'truck', label: '🚚 卡车'},
        {value: 'leaf', label: '🌿 叶子'},{value: 'fire', label: '🔥 火焰'}
      ];
    }
    html += '<select class=\"form-select form-select-sm\" name=\"' + prefix + key + '\"><option value=\"\">请选择</option>';
    selOptions.forEach(function(opt) {
      var optValue = typeof opt === 'object' ? opt.value : opt;
      var optLabel = typeof opt === 'object' ? (opt.label || opt.value) : opt;
      html += '<option value=\"' + escapeHtml(optValue) + '\"' + (String(value || '') === String(optValue) ? ' selected' : '') + '>' + escapeHtml(optLabel) + '</option>';
    });
    html += '</select>';
  } else if (type === 'number') {
    html += '<input type=\"number\" class=\"form-control form-control-sm\" name=\"' + prefix + key + '\" value=\"' + escapeHtml(value || '') + '\" placeholder=\"' + escapeHtml(placeholder || '') + '\">';
  } else if (type === 'color' || isColorByKey) {
    // type:color 显式指定或 key 名自动检测
    html += '<div class=\"input-group input-group-sm\"><input type=\"color\" class=\"form-control form-control-color\" value=\"' + escapeHtml(value || '#888888') + '\" oninput=\"this.parentElement.querySelector(\\'input[type=text]\\').value=this.value\"><input type=\"text\" class=\"form-control form-control-sm\" name=\"' + prefix + key + '\" value=\"' + escapeHtml(value || '') + '\" placeholder=\"' + escapeHtml(placeholder || '') + '\" oninput=\"this.parentElement.querySelector(\\'input[type=color]\\').value=this.value\"></div>';
  } else if (type === 'url') {
    html += '<input type=\"url\" class=\"form-control form-control-sm\" name=\"' + prefix + key + '\" value=\"' + escapeHtml(value || '') + '\" placeholder=\"' + escapeHtml(placeholder || '') + '\">';
  } else if (type === 'date') {
    html += '<input type=\"date\" class=\"form-control form-control-sm\" name=\"' + prefix + key + '\" value=\"' + escapeHtml(value || '') + '\">';
  } else if (type === 'image') {
    // 图片字段：URL 文本 + 文件上传
    html += '<input type=\"text\" class=\"form-control form-control-sm\" name=\"' + prefix + key + '\" value=\"' + escapeHtml(value || '') + '\" placeholder=\"' + escapeHtml(placeholder || '图片URL') + '\">';
    html += '<input type=\"file\" class=\"form-control form-control-sm mt-1\" name=\"' + prefix + key + '_file\" accept=\"image/*\">';
    html += '<div class=\"form-text\">上传后自动转 WebP 并覆盖 URL 字段。</div>';
  } else if (needsUnit) {
    var unitOptions = '';
    if (needsSizeUnit) unitOptions = '<option value=\"\">—</option><option value=\"px\">px</option><option value=\"rem\">rem</option>';
    else if (needsWidthUnit) unitOptions = '<option value=\"\">—</option><option value=\"px\">px</option><option value=\"%\">%</option><option value=\"rem\">rem</option>';
    else if (needsRadiusUnit) unitOptions = '<option value=\"\">—</option><option value=\"px\">px</option><option value=\"rem\">rem</option><option value=\"%\">%</option>';
    else if (needsSpacingUnit) unitOptions = '<option value=\"\">—</option><option value=\"px\">px</option><option value=\"rem\">rem</option>';
    html += '<div class=\"input-group input-group-sm\"><input type=\"text\" class=\"form-control form-control-sm\" name=\"' + prefix + key + '\" value=\"' + escapeHtml(value || '') + '\" placeholder=\"' + escapeHtml(placeholder || '') + '\" style=\"width:60%\"><select class=\"form-select form-select-sm unit-picker\" data-target=\"' + prefix + key + '\" style=\"width:40%\" onchange=\"var inp=this.parentElement.querySelector(\\'[name=\"' + prefix + key + '\"]\\');if(inp){var v=inp.value.replace(/px|rem|%$/i,\\'\\').trim();var u=this.value;if(v&&u)inp.value=v+u;}\">' + unitOptions + '</select></div>';
  } else {
    html += '<input type=\"text\" class=\"form-control form-control-sm\" name=\"' + prefix + key + '\" value=\"' + escapeHtml(value || '') + '\" placeholder=\"' + escapeHtml(placeholder || '') + '\">';
  }
  // 旧版图片 key 检测：非 image 类型但 key 名包含图片相关词时追加文件上传
  if (type !== 'image' && /(image|cover|background|media|photo|logo)/i.test(key) && type !== 'richtext') {
    html += '<input type=\"file\" class=\"form-control form-control-sm mt-1\" name=\"' + prefix + key + '_file\" accept=\"image/*\">';
    html += '<div class=\"form-text\">可上传图片；视频请填写 URL。</div>';
  }
  return html + '</div>';
}"""

assert old_rdf_start in content, "Old renderDynamicField not found!"
content = content.replace(old_rdf_start, new_rdf)
print("1. renderDynamicField upgraded")

# ===== Change 2: Add new functions after renderHiddenControl =====
insert_after = """function renderHiddenControl(idx, device, label) {
  return '<div class=\"mb-2 mt-2\"><label class=\"form-check-label small\"><input type=\"checkbox\" class=\"form-check-input\" name=\"module_' + idx + '_resp_' + device + '_hidden\" value=\"1\"> ' + label + '隐藏此模块</label></div>';
}"""

new_functions = """

// ===== 分组字段渲染 =====
function renderGroupedFields(prefix, fields, values, placeholder) {
  var currentGroup = null;
  var html = '';
  var firstField = true;
  fields.forEach(function(field, idx) {
    var group = field.group || null;
    // 跳过 list 类型（由调用方单独处理）
    if (field.type === 'list') return;
    // 新分组：加分隔和标题
    if (group !== currentGroup) {
      if (!firstField) html += '<hr class=\"my-2\">';
      if (group) {
        html += '<div class=\"small fw-semibold mb-1 text-muted\">' + escapeHtml(group) + '</div>';
      }
      currentGroup = group;
    }
    firstField = false;
    var fieldValue = (values || {})[field.key];
    if (fieldValue === undefined || fieldValue === null) fieldValue = field.default || '';
    html += renderDynamicField(prefix, field, fieldValue, placeholder || field.placeholder || '');
  });
  return html;
}

// ===== 通用列表编辑器 =====
function renderListEditor(prefix, field, items, moduleIndex) {
  var listKey = field.key;
  var itemFields = field.item_fields || [];
  var itemLabel = field.item_label || field.label || listKey;
  var editorClass = 'list-editor-' + listKey;
  var counterName = prefix + listKey + '_count';
  items = items || [{}];
  var html = '<div class=\"' + editorClass + '\" data-list-key=\"' + listKey + '\" data-module-index=\"' + (moduleIndex || '') + '\">' +
    '<div class=\"d-flex justify-content-between align-items-center mb-2\">' +
    '<div class=\"small fw-semibold text-primary\">' + escapeHtml(itemLabel) + '</div>' +
    '<button type=\"button\" class=\"btn btn-sm btn-outline-primary add-list-item-btn\" data-list-key=\"' + listKey + '\">+ 添加' + escapeHtml(itemLabel) + '</button>' +
    '</div>' +
    '<input type=\"hidden\" name=\"' + counterName + '\" class=\"list-item-count\" value=\"' + (items.length || 0) + '\">' +
    '<div class=\"list-items\">' +
    items.map(function(item, idx) {
      return renderListItem(prefix, field, idx, item);
    }).join('') +
    '</div></div>';
  return html;
}

function renderListItem(prefix, field, idx, itemData) {
  var itemFields = field.item_fields || [];
  var itemLabel = field.item_label || field.label || field.key;
  var itemPrefix = prefix + field.key + '_' + idx + '_';
  itemData = itemData || {};
  return '<div class=\"border rounded p-2 mb-2 list-item collapsed\" data-item-index=\"' + idx + '\" data-list-key=\"' + field.key + '\">' +
    '<div class=\"d-flex justify-content-between align-items-center mb-2 list-item-header\" style=\"cursor:pointer; user-select:none;\" onclick=\"this.closest(\\'.list-item\\').classList.toggle(\\'collapsed\\')\">' +
    '<span class=\"small fw-semibold\">' + escapeHtml(itemLabel) + ' ' + (idx + 1) + '</span>' +
    '<button type=\"button\" class=\"btn btn-sm btn-outline-danger remove-list-item-btn\" onclick=\"event.stopPropagation();removeListItem(this);\">删除</button></div>' +
    '<div class=\"list-item-body\">' +
    itemFields.map(function(itemField) {
      var itemValue = (itemData || {})[itemField.key] || '';
      return renderDynamicField(itemPrefix, itemField, itemValue, '');
    }).join('') +
    '</div></div>';
}

function removeListItem(btn) {
  var item = btn.closest('.list-item');
  var editor = btn.closest('[data-list-key]');
  var listKey = editor.dataset.listKey;
  item.remove();
  reindexListItems(editor, listKey);
}

function reindexListItems(editorEl, listKey) {
  var items = editorEl.querySelectorAll('.list-item');
  editorEl.querySelector('.list-item-count').value = items.length;
  items.forEach(function(item, idx) {
    item.dataset.itemIndex = idx;
    // 更新标题序号
    var label = item.querySelector('.small.fw-semibold');
    if (label) {
      var text = label.textContent;
      label.textContent = text.replace(/\\d+$/, idx + 1);
    }
    // 更新所有表单元素的 name 前缀
    item.querySelectorAll('input[name], select[name], textarea[name]').forEach(function(el) {
      var oldName = el.name;
      var newName = oldName.replace(new RegExp('_' + listKey + '_\\\\d+_'), '_' + listKey + '_' + idx + '_');
      el.name = newName;
    });
  });
}

// ===== 全局事件委托：添加列表项 =====
document.addEventListener('click', function(e) {
  var addBtn = e.target.closest('.add-list-item-btn');
  if (!addBtn) return;
  e.stopPropagation();
  var editorEl = addBtn.closest('[data-list-key]');
  var listKey = editorEl.dataset.listKey;
  var countEl = editorEl.querySelector('.list-item-count');
  var listEl = editorEl.querySelector('.list-items');
  var moduleIndex = editorEl.dataset.moduleIndex;
  var next = parseInt(countEl.value || '0', 10);

  // 从 blockLibrary 查找 field 定义
  var moduleItem = addBtn.closest('.module-item');
  var typeInput = moduleItem ? moduleItem.querySelector('input[name$=\"_type\"]') : null;
  var type = typeInput ? typeInput.value : '';
  var meta = type ? findBlockMeta(type) : null;
  var field = meta ? (meta.fields || []).find(function(f) { return f.key === listKey; }) : null;

  if (field) {
    var prefix = 'module_' + (moduleIndex || '0') + '_data_';
    listEl.insertAdjacentHTML('beforeend', renderListItem(prefix, field, next, {}));
    countEl.value = next + 1;
  } else {
    // 无 meta 时尝试从已有列表项复制结构
    var existingItem = listEl.querySelector('.list-item');
    if (existingItem) {
      var cloneHtml = existingItem.outerHTML.replace(new RegExp('_' + listKey + '_\\\\d+_', 'g'), '_' + listKey + '_' + next + '_');
      // 更新序号
      cloneHtml = cloneHtml.replace(/data-item-index=\"\\d+\"/, 'data-item-index=\"' + next + '\"');
      var labelMatch = cloneHtml.match(/<span class=\"small fw-semibold\">([^<]+)<\\/span>/);
      if (labelMatch) {
        cloneHtml = cloneHtml.replace(labelMatch[1], labelMatch[1].replace(/\\d+$/, next + 1));
      }
      listEl.insertAdjacentHTML('beforeend', cloneHtml);
      countEl.value = next + 1;
    }
  }
});
"""

assert insert_after in content, "renderHiddenControl not found!"
content = content.replace(insert_after, insert_after + new_functions)
print("2. New functions added (renderGroupedFields, renderListEditor, etc.)")

# ===== Change 3: Replace desktopFields with renderGroupedFields =====
# The old code:
old_desktop = """    var desktopFields = fields.map(function(field) {
    return renderDynamicField('module_' + idx + '_data_', field, field.default || '', '');
  }).join('');
  var tabletFields = fields.map(function(field) {
    return renderDynamicField('module_' + idx + '_resp_tablet_data_', field, '', '继承电脑端');
  }).join('');
  var mobileFields = fields.map(function(field) {
    return renderDynamicField('module_' + idx + '_resp_mobile_data_', field, '', '继承电脑端');
  }).join('');"""

new_desktop = """    var mdata = savedData || {};
    var desktopForm = renderGroupedFields('module_' + idx + '_data_', fields, mdata, '');
    var tabletFields = fields.map(function(field) {
    return renderDynamicField('module_' + idx + '_resp_tablet_data_', field, '', '继承电脑端');
  }).join('');
  var mobileFields = fields.map(function(field) {
    return renderDynamicField('module_' + idx + '_resp_mobile_data_', field, '', '继承电脑端');
  }).join('');"""

assert old_desktop in content, "Old desktopFields code not found!"
content = content.replace(old_desktop, new_desktop)
print("3. desktopFields replaced with renderGroupedFields")

with open(r'f:\dengtec\mycompany.website\app\templates\dashboard\panel_page_edit.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("All changes applied to panel_page_edit.html!")
