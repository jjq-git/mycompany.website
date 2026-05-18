---
name: feedback-file-editing
description: 修改或新增文件前需询问用户确认
metadata:
  type: feedback
---

修改或新增文件前先询问用户确认，但不要在 IDE 中新开窗口展示文件内容。

**Why:** 用户希望把控文件变更，但不希望被打断工作流（新开窗口会干扰）。

**How to apply:** 每次 Edit/Write 操作前，简要说明要改什么文件、改什么内容，等用户确认后再执行。读取文件不受此限制。
