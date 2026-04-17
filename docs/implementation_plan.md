# 金融市场多Agent仿真系统 — 实现计划

> 目标：开发 agent 仿真系统，能模拟金融市场中不同群体对一个消息的反应
>
> 灵感来源：论文《基于 agent 的计算金融中 agent 的适应性模型》(陶倩, 黄平)
> 仅保留"不同群体具有不同适应性层级"的核心思想，架构采用现代 ReAct Agent

---

## 一、核心理念

### 1.1 场景

给定一条市场消息（如"美联储宣布加息50基点"），7 个不同类型的交易者群体各自做出**决策意向**反应。

### 1.2 输出粒度：决策意向

每个 Agent 输出的不是交易订单，而是**结构化的决策意向**：

```
{
  "agent_id": "macro_fund",
  "agent_name": "宏观对冲基金",
  "stance": "bearish",          # bullish / bearish / neutral
  "confidence": 0.85,           # 0-1 置信度
  "intensity": 0.7,             # 0-1 行动强度
  "action": "减仓成长股，加仓短期国债",
  "reasoning": "加息50bp超预期→利率快速上行→成长股估值承压→...",
  "time_horizon": "1-3个月",
  "affected_assets": ["成长股", "短期国债", "美元"]
}
```

**不需要**：订单簿、撮合引擎、价格冲击模型、仓位管理、风控校验。

### 1.3 设计哲学

- **每个群体 = 一个独立 Agent**，差异通过 `.md` 配置文件体现（角色、思维方式、风险偏好），而非代码硬编码
- **Agent 之间不交互** — 各自独立对消息做出反应，输出汇总后对比
- **论文启发**：不同群体的信息解读深度、决策方式确实不同，体现在 Agent 的 prompt 配置中

---

## 二、Agent 规模

**每类群体 1 个 Agent，共 6 个。**

一个事件触发后：6 次 LLM 并行调用，一轮出结果。

---

## 三、群体类型设计（6类，对齐论文适应性分级）

| # | 群体 | 适应性级别 | 适应机制 | 典型反应风格 |
|---|------|-----------|---------|------------|
| 1 | 被动资金/ETF | 弱式 | 无 | "不因消息交易，等待定期再平衡" |
| 2 | 散户-情绪追涨杀跌 | 半弱式 | 反射+模仿 | "天哪要跌了！赶紧卖！" |
| 3 | 散户-逆向博弈 | 半弱式 | 模仿+反馈 | "大家都在恐慌，正是抄底的好机会" |
| 4 | 量化趋势/CTA | 半弱式 | 反馈学习 | "波动率因子触发，按模型信号减仓" |
| 5 | 公募/长线机构 | 半强式 | 反馈+创新 | "估值仍在合理区间，维持配置不动" |
| 6 | 宏观对冲基金 | 强式 | 创新学习 | "加息→利率上行→成长股承压，做空纳指" |

---

## 四、Agent 配置方式（.md 文件）

每个群体用一个 `.md` 文件定义角色和思维方式。示例：

```markdown
---
agent_id: macro_fund
agent_name: 宏观对冲基金
---

# 角色
你是一家宏观对冲基金的首席策略师。你的核心能力是分析宏观政策变化
对利率、汇率和各类资产价格的传导链条。

# 思维方式
- 你关注政策信号背后的传导路径，不被短期情绪左右
- 你会做跨资产联动分析（股票、债券、外汇、商品）
- 你的分析有因果链条，不是简单的"涨"或"跌"

# 风险偏好
- 风险偏好：中高
- 敢于在市场恐慌时逆向布局
- 但会严格控制单一方向的敞口

# 决策输出要求
给出你的决策意向，包括：
1. 立场（看多/看空/中性）
2. 置信度（0-1）
3. 行动强度（0-1）
4. 具体建议操作
5. 推理过程（展示你的因果链条分析）
6. 时间视角
7. 受影响的资产类别
```

### 论文"适应性分级"在配置中的体现

| 维度 | 低适应性（如被动资金） | 高适应性（如宏观对冲基金） |
|------|---------------------|------------------------|
| 信息抽象深度 | 只看标题 | 因果链推理 |
| 探索倾向 | 保守、按规则执行 | 主动试错、逆向思考 |
| 决策复杂度 | 简单规则 | 多资产联动分析 |
| 风险弹性 | 固定规则不变 | 根据市场环境动态调整 |

---

## 五、一条消息的完整流程

```
1. 消息输入          "美联储宣布加息50基点"
       ↓
2. 信号提取          结构化为：方向(利空)、强度(高)、
                     置信度(0.9)、影响资产(股票、债券、美元)
       ↓
3. 并行触发 Agent    Send() 同时触发 7 个 Agent
   ┌─────────────────────────────────────────────────┐
   │ 散户-动量: stance=bearish, "赶紧卖！"            │
   │ 散户-逆向: stance=bullish, "恐慌就是机会"        │
   │ 公募机构:  stance=neutral, "影响有限，继续持有"    │
   │ 对冲基金:  stance=bearish, "做空成长股+加仓国债"  │
   │ 量化基金:  stance=bearish, "波动率因子触发减仓"    │
   │ 做市商:    stance=neutral, "扩大价差，降低库存"    │
   │ 被动资金:  stance=neutral, "不因消息交易"         │
   └─────────────────────────────────────────────────┘
       ↓
4. 汇总输出          收集所有 Agent 的决策意向
       ↓
5. 生成报告          对比分析各群体反应差异
```

---

## 六、技术架构（经 langchain-docs-mcp 验证）

### 6.1 LangChain 与 LangGraph 的关系

