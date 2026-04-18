# 多 Agent 涌现与遗传算法仿真方案

## Summary

在现有项目基础上，把当前的单轮公式：

```text
AgentResponse = LLM(agent_prompt, news_signal)
```

升级为多轮仿真闭环：

```text
PrototypeSignal = LLM(agent_prompt, news_signal)
Order = policy(genome, PrototypeSignal, market_state, social_state)
market_state' = order_book_match(Order[])
genome' = genetic_algorithm(fitness)
```

核心思想是：LLM 只负责“舆情解读、事件响应、群体原型判断”；真正的交易行为、订单簿撮合、价格反馈、羊群传染和遗传演化由可复现的数值规则驱动。

## Key Changes

- 保留现有新闻信号抽取和 agent prompt 体系，但把每个 `agents/*.md` 视为“群体原型”，不再让每个个体每轮都调用 LLM。
- 新增单一指数市场 `MARKET_INDEX`，初始价格默认 `100.0`，用多轮订单簿撮合生成价格、成交量、波动率和收益反馈。
- 新增个体 agent 群体：每个群体原型下生成多个个体，每个个体持有可遗传的数值基因。
- 新增行为模仿机制：个体决策受自身信号、群体收益、市场趋势、羊群系数共同影响。
- 新增遗传算法：每一代跑若干交易轮，根据收益、回撤、换手和风险惩罚计算 fitness，选择、交叉、变异产生下一代。
- 新增涌现指标：羊群指数、观点分歧、价格波动、成交量、泡沫/崩盘标记、群体权重变化。
- 最终报告同时解释“市场现象如何涌现”和“它如何对应论文里的适应性、反馈学习、模仿、进化”。

## Interfaces And Data Flow

新增或扩展核心类型：

```python
class AgentGenome(BaseModel):
    risk_appetite: float          # 风险偏好
    signal_sensitivity: float     # 对新闻/LLM 信号敏感度
    herd_coefficient: float       # 羊群系数
    contrarian_bias: float        # 逆向倾向
    confidence_threshold: float   # 出手阈值
    position_limit: float         # 最大仓位

class AgentRuntimeState(BaseModel):
    individual_id: str
    archetype_id: str
    genome: AgentGenome
    cash: float
    position: float
    fitness: float
    last_pnl: float

class MarketState(BaseModel):
    round_index: int
    price: float
    volume: float
    volatility: float
    return_rate: float
    order_imbalance: float

class Order(BaseModel):
    individual_id: str
    side: Literal["buy", "sell"]
    quantity: float
    limit_price: float

class Trade(BaseModel):
    buyer_id: str
    seller_id: str
    quantity: float
    price: float
```

仿真主流程：

1. `extract_signal`  
   沿用当前逻辑，把新闻抽成 `news_signal`。

2. `generate_archetype_signals`  
   每个群体原型调用一次 LLM，得到原型级 `AgentResponse`，作为该群体的基础情绪和方向信号。

3. `initialize_population`  
   默认生成 `120` 个个体，平均分配到现有 6 类 agent；每个个体根据群体类型初始化不同基因范围。

4. `run_market_round`  
   每轮中，个体根据以下输入生成订单：

   ```text
   order_intent =
       prototype_stance
       + signal_sensitivity * news_signal
       + herd_coefficient * recent_majority_action
       + contrarian_bias * opposite_of_crowd
       + price_feedback * recent_return
   ```

5. `match_order_book`  
   单一指数订单簿撮合：
   - 买单按价格从高到低排序，卖单按价格从低到高排序。
   - 当最高买价 >= 最低卖价时成交。
   - 成交价使用买卖限价中点。
   - 本轮收盘价使用成交 VWAP；若成交不足，用订单不平衡产生小幅价格冲击。
   - 价格必须保持正数，并设置单轮最大涨跌幅保护，默认 `±10%`。

6. `update_feedback`  
   根据新价格更新每个个体的现金、仓位、PnL、回撤、最近收益，并形成下一轮的社会信号：
   - 多数方向
   - 高收益 agent 行为
   - 群体平均收益
   - 羊群指数

7. `evolve_population`  
   每代默认 `50` 轮交易后执行遗传算法：
   - fitness = 收益率 - 回撤惩罚 - 换手惩罚 - 过度集中惩罚。
   - 保留前 `10%` 精英。
   - 剩余个体通过锦标赛选择父代。
   - 数值基因做算术交叉。
   - 变异使用高斯扰动，并 clamp 到合法区间。
   - 辅助更新群体权重：高 fitness 群体在下一代中占比略升，低 fitness 群体占比略降。

8. `generate_emergence_report`  
   LLM 只读取结构化结果和指标，生成中文报告，不参与数值演化。

建议新增 CLI：

```bash
python main.py "美联储宣布加息50基点" \
  --mode evolve \
  --rounds 50 \
  --generations 20 \
  --population 120 \
  --seed 42
```

默认仍保留当前单轮模式，避免破坏已有用法。

## Paper Mapping

- 感知 agent `P`：`extract_signal` 与原型级 LLM 舆情解读。
- 目标 agent `G`：群体 markdown 中的角色目标，并通过 genome 中的策略参数影响行为。
- 偏好 agent `I`：`risk_appetite`、`position_limit`、`contrarian_bias` 等可遗传参数。
- 映射 `f(P, θ)`：从纯 LLM 决策升级为 `policy(genome, signal, market_state, social_state)`。
- 操作 agent `A`：从 `AgentResponse.action` 升级为真实 `Order`。
- 模仿：由 `herd_coefficient` 和高收益群体行为传染实现。
- 反馈学习：由价格、收益、回撤更新下一轮决策状态实现。
- 进化：由遗传算法淘汰低 fitness 参数组合、保留高 fitness 参数组合实现。
- 涌现：由个体规则经过订单簿和反馈闭环形成宏观价格波动、羊群、抱团、反转或崩盘。

## Test Plan

- 单元测试：
  - genome 初始化范围正确，变异后仍在合法区间。
  - 订单簿撮合满足价格优先，成交价和成交量正确。
  - 市场价格永远为正，单轮涨跌幅不超过限制。
  - 同一 `seed` 下仿真结果完全可复现。
  - fitness 计算能正确惩罚高回撤、高换手和极端仓位。

- 集成测试：
  - 使用固定新闻跑 `2` 代、每代 `5` 轮、`12` 个个体，确认能生成价格序列、交易记录、fitness、下一代 population 和报告。
  - 对强利好新闻，动量类个体早期买单占比应上升。
  - 当 `herd_coefficient` 提高时，羊群指数应显著上升。
  - 当开启遗传算法后，高 fitness 基因在后续代中的平均占比应上升。

## Assumptions

- 第一版只做单一指数市场，不做多资产。
- 第一版采用混合模式：LLM 做原型信号，数值规则做多轮交易和遗传演化。
- 遗传算法主进化数值策略参数，群体权重作为辅助进化结果。
- 不引入真实行情数据，市场价格完全由仿真内生生成。
- 默认参数：`population=120`、`rounds=50`、`generations=20`、`seed=42`、初始价格 `100.0`。
- 当前单轮决策意向模式继续保留，新增仿真模式不破坏已有 README 中的核心公式。
