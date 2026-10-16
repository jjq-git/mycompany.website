# 新模板开发规范清单

本文整理自 `site_templates/apple` 的开发复盘。后续新增模板时，必须按这份清单执行，避免出现“看起来有模板，但细节、数据、交互不完整”的问题。

## 1. 先读设计参考，不要只换皮

每个新模板必须先选定一份 `docs/themes/design-refs/*.md` 作为设计依据，例如 `apple.md`。

实现前要提取这些硬约束：

- 字号层级：hero、section title、正文、caption、按钮分别是多少。
- 间距节奏：section padding、卡片 gap、内容最大宽度、移动端断点。
- 组件规格：按钮 padding/radius、卡片 radius、图片区比例、导航高度、页脚密度。
- 色彩原则：主色、背景、暗色块、是否允许渐变/阴影。
- 交互原则：哪些地方应该有轮播、放大、分页、移动端折叠。

不要用参考站的“氛围词”替代具体数值。比如 Apple 模板应落实为 44px 顶栏、80px section、20-24px 栅格间距、17px 正文、18px 卡片圆角、单一 Action Blue，而不是泛泛地“高级、简洁”。

## 2. 种子数据必须完整

模板交付时，`seed_data` 不能有明显空字段。以下内容必须完整：

- `settings.yaml`：公司信息、联系信息、社交链接、菜单、页脚、启用语言。
- `translations.yaml`：导航、按钮、表单、联系方式、页脚等 UI 文案。
- `pages/*.yaml`：首页、关于、联系、支持/商店等菜单指向的页面。
- `data/*.yaml`：模板声明的数据集都要有示例记录。
- `seed_data/lang/<code>/`：非默认语言必须有完整页面和数据覆盖，不只翻译几个 UI key。

允许为空的字段要谨慎，除非模板明确支持隐藏逻辑。否则宁可填示例值，也不要留下 `""`、`null`、空数组或只显示空壳的模块。

## 3. 首页必须覆盖全部 block

新模板首页要使用该模板提供的所有 block，作为完整演示和回归测试入口。多语言模板中，非默认语言首页也要保持同样的 block 覆盖范围。

检查方式：

```powershell
@'
import yaml, pathlib
p = pathlib.Path('site_templates/<name>/seed_data/pages/home.yaml')
data = yaml.safe_load(p.read_text(encoding='utf-8'))
print(len(data['modules']))
print(','.join(m['type'] for m in data['modules']))
'@ | python -
```

## 4. data-attr block 保持纯声明式

`blocks/*/template.html` 如果是 `data-*` 声明式 block，不要在里面写 Jinja 表达式。

```html
<!-- 不要这样 -->
<button>{{ t.actions.sendMessage }}</button>
```

应使用：

```html
<button data-i18n="actions.sendMessage">Send Message</button>
```

原因：一旦混入 Jinja，block 可能退回旧渲染路径，导致 `data-source` 列表无法展开，出现产品卡片空图、空标题、空摘要等问题。

开发后必须检查：

```powershell
@'
from app import create_app
from app.core.template_loader import scan_blocks
app = create_app()
with app.app_context():
    bad = [b['name'] for b in scan_blocks('<name>') if not b['is_data_attr']]
    print('non_data_attr_blocks:', bad)
'@ | python -
```

除非 block 明确是旧 Jinja 模板，否则 `bad` 应为空。

## 5. 数据集列表和详情要成套

列表页和详情页不能只完成其中一个。数据项至少应包含：

- `id`
- `slug`
- `title` 或 `name`
- `category`
- `summary`
- `description`
- `cover`
- `image` 或 `images`
- `tags`
- `date` 或 `price`
- `meta_label`

通用详情模块不要假设所有数据集都有 `price`。产品可以显示“Starting price”，文章可以显示“Published”，案例可以显示“Presented”。

## 6. 条目详情图片区必须支持多图交互

如果详情数据里有多张图片，详情图片区必须支持：

- 当前大图展示。
- 左右切换。
- 缩略图切换。
- 点击图片或放大按钮打开大图。
- 灯箱中继续左右切换。
- `Esc`、点击背景或关闭按钮退出。
- 单图时隐藏左右切换和缩略图。

