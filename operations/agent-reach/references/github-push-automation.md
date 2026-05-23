# GitHub Push 自动化脚本

## 脚本位置
`E:\Landofdream\输出\06-脚本\github_push.py`

## 功能
用 Python requests 直接调 GitHub API，完成：
1. token 验证 → 获取用户名
2. 创建 private repo（含 auto_init）
3. 读取本地文件（脱敏路径后）
4. Git Data API 全流程：blob → tree → commit → ref update

## 使用前提
- 用户提供 GitHub PAT（`ghp_xxxx`），需要有 `repo` scope
- token 直接写在脚本里（**不上传**），运行时由 agent 注入
- `urllib.request` 是 Python 标准库，无需额外安装

## 脱敏规范
发布到 GitHub 前需脱敏：
- 本地绝对路径 → `/path/to/xxx`
- Cookie/token 凭据 → 不上传
- 具体数字 ID（如 cronjob ID）→ 酌情保留或脱敏

## 注意事项
- **gh CLI 无法做带 token 的自动化**（需要 `gh auth login` 交互式登录）
- **必须用 Python requests 直接调 GitHub API**
- repo 已存在时（"already exists"）跳过创建，继续推送文件
- 中文路径/文件名在 GitHub API 可能 422，改用英文名
