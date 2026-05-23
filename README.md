# trade-debt-skills

债权保全催收与股权投资尽调智能体技能包。Hermes Agent 技能集，适用于贸易业务风险管控与资产重组场景。

核心模型：DeepSeek V4 Flash

## 技能清单

### 核心业务
| 技能 | 说明 |
|------|------|
| **trade-debt-skill** | 债权催收专业知识体系：逾期账款催收策略、化债方案评估、法律程序跟进、股权投资尽调 |

### 信息采集
| 技能 | 说明 |
|------|------|
| **wechat-article-scraper** | 微信公众号文章抓取，可用于债务人背景调查、行业动态跟踪 |
| **xhs-sentiment-monitoring** | 小红书舆情监控，用于目标企业舆情监测、关联方信息采集 |
| **duckduckgo-search** | 网络搜索（全局技能） |

### 知识管理
| 技能 | 说明 |
|------|------|
| **karpathy-llm-wiki** | LLM Wiki知识库维护：lint体检、ingest消化资料、query全文检索 |
| **workspace-audit**（含在operations内） | 工作空间审计：目录清理、三步分流、文件归档、源文件深度学习 |
| **notion** | Notion读写与报告分发 |

### 公文写作
| 技能 | 说明 |
|------|------|
| **meeting-minutes** | 国企公文排版规范：字体层级、行距标准、语体风格 |
| **avoid-ai-writing** | AI写作痕迹审计与去除，确保公文自然可信 |

### 分析工具
| 技能 | 说明 |
|------|------|
| **maoxuan-skill** | 战略分析框架：矛盾分析、持久战策略，适用于谈判策略设计、化债方案推演 |
| **drawio-skill** | 流程图/架构图绘制：法律程序图、化债方案决策树 |

### 工具
| 技能 | 说明 |
|------|------|
| **nano-pdf** | PDF自然语言编辑：修改法律文书、会议纪要 |
| **windows-env-workflow** | Windows环境执行规范（含在operations内） |

### 展示
| 技能 | 说明 |
|------|------|
| **next-slide** | HTML演示文稿制作：汇报材料快速生成 |
| **html-report-to-visual-faithful-pdf** | HTML报告转视觉保真PDF |

## 架构原则

### 三步分流工作流

```
输出/（暂存层）
  ├─ ① 最终成果 → 归档至 源文件/（永久存档）
  ├─ ② 经验模式 → 沉淀至 wiki/（知识复用）
  ├─ ③ 运行产物 → 留在 输出/（工具/策略/数据）
  └─ ④ 其余 → 清理删除
```

### 环境变量

需配置以下 key 以确保技能正常运行（22项）：
- 大模型 API：DeepSeek、火山引擎
- 数据采集：Cloudflare、Tavily、Firecrawl
- 协作工具：Notion API
- GitHub发布：Personal Access Token

## 安装

将技能目录复制到目标 Hermes profile 的 skills 目录：

```bash
cp -r <skill-name> ~/.hermes/profiles/<profile-name>/skills/
```

或在 Hermes 中通过技能中心安装：

```bash
hermes hub install <skill-name>
```

## 维护

技能从 `land-of-dream-planning` 角色迁移复用，核心技能版本与上游保持一致。定期通过 `workspace-audit` 技能进行自检。

## 链接

- [GitHub 仓库](https://github.com/heropanda83017/-trade-debt-skills-Public-)
- [Hermes Agent](https://hermes-agent.nousresearch.com)
