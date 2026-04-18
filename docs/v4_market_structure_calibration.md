# V4：基于真实美股市场结构的参与者标定

日期：2026-04-18

## 背景

V3 修复了仿真的结构性缺陷，但 agent 的人口权重（均等 1/6）和行为参数（GENOME_RANGES）缺乏数据支撑。V4 基于真实美股市场参与者数据进行标定。

## 数据来源

| 数据 | 来源 | 日期 |
|------|------|------|
| 持仓结构 | Fed Z.1 L.224 | 2025 Q4 |
| 基金类型 | ICI Active/Index Report | 2026-02 |
| 交易量 | Cboe/MEMX Year in Review | 2025 |
| 散户行为 | CIBC/FINRA NFCS | 2024-2025 |
| 对冲基金 | Fed B.101.f | 2025 Q4 |

## 真实美股市场结构

| 参与者 | AUM占比 | 交易量占比 | 持仓期 | 换手率 |
|--------|--------|-----------|--------|--------|
| 家庭直接 | 33.8% | 30-37% | 0.6年 | 167% |
| 共同基金 | 15.4% | ~10% | 2年 | 50% |
| ETF/被动 | 9.7% | ~5% | 持续 | 5-10% |
| 外资 | 18.4% | ~10% | — | — |
| 养老/保险 | 8.9% | ~3% | 5-15年 | 15-30% |
| 对冲基金 | 1.2% | ~15% | 3-12月 | 100-300% |
| HFT/做市商 | — | 50%+ | 毫秒 | — |

HFT/做市商已在 V3 中单独建模（engine.py MM注入）。外资行为分散，按比例归入现有6类。

## Archetype → 参与者映射

| Archetype | 对应参与者 | 资本权重 | GA最低权重 |
|-----------|-----------|---------|-----------|
| passive_fund | 被动ETF+被动MF+部分外资被动 | 25% | 12% |
| mutual_fund | 主动MF+养老/保险+部分外资主动 | 25% | 12% |
| retail_momentum | 散户-动量/注意力驱动 | 20% | 10% |
| retail_contrarian | 散户-逆势/价值型 | 8% | 4% |
| quant_fund | 系统化/量化HF | 12% | 5% |
| macro_fund | 宏观/主观HF | 10% | 5% |

## 修改清单

### 1. `src/simulation/population.py`

- **新增 `MARKET_STRUCTURE` 配置**：每类的 capital_weight 和 min_weight
- **校准 `GENOME_RANGES`**：基于实证行为数据
  - confidence_threshold ∝ 1/换手率（散户低、被动高）
  - signal_sensitivity ∝ 反应速度（量化>散户>宏观>主动>被动）
  - herd_coefficient ∝ 羊群实证（散户动量最高，宏观/被动最低）
- **重写 `initialize_population`**：最大余数法加权分配（替代 round-robin 等分）
  - 120 agents → passive 30, mutual 30, retail_mom 24, retail_con 10, quant 14, macro 12

### 2. `src/simulation/genetics.py`

- 删除固定 `MIN_GROUP_WEIGHT = 0.05`，改为从 `MARKET_STRUCTURE[key]["min_weight"]` 读取
- `evolved_group_weights` / `evolve_population` 加可选 `market_structure` 参数

### 3. `src/simulation/events.py`

- 校准 `adapt_archetype_response` style dict（被动更不反应、散户更过度反应、宏观更逆势）

### 4. `src/simulation/policy.py`

- 增强低于基本面的均值回归（multiplier 2.0→3.0, base_weight 0.15→0.20），匹配新的加权种群结构

### 5. `tests/test_validation.py`（新文件）

- 验证种群权重与 MARKET_STRUCTURE 一致
- 验证仿真产生 V 形走势

## 效果

以美伊战争4事件、120 agents、20代×50轮仿真：

```
价格
100 ┤●前期对抗
    │  ╲
 80 ┤   ╲──── 战争爆发
    │        ╲
 63 ┤         ╲── 缓冲反弹（gen9, 涌现行为）
    │             ╲
 48 ┤              ╲ 伊朗报复低点
    │               ╲─ 缓冲反弹（gen14）
    │                  ╱ 停火反弹
 66 ┤                ╱
    │              ╱
 80 ┤            ╱
    │          ╱
 98 ┤        ─── 企稳接近初始水平
    ┴───────────────────────→ 代数
    0    4    8   12   16   19
```

| 指标 | V3（等权） | V4（市场结构加权） |
|------|-----------|------------------|
| 种群权重 | 均等16.7% | 按真实AUM: 25/25/20/8/12/10% |
| GA多样性保底 | 固定5% | 按类型: 12/12/10/4/5/5% |
| 平均羊群指数 | 0.23 | 0.35 |
| 涌现性缓冲反弹 | 2次 | 2次 |
| 最优agent类型 | macro_fund | passive_fund |
| 基因组校准 | 手动 | 实证数据驱动 |

## 已知局限

1. **幅度偏大**：仿真跌幅(-52%)远超真实标普(-8.2%)，因1000轮仿真的复合效应远超37个真实交易日
2. **参数仍有手动调整**：均值回归权重（policy.py）在从V3切换到V4加权种群后需要重新标定
3. **缺少校准框架**：当前没有自动化的参数搜索，未来可用贝叶斯优化对标真实价格数据
