# 热点抓取、分析、写作与分发工具

一个简单的 Python 工具链：抓取热点（Google Trends、Hacker News）、分析打分、生成中文文章（可选连接 LLM）、保存为 Markdown 与 JSON。

## 运行环境
- Python 3.13+

## 安装依赖
```bash
pip install -r requirements.txt
```

## 快速开始
```bash
python main.py --config config.yaml
```

开启 LLM（需设置环境变量 `OPENAI_API_KEY`）：
```bash
export OPENAI_API_KEY=sk-... # 请自行设置
python main.py --llm --top 3
```

生成结果默认输出到 `outputs/YYYYMMDD/` 目录，包含 `.md` 与 `.json` 两种格式。

## 配置项（config.yaml）
- `output_dir`: 输出根目录
- `locale`: Google Trends 语言（默认 zh-CN）
- `geo`: Google Trends 地区（默认 CN）
- `top_n`: 生成文章数量
- `llm.enabled`: 是否启用 LLM
- `llm.model`: LLM 模型名（默认 gpt-4o-mini）