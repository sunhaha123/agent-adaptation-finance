import re

from pydantic import BaseModel, Field

from src.schemas.evolution import MarketEvent
from src.simulation.utils import clamp, stance_to_score


class EventTimeline(BaseModel):
    events: list[MarketEvent] = Field(default_factory=list)


def format_event_line(event: MarketEvent, include_meta: bool = False) -> str:
    line = f"{event.title}：{event.description}"
    if include_meta:
        line += (
            f"（方向={event.direction}，强度={event.intensity:.2f}，"
            f"置信度={event.confidence:.2f}，轮次={event.rounds}）"
        )
    return line


def format_event_timeline(events: list[MarketEvent], include_meta: bool = False) -> str:
    return "\n".join(
        f"{index}. {format_event_line(event, include_meta=include_meta)}"
        for index, event in enumerate(events, start=1)
    )


def looks_like_geopolitical_conflict(raw_news: str) -> bool:
    keywords = [
        "伊朗",
        "美伊",
        "以色列",
        "霍尔木兹",
        "中东",
        "导弹",
        "无人机",
        "战争",
        "军事",
        "舰队",
        "海峡",
        "核设施",
    ]
    return any(keyword in raw_news for keyword in keywords)


def infer_event_direction(text: str) -> str:
    bearish_keywords = [
        "恶化",
        "升级",
        "爆发",
        "打击",
        "报复",
        "反击",
        "外溢",
        "威胁",
        "扰动",
        "中断",
        "封锁",
        "风险",
        "战争",
        "僵持",
        "消耗",
        "制裁",
        "下跌",
        "恐慌",
        "避险",
    ]
    bullish_keywords = [
        "停火",
        "和谈",
        "达成",
        "开放",
        "恢复",
        "缓解",
        "回吐",
        "修复",
        "反弹",
        "协议",
        "调停",
        "降烈度",
        "最坏情形避免",
    ]
    neutral_keywords = ["对峙", "观望", "等待", "脆弱和平", "政策反复"]

    bullish_score = sum(1 for keyword in bullish_keywords if keyword in text)
    bearish_score = sum(1 for keyword in bearish_keywords if keyword in text)
    neutral_score = sum(1 for keyword in neutral_keywords if keyword in text)

    if bullish_score > bearish_score:
        return "bullish"
    if bearish_score > bullish_score and bearish_score >= neutral_score:
        return "bearish"
    return "neutral"


def infer_event_intensity(text: str, direction: str) -> float:
    high_keywords = ["战争爆发", "霍尔木兹", "封锁", "打击", "报复", "核", "海峡", "中断"]
    medium_keywords = ["升级", "外溢", "僵持", "停火", "和谈", "开放", "回吐"]

    if any(keyword in text for keyword in high_keywords):
        return 0.90 if direction != "neutral" else 0.70
    if any(keyword in text for keyword in medium_keywords):
        return 0.70 if direction != "neutral" else 0.50
    return 0.55 if direction != "neutral" else 0.35


def infer_affected_assets(raw_text: str) -> list[str]:
    if looks_like_geopolitical_conflict(raw_text):
        return ["oil", "shipping", "gold", "USD", "equities", "bonds"]
    if "加息" in raw_text or "美联储" in raw_text or "利率" in raw_text:
        return ["equities", "bonds", "USD", "gold", "crypto"]
    return ["MARKET_INDEX"]


def parse_user_event_timeline(
    raw_text: str,
    total_rounds: int,
    default_assets: list[str] | None = None,
) -> list[MarketEvent]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    events = []
    affected_assets = default_assets or infer_affected_assets(raw_text)

    for line in lines:
        cleaned = re.sub(r"^\s*(?:[-*•]|\d+[.)、.．]|[一二三四五六七八九十]+[、.．])\s*", "", line)
        if "：" in cleaned:
            title, description = cleaned.split("：", 1)
        elif ":" in cleaned:
            title, description = cleaned.split(":", 1)
        else:
            continue

        title = title.strip()
        description = description.strip()
        if not title or not description:
            continue

        event_text = f"{title}：{description}"
        direction = infer_event_direction(event_text)
        events.append(
            MarketEvent(
                step=len(events),
                title=title,
                description=description,
                direction=direction,
                intensity=infer_event_intensity(event_text, direction),
                confidence=0.80,
                affected_assets=affected_assets,
                rounds=1,
            )
        )

    if len(events) < 2:
        return []
    return distribute_rounds(events, total_rounds)


def distribute_rounds(events: list[MarketEvent], total_rounds: int) -> list[MarketEvent]:
    if total_rounds <= 0:
        raise ValueError("total_rounds 必须大于 0")
    if not events:
        raise ValueError("events 不能为空")

    base = total_rounds // len(events)
    remainder = total_rounds % len(events)
    distributed = []
    for index, event in enumerate(events):
        rounds = max(1, base + (1 if index < remainder else 0))
        distributed.append(event.model_copy(update={"step": index, "rounds": rounds}))
    return distributed


