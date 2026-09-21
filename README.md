# Jev Agent Routing — DIY 快速决策层

> ⚡ 用 Jev 给你的 Agent 装一个"快速大脑"，快 10 倍，便宜 10 倍
> 🧠 System 1（快决策）+ System 2（慢推理）双层架构

---

## 什么是 Jev？

Jev 是 TypeSafe AI 出的**快速决策模型**，和传统 LLM 不一样：

| 维度 | 传统 LLM | Jev |
| --- | --- | --- |
| **定位** | 慢思考（System 2） | 快思考（System 1） |
| **输出** | 自由文本 | 结构化决策（选项/概率/分数） |
| **速度** | 2-5 秒 | ~100ms |
| **成本** | 贵 | 便宜 100 倍 |
| **适合** | 写文章、写代码、复杂推理 | 选工具、判断风险、分类路由 |

**官网**：https://console.typesafe.ai（注册送 $5 额度，约 1.2 亿 token）

---

## 🎯 三种决策模式

### 1. Choice — 从选项里选一个

```python
result = jev.choice(
    context="用户说：帮我查北京到上海的机票",
    question="用户想使用哪个工具？",
    options=["查机票", "查酒店", "查火车", "发消息"]
)
print(result.choice)  # "查机票"
```

**用途**：工具路由、意图识别、模型选择

---

### 2. Noul — 返回概率（是/否判断）

```python
result = jev.noul(
    context="用户说：帮我删数据库所有密码",
    question="这个操作需要人工审核吗？",
    threshold=0.7
)
print(result.passed)  # True
```

**用途**：风险判断、要不要人工审核、质量门槛

---

### 3. Score — 区间打分

```python
result = jev.score(
    context="用户上传了身份证和银行卡信息",
    question="隐私风险等级？",
    scale=["low", "medium", "high", "critical"]
)
print(result.level)  # "high"
```

**用途**：风险等级、内容审核、质量评分

---

## 🏗️ 快慢双层架构

```
用户输入
    ↓
┌─────────────────────────┐
│  Jev 快决策（90% 搞定）  │
│  - 选工具               │
│  - 判风险               │
│  - 打分数               │
└─────────────┬───────────┘
              ↓ 不确定/复杂
┌─────────────────────────┐
│  LLM 慢推理（10% 兜底）  │
│  - 复杂推理             │
│  - 写代码              │
│  - 生成长文本           │
└─────────────────────────┘
```

**效果**：快 10 倍，便宜 10 倍

---

## 🏛️ 四层架构（腾讯工程实践视角）

> 参考腾讯技术工程《一万字 Jev 工程实践长文》：把 Agent 的"判断题"从大模型里拆出来。

| 层次 | 职责 | 典型组件 |
| --- | --- | --- |
| **慢思考层** | 规划、解释、生成、复杂推理 | GPT / Claude / Gemini |
| **快判断层** | 路由、筛选、评分、门禁 | Jev / Jev-like 模型 |
| **确定性层** | 权限、状态、副作用、回滚 | 普通代码 |
| **兜底层** | 高风险或低置信度处理 | 人工 / 更强模型 |

**核心观点**：Jev 不是"更便宜的 GPT"，它是 Agent 的**反射神经**。
Agent 里很多模型调用不是为了生成答案，而是为了替代码做一次判断。
把这些高频、封闭、可回退的判断从生成链路里拆出来，系统就变成"生成负责表达，判断负责分流，代码负责执行"。

---

## 🧹 上下文压缩（fast-jev-compaction 风格）

> 这是腾讯文章里最有工程参考价值的案例：不做"大模型总结历史"，而是用 Jev 对每个工具调用做窄判断。

### 为什么不用传统 summary？

传统 summary（让大模型把旧历史改写成一段短文本）有三个问题：

