
var prefix = 'test_';
var key = 'field';
var value = 'val';
var unitOptions = '<option>px</option>';
function escapeHtml(s) { return s; }

// Line 75
    html += '<div class="input-group input-group-sm"><input type="text" class="form-control form-control-sm" name="' + prefix + key + '" value="' + escapeHtml(value || '') + '" placeholder="' + escapeHtml(placeholder || '') + '" style="width:60%"><select class="form-select form-select-sm unit-picker" data-target="' + prefix + key + '" style="width:40%" onchange="var inp=this.parentElement.querySelector(\'[name="' + prefix + key + '"]\');if(inp){var v=inp.value.replace(/px|rem|%$/i,'').trim();var u=this.value;if(v&&u)inp.value=v+u;}">' + unitOptions + '</select></div>';

console.log('ok');
