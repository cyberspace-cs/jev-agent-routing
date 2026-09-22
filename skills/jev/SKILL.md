---
name: jev
description: Jev 快速决策模型调用技能。用于需要快速分类、判断、路由、评分的场景，比如工单分类、消息紧急度判断、内容审核、邮件优先级、Agent 决策中间层。当用户需要做结构化决策、批量分类、快速判断时使用。
license: MIT
---

# Jev 快速决策模型

Jev 是 TypeSafe AI 推出的 System One 快速决策模型，不说人话，只输出结构化决策结果。

## 核心特点

- **速度快**：比传统 LLM 快 20-200 倍
- **成本低**：比传统 LLM 便宜 40-400 倍，输出 token 免费
- **零错误**：结构化输出错误率 0%（数学保证）
- **可校准**：概率是校准过的，说 90% 就是真的 90% 准

## 三种 AI 原语

### 1. Noul（判断题）

问"是不是"，返回 0-1 概率值。

```python
from typesafe_sdk import Noul, TypeSafeClient

client = TypeSafeClient()
response = client.system_one(
    state="用户说：我连续3天无法连接Stripe，正在丢失销售额",
    questions={
        "is_urgent": Noul(
            instructions="这条消息是否传达了紧急性或时效性"
        )
    }
)
print(response.answers["is_urgent"].noul)  # 0.95
```

### 2. Choice（选择题）

问"选哪个"，返回选项概率分布。

```python
from typesafe_sdk import Choice, TypeSafeClient

client = TypeSafeClient()
response = client.system_one(
    state="用户说：我被重复扣款了，请退款",
    questions={
        "department": Choice(
            instructions="这个工单应该分配给哪个团队",
            criteria={
                "billing": "付款、发票、退款相关",
                "technical": "Bug、系统故障、集成问题",
                "sales": "定价、账户咨询"
            }
        )
    }
)
print(response.answers["department"].choice)  # "billing"
print(response.answers["department"].confidence)  # 0.87
```

### 3. Score（打分题）

问"打几分"，返回自定义量表评分。

```python
from typesafe_sdk import Score, TypeSafeClient

client = TypeSafeClient()
response = client.system_one(
    state="用户说：我等了两个小时了，再也不用你们的产品了！",
    questions={
        "frustration": Score(
            instructions="客户看起来有多沮丧",
            criteria=[
                "冷静，只是在陈述事实",
                "不满但还算礼貌",
                "非常愤怒，言辞激烈"
            ]
        )
    }
)
print(response.answers["frustration"].score)  # 1.04
```

## 使用场景

- ✅ 工单分类、消息路由
- ✅ 内容审核、风控判断
- ✅ 邮件优先级判断
- ✅ Agent 决策中间层（先 Jev 快速判断，再 LLM 深度处理）
- ✅ 批量打标签、分类
- ❌ 不适合：生成文字、算术推理、日期比较

## API 配置

- Base URL：`https://api.typesafe.ai/v1`
- 环境变量：`TYPESAFE_API_KEY`
- 控制台：https://console.typesafe.ai/

## 实战案例

- 批量分类 1000 封邮件：15.6 秒，$0.0177
- 浏览器自动化 Agent：7.1 秒完成一次航班搜索，$0.0039
- 玩数字华容道：实时决策，速度超过人类

## 项目仓库

https://github.com/cyberspace-cs/jev-agent-routing