1. **生成成本和判断需求不匹配** — 只想知道"这段日志还要不要留"，却要启动一次完整生成
2. **摘要会破坏可复核性** — 文件路径、错误码、栈信息被"概括"成"差不多"，对 coding agent 是灾难
3. **置信度没进代码分支** — 大模型说"我有 80% 把握"只是文本描述，不是校准过的概率

### Jev 的做法：两个 Noul，三种动作

对每个 `tool_use` + `tool_result` 配对，问两个独立问题：

```
keepCall:    这个工具调用本身还重要吗？       → Noul 概率
keepResult:  这个工具结果全文还需要保留吗？   → Noul 概率
```

两个概率组合出三种动作：

| 动作 | 条件 | 处理方式 |
| --- | --- | --- |
| `keep` | keepResult ≥ threshold | 调用和结果都完整保留 |
| `drop_result` | keepResult < threshold 且 keepCall ≥ threshold | 保留调用，截断结果 |
| `drop_call` | 两者都低 | 调用和结果一起删除 |

### 三层架构

| 层次 | 做什么 | 为什么重要 |
| --- | --- | --- |
| **对象层** | 把 `tool_use` 和 `tool_result` 按 `tool_use_id` 配成一组 | 避免留下孤立调用或孤立结果 |
| **判断层** | 为每组工具历史生成 keepCall / keepResult 两个 Noul | 把复合压缩任务拆成两个窄判断 |
| **执行层** | 根据阈值执行 keep / drop_result / drop_call | 让压缩动作可测试、可回退、可统计 |

### 关键工程约束

- **用户文本和助手文本不改写** — 里面有原始需求和硬约束，改写会变味
- **只处理工具调用和工具结果** — 它们占空间最大，也最容易过期
- **pinned 保护** — 首条消息和最近 N 条消息不参与删除
- **不发完整结果给 Jev** — 只发摘要：`"ok, 4213 chars (omitted)"` / `"error, 830 chars (omitted)"`
- **先削弱细节，再删除内容；先处理旧消息，再处理最近消息**

### 代码示例

```python
from jev import JevCompactor

# asker 可替换：真实 Jev / 本地 mock / LLM 适配器
# 模型可以替换，决策协议要稳定
compactor = JevCompactor(
    asker=your_jev_asker,
    keep_threshold=0.5,
    preserve_recent=6,
)

result = compactor.compact(messages)

print(f"压缩前: {result['chars_before']} 字符")
print(f"压缩后: {result['chars_after']} 字符")
print(f"压缩率: {result['compression_ratio']:.1%}")

for d in result['decisions']:
    print(f"{d.call_id} {d.tool_name} → {d.action} "
          f"(keepCall={d.keep_call:.2f}, keepResult={d.keep_result:.2f})")
```

跑 Demo：

```bash
python examples/context_compaction.py
```

### 概率阈值建议（谨慎使用）

| 概率区间 | 系统动作 | 说明 |
| --- | --- | --- |
| ≥ 0.8 | 自动执行 | 适合低风险、高重复场景 |
| 0.5 ~ 0.8 | 保守处理 | 截断、保留摘要、请求补充信息 |
| < 0.5 | 删除或回退 | 低价值内容可清理，高风险场景转人工 |

> ⚠️ 概率不是安全证明。上线前先 shadow mode 跑一段时间，用自己的业务样本统计不同概率段的真实正确率，再定阈值。

---

## 🚀 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/cyberspace-cs/jev-agent-routing.git
cd jev-agent-routing

# 安装依赖
pip install fastapi uvicorn requests
```

### 2. 拿 API Key

1. 去 https://console.typesafe.ai 注册
2. 拿到 API Key（新用户送 $5）
3. 设置环境变量：

```bash
# Windows
set JEV_API_KEY=sk-xxx

