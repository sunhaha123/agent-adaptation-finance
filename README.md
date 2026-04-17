# 金融市场多 Agent 仿真系统

给一条市场消息，看不同交易群体（散户、机构、对冲基金...）各自怎么反应。

> **核心公式：`AgentResponse = LLM(agent_prompt, news_signal)`**
>
> 每个 Agent 的本质是：用 `agents/*.md` 中定义的角色、思维方式和风险偏好作为 `agent_prompt`，再输入统一抽取后的市场信号 `news_signal`，由 LLM 生成结构化决策意向 `AgentResponse`。

## 它能做什么

输入一条新闻：
```
python main.py "美联储宣布加息50基点"
```

输出每个群体的决策意向：
```
🔴 散户-动量追随: 看空 | "天哪要跌了赶紧卖！"
🟢 宏观对冲基金: 看多 | "加息预期已 price in，超跌就是机会"
...
📋 综合分析报告: 散户恐慌性抛售 vs 机构逆向布局...
```

## 工作原理

```
你输入一条新闻
    ↓
系统把新闻结构化（利多/利空、强度、影响哪些资产）
    ↓
7个 Agent 并行读取新闻，各自独立思考
    ↓
每个 Agent 输出：立场 + 置信度 + 操作建议 + 推理过程
    ↓
汇总生成对比分析报告
```

每个 Agent 的"性格"写在 `agents/*.md` 文件里，比如散户就是追涨杀跌、情绪化，对冲基金就是做因果链分析、跨资产联动。想加新群体？新建一个 `.md` 文件就行。

## 快速开始

### 1. 安装

```bash
pip install -e .
```

### 2. 配置 LLM

复制 `.env.example` 为 `.env`，填入你的 API Key：

```bash
cp .env.example .env
```

`.env` 里需要配置（任选一个 LLM 提供商）：

```env
# 智谱 GLM
LLM_PROVIDER=openai-compatible
LLM_API_KEY=你的智谱key
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
LLM_MODEL=glm-4.5

# 或者 OpenAI
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-4.1-mini

# 或者 DeepSeek
LLM_PROVIDER=openai-compatible
LLM_API_KEY=你的deepseek-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 或者 Anthropic / Anthropic 兼容网关
LLM_PROVIDER=anthropic
LLM_API_KEY=你的anthropic-key
LLM_BASE_URL=https://your-anthropic-compatible-endpoint  # 直连官方时可不填
LLM_MODEL=claude-sonnet-4-6
```

### 3. 运行

```bash
# 自定义消息
python main.py "英伟达财报大超预期，营收同比增长200%"

# 不传消息会用默认的
python main.py
```

## 项目结构

```
├── main.py                  # 入口，运行这个就行
├── agents/                  # Agent 配置（每个 .md = 一个群体）
│   ├── retail_momentum.md   #   散户-动量追随
│   └── macro_fund.md        #   宏观对冲基金
├── src/
│   ├── graph/
│   │   ├── state.py         # 数据结构定义
│   │   ├── main_graph.py    # LangGraph 主图（调度流程）
│   │   └── nodes/           # 图的每个节点
│   │       ├── extract_signal.py      # 新闻 → 结构化信号
│   │       ├── dispatch_agents.py     # 并行触发所有 Agent
│   │       ├── collect_responses.py   # 收集 Agent 响应
│   │       └── generate_report.py     # 生成对比报告
│   ├── agent_runtime/
│   │   └── agent_factory.py # 读取 .md 配置 → 创建并运行 Agent
│   └── schemas/
│       └── response.py      # AgentResponse 等数据模型
├── docs/
│   ├── implementation_plan.md         # 实现计划
│   └── agent_finance_paper_markdown.md # 参考论文
└── pyproject.toml
```

## 怎么加一个新的交易群体

在 `agents/` 下新建一个 `.md` 文件，比如 `agents/quant_fund.md`：

```markdown
---
agent_id: quant_fund
agent_name: 量化基金
---

# 角色
你是一个量化基金的交易算法。你只看数据和因子信号，不受情绪影响。

# 思维方式
- 你用统计模型分析市场信号
- ...

# 决策输出要求
1. 立场（看多/看空/中性）
2. 置信度（0-1）
...
```

保存后直接运行 `python main.py`，系统会自动发现并加载新 Agent。

## 技术栈

- **LangGraph**：多 Agent 并行调度
- **LangChain**：LLM 调用 + 结构化输出
- **Pydantic**：数据模型验证
