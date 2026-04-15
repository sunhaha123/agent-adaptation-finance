# 金融市场多Agent仿真系统 — 实现计划

> 目标：开发 agent 仿真系统，能模拟金融市场中不同群体对一个消息的反应
>
> 灵感来源：论文《基于 agent 的计算金融中 agent 的适应性模型》(陶倩, 黄平)
> 仅保留"不同群体具有不同适应性层级"的核心思想，架构采用现代 ReAct Agent

---

## 一、核心理念

### 1.1 场景

给定一条市场消息（如"美联储宣布加息50基点"），系统中不同类型的交易者群体各自做出反应，产生交易行为，最终影响市场价格。

### 1.2 设计哲学

- **每个群体 = 一个独立 ReAct Agent**，差异通过 `.md` 配置文件体现（角色、记忆策略、学习规则、风险偏好），而非代码硬编码
- **Agent 之间通过市场间接交互**——通过订单和价格行为相互影响，不直接通信
- **论文启发**：不同群体的信息解读深度、学习速率、记忆半衰期、决策时滞确实不同，这些差异自然体现在 Agent 的 prompt 配置中

---

## 二、Agent 规模

**MVP：每类群体 1 个 Agent 代表，共 7 个 Agent。**

架构上预留扩展能力：同一个 `.md` 配置可以实例化多个 Agent（如 10 个散户、5 个机构），每个实例可以有参数微调（资金量、风险偏好等）。但初期先每类 1 个，保持简单。

一个事件触发后的调用量：
- 单轮反应：7 次 LLM 调用
- 含二轮反应（N 轮）：最多 7×N 次
- 合理设置 max_ticks（如 5-10 轮），总调用量可控在 35-70 次/事件

---

## 三、群体类型设计（7类）

| 群体 | 信息解读 | 决策速度 | 风险偏好 | 典型行为 |
|------|---------|---------|---------|---------|
| 散户-动量追随 | 标题级、情绪驱动 | 中 | 中高 | 追涨杀跌，跟风操作 |
| 散户-逆向抄底 | 价格偏离后反向 | 中慢 | 中 | 恐慌时买入，狂热时卖出 |
| 公募/长线机构 | 基本面与估值框架 | 慢 | 中低 | 分批建仓，长期持有 |
| 宏观对冲基金 | 政策/利率/跨资产联动 | 中快 | 中高 | 政策套利，方向性交易 |
| 量化中频基金 | 统计信号与规则执行 | 快 | 中 | 因子驱动，算法拆单 |
| 高频做市商 | 订单流与微观结构 | 极快 | 低单笔/高周转 | 双边挂单，赚取价差 |
| 被动资金(ETF/指数) | 非信息驱动，规则调仓 | 慢(定时) | 低 | 跟踪指数，被动再平衡 |

---

## 四、Agent 配置方式（.md 文件）

每个群体用一个 `.md` 文件定义全部行为特征。示例结构：

```markdown
---
agent_id: macro_fund
agent_name: 宏观对冲基金
adaptation_level: L3
decision_latency_ms: 800
memory_half_life_ticks: 40
learning_rate: 0.35
exploration_ratio: 0.15
risk_budget_regime: drawdown_sensitive
max_position: 1000
max_leverage: 3.0
tools_allowlist:
  - read_news_signal
  - read_market_snapshot
  - risk_check
  - place_order
  - cancel_order
  - write_memory
  - query_memory
---

# 角色
你是一家宏观对冲基金的首席交易员。你的核心能力是分析政策变化对利率、
汇率和资产价格的传导链条。你不会追涨杀跌，而是做政策套利和跨资产联动。

# 记忆策略
- 记住过去40个tick的关键事件和仓位变化
- 重点记忆：政策转向信号、仓位盈亏、流动性变化
- 忘记机制：超过半衰期的记忆逐步淡化权重

# 学习策略
- 每次交易结算后评估：预判方向是否正确、时机是否合适
- 学习率 0.35：适度更新策略参数
- 如果连续3次方向错误，降低仓位规模，进入观望期

# 决策协议（ReAct）
1. 观察：读取新闻信号 + 市场快照
2. 思考：分析政策传导路径（加息→利率上行→成长股承压→...）
3. 行动：根据分析下单或观望
4. 反思：记录本次决策逻辑，更新记忆
```

