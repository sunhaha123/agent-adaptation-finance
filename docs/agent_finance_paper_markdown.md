# 基于 agent 的计算金融中 agent 的适应性模型

**作者**：陶倩，黄平  
**单位**：上海理工大学管理学院，上海 200093

---

## 摘要

在有关基于 agent 计算金融的研究中，主要强调 agent 的学习进化机制，却忽略了对 agent 使用相应学习机制的内在原因，即 agent 不同适应属性的研究。在现实的金融市场中，各个 agent 在可用信息的解释、理解，本身的认知结构，对风险的态度，时间范围的认识，以及决策规则等方面都存在相当大的差异。

本文基于 agent 适应性的模型，全面分析了 agent 可能的适应属性，并提出了 agent 适应性的分级结构框架及其相应的实现机制。最后，说明了 agent 的适应性研究对股票市场仿真的重要意义。

**关键词**：智能 agent；金融市场；基于 agent 的计算金融；agent 适应性  
**中图分类号**：F830.49  
**文献标识码**：A

---

## The Model of Agent Adaptation for Agent-based Computational Finance

**TAO Qian, HUANG Ping**  
*(School of Management, University of Shanghai for Science and Technology, Shanghai 200093, China)*

### Abstract

Many current studies on agent-based computational finance focus on learning and evolution. However, they ignore the intrinsic cause of agent learning, namely, agent adaptation. The paper proposes a hierarchy framework of agent adaptation based on agent behavior model. It discusses various mechanisms for adaptation occurring in agent-based computational finance and explains the significance of exploring agent adaptation in multi-agent simulation of stock market.

**Key words**: intelligent agent; financial market; agent-based computational finance; agent adaptation

---

## 一、引言

现代金融理论认为，金融市场是一个复杂适应系统。面对金融市场的复杂性，传统的数学分析方法，如趋势分析、均衡分析、样本均值等陷入了前所未有的困境。正是这些困境，促使了美国 SFI 研究所的研究人员利用基于主体的计算机模型首先描述了人工股票市场（ASM）。从而开辟了基于主体的计算金融方法之先河。

从 1990 年到 1997 年，论文的发表标志着金融的又一分支——基于主体的计算金融的诞生。

基于 agent 的计算金融是动态地分析金融市场内部变化状况的有效方法。它把金融市场模型化成相互作用的 agent 构成的进化系统，通过建立基于 agent 的金融模型，来对各种假设进行实验性的研究，最后通过对实验结果的观察和比较来加深我们对金融市场的理解。最近，有许多关于这方面的文献已发表。

目前，在有关基于 agent 计算金融的研究中，主要强调 agent 的学习进化机制，却忽略了对 agent 使用相应学习机制的内在原因——agent 不同适应属性的研究。在现实的金融市场中，各个 agent 在可用信息的解释、理解，本身的认知结构，对风险的态度，时间范围的认识，以及决策规则等方面都存在相当大的差异。这些差异表明了每个 agent 都具有不同适应属性。因而我们只有对 agent 的适应属性进行全面的分析和研究，才能更深入地理解这些差异是怎样产生，进而更加理性地理解 agent 适应属性的差异对金融市场价格动态所产生的影响。

笔者提出了基于 agent 适应性的模型，全面分析了 agent 可能的适应属性，并提出了 agent 适应性的分级结构框架及其相应的实现机制。最后，说明了 agent 的适应性研究对股票市场仿真的重要意义。

---

## 二、主体的适应性研究

在基于 agent 的计算金融中，一般为了便于调查 agent 系统的数学特性，对 agent 行为的定义通常是采用数学公式来描述的，并假设金融市场中存在较少类型的交易者，且满足均衡条件及有信息效率等。然而，在现实的金融市场中，交易者在认知结构、决策规则和学习能力等方面往往表现出相当大的差异性，这种差异性及交易者形成的金融市场组织结构会对金融市场的价格动态产生重大影响。因此，为了描述 agent 这些行为上的差异性，笔者借鉴人工智能研究中的认知结构，将一个智能 agent 的行为结构模型表示为 agent 复杂多样的行为。

### （一）主体行为的分层结构模型