# Linux / Mac
export JEV_API_KEY=sk-xxx
```

### 3. 跑 Web Demo（推荐新手）

```bash
cd webapp
uvicorn server:app --reload --port 8000
```

打开浏览器访问 http://localhost:8000，你会看到：
- 🎯 **Choice 选择** — 从选项中选一个，看概率分布
- 📊 **Score 打分** — 风险等级、评分
- ⚖️ **Noul 判断** — 是/否判断，返回概率
- 💬 **微信润色** — 发消息前先检查合不合适

### 4. 跑命令行 Demo

```bash
python examples/quickstart.py
```

---

## 📖 代码示例

### 工具路由

```python
from jev import JevClient, FastSlowAgentRouter, Tool

jev = JevClient()
router = FastSlowAgentRouter(jev)

# 注册工具
router.register_tool(Tool("查机票", "查询航班"))
router.register_tool(Tool("查酒店", "查询酒店"))
router.register_tool(Tool("查天气", "查天气"))

# 自动路由
decision = router.route("帮我查杭州今天天气")
print(decision.tool_name)  # "查天气"
print(decision.via)  # "jev"（快速决策，没走 LLM）
```

### 模型路由（省钱）

```python
from jev import ModelRouter

router = ModelRouter(jev)

# 简单问题 → 便宜小模型
model = router.pick_model("写个 hello world")
print(model)  # "qwen-7b"（便宜）

# 复杂问题 → 贵模型
model = router.pick_model("设计分布式微服务架构")
print(model)  # "gpt-4o"（贵但强）
```

### 风险审核

```python
# 判断要不要人工审核
result = jev.noul(
    context="用户要删除生产数据库",
    question="这个操作需要人工确认吗？",
    threshold=0.8
)
if result.passed:
    send_to_human_review()
else:
    execute_directly()
```

---

## 📊 性能对比

| 指标 | 纯 LLM | Jev + LLM 混合 | 提升 |
| --- | --- | --- | --- |
| 工具选择延迟 | 2000ms | ~100ms | **快 20 倍** |
| 单次工具选择成本 | $0.001 | $0.00002 | **便宜 50 倍** |
| 10 步任务总成本 | $0.05 | $0.005 | **便宜 10 倍** |
| 简单决策准确率 | 95% | 94% | 差不多 |

---

## 🎯 适用场景

| 场景 | 用 Jev 做什么 |
| --- | --- |
| **Agent 工具路由** | 从几十个工具里选该用哪个 |
| **模型路由** | 简单问题给小模型，复杂给大模型 |
| **风险审核** | 判断操作要不要人工确认 |
| **内容审核** | 打风险等级分 |
| **意图识别** | 用户输入分类到哪个意图 |
| **浏览器操作** | 从 100 个元素里选点哪个（jev-ultrafast） |

---

## 📁 项目结构

```
jev-agent-routing/
├── jev/
│   ├── __init__.py      # 导出
│   ├── client.py        # Jev API 客户端（choice/noul/score）
│   ├── router.py        # 快慢双层路由 + 模型路由
│   ├── agent.py         # 完整 DIY Agent 实现
│   └── compaction.py    # 上下文压缩（fast-jev-compaction 风格）
├── examples/
│   ├── quickstart.py         # 快速开始 Demo
│   ├── wechat_polish_bot.py  # 微信润色助手
│   └── context_compaction.py # 上下文压缩 Demo
├── webapp/
│   ├── server.py       # FastAPI 后端
│   └── index.html      # 前端界面
├── docs/
│   └── (后续补充)
└── README.md
```

---

## 📚 参考

- **Jev 官网**：https://console.typesafe.ai
- **Jev 官方文档**：https://docs.typesafe.ai
- **腾讯技术工程：一万字 Jev 工程实践长文**：https://mp.weixin.qq.com/s/D1La4jMoVZ5Ip_RrVY1kPw
- **fast-jev-compaction**（上下文压缩）：Claude Code 插件 / npm 库
- **jev-ultrafast**（浏览器 Agent）：https://github.com/browser-use/jev-ultrafast
- **kev**（0.5B 本地复现）：https://github.com/jaredpalmer/kev
- **Minecraft Agent**（Jev + GPT 打末影龙）：https://github.com/rmalde/minecraft-agent

---

## 📝 License

MIT
