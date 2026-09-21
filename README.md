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
│   └── agent.py         # 完整 DIY Agent 实现
├── examples/
│   ├── quickstart.py    # 快速开始 Demo
│   └── wechat_polish_bot.py  # 微信润色助手
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
- **jev-ultrafast**（浏览器 Agent）：https://github.com/browser-use/jev-ultrafast
- **kev**（0.5B 本地复现）：https://github.com/jaredpalmer/kev
- **Minecraft Agent**（Jev + GPT 打末影龙）：https://github.com/rmalde/minecraft-agent

---

## 📝 License

MIT
