# 设计参考 (Design References)

本目录存放**外部网站模板的设计系统分析**，作为本项目网站模板（访客展示端）的设计参考。

每个文件对应一个外部网站/模板，提取其设计令牌（颜色、字体、间距、组件规格等），供开发者在制作 `site_templates/` 下的模板时参考。

## 文件列表

| 文件 | 来源 | 核心特征 |
|---|---|---|
| [apple.md](apple.md) | apple.com | 摄影优先的"美术馆"式展示 —— 全幅产品卡片明暗交替、单一 Action Blue 强调色、SF Pro 负字间距标题、仅一个产品投影 |
| [airbnb.md](airbnb.md) | airbnb.com | 温暖慷慨的消费市场 —— 纯白画布 + Rausch 珊瑚红单色电压、Cereal VF 柔和字重、全胶囊圆角搜索栏、摄影主导的房源卡片 |
| [notion.md](notion.md) | notion.so | 纸张般平静的生产力系统 —— 暖灰白画布 + NotionInter 紧密负字距标题 + 单一蓝色 CTA + 多彩 sticker 调色板纯装饰 |
| [linear.app.md](linear.app.md) | linear.app | 深黑产品画布（#010102）的暗色营销系统 —— 薰衣草蓝单色强调 + 四级表面阶梯承载层级 + 产品 UI 截屏为主角 |
| [claude.md](claude.md) | claude.com (Anthropic) | 暖奶油色画布 + 珊瑚色主 CTA + Copernicus 衬线展示字体的编辑风格设计系统（[中文版](claude.zh.md)）|

## 用途

- **不是直接复制**：这些是分析材料，不是代码。模板开发时参考其设计决策和氛围营造手法
- **每个模板可对应一个参考**：如 `apple.md` 对应偏摄影展示风的模板，`linear.app.md` 对应偏暗色产品风的模板，`notion.md` 对应偏文档/生产力风的模板
- **公共设计词汇表**：让团队讨论"这个模板要什么感觉"时有共同语言

> 新建模板前，请先阅读 [新模板开发规范清单](../template-development-checklist.md)。设计参考解决“像什么”，规范清单约束“必须完整到什么程度”。

## 添加新文件

1. 分析目标网站，提取设计令牌（颜色、字体、间距、圆角、组件）
2. 以 YAML frontmatter + Markdown 说明的格式写入，文件名按来源小写命名（如 `stripe.md`）
3. 在本 README 的文件列表中按字母顺序插入一行