### 论文"适应性分级"在配置中的体现

| 维度 | 低适应性（如被动资金） | 高适应性（如宏观对冲基金） |
|------|---------------------|------------------------|
| 信息抽象深度 | 只看标题 | 因果链推理 |
| 学习速率 | 低（0.05） | 高（0.35） |
| 记忆半衰期 | 短（5 ticks） | 长（40 ticks） |
| 探索倾向 | 保守执行 | 主动试错 |
| 决策时滞 | 慢（定时触发） | 快（毫秒级） |
| 风险弹性 | 固定规则 | 动态调整 |

---

## 五、一条消息的完整仿真流程

```
1. 消息输入        "美联储宣布加息50基点"
       ↓
2. 信号提取        结构化为：方向(利空)、强度(高)、
                   置信度(0.9)、影响资产(股票、债券、美元)
       ↓
3. 市场快照        记录消息前的基线价格、波动率、流动性
       ↓
4. 并行触发Agent   7类群体各自执行 ReAct 循环
   ┌──────────────────────────────────────────────┐
   │ 散户: "天哪要跌了！赶紧卖！" → 市价卖单      │
   │ 机构: "估值还行，先观望" → 不操作              │
   │ 对冲基金: "加息→债券跌→做空债券" → 限价卖单   │
   │ 量化: "信号触发空头因子" → 算法拆单卖出        │
   │ 做市商: "波动加大，扩大价差" → 调整挂单        │
   │ ...                                           │
   └──────────────────────────────────────────────┘
       ↓
5. 风控校验        统一检查仓位/杠杆/单笔限额
       ↓
6. 订单撮合        价格优先/时间优先，生成成交
       ↓
7. 价格更新        新价格广播给所有 Agent
       ↓
8. 二轮反应        Agent 看到价格变化，可能产生新的交易
   （重复 4-7，直到达到停止条件）
       ↓
9. 记忆更新        各 Agent 写入本轮交易记忆
       ↓
10. 输出报告       价格走势、各群体行为分析、市场微观结构
```

---

## 六、技术架构（经 langchain-docs-mcp 验证）

> 以下方案已通过 LangChain/LangGraph 官方文档验证

### 6.1 LangChain 与 LangGraph 的关系

```
用户只需要关心：
┌──────────────────────────────────────────────────────┐
│  LangGraph StateGraph      ← 外层：市场仿真循环       │
│    ├── Send() 并行派发                                │
│    └── 条件边、循环                                   │
│                                                      │
│  LangChain create_agent    ← 内层：每个群体的 Agent    │
│    ├── system_prompt（从 .md 文件加载）               │
│    ├── tools（交易工具集）                             │
│    └── middleware（动态工具过滤等）                     │
└──────────────────────────────────────────────────────┘
安装：pip install langgraph langchain langchain-anthropic
```

**关键**：`create_agent`（langchain v1 新 API）返回的就是一个 LangGraph 图，
天然可以作为 subgraph 嵌入外层 StateGraph。两者不是二选一，而是嵌套使用。

> 注意：`create_react_agent` 在 LangGraph v1 中已废弃，统一使用
> `from langchain.agents import create_agent`

### 6.2 架构模式：Router + Send 并行

参考官方 `multi-agent/router-knowledge-base` 模式：

- **不需要 LLM Supervisor** — 我们的场景是"所有群体都要反应"，确定性派发即可
- **用 `Send()` API 并行触发** 7 个 Agent
- **用 `Annotated[list, operator.add]` reducer** 收集所有 Agent 的订单输出

### 6.3 图定义

