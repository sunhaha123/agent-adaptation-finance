import os
import json
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel
from json_repair import repair_json

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def get_llm(temperature: float = 0.7):
    """根据 LLM_PROVIDER 创建对应的 LLM 客户端

    规则：
    - provider=anthropic → 走 ChatAnthropic，可选 LLM_BASE_URL
    - provider=openai/openai-compatible → 走 ChatOpenAI，可选 LLM_BASE_URL
    """
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    model = os.getenv("LLM_MODEL") or os.getenv("MODEL_NAME") or "gpt-4.1-mini"
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("LLM_BASE_URL") or os.getenv("BASE_URL")
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        kwargs = {
            "model_name": model,
            "api_key": api_key,
            "max_tokens_to_sample": max_tokens,
            "temperature": temperature,
        }
        if base_url:
            kwargs["base_url"] = base_url

        return ChatAnthropic(**kwargs)

    if provider in {"openai", "openai-compatible", "proxy"}:
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": model,
            "api_key": api_key,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if base_url:
            kwargs["base_url"] = base_url

        return ChatOpenAI(**kwargs)

    raise ValueError(
        f"不支持的 LLM_PROVIDER: {provider!r}。请使用 openai、openai-compatible、proxy 或 anthropic。"
    )


def _describe_field(name: str, prop: dict) -> str:
    """把 JSON schema 的一个字段描述成 LLM 能理解的约束"""
    desc = prop.get("description", "")
    enum = prop.get("enum")
    if enum:
        allowed = "/".join(f'"{v}"' for v in enum)
        return f'  "{name}": ({desc}) 必须是以下之一: {allowed}'
    typ = prop.get("type", "")
    constraints = []
    if "minimum" in prop or "exclusiveMinimum" in prop:
        constraints.append(f"最小值 {prop.get('minimum', prop.get('exclusiveMinimum'))}")
    if "maximum" in prop or "exclusiveMaximum" in prop:
        constraints.append(f"最大值 {prop.get('maximum', prop.get('exclusiveMaximum'))}")
    constraint_str = f" ({', '.join(constraints)})" if constraints else ""
    if typ == "array":
        return f'  "{name}": ({desc}) 字符串数组, 如 ["a", "b"]'
    return f'  "{name}": ({desc}) {typ}{constraint_str}'


def llm_with_json_output(messages: list[dict], output_model: type[BaseModel], temperature: float = 0.7) -> BaseModel:
    """调用 LLM 并解析为 Pydantic 模型，用 json_repair 自动修复非标准 JSON"""
    llm = get_llm(temperature)

    schema = output_model.model_json_schema()
    fields_desc = []
    for name, prop in schema.get("properties", {}).items():
        fields_desc.append(_describe_field(name, prop))
    fields_str = "\n".join(fields_desc)

    patched_messages = [dict(msg) for msg in messages]
    patched_messages[-1] = {
        **patched_messages[-1],
        "content": (
            patched_messages[-1]["content"]
            + "\n\n[重要] 请直接输出纯 JSON 对象，不要用 markdown 包裹，不要输出任何其他文字。\n"
            + "所有枚举字段必须使用英文值，不要翻译。字段要求：\n"
            + fields_str
        ),
    }

    response = llm.invoke(patched_messages)
    repaired = repair_json(response.content, return_objects=True)

    if isinstance(repaired, dict):
        return output_model.model_validate(repaired)

    return output_model.model_validate_json(
        repaired if isinstance(repaired, str) else json.dumps(repaired)
    )
