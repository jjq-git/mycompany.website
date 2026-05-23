path = r'f:\dengtec\mycompany.website\app\templates\dashboard\panel_page_edit.html'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# === Jinja2 edits ===

# 1. After text_color line (currently line 1285), add new row for input_radius + form_radius
# Find the end of the text_color row (closing </div> of the row)
for i, line in enumerate(lines):
    if "module_{{ i }}_data_text_color" in line:
        # The row ends at i+1 (</div>)
        # Insert after i+1
        radius_row = '''            <div class="row g-2">
              <div class="col-6"><label class="form-label small mb-1 text-muted">输入框圆角</label><div class="input-group input-group-sm"><input type="text" class="form-control form-control-sm" name="module_{{ i }}_data_input_radius" value="{{ mdata.get('input_radius', '') }}" placeholder="如 8px" style="width:60%"><select class="form-select form-select-sm" style="width:40%" onchange="var inp=this.parentElement.querySelector('[name=\\'module_{{ i }}_data_input_radius\\']');if(inp){var v=inp.value.replace(/px|rem|%$/i,'').trim();var u=this.value;if(v&&u)inp.value=v+u;}"><option value="">—</option><option value="px">px</option><option value="rem">rem</option><option value="%">%</option></select></div></div>
              <div class="col-6"><label class="form-label small mb-1 text-muted">表单圆角</label><div class="input-group input-group-sm"><input type="text" class="form-control form-control-sm" name="module_{{ i }}_data_form_radius" value="{{ mdata.get('form_radius', '') }}" placeholder="如 12px" style="width:60%"><select class="form-select form-select-sm" style="width:40%" onchange="var inp=this.parentElement.querySelector('[name=\\'module_{{ i }}_data_form_radius\\']');if(inp){var v=inp.value.replace(/px|rem|%$/i,'').trim();var u=this.value;if(v&&u)inp.value=v+u;}"><option value="">—</option><option value="px">px</option><option value="rem">rem</option><option value="%">%</option></select></div></div>
            </div>
'''
        lines.insert(i + 2, radius_row)
        print(f'Jinja2: Added radius row after line {i+1}')
        break

# 2. After map_height row, add map_radius
for i, line in enumerate(lines):
    if "module_{{ i }}_data_map_height" in line:
        # This is the map_height field. The row closes with </div> at some point.
        # Find the closing </div> for this row
        for j in range(i, min(i+3, len(lines))):
            if lines[j].strip() == '</div>' and 'row g-2' in lines[j-2]:
                map_radius_row = '''            <div class="row g-2">
              <div class="col-6"><label class="form-label small mb-1 text-muted">地图圆角</label><div class="input-group input-group-sm"><input type="text" class="form-control form-control-sm" name="module_{{ i }}_data_map_radius" value="{{ mdata.get('map_radius', '') }}" placeholder="如 12px" style="width:60%"><select class="form-select form-select-sm" style="width:40%" onchange="var inp=this.parentElement.querySelector('[name=\\'module_{{ i }}_data_map_radius\\']');if(inp){var v=inp.value.replace(/px|rem|%$/i,'').trim();var u=this.value;if(v&&u)inp.value=v+u;}"><option value="">—</option><option value="px">px</option><option value="rem">rem</option><option value="%">%</option></select></div></div>
            </div>
'''
                lines.insert(j + 1, map_radius_row)
                print(f'Jinja2: Added map_radius row after line {j+1}')
                break
        break

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('Jinja2 done')

# === addModule edits (string replacement) ===
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add input_radius + form_radius after text_color
old_text_color = """'<div class="col-6">' + cP('module_' + idx + '_data_text_color', '文字颜色') + '</div>' +
    '</div>' +
    '<div class="row g-2">' +
      '<div class="col-6">' + uP('module_' + idx + '_data_title_size', '标题字号', ['px','rem','em']) + '</div>'"""

new_text_color = """'<div class="col-6">' + cP('module_' + idx + '_data_text_color', '文字颜色') + '</div>' +
    '</div>' +
    '<div class="row g-2">' +
      '<div class="col-6">' + uP('module_' + idx + '_data_input_radius', '输入框圆角', ['px','rem','%']) + '</div>' +
      '<div class="col-6">' + uP('module_' + idx + '_data_form_radius', '表单圆角', ['px','rem','%']) + '</div>' +
    '</div>' +
    '<div class="row g-2">' +
      '<div class="col-6">' + uP('module_' + idx + '_data_title_size', '标题字号', ['px','rem','em']) + '</div>'"""

if old_text_color in content:
    content = content.replace(old_text_color, new_text_color)
    print('addModule: Added input_radius + form_radius')
else:
    print('ERROR: old_text_color not found')

# 2. Add map_radius after map_height
old_map_height = """'<div class="col-6">' + uP('module_' + idx + '_data_map_height', '地图高度', ['px','rem','vh']) + '</div>' +
    '</div>' +
    '<div class="small text-muted mt-2 mb-1" style="font-size:11px">地图外边距</div>'"""

new_map_height = """'<div class="col-6">' + uP('module_' + idx + '_data_map_height', '地图高度', ['px','rem','vh']) + '</div>' +
    '</div>' +
    '<div class="row g-2">' +
      '<div class="col-6">' + uP('module_' + idx + '_data_map_radius', '地图圆角', ['px','rem','%']) + '</div>' +
    '</div>' +
    '<div class="small text-muted mt-2 mb-1" style="font-size:11px">地图外边距</div>'"""

if old_map_height in content:
    content = content.replace(old_map_height, new_map_height)
    print('addModule: Added map_radius')
else:
    print('ERROR: old_map_height not found')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('addModule done')