```
START
  ↓
InitScenario          ← 加载消息 + 初始市场状态
  ↓
ExtractSignal         ← LLM 结构化信号提取
  ↓
BuildTickContext      ← 构建当前 tick 的市场上下文
  ↓
DispatchAgents        ← Send() 并行触发 7 个 Agent
  │
  ├── Send("retail_momentum", {...})
  ├── Send("retail_contrarian", {...})
  ├── Send("mutual_fund", {...})
  ├── Send("macro_fund", {...})      ← 每个 Agent 内部是
  ├── Send("quant_fund", {...})         create_agent 构建的
  ├── Send("market_maker", {...})       ReAct 子图
  └── Send("passive_fund", {...})
  │
CollectIntents        ← reducer 自动汇总所有订单
  ↓
RiskGate              ← 统一风控校验（纯规则，无 LLM）
  ↓
MatchEngine           ← 订单撮合（纯计算，无 LLM）
  ↓
UpdateMarketState     ← 更新价格、盘口、成交记录
  ↓
UpdateAgentMemory     ← 各 Agent 写入记忆
  ↓
StopCheck ──→ No  ──→ BuildTickContext（下一轮）
  │
  Yes
  ↓
GenerateReport        ← 生成仿真报告
  ↓
END
```

### 6.4 群体 Agent 创建方式（langchain create_agent）

```python
from langchain.agents import create_agent
from langchain.tools import tool

# 从 .md 文件加载 system prompt
def load_agent_prompt(md_path: str) -> str:
    with open(md_path) as f:
        return f.read()

# 创建群体 Agent（每个都是一个 LangGraph 子图）
macro_fund_agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[read_news_signal, read_market_snapshot,
           read_portfolio, risk_check, place_order],
    system_prompt=load_agent_prompt("agents/macro_fund.md"),
)

# 在外层 StateGraph 中作为 subgraph 调用
def query_macro_fund(state: AgentInput) -> dict:
    result = macro_fund_agent.invoke(
        {"messages": [{"role": "user", "content": state["news_context"]}]}
    )
    return {"orders": [parse_order(result["messages"][-1].content)]}
```

### 6.5 Agent 工具集（langchain @tool）

```python
from langchain.tools import tool

@tool
def read_news_signal(query: str) -> str:
    """读取当前新闻的结构化信号（方向、强度、影响资产）"""

@tool
def read_market_snapshot() -> str:
    """读取当前市场快照（价格、盘口、波动率、成交量）"""

@tool
def read_portfolio() -> str:
    """读取自身当前持仓、资金和盈亏"""

@tool
def risk_check(side: str, qty: float, price: float) -> str:
    """检查下单是否符合风控约束（仓位限制、杠杆限制）"""

@tool
def place_order(side: str, qty: float, order_type: str,
                limit_price: float = None) -> str:
    """提交交易订单（market 市价单 / limit 限价单）"""

@tool
def cancel_order(order_id: str) -> str:
    """撤销挂单"""

@tool
def write_memory(key: str, content: str) -> str:
    """写入本轮交易记忆"""

@tool
def query_memory(query: str) -> str:
    """查询历史交易记忆"""
```

### 6.6 State 设计

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

class Order(TypedDict):
    order_id: str
    agent_id: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["market", "limit"]
    qty: float
    limit_px: Optional[float]
    tick: int

class Trade(TypedDict):
    buyer_id: str
    seller_id: str
    qty: float
    px: float
    tick: int

class AgentSnapshot(TypedDict):
    agent_id: str
    cash: float
    positions: dict[str, float]
    nav: float
    pnl: float
    last_action: str
    memory: list[str]

class SimulationState(TypedDict):
    # 场景
    scenario_id: str
    news: NewsSignal
    tick: int
    max_ticks: int

    # 市场
    price: float
    price_history: list[float]
    volatility: float
    bid_ask_spread: float

    # Agent
    agents: dict[str, AgentSnapshot]
    agent_configs: dict[str, str]     # agent_id -> .md 文件路径

    # 订单流
    pending_orders: Annotated[list[Order], operator.add]
    trades: Annotated[list[Trade], operator.add]

    # 控制
    stop_reason: Optional[str]
    report: Optional[str]
