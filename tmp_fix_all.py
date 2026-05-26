"""Fix panel_page_edit.html Path 1 and Path 2:
1. Path 1: card_radius row g-2 → input-group + add defaults
2. Path 1: card_padding add defaults
3. Path 2: card_radius row g-2 → input-group + add defaults
4. Path 2: card_padding add defaults
"""
with open(r'f:\dengtec\mycompany.website\app\templates\dashboard\panel_page_edit.html', 'r', encoding='utf-8') as f:
    content = f.read()

# ── Path 1: card_radius row g-2 → input-group + defaults ──
old_p1_radius = '''            <div class="small text-muted mt-2 mb-1" style="font-size:11px">卡片圆角</div>
            <div class="row g-2">
              <div class="col-6"><label class="form-label small mb-1 text-muted">左上</label><div class="input-group input-group-sm"><input type="text" class="form-control form-control-sm" name="module_{{ i }}_data_card_radius_top_left" value="{{ mdata.get('card_radius_top_left', mdata.get('card_radius', '')) }}" placeholder="如 12px" style="width:60%"><select class="form-select form-select-sm" style="width:40%" onchange="var inp=this.parentElement.querySelector('[name=\\'module_{{ i }}_data_card_radius_top_left\\']);if(inp){var v=inp.value.replace(/px|rem|%$/i,\\'\\').trim();var u=this.value;if(v&&u)inp.value=v+u;}"><option value="px">px</option><option value="rem">rem</option><option value="%">%</option></select></div></div>
              <div class="col-6"><label class="form-label small mb-1 text-muted">右上</label><div class="input-group input-group-sm"><input type="text" class="form-control form-control-sm" name="module_{{ i }}_data_card_radius_top_right" value="{{ mdata.get('card_radius_top_right', mdata.get('card_radius', '')) }}" placeholder="如 12px" style="width:60%"><select class="form-select form-select-sm" style="width:40%" onchange="var inp=this.parentElement.querySelector('[name=\\'module_{{ i }}_data_card_radius_top_right\\']);if(inp){var v=inp.value.replace(/px|rem|%$/i,\\'\\').trim();var u=this.value;if(v&&u)inp.value=v+u;}"><option value="px">px</option><option value="rem">rem</option><option value="%">%</option></select></div></div>
              <div class="col-6"><label class="form-label small mb-1 text-muted">右下</label><div class="input-group input-group-sm"><input type="text" class="form-control form-control-sm" name="module_{{ i }}_data_card_radius_bottom_right" value="{{ mdata.get('card_radius_bottom_right', mdata.get('card_radius', '')) }}" placeholder="如 12px" style="width:60%"><select class="form-select form-select-sm" style="width:40%" onchange="var inp=this.parentElement.querySelector('[name=\\'module_{{ i }}_data_card_radius_bottom_right\\']);if(inp){var v=inp.value.replace(/px|rem|%$/i,\\'\\').trim();var u=this.value;if(v&&u)inp.value=v+u;}"><option value="px">px</option><option value="rem">rem</option><option value="%">%</option></select></div></div>
              <div class="col-6"><label class="form-label small mb-1 text-muted">左下</label><div class="input-group input-group-sm"><input type="text" class="form-control form-control-sm" name="module_{{ i }}_data_card_radius_bottom_left" value="{{ mdata.get('card_radius_bottom_left', mdata.get('card_radius', '')) }}" placeholder="如 12px" style="width:60%"><select class="form-select form-select-sm" style="width:40%" onchange="var inp=this.parentElement.querySelector('[name=\\'module_{{ i }}_data_card_radius_bottom_left\\']);if(inp){var v=inp.value.replace(/px|rem|%$/i,\\'\\').trim();var u=this.value;if(v&&u)inp.value=v+u;}"><option value="px">px</option><option value="rem">rem</option><option value="%">%</option></select></div></div>
            </div>'''

new_p1_radius = '''            <div class="small text-muted mt-2 mb-1" style="font-size:11px">卡片圆角</div>
            <div class="input-group input-group-sm">
              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_card_radius_top_left" value="{{ mdata.get('card_radius_top_left') or '12px' }}" placeholder="↖ 左上">
              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_card_radius_top_right" value="{{ mdata.get('card_radius_top_right') or '12px' }}" placeholder="↗ 右上">
              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_card_radius_bottom_right" value="{{ mdata.get('card_radius_bottom_right') or '12px' }}" placeholder="↘ 右下">
              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_card_radius_bottom_left" value="{{ mdata.get('card_radius_bottom_left') or '12px' }}" placeholder="↙ 左下">
              <select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll('input[type=text]').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option><option value=\"%\">%</option></select>
            </div>'''

if old_p1_radius in content:
    content = content.replace(old_p1_radius, new_p1_radius)
    print("Path 1 card_radius: OK")
else:
    print("Path 1 card_radius: NOT FOUND")

# ── Path 1: card_padding defaults ──
# Line 841: mdata.get('card_padding_top', mdata.get('card_padding', '')) → mdata.get('card_padding_top') or '2rem'
old_p1_ptop = "mdata.get('card_padding_top', mdata.get('card_padding', ''))"
new_p1_ptop = "mdata.get('card_padding_top') or '2rem'"
if old_p1_ptop in content:
    content = content.replace(old_p1_ptop, new_p1_ptop)
    print("Path 1 card_padding_top: OK")