agent 行为的结构模型是由 5 大子 agent 构成，即感知 agent P、操作 agent A、目标 agent G、偏好 agent I、感知和操作之间的映射 `f(P, θ)`，如图 1 所示。

> **图 1 构成主体的 5 大要件**

- **环境状态**：Agent 所处的环境状态用  
  `S = {s1, s2, s3...}`  
  来表示。
- **操作 agent A**：根据操作规则来对环境进行操作。
- **感知 agent P**：感知 agent 给全局或局部适应机制组成。感知 agent 根据目标来给环境状态赋予不同的效用，以吸收一定的环境状态子集，然后根据感知/学习产生对外部环境状态的感知。
- **映射 `f(P, θ)`**：对应从感知到操作之间的决策逻辑，由预测规则、决策规则和相应的规则适应机制组成。其过程可以用三层结构来描述。即预测层、决策层、在预测结果基础上运用相应的预测规则，再根据所观察到的结果，agent 在预测结果基础上运用相应的决策规则来产生相应的操作。映射 `f(P, θ)` 中的 `θ` 表示一组参数。
- **目标 agent G**：由目标的集合和目标适应机制组成，agent 根据目标来感知不同的环境状态。
- **偏好 agent I**：由偏好的集合和偏好适应机制组成。agent 根据不同的偏好对目标赋予不同的优化权。

### （二）主体适应性的分类

为了更加全面地理解和分析 agent 的适应属性，针对上述 agent 行为的分层结构模型，笔者提出了 agent 适应性的一个分级结构框架。用于区分 agent 的适应性层次。

#### 1. 弱式适应性

在这种水平的适应性上，agent 根据它的感知按照一个静态的映射 `f(P)` 来决定它的操作。这个映射（连同 agent P 和 agent A 一起）都是在设计时就被决定的，并且在 agent 的生命周期中保持稳定。这时，agent 本身不具有适应性，因为它没有被修改。

#### 2. 半弱式适应性

在这个水平的适应性上，从感知到操作的映射能够被修改。也就是说，映射 `f(P, θ)` 是具有适应性的，agent 可以修改从感知到操作之间的映射规则。

#### 3. 半强式适应性

在这个水平的适应性上，目标 agent G 是具有适应性的。agent 可以通过目标 agent G 的适应机制，对目标集合进行修改。感知 agent P 也是有适应性的，可以通过感知 agent P 的适应机制来对感知的规则进行修改。因为 agent 通过它的感知来观察环境状态，改变感知将自动地导致它在系统（主体能够被假设对世界具有不同的认知）的目标上的一个功能改变。

#### 4. 强式适应性

在这个水平的适应性上，偏好 agent I 是具有适应性的。agent 可以通过偏好 agent I 的适应机制对偏好集合进行修改。操作 agent A 也是具有适应性的，agent 可以通过操作 agent A 的适应机制对操作规则进行修改。

上述分类是单纯从 agent 本身的适应性出发做出的。且分类级别是遵循包含式的，即显示半弱式适应性 agent 能够表现出弱式适应性，显示强式适应性的 agent 也能显示出其它类型的适应性等。

### （三）主体适应性机制

既然 agent 可以通过其行为结构模型中各种 agent 的适应机制来实现不同水平的适应性，一个重要的问题就是：这些修改如何在不同的适应性水平上被操作。下面笔者列出了 agent 实现不同水平适应性的各种机制，包括：模仿、反射、反馈学习、创新的学习、进化。

#### 1. 模仿

模仿是一种简单的将观察到的数据、操作和解决方案进行拷贝的方式。不同适应级别的 agent 能够拷贝其它 agent 的感知、操作、目标或偏好。从感知到操作的映射也能够通过拷贝某个被观察的 agent 操作来获得。当然，这必须在有可能去观察某些其他 agent 的构成和操作的前提下才行。例如在金融市场中，交易者可以模仿其他交易者（比如那些被认为是成功交易者）的操作。

#### 2. 反射

反射是一种对特殊事件和变化的直接反应。他们能表现出用 if...then 规则或者教学公式来表示。当 agent 具有半弱式的适应性时，能够用反射原理来修改映射或决策规则。例如：当某资产价格跌到低于一个示范的适应性条件值时，交易者将通过反射方式卖出该类资产。

