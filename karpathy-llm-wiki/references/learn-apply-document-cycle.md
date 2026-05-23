# 学习实践闭环：学→用→记

> 用户胡盼的学习方法论：不学抽象理论，每项AI知识必须在实际工作中验证，然后写成实战笔记固化。

## 双循环模型

日常并行两条循环：

### 工作循环（每天执行）
```
① 源文件/ → 读取存量数据 + 用户输入新资料
② 生成成果到 输出/ + 同步更新 wiki
③ 稳定后归档到 源文件/ + 清理输出
```

### 学习循环（每完成一个技术任务触发）
```
① 复盘：刚才用到了什么AI知识？（Prompt/RAG/Agent/工具调用）
② 提炼：写成一篇实战笔记，放入 07-practices/
③ 归档：更新 index.md，关联到对应理论页面
```

## 实战笔记模板

```markdown
# 标题（从具体任务提炼）
## 一、场景描述
## 二、关键概念
## 三、实际案例（附代码/配置/数据）
## 四、经验总结
## 五、关联阅读
```

## 写入位置

- `E:/AIGC-KB/wiki/07-practices/` — 实战提炼笔记
- `E:/AIGC-KB/wiki/04-tools/prompt-templates-collection.md` — 高频场景Prompt模板

## 已完成笔记（2026-05-23）

| # | 触发任务 | 产出 |
|---|---------|------|
| 1 | 恒江雅筑维稳方案 → 总结工作流 | `hermes-agent-workflow-patterns.md` |
| 2 | wiki+Notion知识管理 → 总结RAG实践 | `rag-wiki-knowledge-retrieval.md` |
| 3 | 工具调用踩坑（CDP/Notion/GitHub API） | `agent-tool-calling-patterns.md` |
| 4 | 用户反复纠正写作风格 | `prompt-engineering-gov-doc-and-opinion.md` |
| 5 | 固化6个高频场景Prompt | `prompt-templates-collection.md`（04-tools/）|