def fallback_event_timeline(
    raw_news: str,
    initial_signal: dict,
    event_count: int,
    total_rounds: int,
) -> list[MarketEvent]:
    direction = initial_signal.get("direction", "neutral")
    affected_assets = initial_signal.get("affected_assets", ["MARKET_INDEX"])
    base_intensity = float(initial_signal.get("intensity", 0.6))
    base_confidence = float(initial_signal.get("confidence", 0.7))

    if looks_like_geopolitical_conflict(raw_news):
        templates = [
            ("前期对抗升级", "美伊关系恶化，地区驻军、舰队与防空力量加强部署，市场开始计入中东地缘风险溢价。", "bearish", 0.85),
            ("战争爆发", "美国与以色列对伊朗关键军事、核相关或指挥目标实施打击，冲突从威慑转为公开战争。", "bearish", 1.00),
            ("伊朗报复", "伊朗以导弹、无人机、代理武装等方式反击美以目标，战争进入双向升级阶段。", "bearish", 0.95),
            ("地区外溢", "伊拉克、叙利亚、海湾方向安全风险同步抬升，周边国家进入防御与外交斡旋状态。", "bearish", 0.80),
            ("霍尔木兹风险冲击", "海峡通航受威胁，油轮、保险、航运与能源供应预期遭扰动，全球市场进入避险交易。", "bearish", 0.95),
            ("高烈度僵持", "双方继续施压，但都面临军事消耗、经济代价与国际压力，全面长期战风险上升。", "bearish", 0.70),
            ("停火窗口出现", "在多方调停下，双方接受临时停火或降烈度安排，市场开始交易最坏情形避免。", "bullish", 0.55),
            ("正式和谈启动", "美国与伊朗进入实质谈判，核心议题转向停火巩固、航运安全、制裁与安全承诺。", "bullish", 0.50),
            ("和谈达成", "双方形成阶段性协议，公开战争基本结束，地区从热战转入脆弱和平。", "bullish", 0.65),
            ("霍尔木兹海峡开放", "海峡恢复开放，能源运输与商船通行重建，原油供应中断预期明显缓解。", "bullish", 0.75),
            ("市场回吐战争溢价", "油价、航运保险费、避险资产涨幅部分回落，风险资产出现修复性反弹。", "bullish", 0.70),
            ("战后高压对峙延续", "虽然和谈达成，但互信不足、局部摩擦与政策反复风险仍在，市场保留一部分长期地缘溢价。", "neutral", 0.45),
        ]
    elif direction == "bearish":
        templates = [
            ("初始冲击", f"{raw_news}，市场首先按利空冲击重新定价。", "bearish", 1.0),
            ("风险偏好下降", "投资者降低风险资产敞口，短线卖压扩散。", "bearish", 0.75),
            ("分歧出现", "部分机构认为冲击已被部分计价，市场开始出现观望与分歧。", "neutral", 0.45),
            ("趋势资金跟随", "价格下跌触发趋势资金和止损规则，卖压阶段性增强。", "bearish", 0.65),
            ("逆向资金试探", "估值回落后，长线和逆向资金开始小规模承接。", "bullish", 0.45),
            ("政策再解读", "市场重新评估后续政策路径，情绪从恐慌转向数据依赖。", "neutral", 0.40),
            ("再平衡交易", "被动与机构资金完成部分再平衡，流动性有所恢复。", "neutral", 0.35),
            ("新均衡探索", "多空双方围绕新价格中枢重新博弈。", "neutral", 0.30),
        ]
    elif direction == "bullish":
        templates = [
            ("初始冲击", f"{raw_news}，市场首先按利好冲击重新定价。", "bullish", 1.0),
            ("风险偏好升温", "投资者提高风险资产敞口，短线买盘扩散。", "bullish", 0.75),
            ("获利了结", "快速上涨后部分资金选择兑现收益。", "neutral", 0.45),
            ("趋势资金跟随", "价格上涨触发动量与趋势资金继续加仓。", "bullish", 0.65),
            ("估值担忧", "估值抬升后，逆向和长线资金开始降低追高意愿。", "bearish", 0.40),
            ("基本面再验证", "市场等待后续数据验证利好能否持续兑现。", "neutral", 0.40),
            ("再平衡交易", "机构和被动资金围绕目标权重进行再平衡。", "neutral", 0.35),
            ("新均衡探索", "多空双方围绕新价格中枢重新博弈。", "neutral", 0.30),
        ]
    else:
        templates = [
            ("初始解读", f"{raw_news}，市场首先把消息解释为中性偏观察。", "neutral", 0.70),
            ("分歧扩散", "不同类型投资者对消息含义形成分歧。", "neutral", 0.55),
            ("短线资金试探", "短线资金根据价格变化进行方向试探。", "neutral", 0.45),
            ("等待确认", "市场等待更多数据确认方向。", "neutral", 0.35),
        ]

    selected = templates[: max(1, min(event_count, len(templates)))]
    events = [
        MarketEvent(
            step=index,
            title=title,
            description=description,
            direction=event_direction,
            intensity=clamp(base_intensity * multiplier, 0.05, 1.0),
            confidence=clamp(base_confidence * max(0.55, multiplier), 0.05, 1.0),
            affected_assets=affected_assets,
            rounds=1,
        )
        for index, (title, description, event_direction, multiplier) in enumerate(selected)
    ]
    return distribute_rounds(events, total_rounds)