```

---

## 七、项目目录结构

```
agent-adaptation-finance/
├── CLAUDE.md
├── pyproject.toml
├── README.md
├── configs/
│   ├── simulation.yaml               # 仿真参数（tick数、初始价格等）
│   └── market.yaml                    # 市场参数（撮合规则、价差等）
├── agents/                            # 每个群体的 .md 配置
│   ├── retail_momentum.md             # 散户-动量追随
│   ├── retail_contrarian.md           # 散户-逆向抄底
│   ├── mutual_fund.md                 # 公募/长线机构
│   ├── macro_fund.md                  # 宏观对冲基金
│   ├── quant_fund.md                  # 量化中频基金
│   ├── market_maker.md                # 高频做市商
│   └── passive_fund.md                # 被动资金(ETF/指数)
├── src/
│   ├── __init__.py
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py                   # SimulationState 定义
│   │   ├── supervisor_graph.py        # 主仿真图
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── ingest_news.py         # 消息接收
│   │       ├── extract_signal.py      # 信号提取
│   │       ├── dispatch_agents.py     # 并行触发 Agent
│   │       ├── risk_gate.py           # 风控校验
│   │       ├── match_engine.py        # 订单撮合
│   │       ├── update_market.py       # 市场状态更新
│   │       ├── update_memory.py       # Agent 记忆更新
│   │       └── report.py             # 报告生成
│   ├── agent_runtime/
│   │   ├── __init__.py
│   │   ├── react_executor.py          # 统一 ReAct 执行器
│   │   ├── prompt_loader.py           # 从 .md 加载 prompt
│   │   ├── tool_registry.py           # Agent 工具注册
│   │   └── memory_store.py            # Agent 记忆管理
│   ├── market/
│   │   ├── __init__.py
│   │   ├── order_book.py              # 订单簿
│   │   ├── matching.py                # 撮合引擎
│   │   └── price_impact.py            # 价格冲击模型
│   └── schemas/
│       ├── __init__.py
│       ├── order.py
│       ├── market_state.py
│       └── agent_action.py
├── scenarios/                         # 预定义场景
│   ├── fed_rate_hike.yaml
│   ├── earnings_beat.yaml
│   └── black_swan.yaml
├── outputs/
│   └── runs/                          # 仿真结果存储
├── tests/
│   ├── test_match_engine.py
│   ├── test_react_executor.py
│   └── test_graph_flow.py
└── notebooks/
    └── simulation_demo.ipynb
```

---

## 八、技术栈

```
pip install langgraph langchain langchain-anthropic
```

| 层 | 包 | 做什么 |
|----|-----|--------|
| 外层仿真循环 | `langgraph` StateGraph + Send | 消息进来 → 并行触发7个Agent → 撮合 → 更新价格 → 循环 |
| 每个群体 Agent | `langchain` 的 `create_agent` | 读消息 → 思考 → 调用工具 → 下单（返回的是 LangGraph 子图） |
| 工具定义 | `langchain` 的 `@tool` | read_news、place_order、risk_check 等 |
| LLM | `langchain-anthropic` | Agent 的大脑（Claude） |
| 数据模型 | `pydantic` v2 | State 和 Action 的类型定义 |
| 数值计算 | `numpy` | 价格计算、指标统计 |
| 可视化 | `matplotlib` / `plotly` | 价格走势、群体行为图表 |
| 测试 | `pytest` | 单元测试和集成测试 |

两者关系：`create_agent`（langchain）返回的就是 LangGraph 图对象，
天然嵌套进外层 `StateGraph`。不是"选哪个"，而是"外层 LangGraph 编排 + 内层 LangChain Agent"。

---

## 九、实施路线

### Phase 1: 最小可运行系统
1. 项目初始化（pyproject.toml、目录结构）
2. 定义 SimulationState
3. 实现 2 个群体的 `.md` 配置（散户-动量 + 宏观对冲基金）
4. 实现 ReAct 执行器 + prompt 加载器
5. 实现简化撮合引擎
6. 搭建主仿真图，跑通"1条消息 → 2个Agent反应 → 价格变化"

### Phase 2: 完整群体 + 多轮反应
7. 补全 7 类群体的 `.md` 配置
8. 实现多轮反应循环（Agent 看到价格变化后二次反应）
9. 实现 Agent 记忆系统
10. 实现风控校验节点

### Phase 3: 丰富场景 + 分析
11. 创建多种消息场景（加息、财报、黑天鹅等）
12. 实现仿真报告生成（价格走势、群体行为分析）
13. 可视化 dashboard

### Phase 4: 进阶特性
14. 信息扩散网络（散户受社媒影响）
15. Agent 学习与适应（跨场景记忆累积）
16. 实验框架（ablation 对比不同群体组合的市场影响）
