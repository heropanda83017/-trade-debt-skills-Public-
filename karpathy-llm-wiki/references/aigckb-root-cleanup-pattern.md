# AIGC-KB / Landofdream 根目录清理模式

## 原则

知识库根目录应只保留 `wiki/` 一个目录，其它杂物（配置/脚本/venv/空目录）要么移入 wiki 内部，要么删除或移到正确位置。

## 清理清单

| 项目 | 处理方式 | 说明 |
|------|---------|------|
| `.obsidian/` | 移入 `wiki/.obsidian/` | Obsidian 配置应在 vault 内部，不是在父目录 |
| `.venv/` (193MB) | 可删 | Python 虚拟环境，随时可重建 |
| `config/soul.md` | 移至 `~/.hermes/profiles/<name>/SOUL.md` | AI 角色配置应在 profile 目录下 |
| `scripts/` | 删除或归档 | 过时脚本未维护则删 |
| 空目录 | 直接删除 | 无任何文件的目录 |
| `venv/` | 可删 | 同 `.venv/`，可重建 |
| `desktop.ini` | 忽略 | Windows 系统文件 |

## 执行示例

```python
import os, shutil

root = 'E:/AIGC-KB'

# 移入 .obsidian
shutil.move(root + '/.obsidian', root + '/wiki/.obsidian')

# 移入 SOUL 配置
shutil.move(root + '/config/soul.md', 
            '~/.hermes/profiles/ai-investor/SOUL.md')

# 删除空目录
for d in ['Numpy', 'Pandas', 'projects', '源文件', '输出']:
    shutil.rmtree(root + '/' + d, ignore_errors=True)

# 删除无用目录
for d in ['scripts', 'venv', 'config']:
    shutil.rmtree(root + '/' + d, ignore_errors=True)
```

## 验收标准

清理后 `os.listdir('E:/AIGC-KB')` 应只返回 `['wiki/']`。
