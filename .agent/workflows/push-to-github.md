---
description: 提交代码到 GitHub 仓库
---

# 提交代码到 GitHub 仓库

这个 workflow 用于将当前项目的所有文件提交到 GitHub 仓库。

## 前置条件

- 已配置 SSH 密钥并添加到 GitHub 账户
- 已在 `~/.ssh/config` 中配置了 GitHub SSH 别名（如 `github-gigclanmac`）

## 步骤

### 1. 检查 Git 状态

```bash
git status
```

### 2. 检查远程仓库配置

```bash
git remote -v
```

### 3. 如果没有远程仓库，创建 GitHub 仓库并添加远程源

首先在 GitHub 上创建同名仓库（仓库名与文件夹名相同），然后执行：

```bash
git remote add origin git@github-gigclanmac:YOUR_USERNAME/REPO_NAME.git
```

将 `YOUR_USERNAME` 替换为你的 GitHub 用户名，`REPO_NAME` 替换为仓库名称。

### 4. 初始化 Git 仓库（如果尚未初始化）

```bash
git init
```

### 5. 添加所有文件到暂存区

// turbo
```bash
git add .
```

### 6. 提交更改

```bash
git commit -m "Initial commit: 添加项目所有文件"
```

或使用更具体的提交信息：

```bash
git commit -m "你的提交信息"
```

### 7. 设置默认分支为 main（如果需要）

```bash
git branch -M main
```

### 8. 推送到远程仓库

```bash
git push -u origin main
```

如果是首次推送，使用 `-u` 参数设置上游分支。后续推送只需：

```bash
git push
```

## 常见问题

### 如果推送被拒绝（远程有更新）

```bash
git pull --rebase origin main
git push
```

### 如果需要强制推送（谨慎使用）

```bash
git push -f origin main
```

### 查看提交历史

```bash
git log --oneline
```

### 查看远程仓库信息

```bash
git remote show origin
```

## 注意事项

- 确保 `.gitignore` 文件已正确配置，避免提交不必要的文件（如 `node_modules/`, `.DS_Store` 等）
- 首次推送前，确认 GitHub 仓库已创建
- 使用有意义的提交信息，便于后续追踪
