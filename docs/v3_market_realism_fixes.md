# V3：市场真实性修复

日期：2026-04-18

## 背景

V2 版本在美伊战争情景仿真中出现严重偏离现实的结果：

- 价格从 100 单向下跌至 75.48（-24.3%）后**完全冻结**，停火信号毫无效果
- 羊群指数（herd_index）锁死在 1.0，市场丧失价格发现功能
- 成交量在多个代次归零，市场流动性完全枯竭
- 遗传算法将逆势型 agent（retail_contrarian）几乎完全淘汰，种群多样性丧失
- 最优策略是"什么都不做"（fitness=0），动量型 agent 占据 50% 种群

这与真实市场表现完全相反——标普500在美伊战争期间经历了下跌→反弹→震荡的完整周期，从未出现流动性枯竭或价格冻结。

## 根因分析

识别出 4 个相互关联的结构性缺陷：

### 1. 无做市商（No Market Maker）

原始 `order_book.py` 仅撮合 agent 之间的订单。当所有 agent 方向一致时（如全部看空），没有对手方，成交量归零，价格无法变动。真实市场始终有做市商提供双向流动性。

### 2. 羊群正反馈无阻尼（Uncontrolled Herd Feedback Loop）

`policy.py` 中的羊群分量 `0.35 × herd_coefficient × majority_action` 形成自我强化循环：

```
多数卖出 → majority_action=-1 → herd_component 加强卖出 → 更多卖出 → majority_action 维持 -1
```

一旦 herd_index 到达 1.0，没有任何机制能打破这一均衡。

### 3. 无均值回归（No Mean Reversion）

价格偏离基本面后缺乏拉回力量。现实中当资产被严重低估时，价值投资者会进场买入，形成天然的价格锚定。仿真中完全缺失这一机制。

### 4. GA 过度消灭多样性（Excessive Diversity Loss in GA）

遗传算法的 softmax 权重分配没有下限保护，导致短期表现差的 archetype（如逆势型）被快速淘汰。但这些 agent 恰恰是停火后提供买入力量的关键参与者。

## 修复方案

### Fix 1: 做市商注入 — `engine.py`

在每轮撮合前注入做市商（Market Maker）双向订单，确保始终有对手方。

**关键设计**：
- 做市商以 `__mm__` 为 ID 前缀，与普通 agent 区分
- 每侧深度 = 总权益 × 2%（`MM_DEPTH_FRACTION = 0.02`）
- 买卖价差 0.3%~0.5%（含随机抖动），符合真实做市商行为
- 做市商不参与 fitness 计算和遗传演化

```python
MM_DEPTH_FRACTION = 0.02

def _market_maker_orders(price, total_equity, rng) -> list[Order]:
    notional = total_equity * MM_DEPTH_FRACTION
    quantity = notional / price
    spread = 0.003 + rng.uniform(0.0, 0.002)
    return [
        Order(id="__mm__", side="buy",  quantity=quantity, limit_price=price*(1-spread), intent=0),
        Order(id="__mm__", side="sell", quantity=quantity, limit_price=price*(1+spread), intent=0),
    ]
```

**联动修改**：
- `feedback.py` 中 `apply_trades` 改用 `.get()` 查找 agent，跳过做市商一侧的资金/仓位更新
- `build_social_state` 过滤 `__mm__` 前缀订单，确保社会信号仅反映真实 agent 行为

### Fix 2: 羊群阻尼 — `policy.py`

引入基于 herd_index 的二次方阻尼因子，当市场行为高度一致时自动削弱羊群放大效应：

```python
herd_damping = max(0.05, 1.0 - social_state.herd_index ** 2)
herd_component = 0.35 * genome.herd_coefficient * social_state.majority_action * herd_damping
```

| herd_index | damping | 效果 |
|-----------|---------|------|
| 0.0 | 1.00 | 无衰减 |
| 0.5 | 0.75 | 轻度衰减 |
| 0.8 | 0.36 | 显著衰减 |
| 0.95 | 0.10 | 强烈衰减 |
| 1.0 | 0.05 | 接近归零 |

这模拟了真实市场中"当所有人方向一致时，套利者和逆势者的利润空间反而最大"的自然调节机制。

### Fix 3: 非对称均值回归 — `policy.py`

新增 `reference_price` 参数（默认使用初始价格 100 作为基本面锚点），计算价格偏离程度并生成回归力量：