def generate_event_timeline(
    raw_news: str,
    initial_signal: dict,
    event_count: int,
    total_rounds: int,
) -> list[MarketEvent]:
    user_events = parse_user_event_timeline(
        raw_news,
        total_rounds=total_rounds,
        default_assets=initial_signal.get("affected_assets") or None,
    )
    if user_events:
        return user_events

    try:
        from src.agent_runtime.llm import llm_with_json_output

        messages = [
            {"role": "system", "content": (
                "你是一个金融市场事件链生成器。根据初始新闻，生成后续市场演化事件。"
                "事件应体现冲击、分歧、情绪扩散、趋势资金、逆向资金、再平衡、新均衡等过程。"
                "不要把同一条新闻重复写多次；每个事件必须是下一阶段市场可能发生的新发展。"
                "每个事件的 title 必须是简短阶段名，description 必须是一句具体、可读的中文事件描述。"
                "如果是地缘冲突或战争新闻，要按对抗升级、冲突爆发、报复、地区外溢、关键通道风险、僵持、停火、和谈、协议、风险溢价回落、余波风险等逻辑推进。"
            )},
            {"role": "user", "content": (
                f"初始新闻: {raw_news}\n"
                f"初始信号: {initial_signal}\n"
                f"请生成 {event_count} 个事件，direction 只能是 bullish/bearish/neutral。"
            )},
        ]
        timeline = llm_with_json_output(messages, EventTimeline, temperature=0.2)
        events = timeline.events[:event_count]
        if events:
            return distribute_rounds(events, total_rounds)
    except Exception:
        pass

    return fallback_event_timeline(raw_news, initial_signal, event_count, total_rounds)


def event_to_signal(event: MarketEvent, local_round: int = 0) -> dict:
    half_life = max(1.0, event.rounds / 2.0)
    decay = 0.45 + 0.55 * (0.5 ** (local_round / half_life))
    return {
        "raw_text": event.description,
        "direction": event.direction,
        "intensity": clamp(event.intensity * decay, 0.0, 1.0),
        "confidence": event.confidence,
        "affected_assets": event.affected_assets,
        "summary": event.title,
    }


def build_event_schedule(events: list[MarketEvent]) -> list[tuple[MarketEvent, int]]:
    schedule: list[tuple[MarketEvent, int]] = []
    for event in events:
        for local_round in range(event.rounds):
            schedule.append((event, local_round))
    return schedule


def adapt_archetype_response(
    baseline_response: dict,
    event_signal: dict,
    archetype_id: str,
) -> dict:
    event_score = stance_to_score(event_signal.get("direction", "neutral"))
    event_intensity = float(event_signal.get("intensity", 0.5))
    event_confidence = float(event_signal.get("confidence", 0.6))

    style = {
        "passive_fund": {"signal": 0.10, "contrarian": 0.00, "intensity": 0.25},
        "retail_momentum": {"signal": 1.00, "contrarian": 0.00, "intensity": 1.15},
        "retail_contrarian": {"signal": 0.35, "contrarian": 0.70, "intensity": 0.85},
        "quant_fund": {"signal": 0.80, "contrarian": 0.10, "intensity": 1.00},
        "mutual_fund": {"signal": 0.45, "contrarian": 0.25, "intensity": 0.65},
        "macro_fund": {"signal": 0.75, "contrarian": 0.20, "intensity": 0.95},
    }.get(archetype_id, {"signal": 0.60, "contrarian": 0.15, "intensity": 0.80})

    baseline_score = stance_to_score(baseline_response.get("stance", "neutral"))
    combined_score = (
        0.25 * baseline_score
        + style["signal"] * event_score
        - style["contrarian"] * event_score * event_intensity
    )
    if abs(combined_score) < 0.20 or archetype_id == "passive_fund":
        stance = "neutral"
    else:
        stance = "bullish" if combined_score > 0 else "bearish"

    adapted = dict(baseline_response)
    adapted["stance"] = stance
    adapted["confidence"] = clamp(0.30 + event_confidence * (0.40 + 0.30 * style["signal"]), 0.0, 1.0)
    adapted["intensity"] = clamp(event_intensity * style["intensity"], 0.0, 1.0)
    adapted["reasoning"] = (
        f"事件链阶段：{event_signal.get('summary', '')}。"
        f"根据该阶段信号和本群体风格调整原型判断。"
    )
    adapted["affected_assets"] = event_signal.get("affected_assets", adapted.get("affected_assets", []))
    return adapted
