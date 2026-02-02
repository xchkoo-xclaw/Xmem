import json
from openai import OpenAI

from ..config import settings


def _get_client() -> OpenAI:
    if settings.llm_provider != "deepseek":
        raise ValueError("LLM 未配置")
    if not settings.llm_api_key:
        raise ValueError("LLM_API_KEY 未配置")
    base_url = settings.llm_api_url or "https://api.deepseek.com"
    return OpenAI(api_key=settings.llm_api_key, base_url=base_url)


def _unwrap_json_content(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if len(lines) > 2:
            text = "\n".join(lines[1:-1]).strip()
    return text


def generate_note_summary(note_text: str) -> str:
    client = _get_client()
    prompt = (
        "你是笔记整理助手。请基于用户笔记内容输出简洁总结，要求："
        "1) 使用中文；2) 用 Markdown 列表呈现要点；3) 保留关键事实与行动项；"
        "4) 不要输出任何额外说明。"
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": note_text},
        ],
        stream=False,
    )
    return response.choices[0].message.content.strip()


def generate_note_todos(note_text: str) -> list[str]:
    client = _get_client()
    prompt = (
        "你是待办提取助手。请从用户笔记中提取可执行的待办事项，输出 JSON 数组，"
        "数组元素为对象，字段仅包含 title。要求："
        "1) 不要输出解释；2) 标题简洁明确；3) 至多 10 条；"
        "4) 如果没有待办，返回空数组。"
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": note_text},
        ],
        stream=False,
    )
    content = _unwrap_json_content(response.choices[0].message.content)
    data = json.loads(content)
    if not isinstance(data, list):
        raise ValueError("AI 返回的待办格式无效")
    titles: list[str] = []
    for item in data:
        if isinstance(item, str):
            title = item.strip()
        elif isinstance(item, dict):
            title = str(item.get("title", "")).strip()
        else:
            title = ""
        if title:
            titles.append(title)
    return titles[:10]
