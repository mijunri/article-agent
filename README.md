# 热点抓取-分析-生成-分发 系统技术设计

本文档定义系统的模块划分、接口契约、数据模型、配置与运维要点，指导实现“抓取热点 → 分析打分 → 文章生成 → 分发输出”的流水线。面向后端/数据/内容工程师。

## 架构总览
- 形态：批处理流水线（可扩展为准实时）。
- 流程：Source Connectors → 规范化 → 去重/缓存 → 分析与打分 → 选题 → 内容生成（LLM 可选）→ 分发/存储 → 监控与审计。
- 设计原则：可插拔、幂等、可观察、配置驱动、失败可恢复。

## 模块划分
### 1. Source Connectors（数据源适配）
- 目标：对接多种热点来源（RSS/API/HTML），拉取原始条目并输出统一 Topic。
- 示例来源：Google Trends、Hacker News、微博热搜、知乎热榜、B站热榜、Twitter/X、Reddit、新闻媒体RSS等。
- 接口：`List[Topic] fetch(params: Dict) -> List[Topic]`
- 关键点：
  - 网络重试与超时、速率限制、代理与UA。
  - 解析健壮性与降级；来源特定热度信号通过 tags 扩展。

### 2. Normalization（规范化）
- 目标：统一字段、时间时区、文本清洗与长度裁剪，生成稳定 id（hash(source+title+url)）。
- 接口：`List[RawItem] -> List[Topic]`

### 3. Dedup & Cache（去重与缓存）
- 目标：同批/跨批去重，避免重复生成；短期缓存避免重复抓取。
- 策略：键为 `(title_norm, url_or_empty, source)`；TTL 可配（如48h）。
- 存储：内存/本地KV（开发）；Redis/SQLite（生产）。

### 4. Analysis & Scoring（分析与打分）
- 特征：
  - Recency 指数衰减（半衰期可配）
  - 热度信号（如 HN points、点赞/转发、趋势指数）
  - 标题质量（长度/关键词命中）
  - 来源权重（可信度/相关性）
  - 摘要可用性/实体识别命中（可选）
- 接口：`List[ScoredTopic] analyze_and_score(List[Topic], now=None)`
- 可配：特征权重、半衰期、阈值、关键词黑白名单。

### 5. Content Generation（内容生成）
- 策略：默认 LLM（有 Key 时），失败或关闭时回退模板。
- 输出：结构化 Markdown（标题、摘要、背景、进展、数据与证据、影响与前景、风险与争议、参考链接、要点总结）。
- 接口：`Article generate_article(ScoredTopic, use_llm=True, model='...')`
- 约束：
  - 提示词包含事实性要求与不确定性标注；限制长度与语气。
  - 引用来源链接；允许显式“不确定/暂无信息”。

### 6. Distribution（分发）
- 通道：
  - 文件：Markdown + JSON（默认）
  - API：公众号/企业微信/飞书/Notion/博客平台
  - 站点：静态站点构建触发、Feed 更新
- 接口：
  - `save_article(Article, output_dir) -> (md_path, json_path)`
  - 可扩展 `Distributor.send(article) -> DeliveryResult`

### 7. Orchestration & CLI（编排/命令行）
- 职责：按配置驱动执行，支持参数覆盖，输出运行日志与产出索引。
- 接口：`run_pipeline(config: Dict) -> (List[Article], List[Outputs])`
- 调度：Cron/K8s CronJob/Airflow/Prefect 定时运行。

### 8. Storage（存储）
- 默认：`outputs/YYYYMMDD/*.md|.json`
- 扩展：SQLite 记录索引与运行元数据；对象存储（S3/OSS）；ES 用于检索。

### 9. Observability（可观测性）
- 日志：拉取量、失败数、打分Top-N、生成耗时、分发结果。
- 指标：生成成功率、平均生成时间、点击/阅读（回传）。
- 告警：数据源连续失败、产出为0、LLM 报错率过高。

## 数据模型
- Topic
  - `id: str`（稳定ID）
  - `title: str`
  - `url: str`
  - `summary: Optional[str]`
  - `published: Optional[datetimeUTC]`
  - `source: str`
  - `tags: List[str]`（如 `points:123`）
- ScoredTopic
  - `topic: Topic`
  - `score: float`
  - `rationale: str`
  - `features: Dict[str, float]`
- Article
  - `id: str`
  - `title: str`
  - `content_markdown: str`
  - `summary: str`
  - `tags: List[str]`
  - `topic_url: str`
  - `source: str`
  - `created_at: datetime`

## 配置（示例）
```yaml
output_dir: outputs
locale: zh-CN
geo: CN
top_n: 5
llm:
  enabled: true
  model: gpt-4o-mini
scoring:
  weights: {recency: 0.4, heat: 0.3, title: 0.1, summary: 0.1, source: 0.1}
  halflife_hours: 24
  min_score: 0.0
sources:
  enabled: [google_trends, hn]
  network: {timeout_s: 15, retries: 2, backoff: 0.5}
dedupe:
  ttl_hours: 48
```

## 打分算法（参考实现）
- Recency：`score = 0.5^(hours / halflife)`；`halflife`可配。
- 热度：来源特定指标归一化并截断（如 `min(points/300, 1)`）。
- 标题质量：与理想长度差距归一。
- 摘要可用：存在/长度阈值加分。
- 来源权重：按可信度/相关性配置。
- 总分：加权求和，排序取 Top-N。

## 错误处理与幂等
- 网络：指数退避 + 最大重试；按来源隔离失败。
- 解析：单条失败不影响批次；记录错误与样本。
- 生成：LLM 失败回退模板；按比例告警。
- 幂等：键 `(source, title_norm, url_or_empty)` 与稳定 `id`；输出文件名包含 `slug+短id`。

## 安全合规
- 尊重 Robots/ToS；不抓取敏感个人信息。
- 标注与引用来源链接；避免版权侵权。
- 密钥通过环境变量注入，不写入仓库。

## 部署与运行
- 环境：Python ≥ 3.11；可写输出目录；网络出站。
- 运行：容器化/脚本；Cron/调度平台定时执行；日志与指标上报。

## 测试策略
- 单元：解析、规范化、去重、打分、模板生成。
- 集成：端到端（Mock 外部源与 LLM）。
- 回归：Top-N 稳定性、幂等性、错误回退与告警路径。

## 里程碑建议
- M1：两类来源 + 模板生成 + Markdown/JSON 分发
- M2：完善打分、并发抓取、缓存与去重
- M3：接入 LLM、监控告警、API 分发
- M4：更多来源/多语言/实体抽取与话题聚类