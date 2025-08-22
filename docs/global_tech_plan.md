## 全局技术方案

### 目标与范围
- 覆盖“抓取热点 → 规范化与去重 → 分析打分 → 文章生成 → 分发输出”的闭环。
- 支持多来源、多语言（以中文输出为主），按配置驱动与模块化扩展。

### 关键指标（SLI/SLO & KPI）
- 抓取成功率 ≥ 98%，端到端生成成功率 ≥ 95%。
- 单批处理时延 P95 ≤ 5 分钟（Top-N=10，常规来源）。
- 重复文章率 ≤ 1%，合格文章比例 ≥ 90%。

### 总体架构
- 形态：批处理流水线（支持定时与手动触发，可演进准实时）。
- 流程：Source Connectors → Normalization → Dedup/Cache → Analysis/Scoring → Selection → Content Generation（LLM/模板）→ Distribution → 监控与审计。
- 原则：可插拔、幂等、可观察、配置化、失败可恢复。

### 核心模块
- Source Connectors：对接各热点渠道（RSS/API/HTML）。
- Normalization：字段统一、清洗、时间时区处理、稳定 ID 生成。
- Dedup/Cache：同批/跨批去重；内容/相似去重（SimHash/MinHash 可选）。
- Analysis/Scoring：特征工程与权重打分（可配置）。
- Content Generation：LLM 优先，模板兜底；结构化 Markdown 输出。
- Distribution：Markdown/JSON 落盘；可扩展企业微信/飞书/博客等 API 渠道。
- Orchestration & Config：定时编排、参数覆盖、运行状态记录。
- Observability：日志、指标、告警；产出索引与审计追踪。

### 技术选型
- 语言/运行：Python。
- 解析：feedparser、lxml/BeautifulSoup（按来源选择）。
- 调度：Cron/K8s CronJob（可迁移 Prefect/Airflow）。
- 存储：本地目录/对象存储（产出）；SQLite/Redis（索引与幂等）。
- 监控：结构化日志 + 指标（Prom/Grafana 或云监控）。

### 数据模型（核心）
- Topic：id、title、url、summary、published(UTC)、source、tags。
- ScoredTopic：topic、score、rationale、features。
- Article：id、title、content_markdown、summary、tags、topic_url、source、created_at。

### 配置与密钥
- 全局：output_dir、top_n、locale、geo。
- LLM：enabled、model、超时/tokens、重试策略。
- 抓取：enabled_sources、超时/重试/并发/节流/代理。
- 去重：TTL、近似去重阈值。
- 分发：目标通道与凭证；密钥经环境变量/密钥管理注入。

### 非功能性要求
- 幂等：稳定 ID 与输出文件命名（slug+短 id）。
- 可扩展：新增来源、特征、分发通道仅需增量模块。
- 可靠性：失败隔离、熔断与降级（LLM→模板）。

### 安全与合规
- 遵守 Robots/ToS；仅抓取公共信息。
- 标注与引用来源；避免版权侵权与敏感信息。
- 审计日志保留 7–30 天（可配）。

### 部署与运行
- 开发：脚本/容器本地运行。
- 生产：容器化 + 定时任务；只读网络白名单；可写输出卷。

### 监控与告警
- 指标：抓取成功率、端到端成功率、生成耗时、分发成功率。
- 告警：连续抓取失败、零产出、LLM 报错率高、重复率异常。

### 里程碑
- M1：两类来源 + 模板生成 + Markdown/JSON 分发。
- M2：权重打分完善、并发抓取、缓存与去重。
- M3：LLM 接入、监控告警、API 分发。
- M4：更多来源/多语言/聚类与话题跟踪。