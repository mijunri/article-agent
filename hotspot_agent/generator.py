from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from hotspot_agent.models import Article, ScoredTopic


def _generate_with_llm(scored: ScoredTopic, model: str) -> Optional[str]:
    try:
        from openai import OpenAI
    except Exception:
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    client = OpenAI(api_key=api_key)
    topic = scored.topic

    system_prompt = (
        "你是一位中文科技与时事分析写作助手，写作风格专业、克制、信息密度高。"
        "生成结构化 Markdown 文章，包含标题、摘要、分节内容与要点列表。"
    )
    user_prompt = f"""
基于以下主题生成一篇 600-900 字的中文文章。

要求：
- 使用 Markdown 二级/三级标题组织结构。
- 开头给出 1 段 60-100 字的摘要。
- 主体包含：背景、最新进展、数据与证据、影响与前景、风险与争议、参考链接。
- 语言简洁、客观，避免夸张与无依据的结论。
- 若信息不足，请明确说明不确定性。
- 结尾给出 3-5 个要点总结。

主题：{topic.title}
来源：{topic.source}
链接：{topic.url}
简述：{topic.summary or ''}
得分：{scored.score:.2f}（{scored.rationale}）
"""

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
        )
        content = completion.choices[0].message.content
        return content or None
    except Exception:
        return None


def _generate_template(scored: ScoredTopic) -> str:
    topic = scored.topic
    summary = topic.summary or "该主题暂无官方摘要，以下为基于公开信息的简要整理。"
    lines = []
    lines.append(f"# {topic.title}")
    lines.append("")
    lines.append(f"> 摘要：{summary[:160]}")
    lines.append("")
    lines.append("## 背景")
    lines.append("该话题近期登上热点。我们将基于公开来源对其背景与脉络进行简述。")
    lines.append("")
    lines.append("## 最新进展")
    lines.append("可见于来源链接与社区讨论。若有官方通告或权威媒体报道，应以其为准。")
    lines.append("")
    lines.append("## 数据与证据")
    lines.append("如果有可靠的指标、时间线或第三方评估，应在此列示与对比。")
    lines.append("")
    lines.append("## 影响与前景")
    lines.append("对产业、用户与监管可能产生的影响需要结合历史案例进行判断。")
    lines.append("")
    lines.append("## 风险与争议")
    lines.append("应关注信息源的可信度与潜在偏差，并标注不确定性。")
    lines.append("")
    lines.append("## 参考链接")
    if topic.url:
        lines.append(f"- 来源：{topic.url}")
    lines.append("")
    lines.append("## 要点总结")
    lines.append("- 热点来源与热度信号\n- 核心事实与时间线\n- 关键不确定性\n- 可能影响与应对建议")
    return "\n".join(lines)


def generate_article(scored: ScoredTopic, use_llm: bool = True, model: str = "gpt-4o-mini") -> Article:
    topic = scored.topic
    content_md: Optional[str] = None

    if use_llm:
        content_md = _generate_with_llm(scored, model=model)

    if not content_md:
        content_md = _generate_template(scored)

    created_at = datetime.now(timezone.utc)
    summary_line = topic.summary or f"围绕‘{topic.title}’的热点话题简析。"
    return Article(
        id=topic.id,
        title=topic.title,
        content_markdown=content_md,
        summary=summary_line,
        tags=topic.tags,
        topic_url=topic.url,
        source=topic.source,
        created_at=created_at,
    )