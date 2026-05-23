# 三步分流工作流：输出→源文件→wiki 文件管理体系

适用于任何需要管理「原始材料→中间产出→最终成果→知识沉淀」全链路的项目。

## 核心理念

```
源文件/ ──→ [读取+分析] ──→ 输出/ ──→ ① 最终成果 → 源文件/ 归档
                                     ├─ ② 经验模式 → wiki/ 沉淀
                                     ├─ ③ 运行产物 → 留在 输出/
                                     └─ ④ 其余 → 清理删除
```

三层存储各司其职，不越界：

| 层 | 存放什么 | 生命周期 | 示例 |
|----|---------|---------|------|
| **源文件/** | 原始材料 + 最终归档成果 | 永久 | 合同扫描件、汇报定稿、设计PDF |
| **输出/** | 暂存层的运行产物 | 工具在用期间 | 脚本、缓存DB、监控系统 |
| **wiki/** | 结构化知识 | 持续迭代 | entities/概念/方法论 |

## 目录命名规范

### 编号体系

一级目录统一使用 `0N-名称` 双位编号：

```
01-脚本/         运行工具（长期驻留输出/）
02-策略/         策略方案（暂存层）
03-数据/         运行时缓存
```

源文件/ 下的分类同理（01-债务人档案/、02-债权凭证/ … 09-参考素材/）。

### 核心原则
- 编号连续，不留空号
- 名称简洁，中文为主
- 不超过9个一级目录，超则需合并

## 输出/ 定期清理审计

当输出/ 累积到需要优化时，执行以下审计流程：

### Step 1：全量扫描

```python
from pathlib import Path

base = Path("E:/项目根目录")
for f in sorted(base.iterdir()):
    if f.is_dir():
        count = sum(1 for _ in f.rglob('*') if _.is_file())
        print(f"{f.name}/ — {count}个")
```

### Step 2：分类评估

| 类别 | 判断标准 | 去向 |
|------|---------|------|
| 最终成果（报告/方案/计划） | 已完成，不再修改 | → 源文件/ 对应目录 |
| 经验模式（方法论/模式） | wiki 未覆盖 | → wiki/ 对应页面 |
| 运行产物（脚本/DB/日志） | cronjob 或工具依赖 | 留在输出/ |
| 冗余（旧版本/空目录/依赖包） | 无引用 | 删除 |

### Step 3：执行分流

```python
import shutil

分流规则：
# ① 最终成果 → 源文件/
shutil.move("输出/某报告.md", "源文件/06营销/")

# ② 经验模式 → wiki/（提炼后创建页面）
wiki_content = "## 核心要点\n..."
with open("wiki/concepts/某方法论.md", 'w') as f:
    f.write(wiki_content)

# ③ 运行产物 → 留在输出/（不动）

# ④ 删除
os.remove("输出/冗余文件.md")
```

## 源文件/ 目录审计

### 诊断清单

```python
# 1. 根目录游离文件
root_files = [f for f in base.iterdir() if f.is_file()]
if root_files: print(f"根目录有 {len(root_files)} 个游离文件")

# 2. 空目录
for root, dirs, files in os.walk(base):
    if not dirs and not files and root != str(base):
        print(f"空目录: {os.path.relpath(root, base)}")

# 3. 特殊符号目录名
for root, dirs, files in os.walk(base):
    for d in dirs:
        if any(c in d for c in '☆★'):
            print(f"特殊符号: {os.path.relpath(os.path.join(root, d), base)}")

# 4. 重复文件（按内容哈希）
from collections import defaultdict
import hashlib

hash_map = defaultdict(list)
for f in base.rglob('*'):
    if f.is_file():
        h = hashlib.md5(f.read_bytes()).hexdigest()
        hash_map[h].append(f)

for h, files in hash_map.items():
    if len(files) > 1:
        print(f"重复 ({len(files)}份): {files[0].name}")
        for fp in files[1:]:
            print(f"  删除: {fp.relative_to(base)}")
```

### 命名规范化

```
# 特殊符号 → 普通字符
☆26年常规活动/  →  26年常规活动/

# 空目录 → 删除
os.rmdir(空目录路径)
```

## 跨 Profile 复用模式

当将一个项目中总结的经验复用到另一个 profile 时：

### 复用检查清单

| 可复用项 | 需要适配 | 示例 |
|---------|---------|------|
| 输出/ 目录结构 | 业务语义 | ideal-land: 01-脚本/02-舆情/03-数据 → trade-debt: 01-策略/02-脚本 |
| 三步分流工作流 | 路径和SOUL.md | 直接模板化写入新profile的SOUL.md |
| wiki 链接审计工具 | 无 | 扫描+修复代码可原样复用 |
| 源文件/ 清理模式 | 目录名 | 去重/删空/删特殊符的逻辑完全相同 |
| SOUL.md 文件保存规范 | 目录映射 | 模板化后替换路径和目录名 |

### SOUL.md 迁移模板

```markdown
# 三步分流工作流

产出物按以下路径分流：
① 运行产物（脚本/缓存） → 保留在 `暂存目录`
② 最终成果（方案/文书/汇报） → 归档至 `源文件/` 对应分类目录
③ 经验模式（方法论/框架） → 沉淀至 `wiki/` 对应页面

# 文件保存规范

正式产出物流转路径，按类别暂存：
- `01-xxx/` — xxx（长期驻留）
- `02-yyy/` — yyy（长期驻留）
- `源文件/01-分类/` — 最终归档
```

## 典型执行记录

| 项目 | 清理前 | 清理后 | 清理内容 |
|------|--------|--------|---------|
| 理想之地 | ~80文件/300MB+ | 16文件/260KB | 删.venv 189MB、删依赖库10.7MB、去重、空目录 |
| trade-debt | 87文件/321MB | 76文件/48MB | 删.venv 260MB、10组重复12.4MB、7个空目录 |