#### 3. 反馈学习

反馈学习反映 agent 为了完成其适应任务，用基于过去的学习经验对 agent 行为结构模型中的各种规则和集合进行修改的机制。进行反馈学习的 agent 可以连续地使用被收到的反馈。半强式适应性水平的一种实现方式适应性下的操作，偏好的修正规则以及偏好集合也都能够被修改。例如：技术交易者修改自己的交易模型就是上述的交易数据来进行反馈学习的。

#### 4. 创新学习

创新学习对 agent 行为结构模型中的各种规则和集合根据环境变化进行修改的一种机制，这种类型的学习更加强调目标。在强式适应性和半强式适应性中，为 agent 设计一个新的目标、偏好，或者操作意味着创新学习。例如：金融机构基于新的市场条件开发了一种新的金融产品就是创新学习。

#### 5. 进化

进化可以在 agent 连续的后代产生期间逐渐地修改 agent 行为结构模型中的各种规则和集合。这种机制可以被用于半强式适应性、半弱式适应性和强式适应性。例如，在金融市场中，导致不断断货的交易规则将逐渐被进化机制淘汰掉。

---

## 三、agent 适应性研究对股票市场仿真的意义

基于 agent 的股票市场仿真是采用基于 agent 计算金融的方法把股票市场模型化成许多相互作用的 agent 构成的进化系统。基于 agent 的股票市场仿真能够在很大程度上复现股票市场中发生的现象，对这些现象进行深入的分析和研究，可以使我们进一步理解股票市场价格形成的深层次原因。

在基于 agent 的股票市场仿真中，agent 可以根据信息由目标和偏好建立起感知股票市场的各种价值信息，进行预测和决策，产生具体的市场操作。而且，agent 是自适应的，可以根据其相应的适应属性，调整自身的学习进化策略。

股票市场的价格动态很大程度上由交易者的认知结构的多样性（包括决策方式和学习能力）、交易者所处的外部环境，以及交易者对市场的组织结构（市场的规则结构）所影响。笔者提出的 agent 适应性的分级结构模型，揭示了 agent 具有不同的认知结构、决策方式和学习能力。并在此基础上将 agent 分成了不同水平的适应性，进而，在关于 agent 的股票市场仿真中，就可以根据 agent 适应性的不同，对其进行分类，从而改变了传统的基于 agent 的股票市场仿真中对 agent 的分类方式，有利于更深入地研究 agent 不同的认知结构、对风险的态度、决策方式和学习能力对股票市场价格动态的影响。

---

## 参考文献

1. Holland J. *Modeling Complex Adaptive System* [M]. 2001.  
   URL: `www.edu.au/ci/vol02/forrest/node16.html`

2. Arthur, W. B., Holland, J., LeBaron, B., Palmer, R., Taylor, P.  
   Asset pricing under endogenous expectations in an artificial stock market. In W. B. Arthur, S. Durlauf, and D. Lane (eds.), *The Economy as an Evolving Complex System II*. Addison-Wesley, MA, 1997: 15-44.

3. LeBaron, W. B. Arthur, and R. Palmer.  
   Time series properties of an artificial stock market. *Journal of Economic Dynamics and Control*, 1999, 23: 1487-1516.

4. M. Lettau.  
   Explaining the fact with adaptive agents: the case of mutual fund flows. *Journal of Economic Dynamics and Control*, 1997, 21: 1117-1147.

5. P. Noriega and C. Sierra.  
   Auctions and multi-agent system. In M. Klusch (ed.), *Intelligent Information Agents*. Berlin: Springer, 1999: 153-175.

6. Y. Shoham and M. Tennenholtz.  
   On the emergence of social conventions: modeling, analysis, and simulations. *Artificial Intelligence*, July 1997, 94(1-2): 139-166.

7. L. Tesfatsion.  
   Introduction to the special issue on agent-based computational economics. *Journal of Economic Dynamics and Control*, 2001, 25: 281-293.

---

## 说明

这是根据图片内容整理的 Markdown 版。由于原图为扫描页，个别字词、标点和参考文献格式可能存在轻微识别误差，但整体结构与核心内容已完整保留。
