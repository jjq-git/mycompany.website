"""
统一替换所有 margin 字段为紧凑布局。
所有替换合并到一次 bottom-up 处理，避免行号偏移。
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
# 模板
# ============================================================

# Jinja2 (12空格缩进)
J2_M4 = (
    '            <div class="small text-muted mt-2 mb-1" style="font-size:11px">外边距</div>\n'
    '            <div class="input-group input-group-sm">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_margin_top" value="{{ mdata.get(\'margin_top\', \'\') }}" placeholder="↑ 上">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_margin_right" value="{{ mdata.get(\'margin_right\', \'\') }}" placeholder="→ 右">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_margin_bottom" value="{{ mdata.get(\'margin_bottom\', \'\') }}" placeholder="↓ 下">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_margin_left" value="{{ mdata.get(\'margin_left\', \'\') }}" placeholder="← 左">\n'
    '              <select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>\n'
    '            </div>\n')

J2_M4_NO_TITLE = (
    '            <div class="input-group input-group-sm">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_margin_top" value="{{ mdata.get(\'margin_top\', \'\') }}" placeholder="↑ 上">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_margin_right" value="{{ mdata.get(\'margin_right\', \'\') }}" placeholder="→ 右">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_margin_bottom" value="{{ mdata.get(\'margin_bottom\', \'\') }}" placeholder="↓ 下">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_margin_left" value="{{ mdata.get(\'margin_left\', \'\') }}" placeholder="← 左">\n'
    '              <select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>\n'
    '            </div>\n')

J2_M2 = (
    '            <div class="small text-muted mt-2 mb-1" style="font-size:11px">外边距</div>\n'
    '            <div class="input-group input-group-sm">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_margin_top" value="{{ mdata.get(\'margin_top\', \'\') }}" placeholder="↑ 上">\n'
    '              <input type="text" class="form-control form-control-sm placeholder-light" name="module_{{ i }}_data_margin_bottom" value="{{ mdata.get(\'margin_bottom\', \'\') }}" placeholder="↓ 下">\n'
    '              <select class="form-select form-select-sm" onchange="var u=this.value;this.parentElement.querySelectorAll(\'input[type=text]\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\'\').trim();if(v&&u)el.value=v+u;});"><option value="px">px</option><option value="rem">rem</option></select>\n'
    '            </div>\n')

# JS panel_page_edit.html (4空格缩进)
JS_M4 = (
    "    '<div class=\"small text-muted mt-2 mb-1\" style=\"font-size:11px\">外边距</div>' +\n"
    "    '<div class=\"input-group input-group-sm\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_top\" placeholder=\"↑ 上\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_right\" placeholder=\"→ 右\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_bottom\" placeholder=\"↓ 下\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_left\" placeholder=\"← 左\">' +\n"
    "      '<select class=\"form-select form-select-sm\" onchange=\"var u=this.value;this.parentElement.querySelectorAll(\\'input[type=text]\\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});\">' +\n"
    "        '<option value=\"px\">px</option>' +\n"
    "        '<option value=\"rem\">rem</option>' +\n"
    "      '</select>' +\n"
    "    '</div>' +\n")

JS_M4_NO_TITLE = (
    "    '<div class=\"input-group input-group-sm\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_top\" placeholder=\"↑ 上\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_right\" placeholder=\"→ 右\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_bottom\" placeholder=\"↓ 下\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_left\" placeholder=\"← 左\">' +\n"
    "      '<select class=\"form-select form-select-sm\" onchange=\"var u=this.value;this.parentElement.querySelectorAll(\\'input[type=text]\\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});\">' +\n"
    "        '<option value=\"px\">px</option>' +\n"
    "        '<option value=\"rem\">rem</option>' +\n"
    "      '</select>' +\n"
    "    '</div>' +\n")

JS_M2 = (
    "    '<div class=\"small text-muted mt-2 mb-1\" style=\"font-size:11px\">外边距</div>' +\n"
    "    '<div class=\"input-group input-group-sm\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_top\" placeholder=\"↑ 上\">' +\n"
    "      '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_bottom\" placeholder=\"↓ 下\">' +\n"
    "      '<select class=\"form-select form-select-sm\" onchange=\"var u=this.value;this.parentElement.querySelectorAll(\\'input[type=text]\\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});\">' +\n"
    "        '<option value=\"px\">px</option>' +\n"
    "        '<option value=\"rem\">rem</option>' +\n"
    "      '</select>' +\n"
    "    '</div>' +\n")

# admin_modules.js (8/10空格缩进)
ADM_M4 = (
    "        '<div class=\"small text-muted mt-2 mb-1\" style=\"font-size:11px\">外边距</div>' +\n"
    "        '<div class=\"input-group input-group-sm\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_top\" value=\"' + esc(d.margin_top) + '\" placeholder=\"↑ 上\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_right\" value=\"' + esc(d.margin_right) + '\" placeholder=\"→ 右\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_bottom\" value=\"' + esc(d.margin_bottom) + '\" placeholder=\"↓ 下\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_left\" value=\"' + esc(d.margin_left) + '\" placeholder=\"← 左\">' +\n"
    "          '<select class=\"form-select form-select-sm\" onchange=\"var u=this.value;this.parentElement.querySelectorAll(\\'input[type=text]\\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});\"><option value=\"px\">px</option><option value=\"rem\">rem</option></select>' +\n"
    "        '</div>' +\n")

ADM_M4_SEMI = (
    "        '<div class=\"small text-muted mt-2 mb-1\" style=\"font-size:11px\">外边距</div>' +\n"
    "        '<div class=\"input-group input-group-sm\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_top\" value=\"' + esc(d.margin_top) + '\" placeholder=\"↑ 上\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_right\" value=\"' + esc(d.margin_right) + '\" placeholder=\"→ 右\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_bottom\" value=\"' + esc(d.margin_bottom) + '\" placeholder=\"↓ 下\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_left\" value=\"' + esc(d.margin_left) + '\" placeholder=\"← 左\">' +\n"
    "          '<select class=\"form-select form-select-sm\" onchange=\"var u=this.value;this.parentElement.querySelectorAll(\\'input[type=text]\\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});\"><option value=\"px\">px</option><option value=\"rem\">rem</option></select>' +\n"
    "        '</div>';\n")

ADM_M2 = (
    "        '<div class=\"small text-muted mt-2 mb-1\" style=\"font-size:11px\">外边距</div>' +\n"
    "        '<div class=\"input-group input-group-sm\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_top\" value=\"' + esc(d.margin_top) + '\" placeholder=\"↑ 上\">' +\n"
    "          '<input type=\"text\" class=\"form-control form-control-sm placeholder-light\" name=\"module_' + idx + '_data_margin_bottom\" value=\"' + esc(d.margin_bottom) + '\" placeholder=\"↓ 下\">' +\n"
    "          '<select class=\"form-select form-select-sm\" onchange=\"var u=this.value;this.parentElement.querySelectorAll(\\'input[type=text]\\').forEach(function(el){var v=el.value.replace(/px|rem|%$/i,\\'\\').trim();if(v&&u)el.value=v+u;});\"><option value=\"px\">px</option><option value=\"rem\">rem</option></select>' +\n"
    "        '</div>' +\n")


def main():
    # ================================================================
    # panel_page_edit.html: 所有替换合并, bottom-up
    # ================================================================
    print('=== panel_page_edit.html ===')
    html_all = []

    # JS 部分 (高行号, 先处理)
    html_all.append((1899, 1904, JS_M4, 'text_content JS'))
    html_all.append((1830, 1832, "		    '</div>' +\n" + JS_M2, 'highlight_card JS'))
    html_all.append((1798, 1803, JS_M4, 'feature_grid JS'))
    html_all.append((1761, 1766, JS_M4_NO_TITLE, 'data_grid JS'))
    html_all.append((1676, 1681, JS_M4, 'section_title JS'))

    # Jinja2 部分 (低行号, 后处理)
    html_all.append((778, 783, J2_M4_NO_TITLE, 'text_content J2'))
    html_all.append((708, 713, J2_M4, 'feature_grid J2'))
    html_all.append((466, 471, J2_M4_NO_TITLE, 'data_grid J2'))
    html_all.append((334, 339, J2_M4, 'section_title J2'))
    html_all.append((261, 263, '            </div>\n' + J2_M2, 'hero_banner J2'))

    replace_lines(HTML, html_all)

    # ================================================================
    # admin_modules.js: bottom-up
    # ================================================================
    print('\n=== admin_modules.js ===')
    adm_all = []

    adm_all.append((464, 469, ADM_M4, 'text_content adm'))
    adm_all.append((402, 404, "        '</div>' +\n" + ADM_M2, 'highlight_card adm'))
    adm_all.append((358, 363, ADM_M4, 'feature_grid adm'))
    adm_all.append((324, 329, ADM_M4_SEMI, 'data_grid adm'))
    adm_all.append((251, 256, ADM_M4, 'section_title adm'))

    replace_lines(ADM, adm_all)

    print('\n=== 全部完成 ===')


if __name__ == '__main__':
    main()