```
┌──────────────────────────────────────────────────────┐
│  LangGraph StateGraph       ← 外层：消息进来 → 并行   │
│    ├── Send() 并行派发 7 个 Agent                     │
│    └── 汇总结果 → 生成报告                            │
│                                                      │
│  LangChain create_agent     ← 内层：每个群体的 Agent   │
│    ├── system_prompt（从 .md 文件加载）               │
│    └── tools（读取新闻信号等）                         │
└──────────────────────────────────────────────────────┘
安装：pip install langgraph langchain langchain-anthropic
```

> `create_react_agent` 在 LangGraph v1 中已废弃，统一使用
> `from langchain.agents import create_agent`

### 6.2 图定义

```
START
  ↓
ExtractSignal         ← LLM 将原始消息结构化
  ↓
DispatchAgents        ← Send() 并行触发 7 个 Agent
  │
  ├── Send("retail_momentum", {...})
  ├── Send("retail_contrarian", {...})
  ├── Send("mutual_fund", {...})
  ├── Send("macro_fund", {...})
  ├── Send("quant_fund", {...})
  ├── Send("market_maker", {...})
  └── Send("passive_fund", {...})
  │
CollectResponses      ← reducer 自动汇总所有决策意向
  ↓
GenerateReport        ← 生成对比分析报告
  ↓
END
```

就这么简单。4 个节点，没有循环。

### 6.3 群体 Agent 创建方式

```python
from langchain.agents import create_agent
from langchain.tools import tool

@tool
def read_news_signal() -> str:
    """读取当前新闻的结构化信号（方向、强度、影响资产）"""

macro_fund_agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[read_news_signal],
    system_prompt=load_md("agents/macro_fund.md"),
)
```

### 6.4 State 设计

```python
from typing import TypedDict, Literal, Optional
from typing_extensions import Annotated
import operator

class NewsSignal(TypedDict):
    raw_text: str
    direction: Literal["bullish", "bearish", "neutral"]
    intensity: float          # 0-1
    confidence: float         # 0-1
    affected_assets: list[str]

class AgentResponse(TypedDict):
    agent_id: str
    agent_name: str
    stance: Literal["bullish", "bearish", "neutral"]
    confidence: float         # 0-1
    intensity: float          # 0-1
    action: str               # 具体建议操作
    reasoning: str            # 推理过程
    time_horizon: str         # 时间视角
    affected_assets: list[str]

class SimulationState(TypedDict):
    # 输入
    raw_news: str
    news_signal: Optional[NewsSignal]

    # Agent 配置
    agent_configs: dict[str, str]       # agent_id -> .md 文件路径

    # 输出（reducer 自动汇总并行结果）
    responses: Annotated[list[AgentResponse], operator.add]

    # 报告
    report: Optional[str]
```

---

## 七、项目目录结构

```
agent-adaptation-finance/
├── CLAUDE.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── agents/                            # 每个群体的 .md 配置
│   ├── retail_momentum.md
│   ├── retail_contrarian.md
│   ├── mutual_fund.md
│   ├── macro_fund.md
│   ├── quant_fund.md
│   ├── market_maker.md
│   └── passive_fund.md
├── src/
│   ├── __init__.py
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py                   # SimulationState 定义
│   │   ├── main_graph.py              # 主图（4个节点）
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── extract_signal.py      # 消息 → 结构化信号
│   │       ├── dispatch_agents.py     # Send() 并行触发
│   │       ├── collect_responses.py   # 汇总决策意向
│   │       └── generate_report.py     # 生成对比报告
│   ├── agent_runtime/
│   │   ├── __init__.py
│   │   ├── agent_factory.py           # 从 .md 创建 Agent
│   │   └── tools.py                   # Agent 可用工具
│   └── schemas/
│       ├── __init__.py
│       └── response.py                # AgentResponse 等
├── scenarios/                         # 预定义消息场景
│   ├── fed_rate_hike.yaml
│   ├── earnings_beat.yaml
│   └── black_swan.yaml
├── tests/
│   ├── test_agent_factory.py
│   └── test_graph_flow.py
├── docs/
│   ├── agent_finance_paper_markdown.md
│   └── implementation_plan.md
└── notebooks/
    └── demo.ipynb
```

---

## 八、技术栈

```
pip install langgraph langchain langchain-anthropic pydantic
```

| 层 | 包 | 做什么 |
|----|-----|--------|
| 外层编排 | `langgraph` StateGraph + Send | 并行触发 7 个 Agent，汇总结果 |
| 每个群体 Agent | `langchain` create_agent | 从 .md 加载 prompt，执行 ReAct |
| 工具 | `langchain` @tool | read_news_signal 等 |
| LLM | `langchain-anthropic` | Claude |
| 数据模型 | `pydantic` v2 | AgentResponse 结构化输出 |
| 测试 | `pytest` | 测试 |

---

## 九、实施路线

### Phase 1: 最小可运行系统
1. 项目初始化（pyproject.toml、目录结构）
2. 定义 SimulationState 和 AgentResponse
3. 实现 2 个群体的 `.md` 配置（散户-动量 + 宏观对冲基金）
4. 实现 agent_factory（从 .md 创建 Agent）
5. 搭建主图（4 个节点），跑通"1条消息 → 2个Agent → 2个决策意向"

### Phase 2: 完整群体
6. 补全 7 类群体的 `.md` 配置
7. 实现报告生成节点（对比分析各群体反应差异）
8. 预定义多种消息场景

### Phase 3: 丰富与分析
9. 可视化（各群体立场对比图表）
10. 批量场景测试（同一群体对不同消息的反应一致性）
11. Agent 记忆系统（跨场景记忆累积，可选）