else:
    print("Path 1 card_padding_top: NOT FOUND")

old_p1_pright = "mdata.get('card_padding_right', mdata.get('card_padding', ''))"
new_p1_pright = "mdata.get('card_padding_right') or '1.5rem'"
if old_p1_pright in content:
    content = content.replace(old_p1_pright, new_p1_pright)
    print("Path 1 card_padding_right: OK")
else:
    print("Path 1 card_padding_right: NOT FOUND")

old_p1_pbottom = "mdata.get('card_padding_bottom', mdata.get('card_padding', ''))"
new_p1_pbottom = "mdata.get('card_padding_bottom') or '2rem'"
if old_p1_pbottom in content:
    content = content.replace(old_p1_pbottom, new_p1_pbottom)
    print("Path 1 card_padding_bottom: OK")
else:
    print("Path 1 card_padding_bottom: NOT FOUND")

old_p1_pleft = "mdata.get('card_padding_left', mdata.get('card_padding', ''))"
new_p1_pleft = "mdata.get('card_padding_left') or '1.5rem'"
if old_p1_pleft in content:
    content = content.replace(old_p1_pleft, new_p1_pleft)
    print("Path 1 card_padding_left: OK")
else:
    print("Path 1 card_padding_left: NOT FOUND")

# ── Path 2: card_radius row g-2 → input-group + defaults ──
old_p2_radius = '''    '<div class="small text-muted mt-2 mb-1" style="font-size:11px">卡片圆角</div>' +
    '<div class="row g-2">' +
      '<div class="col-6">' + uP('module_' + idx + '_data_card_radius_top_left', '左上', ['px','rem','%']) + '</div>' +
      '<div class="col-6">' + uP('module_' + idx + '_data_card_radius_top_right', '右上', ['px','rem','%']) + '</div>' +
      '<div class="col-6">' + uP('module_' + idx + '_data_card_radius_bottom_right', '右下', ['px','rem','%']) + '</div>' +
      '<div class="col-6">' + uP('module_' + idx + '_data_card_radius_bottom_left', '左下', ['px','rem','%']) + '</div>' +
    '</div>' +'''

new_p2_radius = """    '<div class="small text-muted mt-2 mb-1" style="font-size:11px">卡片圆角</div>' +
    '<div class="input-group input-group-sm">' +
      '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_radius_top_left" placeholder="↖ 左上" value="12px">' +
      '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_radius_top_right" placeholder="↗ 右上" value="12px">' +
      '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_radius_bottom_right" placeholder="↘ 右下" value="12px">' +
      '<input type="text" class="form-control form-control-sm placeholder-light" name="module_' + idx + '_data_card_radius_bottom_left" placeholder="↙ 左下" value="12px">' +
      '<select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\\'input[type=text]\\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option><option value=\\"%\\">%</option></select>' +
    '</div>' +"""

if old_p2_radius in content:
    content = content.replace(old_p2_radius, new_p2_radius)
    print("Path 2 card_radius: OK")
else:
    print("Path 2 card_radius: NOT FOUND")

# ── Path 2: card_padding defaults ──
# Currently no value attr → add value="2rem" etc.
old_p2_ptop = "name=\"module_' + idx + '_data_card_padding_top\" placeholder=\"↑ 上\">"
new_p2_ptop = "name=\"module_' + idx + '_data_card_padding_top\" placeholder=\"↑ 上\" value=\"2rem\">"
if old_p2_ptop in content:
    content = content.replace(old_p2_ptop, new_p2_ptop)
    print("Path 2 card_padding_top: OK")
else:
    print("Path 2 card_padding_top: NOT FOUND")

old_p2_pright = "name=\"module_' + idx + '_data_card_padding_right\" placeholder=\"→ 右\">"
new_p2_pright = "name=\"module_' + idx + '_data_card_padding_right\" placeholder=\"→ 右\" value=\"1.5rem\">"
if old_p2_pright in content:
    content = content.replace(old_p2_pright, new_p2_pright)
    print("Path 2 card_padding_right: OK")
else:
    print("Path 2 card_padding_right: NOT FOUND")

old_p2_pbottom = "name=\"module_' + idx + '_data_card_padding_bottom\" placeholder=\"↓ 下\">"
new_p2_pbottom = "name=\"module_' + idx + '_data_card_padding_bottom\" placeholder=\"↓ 下\" value=\"2rem\">"
if old_p2_pbottom in content:
    content = content.replace(old_p2_pbottom, new_p2_pbottom)
    print("Path 2 card_padding_bottom: OK")
else:
    print("Path 2 card_padding_bottom: NOT FOUND")

old_p2_pleft = "name=\"module_' + idx + '_data_card_padding_left\" placeholder=\"← 左\">"
new_p2_pleft = "name=\"module_' + idx + '_data_card_padding_left\" placeholder=\"← 左\" value=\"1.5rem\">"
if old_p2_pleft in content:
    content = content.replace(old_p2_pleft, new_p2_pleft)
    print("Path 2 card_padding_left: OK")
else:
    print("Path 2 card_padding_left: NOT FOUND")

with open(r'f:\dengtec\mycompany.website\app\templates\dashboard\panel_page_edit.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done writing panel_page_edit.html")
