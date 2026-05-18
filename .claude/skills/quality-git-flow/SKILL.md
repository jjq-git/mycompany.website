---
description: "Git 操作规范(提交/分支/PR/打 tag)"
---

当用户说"提交代码"、"创建分支"、"合并"、"发 PR"时触发.
标准化 git 操作,遵循项目的提交信息约定和分支策略.

提交信息约定(CLAUDE.md 第九节):
- 中文,简洁
- 说"为什么"而不只是"什么"
- 格式:`<type>: <简短说明>`

## 提交信息格式

格式:`<type>: <简短说明(为什么而不只是什么)>`

type 类型:
| type | 用途 | 示例 |
|------|------|------|
| feat | 新功能 | `feat: 增加字体子集化(首屏字体从 9MB 降到 15KB)` |
| fix | 修 bug | `fix: 修复发布时旧字体文件未清除导致的乱码` |
| refactor | 重构(不改行为) | `refactor: 简化模板加载逻辑,去掉未使用的扩展点` |
| docs | 文档 | `docs: 调整产品定位,明确不做整页所见即所得编辑器` |
| chore | 杂项(依赖、配置) | `chore: 更新 Pillow 到 10.x` |
| style | 代码风格(不影响逻辑) | `style: 统一缩进为 4 空格` |

提交信息规则:
- 一行标题,50 字以内
- 必要时空一行写详细说明(如果一行说不清楚"为什么")
- 不写"修改了 X 文件"(git diff 已经能看)
- 不写"根据需求调整"(太笼统)

示例对比:
```
好:feat: 图片上传时自动转 WebP(5MB PNG → 200KB WebP)
坏:更新了图片处理功能
好:fix: 模板扫描跳过 .DS_Store 隐藏文件
坏:修了个小 bug
```

## 分支策略

当前项目结构:
- `main`:稳定分支(可部署)
- `dev-YYYYMMDD`:开发分支(当前在 `dev-20260514`)

新建功能分支:
```
git checkout -b feat/font-subsetting
git checkout -b fix/image-upload-bug
git checkout -b refactor/template-loader
```

分支命名:
| 前缀 | 用途 |
|------|------|
| feat/ | 新功能 |
| fix/ | 修 bug |
| refactor/ | 重构 |
| docs/ | 文档 |
| chore/ | 杂项 |

## 提交前检查

提交前确认:
1. 不提交敏感文件(`.env`、`instance/`、`uploads/`)
2. 不提交构建产物(`output/`)
3. 不提交站点数据(`sites/`)
4. 不提交依赖包(`venv/`、`node_modules/`)

这些都在 `.gitignore` 中,但提交前还是确认一下:
```
git status
```

如果 `git status` 显示了不该提交的文件,检查 `.gitignore`.

## 创建提交

1. 暂存变更(按文件选择,不用 `git add -A`):
   ```
   git add app/core/builder.py docs/publish.md
   ```

2. 提交:
   ```
   git commit -m "feat: 说明为什么改"
   ```

3. 如果 pre-commit hook 失败:
   - 阅读 hook 输出的错误信息
   - 修复问题后重新 `git add` + `git commit`(创建新 commit,不是 amend)
   - 绝对不要用 `--no-verify` 跳过 hook

## 查看历史

```
# 最近 10 条提交
git log --oneline -10

# 查看特定文件的变更历史
git log --oneline -- app/core/builder.py

# 比较当前分支和 main 的差异
git diff main...HEAD

# 查看某次提交的详细内容
git show <commit_hash>
```

## 创建 PR

```
gh pr create --title "feat: 简短说明" --body "$(cat <<'EOF'
## 概述
<做了什么,为什么>

## 变更文件
- <文件>:<改了什么>

## 验证
- [ ] 构建测试通过
- [ ] 预览功能正常
- [ ] ZIP 导出可用
- [ ] 不影响已有站点
EOF
)"
```

## 禁止操作

来自 CLAUDE.md 禁止事项 + Git 安全操作:

| ❌ 禁止 | 原因 |
|----------|------|
| `git push --force` 到 main | 破坏协作基础 |
| `git rebase -i`(交互式变基) | 不可逆地修改历史 |
| `git reset --hard` | 丢失未提交的工作 |
| `git commit --amend`(对已推送的 commit) | 造成历史不一致 |
| `--no-verify` 跳过 hook | hook 存在是有原因的 |
| 修改 git config | 保持项目配置一致 |
| `git add -A` 或 `git add .` | 可能包含不该提交的文件 |

## 关联技能

- `review-code`:提交前的代码审查