```python
if price_deviation < 0:  # 低于基本面
    reversion_signal = -clamp(price_deviation * 2.0, -1, 1)
    reversion_weight = 0.15 + 0.25 * genome.contrarian_bias
else:  # 高于基本面
    reversion_signal = -clamp(price_deviation * 5.0, -1, 1)
    reversion_weight = 0.30 + 0.15 * genome.contrarian_bias
```

**设计理由**：
- **低于基本面时温和拉回**：允许战争冲击造成有意义的下跌（15-30%），但防止无底洞式崩溃
- **高于基本面时强力抑制**：防止停火反弹过度超调，模拟"估值天花板"效应
- **逆势型 agent 响应更强**：contrarian_bias 高的 agent 对均值偏离更敏感，符合价值投资逻辑
- **动量型 agent 也有基础响应**：即使 contrarian_bias=0，仍有 0.15/0.30 的最低权重

### Fix 4: 物种多样性下限 — `genetics.py`

在 `evolved_group_weights` 中为每个 archetype 设置 5% 最低权重：

```python
MIN_GROUP_WEIGHT = 0.05

# 在权重混合之后:
for key in mixed:
    mixed[key] = max(mixed[key], MIN_GROUP_WEIGHT)
```

确保即使在极端熊市中，逆势型、被动型等 agent 也不会被完全淘汰，保持生态多样性。

## 修复效果对比

### 价格走势

| 阶段 | V2（修复前） | V3（修复后） |
|------|------------|------------|
| 前期对抗（gen 0-4） | 100→88.65 (-11.4%) | 100→94.84 (-5.2%) |
| 战争爆发（gen 5-9） | 88.65→82.07 (-7.4%) | 94.84→78.25 (-17.5%) |
| 伊朗报复（gen 10-14） | 82.07→75.48 (-8.0%) | 78.25→63.83 (-18.4%) |
| 停火（gen 15-19） | 75.48→75.48 (0.0%) | 63.83→103.39 (+62.0%) |
| **总计** | **-24.5%，冻结** | **-36% 低谷，+3.4% 终值** |

### 关键指标

| 指标 | V2 | V3 |
|------|-----|-----|
| 平均羊群指数 | 0.993 | 0.232 |
| 零成交量代次 | 11/20 | 1/20 |
| 最优 agent 类型 | retail_momentum | macro_fund |
| 最优 fitness | 0.000 | 0.034 |
| 停火反弹幅度 | 0% | +62% |
| retail_contrarian 权重 | 10.0% | >5%（保底） |

### 涌现行为改善

1. **价格动态恢复**：市场在战争期间逐步下跌，在停火后 V 形反弹，符合真实地缘冲突市场表现
2. **涌现性反弹**：gen 9 和 gen 14 出现自发性缓冲反弹（非事件驱动），源于均值回归力量
3. **羊群指数健康**：0.23 均值（正常范围 0.2-0.5），从未锁死在 1.0
4. **策略多样性**：宏观基金成为最优策略（而非"什么都不做"），逆势型 agent 在停火阶段盈利
5. **流动性连续**：做市商保障了基本成交量，价格发现功能始终正常运作

## 文件变更清单

| 文件 | 变更 | 行数 |
|------|------|------|
| `src/simulation/engine.py` | 新增做市商函数及订单注入，传入 reference_price | +18 |
| `src/simulation/policy.py` | 羊群阻尼、非对称均值回归、reference_price 参数 | +19/-3 |
| `src/simulation/feedback.py` | apply_trades 兼容做市商，social_state 排除做市商 | +10/-7 |
| `src/simulation/genetics.py` | MIN_GROUP_WEIGHT 下限保护 | +5 |

所有 12 个既有测试通过，无破坏性变更。

## 已知局限

1. **做市商无限容量**：当前做市商每轮重新生成，不跟踪库存和盈亏，可能在极端情景下提供过多流动性
2. **固定参考价格**：均值回归使用固定初始价格（100）作为锚点，不随基本面变化调整；使用移动均线会更准确
3. **最后一代零成交**：gen 19 偶尔出现零成交量，原因是价格接近参考价时强力均值回归将 intent 压至 confidence_threshold 以下
4. **参数敏感性**：MM_DEPTH_FRACTION、均值回归权重等参数对结果影响显著，未做系统性敏感性分析
