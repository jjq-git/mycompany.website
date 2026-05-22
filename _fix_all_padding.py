"""
统一替换所有 padding 字段为紧凑布局.
所有替换合并到一次 bottom-up 处理, 避免行号偏移.
"""
import os

HTML = r'f:\dengtec\mycompany.website\app\templates\dashboard\panel_page_edit.html'
ADM = r'f:\dengtec\mycompany.website\app\static\js\admin_modules.js'


def replace_lines(filepath, replacements):
    """replacements: [(start_line, end_line, new_text, label), ...]  1-indexed, inclusive.
    Processed bottom-up automatically."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for start, end, new_text, label in sorted(replacements, key=lambda x: -x[0]):
        old = ''.join(lines[start-1:end])
        lines[start-1:end] = [new_text]
        print(f'  [{label}] Lines {start}-{end}: {len(old)} -> {len(new_text)} chars')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)


# ============================================================
# Jinja2 模板 (12空格缩进)
# ============================================================

# 关闭行 + 标题 + 紧凑4字段 (hero_banner, section_title, feature_grid)
J2_P4_CLOSE = (
    '            </div>\n'
    '            <div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>\n'
    '            <div class="input-group input-group-sm">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_top" value="{{ mdata.get(\'padding_top\', \'\') }}" placeholder="↑ 上">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_right" value="{{ mdata.get(\'padding_right\', \'\') }}" placeholder="→ 右">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_bottom" value="{{ mdata.get(\'padding_bottom\', \'\') }}" placeholder="↓ 下">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_left" value="{{ mdata.get(\'padding_left\', \'\') }}" placeholder="← 左">\n'
    '              <select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>\n'
    '            </div>\n')

# 标题 + 紧凑4字段 (process_steps)
J2_P4 = (
    '            <div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>\n'
    '            <div class="input-group input-group-sm">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_top" value="{{ mdata.get(\'padding_top\', \'\') }}" placeholder="↑ 上">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_right" value="{{ mdata.get(\'padding_right\', \'\') }}" placeholder="→ 右">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_bottom" value="{{ mdata.get(\'padding_bottom\', \'\') }}" placeholder="↓ 下">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_left" value="{{ mdata.get(\'padding_left\', \'\') }}" placeholder="← 左">\n'
    '              <select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>\n'
    '            </div>\n')

# 无标题紧凑4字段 (text_content - 标题已存在)
J2_P4_NT = (
    '            <div class="input-group input-group-sm">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_top" value="{{ mdata.get(\'padding_top\', \'\') }}" placeholder="↑ 上">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_right" value="{{ mdata.get(\'padding_right\', \'\') }}" placeholder="→ 右">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_bottom" value="{{ mdata.get(\'padding_bottom\', \'\') }}" placeholder="↓ 下">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_left" value="{{ mdata.get(\'padding_left\', \'\') }}" placeholder="← 左">\n'
    '              <select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>\n'
    '            </div>\n')

# 卡片内边距紧凑 (highlight_card, 标题已存在)
J2_CP4 = (
    '            <div class="input-group input-group-sm">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_card_padding_top" value="{{ mdata.get(\'card_padding_top\', mdata.get(\'card_padding\', \'\')) }}" placeholder="↑ 上">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_card_padding_right" value="{{ mdata.get(\'card_padding_right\', mdata.get(\'card_padding\', \'\')) }}" placeholder="→ 右">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_card_padding_bottom" value="{{ mdata.get(\'card_padding_bottom\', mdata.get(\'card_padding\', \'\')) }}" placeholder="↓ 下">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_card_padding_left" value="{{ mdata.get(\'card_padding_left\', mdata.get(\'card_padding\', \'\')) }}" placeholder="← 左">\n'
    '              <select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>\n'
    '            </div>\n')

# 标题 + 紧凑4字段 + % (logo_cloud)
J2_P4_PCT = (
    '            <div class="small text-muted mt-2 mb-1" style="font-size:11px">内边距</div>\n'
    '            <div class="input-group input-group-sm">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_top" value="{{ mdata.get(\'padding_top\', \'\') }}" placeholder="↑ 上">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_right" value="{{ mdata.get(\'padding_right\', \'\') }}" placeholder="→ 右">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_bottom" value="{{ mdata.get(\'padding_bottom\', \'\') }}" placeholder="↓ 下">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_padding_left" value="{{ mdata.get(\'padding_left\', \'\') }}" placeholder="← 左">\n'
    '              <select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option><option value="%">%</option></select>\n'
    '            </div>\n')


# ============================================================
# panel_page_edit.html JS 模板 (4空格缩进)
# ============================================================

# 关闭行 + 标题 + 紧凑4字段 (section_title, hero_banner, feature_grid)
JS_P4_CLOSE = (
    "    '</div>' +\n"
    "    '<div class=\"small text-muted mt-2 mb-1\" style=\"font-size:11px\">内边距</div>' +\n"
    "    '<div class=\"input-group input-group-sm\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_top\" placeholder=\"↑ 上\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_right\" placeholder=\"→ 右\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_bottom\" placeholder=\"↓ 下\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_left\" placeholder=\"← 左\">' +\n"
    "      '<select class=\"form-select form-select-sm\" onchange=\"var u=this.value;this.parentElement.querySelectorAll(\\'input[type=text]\\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});\">' +\n"
    "        '<option value=\"px\">px</option>' +\n"
    "        '<option value=\"rem\">rem</option>' +\n"
    "      '</select>' +\n"
    "    '</div>' +\n")

# 标题 + 紧凑4字段 (text_content, process_steps)
JS_P4 = (
    "    '<div class=\"small text-muted mt-2 mb-1\" style=\"font-size:11px\">内边距</div>' +\n"
    "    '<div class=\"input-group input-group-sm\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_top\" placeholder=\"↑ 上\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_right\" placeholder=\"→ 右\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_bottom\" placeholder=\"↓ 下\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_left\" placeholder=\"← 左\">' +\n"
    "      '<select class=\"form-select form-select-sm\" onchange=\"var u=this.value;this.parentElement.querySelectorAll(\\'input[type=text]\\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});\">' +\n"
    "        '<option value=\"px\">px</option>' +\n"
    "        '<option value=\"rem\">rem</option>' +\n"
    "      '</select>' +\n"
    "    '</div>' +\n")

# 卡片内边距紧凑 (highlight_card, 标题已存在)
JS_CP4 = (
    "    '<div class=\"input-group input-group-sm\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_card_padding_top\" placeholder=\"↑ 上\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_card_padding_right\" placeholder=\"→ 右\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_card_padding_bottom\" placeholder=\"↓ 下\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_card_padding_left\" placeholder=\"← 左\">' +\n"
    "      '<select class=\"form-select form-select-sm\" onchange=\"var u=this.value;this.parentElement.querySelectorAll(\\'input[type=text]\\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});\">' +\n"
    "        '<option value=\"px\">px</option>' +\n"
    "        '<option value=\"rem\">rem</option>' +\n"
    "      '</select>' +\n"
    "    '</div>' +\n")

# 标题 + 紧凑4字段 + % (logo_cloud)
JS_P4_PCT = (
    "    '<div class=\"small text-muted mt-2 mb-1\" style=\"font-size:11px\">内边距</div>' +\n"
    "    '<div class=\"input-group input-group-sm\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_top\" placeholder=\"↑ 上\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_right\" placeholder=\"→ 右\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_bottom\" placeholder=\"↓ 下\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_left\" placeholder=\"← 左\">' +\n"
    "      '<select class=\"form-select form-select-sm\" onchange=\"var u=this.value;this.parentElement.querySelectorAll(\\'input[type=text]\\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});\">' +\n"
    "        '<option value=\"px\">px</option>' +\n"
    "        '<option value=\"rem\">rem</option>' +\n"
    "        '<option value=\"%\">%</option>' +\n"
    "      '</select>' +\n"
    "    '</div>' +\n")


# ============================================================
# admin_modules.js JS 模板 (8空格缩进)
# ============================================================

# 关闭行 + 标题 + 紧凑4字段 (section_title, hero_banner, feature_grid)
ADM_P4_CLOSE = (
    "        '</div>' +\n"
    "        '<div class=\"small text-muted mt-2 mb-1\" style=\"font-size:11px\">内边距</div>' +\n"
    "        '<div class=\"input-group input-group-sm\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_top\" value=\"' + esc(d.padding_top) + '\" placeholder=\"↑ 上\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_right\" value=\"' + esc(d.padding_right) + '\" placeholder=\"→ 右\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_bottom\" value=\"' + esc(d.padding_bottom) + '\" placeholder=\"↓ 下\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_left\" value=\"' + esc(d.padding_left) + '\" placeholder=\"← 左\">' +\n"
    "          '<select class=\"form-select form-select-sm\" onchange=\"var u=this.value;this.parentElement.querySelectorAll(\\'input[type=text]\\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});\"><option value=\"px\">px</option><option value=\"rem\">rem</option></select>' +\n"
    "        '</div>' +\n")

# 标题 + 紧凑4字段 (text_content, process_steps)
ADM_P4 = (
    "        '<div class=\"small text-muted mt-2 mb-1\" style=\"font-size:11px\">内边距</div>' +\n"
    "        '<div class=\"input-group input-group-sm\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_top\" value=\"' + esc(d.padding_top) + '\" placeholder=\"↑ 上\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_right\" value=\"' + esc(d.padding_right) + '\" placeholder=\"→ 右\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_bottom\" value=\"' + esc(d.padding_bottom) + '\" placeholder=\"↓ 下\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_left\" value=\"' + esc(d.padding_left) + '\" placeholder=\"← 左\">' +\n"
    "          '<select class=\"form-select form-select-sm\" onchange=\"var u=this.value;this.parentElement.querySelectorAll(\\'input[type=text]\\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});\"><option value=\"px\">px</option><option value=\"rem\">rem</option></select>' +\n"
    "        '</div>' +\n")

# 卡片内边距紧凑 (highlight_card, 标题已存在)
ADM_CP4 = (
    "        '<div class=\"input-group input-group-sm\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_card_padding_top\" value=\"' + esc(d.card_padding_top) + '\" placeholder=\"↑ 上\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_card_padding_right\" value=\"' + esc(d.card_padding_right) + '\" placeholder=\"→ 右\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_card_padding_bottom\" value=\"' + esc(d.card_padding_bottom) + '\" placeholder=\"↓ 下\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_card_padding_left\" value=\"' + esc(d.card_padding_left) + '\" placeholder=\"← 左\">' +\n"
    "          '<select class=\"form-select form-select-sm\" onchange=\"var u=this.value;this.parentElement.querySelectorAll(\\'input[type=text]\\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});\"><option value=\"px\">px</option><option value=\"rem\">rem</option></select>' +\n"
    "        '</div>' +\n")

# 标题 + 紧凑4字段 + % (logo_cloud)
ADM_P4_PCT = (
    "        '<div class=\"small text-muted mt-2 mb-1\" style=\"font-size:11px\">内边距</div>' +\n"
    "        '<div class=\"input-group input-group-sm\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_top\" value=\"' + esc(d.padding_top) + '\" placeholder=\"↑ 上\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_right\" value=\"' + esc(d.padding_right) + '\" placeholder=\"→ 右\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_bottom\" value=\"' + esc(d.padding_bottom) + '\" placeholder=\"↓ 下\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_padding_left\" value=\"' + esc(d.padding_left) + '\" placeholder=\"← 左\">' +\n"
    "          '<select class=\"form-select form-select-sm\" onchange=\"var u=this.value;this.parentElement.querySelectorAll(\\'input[type=text]\\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});\"><option value=\"px\">px</option><option value=\"rem\">rem</option><option value=\"%\">%</option></select>' +\n"
    "        '</div>' +\n")


def main():
    # ================================================================
    # panel_page_edit.html: 所有替换合并, bottom-up
    # ================================================================
    print('=== panel_page_edit.html ===')
    html_all = []

    # JS 部分 (高行号, 先处理)
    html_all.append((2110, 2115, JS_P4,              'process_steps JS'))
    html_all.append((2038, 2045, JS_P4_PCT,           'logo_cloud JS'))
    html_all.append((1969, 1973, JS_P4_CLOSE,         'feature_grid JS'))
    html_all.append((1941, 1946, JS_P4,               'text_content JS'))
    html_all.append((1869, 1873, JS_P4_CLOSE,         'hero_banner JS'))
    html_all.append((1835, 1840, JS_CP4,              'highlight_card JS'))
    html_all.append((1701, 1705, JS_P4_CLOSE,         'section_title JS'))

    # Jinja2 部分 (低行号, 后处理)
    html_all.append((1004, 1009, J2_P4,               'process_steps J2'))
    html_all.append((921,  928,  J2_P4_PCT,           'logo_cloud J2'))
    html_all.append((802,  807,  J2_P4_NT,            'text_content J2'))
    html_all.append((736,  741,  J2_CP4,              'highlight_card J2'))
    html_all.append((608,  612,  J2_P4_CLOSE,         'feature_grid J2'))
    html_all.append((351,  355,  J2_P4_CLOSE,         'section_title J2'))
    html_all.append((274,  278,  J2_P4_CLOSE,         'hero_banner J2'))

    replace_lines(HTML, html_all)

    # ================================================================
    # admin_modules.js: bottom-up
    # ================================================================
    print('\n=== admin_modules.js ===')
    adm_all = []

    adm_all.append((645, 650, ADM_P4,      'process_steps adm'))
    adm_all.append((599, 604, ADM_P4_PCT,  'logo_cloud adm'))
    adm_all.append((533, 537, ADM_P4_CLOSE,'feature_grid adm'))
    adm_all.append((482, 487, ADM_P4,      'text_content adm'))
    adm_all.append((420, 424, ADM_P4_CLOSE,'hero_banner adm'))
    adm_all.append((377, 382, ADM_CP4,     'highlight_card adm'))
    adm_all.append((262, 266, ADM_P4_CLOSE,'section_title adm'))

    replace_lines(ADM, adm_all)

    print('\n=== 全部完成 ===')


if __name__ == '__main__':
    main()