模板内的 `item_detail` block 和独立详情模板（如 `product_detail.html`）要使用同一套 class 和初始化逻辑，避免首页 block 有交互、真实产品详情页却退回单图。

建议结构：

```html
<section class="item-detail-carousel">
  <div class="detail-carousel-stage">
    <div class="detail-images">
      <img class="detail-gallery-img">
    </div>
    <button class="detail-carousel-prev"></button>
    <button class="detail-carousel-next"></button>
    <button class="detail-zoom-btn"></button>
  </div>
  <div class="detail-thumbs"></div>
</section>
```

初始化脚本建议放在 `_base.html`，这样所有详情页面都能复用。

## 7. CSS 不能靠旧模板残留叠加

从旧模板复制新模板时，必须清理命名和视觉残留。

必须检查：

- 注释里不应继续出现旧模板名。
- 翻译 key 不应保留旧产品名，例如 `tryClaude`。
- CSS 不应残留旧主题主色、旧 hover 阴影、旧动画。
- 不要用一层新 CSS 覆盖大量旧规则后就交付；至少要追加明确的 final calibration layer，并清掉明显冲突规则。

常用检查：

```powershell
rg -n "Claude|Nova|tryClaude|rgba\\(204,120,92|animation:\\s*fadeInUp|box-shadow: var\\(--shadow-md\\)|letter-spacing:\\s*-" site_templates/<name>
```

注意：当前前端规范要求 `letter-spacing` 不使用负值，即使参考文档中分析了负字距，也要按项目规范处理。

## 8. 视觉规格要落到具体数值

实现时要把参考文档的组件规格写进 CSS，而不是凭感觉调。

以 Apple 模板为例：

- 顶栏：44px。
- section：桌面 80px，移动端 48px。
- 正文：17px / 1.47。
- hero 标题：最大 56px，小桌面 40px，手机 34px，小手机 28px。
- 栅格 gap：20-24px。
- utility card：18px radius，24px padding。
- 按钮：pill，11px 22px，最小 44px 高。
- 阴影：卡片不使用大阴影，产品图可以使用单一 drop-shadow。

不同参考文档有不同数值，但都必须这样落地。

## 9. 多语言必须是真正可预览

模板声明支持哪些语言，就要让这些语言都能完整预览：

- 头部语言切换后，中间预览内容要变。
- 菜单标签、页面正文、数据集记录、详情页、页脚都要对应语言。
- 公司信息、联系方式、页脚等全局内容也要考虑语言覆盖或保持合理通用。
- 不要只翻译 `translations.yaml`，页面和数据也要覆盖。

## 10. 交付前验证

每次模板改完至少跑这些验证：

```powershell
# YAML 解析
@'
import pathlib, yaml
for path in sorted(pathlib.Path('site_templates/<name>').rglob('*.yaml')):
    yaml.safe_load(path.read_text(encoding='utf-8'))
print('yaml ok')
'@ | python -

# 模板扫描 + 预览构建
@'
from app import create_app
from app.core.template_loader import scan_templates, scan_blocks
from app.core.builder import build_template_preview
app = create_app()
with app.app_context():
    print('<name>' in [t.name for t in scan_templates()])
    print([b['name'] for b in scan_blocks('<name>') if not b['is_data_attr']])
    print(build_template_preview('<name>', base_url='/templates/<name>/preview'))
'@ | python -
```

再检查构建产物：

- 首页和详情页没有 `src=""`。
- 没有 `href=""`。
- 主要文本节点不为空。
- 详情页多图交互结构存在。
- 不出现旧模板文案和旧产品文案。

如果环境支持浏览器自动化，最后再用 Playwright 截图检查桌面和移动端首屏、详情页图片区、灯箱、导航折叠。

## 11. 常见问题

- 列表卡片为空：通常是 data-attr block 里混入了 Jinja，导致 `data-source` 没展开。
- 首页没空，但详情页空：通常是 `item_data` 或详情模板假设了不存在的字段。
- 中文预览还是英文：通常只写了 `translations.yaml`，没有 `seed_data/lang/zh-CN/pages` 和 `data` 覆盖。
- 看起来不像参考站：通常 CSS 还混着旧模板的字号、间距、颜色、动画或阴影。
- block 首页有交互，真实详情页没有：通常 block 模板和 `product_detail.html` / `_generic_detail.html` 没同步。
