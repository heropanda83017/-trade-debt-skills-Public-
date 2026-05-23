---
name: karpathy-llm-wiki
description: 基于 Andrej Karpathy LLM Wiki 规范的知识库维护技能。支持多 vault（理想之地/AIGC-KB双库），对 wiki 做体检（lint）、消化新资料（ingest）、全文检索（query）。触发词：「lint一下wiki」「查一下wiki里关于XXX」「给wiki做个全身体检」「在AIGC-KB里搜XXX」。
version: "2.2"
author: hermes-agent
---

# Karpathy LLM Wiki 维护技能（多 vault 版）

基于 [Karpathy LLM Wiki 模式](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 构建的 wiki 维护系统。

## 核心理念

传统 RAG：每次问题从原始文档重新检索，LLM 每次"重新发现"知识。  
LLM Wiki：知识被编译一次，之后**积累复利**——交叉引用、矛盾标记、跨文档综合都提前做好。

### 销售驱动视角（理想之地专属）

wiki 以**促进销售**为核心目标，按四维驱动体系组织：
- 政策驱动（房票/学区/人才）→ 降低购房门槛
- 宣传驱动（舆情/品牌/媒体）→ 建立销售信任
- 活动驱动（圈层/商业/产品）→ 吸引到访转化
- 管理驱动（工程/物业/团队）→ 保障承诺兑现

详见 `index.md` 仪表盘设计。所有 wiki 养护工作围绕这个核心目标展开。

三层架构：
- **raw/** — 原始资料（Immutable，只读）
- **wiki 页面** — LLM 生成维护的 markdown（entities/concepts/queries）
- **SCHEMA.md / index.md / log.md** — 规范约定与导航

## 支持的 Vault

| 名称 | 路径 | 用途 |
|------|------|------|
| 理想之地 | `E:/Landofdream/wiki/` | 房地产营销项目知识库 |
| AIGC-KB | `E:/AIGC-KB/wiki/` | AI学习/量化/圈层运营/投资研究知识库（三方向框架） |

默认操作**理想之地**，在参数或函数调用中指定 `vault="AIGC-KB"` 可切换。

## 函数（通过 execute_code Python 执行）

### 1. wiki_lint(vault=None, focus_on=None) — 体检

检查三类问题：
- **孤立页面**：无入链也无出链
- **过时页面**：`updated` 日期早于文件修改日期（>7天）
- 字段一致性（统一 `updated` 而非 `last_updated`）

```python
wiki_lint()                        # 默认 vault（理想之地）
wiki_lint(vault="AIGC-KB")         # 指定 vault
wiki_lint(focus_on="concepts/")    # 只检查子目录
```

### 2. wiki_query(keyword, vault=None, limit=5) — 检索

基于文件名+内容正则匹配，返回按命中次数排序的页面列表。

```python
wiki_query("一初学苑")              # 默认双库搜索
wiki_query("Transformer", vault="AIGC-KB")  # 只搜 AIGC-KB
```

### 3. wiki_ingest(source_path, vault=None, ...) — 消化资料

把新文档写入指定 vault：
1. 读取源文件（.md/.txt/.docx），自动提取标题
2. 生成带 frontmatter 的 wiki 页面 → `entities/`
3. 更新 `index.md`
4. 追加 `log.md`

```python
wiki_ingest("E:/doc.docx", vault="AIGC-KB", category="activities")
wiki_ingest("xxx.pdf", dry_run=True)  # 预览，不实际写入
```

### 4. vault_status(vault=None) — 查看 vault 状态

```python
vault_status()           # 查看所有 vault
vault_status("AIGC-KB")  # 只看指定 vault
```

## 命令行用法

```bash
python wiki_lib.py lint [vault]
python wiki_lib.py query <关键词> [vault]
python wiki_lib.py ingest <文件路径> [vault]
python wiki_lib.py status [vault]
```

## 已知缺陷 ⚠️

### frontmatter 边界情况
`_get_fm()` 使用 `(?s)^---\n(.+?)\n---` 匹配。文件以 Markdown 标题开头（无空行隔开 frontmatter）时解析失败，需手动补充 frontmatter。

### 字段名统一
frontmatter 规范字段名是 **`updated`**，历史遗留的 `last_updated` 应替换为 `updated`。

### AIGC-KB 孤立页面较多是正常现象 ⚠️
AIGC-KB 是**学习笔记风格**的 vault，页面以 `[[wikilink]]` 互相引用的密度远低于理想之地项目 wiki。因此 `wiki_lint()` 报告的"孤立页面"数量对 AIGC-KB 无参考价值。判断标准：
- **理想之地**：孤立页面 = 真正未链接的悬浮页，需要修复
- **AIGC-KB**：孤立页面仅表示该页没有 wikilink，不代表内容有问题，忽略即可
### vault_status() 优先于 lint() ⚠️

首次操作任意 vault 前，**必须先运行 `vault_status()`** 确认：
1. vault 路径存在
2. 实际页面数量（排除 node_modules 等干扰目录后）
3. index.md / log.md 是否完整

AIGC-KB 未归档 `源文件/` 目录前曾有 5,418 个 .md 文件（其中 5,360 个是 node_modules），扫描前先确认跳过这些目录。

### 三中心图谱规则（2026-05-23 更新 v2）

index.md 只出链到三个中心页，不接受回链：index 是纯入口，图谱上只显示 3 条出链。中心页不包含 `[[index]]` 链接。内容页回链到所属中心，中心页互相链接（三角形结构）。04-tools 和 07-practices 作为共享工具节点不挂载到任何中心。

### AIGC-KB 三方向组织框架（2026-05-23 新增）

AIGC-KB 知识库按三个学习方向组织：

| 方向 | 核心目录 | 知识类型 | 更新频率 |
|------|---------|---------|---------|
| ① 理想之地实战 | 05-applications | 案例、模板、经验 | 每周（活动后） |
| ② AI基础系统学习 | 01-theory → 03-core-ai | 概念、原理、代码 | 学习周期 |
| ③ 金融投资 | 08-investment（6子目录） | 数据源、策略、分析 | 持续 |

### 信息四步闭环（2026-05-23 新增）

每条知识从获取到沉淀：获取（采集/阅读）→ 处理（分类/压缩/加链接）→ 积累（按三种模板入库+更新index）→ 进化（周六Notion消化+lint体检+季度合并）。

### 08-investment 投资研究目录结构（2026-05-23 新增）

```
08-investment/
├── README.md              # 总览
├── 01-数据源与工具/       # 爬虫/API/采集脚本说明
├── 02-投研分析/           # 研报框架/公司分析
├── 03-量化策略/           # 策略代码/回测
├── 04-宏观行业/           # 宏观指标/行业研究
├── 05-读书笔记/           # 投资类书籍笔记
└── 06-随堂笔记/           # 课程笔记（如迪哥AI量化）
```

各子目录文件超 10 个时按子主题拆分。

### AIGC-KB 学习笔记 Vault 定期养护

AIGC-KB 是与理想之地**完全不同性质**的 vault：学习笔记用文件夹+文件名组织，wikilink 密度极低。因此「孤立页面」是正常的，不需要修复。

#### 合并后内容质检清单（Post-Merge Content QA）

当从多个源文件合并为一篇后，**必须**执行以下 8 项检查（跳过任何一项都可能产生上次优化时发现的"配置文件里代码块嵌套+裸露命令"等问题）：

```python
# 检查清单（执行顺序排列）
checks = [
    # 1. 嵌套代码块检测
    ("嵌套代码块", lambda c: len(re.findall(r'^```', c, re.M)) // 2 !=
        sum(1 for m in re.finditer(r'^```(\w*)\n(.*?)\n```', c, re.DOTALL | re.M)
            if '```' not in m.group(2))),

    # 2. 裸露命令检测
    ("裸露命令", lambda c: any(
        l.strip().startswith(p) for p in ['pip ', 'sudo ', 'npm ', 'git ',
        'docker ', 'wget ', 'curl ', 'pnpm ', 'conda ']
        for l in _outside_blocks(c))),

    # 3. 编号体系冲突检测
    ("编号冲突", lambda c: len({_detect_numbering(c)}) > 1),

    # 4. 代码块语言标注检测
    ("语言误标", lambda c: bool(re.search(r'^```python\n(?:[^#]|#.*sudo |#.*apt )',
        c, re.M))),  # python块里出现bash命令

    # 5. 重复内容检测（合并源尾部的"冗余总结"）
    ("重复尾部", lambda c: _count_repeated_tail(c)),

    # 6. index.md 死引用检测
    ("死引用", lambda c: any(
        os.path.exists(re.sub(r'\[\[(.+?)\]\]', r'\1', link)) == False
        for link in re.findall(r'\[\[(.+?)\]\]', c)
    )),

    # 7. 合并说明残留检测（"合并自XXX三篇"）
    ("合并注释", lambda c: '合并自' in c and '合并自' in c.split('\n')[5:]),

    # 8. 文件大小合理性（合并后不应膨胀超过预期2倍）
    ("体积异常", lambda c: len(c) > sum(
        os.path.getsize(f) for f in _source_files) * 2),
]
```

**典型修复模式（基于本次4-tools三篇合并实战）：**

| 问题 | 检测方式 | 修复方式 |
|------|---------|---------|
| 嵌套代码块 | `re.findall(r'```', c)` 成对计数与实际代码块数不一致 | 将外层多余的 ` ``` ` 删除，或用 `re.sub` 折叠多层嵌套 |
| 裸露命令 | 遍历非代码块行的前4个字符与命令前缀匹配 | 包裹 ` ```bash ... ``` ` |
| 编号冲突 | 同时检测 `## 一、`、`### 1.1`、`## ✅` 模式 | 统一为 `1.1/2.1/3.1` 编号体系 |
| 代码块语言误标 | ```` ```python ```` 块内有 `apt install` / `sudo` / `export` 等bash命令 | 改为 ```` ```bash ```` 或拆分为语言+说明注释 |
| 重复尾部 | 文件尾部出现独立于章节的✅方案一/二/三等重复总结 | 删除，保留章节之内的内容即可 |
| index.md死引用 | 引用路径对应的 .md 文件不存在 | 删除引用项或更新路径 |

**工具链：** 上述检查在 `execute_code` 中通过 Python + `re` 模块执行，无需额外依赖。`write_file` 和 `read_file` 在 Windows E: 盘路径下可能因 MSYS git-bash 内部 `cd` 失败而不可用，改用 `execute_code` + Python `open()` 读写。

但长期使用后会出现以下问题，需按季度养护或按需执行：

#### 养护三步法

```
Step 1: 按目录逐篇审阅
  逐篇读取，判断每篇质量：
  - <500字且内容不完整 → 标记删除
  - <1500字且内容太薄 → 标记合并
  - 内容充实 → 保留

Step 2: 合并/删除执行
  同目录下相似主题 → 合并为一篇
  跨目录补关系 → 理论合入实践篇
  学习资源类 → 合入学习路径
  太薄的独立文件 → 直接删除

Step 3: 目录编号重排
  删除合并后检查空缺：
  确保 01-08 连续不断号
  更新 index.md 中的路径引用
```

#### 跨目录合并的具体判断

| 源文件 | 目标文件 | 理由 |
|--------|---------|------|
| AI学习推荐渠道 → 学习路径 | 路径讲顺序，渠道讲来源 | 互补 |
| RAG原理 → RAG实战笔记 | 概念+实战合并为一本通 | 完整 |
| 数学基础三篇 → 数学基础 | 同一主题拆分过细 | 合并 |

#### 文件瘦身判定标准

```
判定删除（任一）：
  字数 < 500 且无实质内容（仅有外部链接或标题）
  文件名与内容不符（标题是TF但内容是npm配置）
  仅有外部链接无自主内容

判定合并（任一）：
  字数 < 1500 且与已有主题重合
  内容互补（理论+实践、路径+资源）
  同一课程系列的拆篇笔记
```

#### 三种合并模式详解

实践中发现三种不同合并模式，需区别对待：

**模式A：多小文件→合集（案例集模式）**

适用场景：10+ 个结构高度相似的小文件（如活动案例/事件记录），每篇 < 1,500 字且遵循相同模板。

执行步骤：
```
Step 1: 读取所有源文件，识别共同结构（如：基本信息/活动内容/效果总结/经验沉淀）
Step 2: 建立分类索引表，按主题/类型/时间分组，方便快速定位
Step 3: 将每个文件转为一个二级标题 `## [标题]`，保留原始内容
Step 4: 更新引用它的父文件（README/RAG配置说明），指向新合集
Step 5: 删除源文件目录，确认无残留引用
```

**模式B：单文件子目录→合并入父README（目录瘦身模式）**

适用场景：子目录下仅有 1 个文件（如 templates/ 或 practices/ 各只有 1 篇），独立成目录过重。

执行步骤：
```
Step 1: 读取该单文件，嵌入父 README 的对应小节
Step 2: 确保 README 的文件结构表不再引用已删除的目录
Step 3: 删除子目录
```

**模式C：跨目录文件迁移（学习笔记归类模式）**

适用场景：某个目录下的文件实际属于另一目录的类别（如 quant 下的课程笔记应归入 reading-notes）。

执行步骤：
```
Step 1: 确认目标目录已有同类文件，或结构上适合承接
Step 2: 使用 shutil.move() 迁移文件（保留 Git 历史）
Step 3: 在目标目录的 section 下更新 index.md 引用
Step 4: 源目录如只剩 1 个文件则保留，如变空则删除
```

#### 合并后清理顺序

每次合并/删除后必须按以下顺序执行，否则 index.md 会产生死引用或文件残留：

```python
# 1. 先创建新文件（合集/README/迁移目标）
# 2. 更新父目录 README 中的文件结构表
# 3. 删除旧文件/旧目录（shutil.rmtree）
# 4. 更新 index.md 中的对应章节
# 5. 走一遍 Post-Merge Content QA 清单
# 6. （AIGC-KB 专有）检查 category/type frontmatter 标签是否准确
```

**典型执行示例（2026-05-23 05-applications 瘦身）：**

| 操作 | 文件数变化 | 备注 |
|------|-----------|------|
| 13 个 case-studies → 1 个合集 `圈层活动案例集.md` | 13 → 1 | 模式A，含分类索引表 |
| templates/ (1文件) → 合入 README | 1 → 0 | 模式B |
| practices/ (1文件) → 合入 README | 1 → 0 | 模式B |
| 4 篇 迪哥AI 课程笔记 → 06-reading-notes | 4 → 移出 | 模式C |
| applications-agent/ (空) | 1 → 0 | 直接删除 |
| **合计** | 22 文件 → 4 文件 | 内容零损失 |

#### 从待办/笔记提取为可复用模板

适用场景：速记.txt/桌面笔记/Notion待办中有结构清晰的任务描述，需要转化为 `{{变量}}` 格式的模板加入 AIGC-KB wiki。

**模板化四步法**

```
Step 1: 识别结构化元素
  从原始任务描述中提取：
  - 输入参数（工具列表、角色名、环境名等）
  - 步骤流程（第1步、第2步…）
  - 输出格式（表格、报告、清单等）
  - 约束条件（时间范围、数量、风格等）

Step 2: 确定变量字段
  将实例值（如"akshare、Tavily、Firecrawl"）替换为 {{变量}} 占位符
  规则：凡在不同场景下会变化的值 → 变量；不变的逻辑骨架 → 保留

Step 3: 补充实际案例参数
  在模板末尾加「实际案例参数」小节，记录首次使用的真实值
  方便后续复用者理解变量的含义和格式

Step 4: 附加到对应模板集文件
  1. 读入目标 .md 文件
  2. 在最后一个模板的 --- 分隔线后面追加新模板
  3. 更新文件标题/描述（如从「6模板」改为「10模板」）
  4. 更新 index.md 中的引用描述
```

**实战案例（2026-05-23 速记→模板转化）**

| 速记原文 | 模板 | 关键变量 |
|---------|------|---------|
| ai-investor 角色创建任务（4条特质） | 模板七：创建AI角色 | 领域/赛道/数据类型/产出类型 |
| akshare/Tavily/Firecrawl 数据源配置（6条要求） | 模板八：数据源集成配置 | 工具列表 |
| WSL→Windows 迁移自检清单（5步） | 模板九：系统迁移自检 | 角色名/目标环境/原环境 |
| 系统定期自检（4模块） | 模板十：系统定期自检 | 检查模块 |

**模板质量审查标准**

追加到文件后检查：
1. 变量占位符统一使用 `{{双花括号}}`，不含空格
2. 模板正文和实际案例参数之间用 `---` 分隔
3. 验证次数标记为「待验证」直到实际使用过
4. 模板描述不涉及具体 API Key、密码等敏感信息
5. 在 index.md 的对应章节更新文件描述

**模板交叉验证（2026-05-23 新增）**

追加到文件后，对每个新模板依次执行：

```
① 变量语义检查
   逐个阅读 {{变量}}，判断两个变量是否指向同一概念（如{{领域}}与{{具体赛道}}实质重叠）
   修复：合并为同一变量，案例参数同步去掉冗余行

② 输出示例检查
   模板仅描述「做什么」而没有「做出来长什么样」→ 在案例参数后补充示例输出片段
   示例输出目的是展示格式模板（表格/清单/结构），不是展示具体数据

③ 模板完整性检查
   模板内的指令在不同参数场景下是否都成立？
   （如 {{工具列表}} 中假设有4个工具，但使用者可能只传2个→ 加"如"字示例或注明灵活调整）

④ 敏感信息兜底
   速记/检查的内容中是否有 API Key、Token、密码等被顺手带入模板？
   正则扫描：`sk-`、`ghp_`、`cfut_`、`tvly-`、`fc-` 等模式
```

**源文件清理指引（2026-05-23 新增）**

模板转移到目标文件后，源文件（如速记.txt/桌面笔记）中已迁移的部分应同步删除，保持源文件只保留未迁移内容。

清理原则：

```
1. 定位已迁移区段（按标题/关键词定位，不要模糊匹配）
2. 截取：保留"第一个迁移区段之前"的所有内容 → 丢弃迁移区段
3. 核查剩余内容：
   - API Key/Token/密码 → 保留在源文件（不应进 wiki）
   - 快捷命令/别名 → 保留在源文件
   - 待办事项 → 保留（未处理的独立待办，不与模板重叠）
4. 最终源文件仅保留：配置密钥 + 操作命令 + 未处理待办
```

### 章节删除操作流程

当审阅发现某章节内容不适用需删除时，执行：

#### 适用性评估标准| 通用知识（如"什么是 Linux"、"Docker 概念"） | ❌ 删除 | wiki 定位是实战指引，不是教科书 |
| AI生成的思维推导草稿（如量化策略推演文） | ❌ 删除 | 用户判断标准：未经实战验证的推演不保留 |
| 代码未实际跑过的策略或方案 | ❌ 删除 | 用户判断标准：代码必须实际执行过 |
| 已验证的模板 | ✅ 保留 | 原样不动，只改编号和标题 |

#### 删除执行步骤

```
1. 定位待删除章节的起止行（从 ## 标题到下一个 ## 标题或文件末尾）
2. 截取文件内容：保留前段 + 后段，删除中间
3. 更新文件标题/描述（删除后的文件定位变化了需反映）
4. 检查 index.md 引用描述是否需要同步更新
5. 代码块计数验证：删除后不应出现裸露命令或嵌套代码块
```

#### 例外情况

- 第二章内的高度复用模板（经过 1-7 次验证）→ **不要改动正文，只改外围结构**
- 模板内部带 `## 输入/## 结构/## 约束` 等结构标记 → 这些属于模板语法，不是章节标题，不要误删

## Notion → Wiki 每周消化工作流（周六例行）

用于"理想之地"项目每周的 Notion 工作记录消化。胡盼的工作记录以无标题 Notion 页面形式存在（搜索关键词：`工作记录`、`2026年5月`等），内容涵盖学校、工程、圈层、人事等多类信息。

### 三步流程

```
Step 1: 读取 Notion 本周记录
Step 2: 筛选值得沉淀的内容 → ingest 进 wiki（entities/ 页）
Step 3: wiki_lint 体检，修复链接损坏
```

### Step 1 细节：Notion 读取

Notion 页面标题常为空，需通过内容关键词搜索定位。使用 `notion_client` Python 库：

```python
from notion_client import Client
client = Client(auth=os.getenv('NOTION_API_KEY'))
# 搜索本周记录
res = client.search(query="工作记录", page_size=10)
# 筛选最近编辑的页（last_edited_time）
for p in res.get('results', []):
    blocks = client.blocks.children.list(block_id=p['id'])
    # 取前1-5个 rich_text 块判断内容主题
```

**注意：** 在 Windows 环境下，通过 `execute_code`（Python subprocess）调用 Windows Python 解释器执行 Notion API 操作（`C:\Program Files\Python312\python.exe`）。不要使用 WSL/terminal 的 python3，因为 noton-client 包安装位置不同。

### Step 2 细节：筛选原则

| 内容类型 | 是否沉淀 | 理由 |
|---------|---------|------|
| 学区/学校进展（教育局沟通、工程动态） | ✅ 沉淀 | 影响项目核心卖点，需实时更新 |
| 圈层活动合作（新渠道/新资源） | ✅ 沉淀 | 补充圈层活动体系 |
| 内部人事/个案协调 | ❌ 不沉淀 | 临时性/内部管理 |
| 工程建设进展 | ✅ 沉淀 | 更新 entities/project-engineering.md |

对应更新目标：

| 主题 | 目标 wiki 页 |
|------|-------------|
| 学区进展 | `entities/yichuxueyuan.md` |
| 学校工程进展 | `entities/project-engineering.md` |
| 圈层活动/金融合作 | `entities/circle-activities.md` |
| 营销数据 | `entities/sales-funnel.md` / `entities/daily-sales-data.md` |
| 品牌事件 | `entities/brand-events.md` |

### Step 3 细节：wiki_lint 手动检查项

当 `wiki_lint()` Python 函数不可用时（如 Windows 下工具链不完整），手动执行以下检查：

1. **文件完整性**：`os.walk()` 遍历所有 .md 文件，检查是否有空文件 (<10 bytes)
2. **Frontmatter 检查**：是否以 `---` 开头，是否包含 `title:`、`created:`、`type:` 字段
3. **Wiki 链接完整性**：`re.findall(r'\\\\[\\\\[([^\\\\]]+)\\\\\\]\\\\]', content)` 提取所有链接，逐个检查目标文件是否存在（不区分大小写）。注意排除 `log.md` 和 `SCHEMA.md` 中的模板文本 `[[wikilinks]]`（误报）
4. **常见格式错误**：`[[page\\\\|display]]`（末尾多余反斜杠）→ 应修复为 `[[page|display]]`。修复命令：
   ```python
   re.sub(r'\\[\\[([^\\]|]+)\\\\\\|', r'[[\\1|', content)
   ```
   常见于 Obsidian 格式迁移后的遗留问题，影响 3 个核心文件（`1-plus-235-system.md`、`ideal-land-project.md`、`weekly-report-*.md`）
5. **孤立概念检查**：检查 wiki 链接指向不存在的页面（如 `[[高线云廊]]`），标记为待建页面
6. **过时文件**：检查 `updated` 字段是否超过 90 天未更新

### Step 3b：链接网络审计（增强版）

当需要系统性地优化 wiki 链接体系时，执行以下审计：

```
① 遍历所有核心页（entities/ + concepts/），对每个页面统计：
   出链数 = len(re.findall(r'\[\[([^\]]+)\]\]', content))
   入链数 = 反向索引中指向本页的页面数量

② 识别三类问题：
   🔴 孤立页：出链=0 且 入链=0 → 要么删除，要么加链接
   🟡 单向页：出链>0 但 入链=0 → 需从相关页面链入
   🟢 双向页：出链>0 且 入链>0 → 健康

③ 修复顺序：🔴 优先 → 🟡 次要 → 🟢 维护
```

**经验值：** 35页左右的 wiki，理想状态是所有核心页均为 🟢。🔴 和 🟡 合计不应超过 5 个。

### Step 3c：内容重叠检测（季度级养护）

当需要判断两个页面是否可以合并时，执行以下分析：

```python
# 1. 提取两页正文（去掉 frontmatter）
# 2. 提取所有 2 字以上中文词（re.findall(r'[\u4e00-\u9fff]{2,}', content)）
# 3. 计算重叠率 = len(词A ∩ 词B) / len(词A)
```

**参考阈值：**
- 重叠率低于 10% → 内容差异大，不合并
- 重叠率 10%-30% → 上下游关系，加强双向链接即可
- 重叠率高于 30% → 考虑合并为一个页面

### Step 3d：散落页面清理流程

`raw/`、`events/`、`queries/` 等非核心目录的页面如果无人链接，应按以下流程处理：

```
① 判断页面是否还有价值：
   - 小于 500 字且内容不完整 → 直接删除
   - 有参考价值但信息量少 → 合并到关联的核心实体页，然后删除
   - 完整的独立内容 → 保留并确保被核心页链入

② 更新链接：在关联的核心页上加 [[page_name|description]] 链接
③ 清理空目录：删除空了的子目录
```

### Windows 环境已知限制与兜底

| 工具 | 限制 | 兜底方案 |
|------|------|---------|
| `read_file` | E:\ 路径解析失败 | 用 `execute_code` + Python `open()` |
| `search_files` | 需要 ripgrep (rg) | 用 `execute_code` + Python `os.walk()` + `glob` |
| `terminal` git-bash | cd 到 C:\Users 路径失败 | 用 `execute_code` 运行 Windows Python subprocess |
| `patch` | 正则匹配可能因转义字符失效 | 用 `execute_code` 里的 `re.sub()` |

### 阅读笔记分类工作流（AIGC-KB 专用）

详见 `references/reading-notes-categorization.md`。

原则：按「认知方法论」和「AI技术」二分法归类。认知方法论类笔记顶部加「核心观点速查」表格（3-5条，含「可用在哪」列）。同课程多篇笔记合并为单篇。

### 学习实践闭环工作流

详见 `references/learning-practice-loop.md`。

### 方法论工具嵌入工作流（2026-05-23 新增）

认知方法论类笔记的「核心观点速查」不应止于笔记内——应进一步嵌入日常工作流的 Prompt 模板，实现「读了就能用，用了就提升」的闭环。

#### 三步嵌入法

```
Step 1: 从读书笔记提取可操作工具
  从「核心观点速查」中筛选出能直接执行的工具卡：
  - 有明确操作步骤（几步做、什么时候用、检验标准）
  - 对应一个具体工作场景（写方案/汇报/复盘/沟通）
  - 排除纯认知框架（只改变思维方式，不改变操作流程的）

Step 2: 映射到现有工作流模板
  为每个工具卡找到最匹配的模板：

  | 工具卡 | 适合嵌入的模板 | 嵌入位置 |
  |--------|---------------|---------|
  | 思考环六步法 | 模板二：方案撰写 | 写前思路梳理 |
  | 删减清单 | 模板二：方案撰写 | 写后质量检查 |
  | 沟通四层次诊断 | 模板三：话术手册 | 输出质量检查 |
  | ABC 决策复盘 | 模板四：会议记录 | 整体跟进建议 |
  | T字形三问 | Hermes 通用 Prompt | 关键假设追问 |
  | 认领任务三问法 | 团队工作流 | 任务布置阶段 |

Step 3: 嵌入模板并做格式适配
  工具卡原文 → 适配为可嵌入的格式：
  - 保留核心步骤（去掉过度理论化的背景说明）
  - 保留检验标准
  - 转为模板内可执行的指令（用 ☐ 检查清单或 ## 分步指令）
  - 目标受众：使用模板的人需要看完就知道怎么自检
```

#### 嵌入后的模板结构变化

```
嵌入前：
  ## 输入 → ## 处理规则 → ## 输出格式

嵌入后：
  ## 输入 → ## 写前思路梳理（新） → ## 处理规则 → 
  ## 输出格式 → ## 写后质量检查（新）
```

#### 创建独立速查卡

当嵌入的模板覆盖 5+ 个技能场景时，创建独立速查卡文件（`07-practices/工作技能优化速查卡.md`）：

```
结构：技能一→技能二→…→技能N
每项技能：痛点 → 优化工具 → 具体步骤 → 可嵌入 Prompt 指令
末尾：工具卡速查索引表（场景→卡名→来源）
```

#### 验证标准

```
① 嵌入后模板运行一次，输出质量是否高于嵌入前？
② 用户是否愿意继续使用而不是再改回旧模板？
③ 工具卡的理论来源是否在嵌入过程中丢失了核心信息？
   → 如果工具变成了"形式化检查"，说明嵌入深度不够
```

### 配套参考文件

- `references/three-center-graph-pattern.md` — Obsidian 图谱三中心结构模式（index→中心→内容页三层链接，避免单中心星爆图）
- `references/notion-weekly-ingest-example.md` — 本工作流的完整执行示例（代码+日志）
- `references/wiki-link-audit-20260523.md` — 链接网络审计实战记录（含代码模板、修复模式、散落页处理流程）
- `references/aigckb-vault-audit.md` — AIGC-KB 学习笔记 vault 审计实战记录（目录编号去重、Index完整度、关键词分布检测）
- `references/learn-apply-document-cycle.md` — 学习实践闭环：学→用→写，每完成一个技术任务生成一篇实战笔记
- `references/skill-github-sync-pattern.md` — GitHub API 直推技能更新模式（git 不可用时的替代方案）
- `references/aigckb-root-cleanup-pattern.md` — AIGC-KB/Landofdream 根目录清理模式（只保留 wiki/ 目录）
- `references/pdf-knowledge-extraction.md` — PDF 知识提取→wiki 更新管线（pymupdf+关键词过滤，从大型设计PDF中提取设计理念知识）
- `references/three-way-file-workflow.md` — 三步分流工作流：输出→源文件→wiki 文件管理体系（含目录审计、跨profile复用模式）