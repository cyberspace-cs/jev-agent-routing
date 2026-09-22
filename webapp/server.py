"""
Jev Web Demo — 后端 API
=========================
FastAPI 后端，调用 Jev API，提供三种决策模式：
- Choice: 从选项中选一个
- Score: 打分
- Noul: 是/否判断

运行：
    pip install fastapi uvicorn requests
    uvicorn server:app --reload --port 8000
"""

import os
from typing import List, Optional
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import requests

app = FastAPI(title="Jev Demo", version="0.1.0")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ 配置 ============
JEV_API_KEY = os.getenv("JEV_API_KEY", "")
JEV_BASE_URL = "https://api.typesafe.ai/v1"


# ============ 请求模型 ============
class ChoiceRequest(BaseModel):
    state: str
    question: str
    options: List[str]


class ScoreRequest(BaseModel):
    state: str
    question: str
    scale: List[str]


class NoulRequest(BaseModel):
    state: str
    question: str
    threshold: float = 0.5


class WechatPolishRequest(BaseModel):
    message: str
    recipient: str = "朋友"


# ============ API 调用 ============
import random

def mock_jev_multi(questions: dict) -> dict:
    """Mock Jev 响应（无 API Key 时使用），支持多问题"""
    results = {}
    for q_name, q_config in questions.items():
        q_type = q_config.get("type", "noul")
        if q_type == "noul":
            results[q_name] = {
                "type": "noul",
                "noul": random.uniform(0.1, 0.95),
                "confidence": random.uniform(0.7, 0.99)
            }
        elif q_type == "choice":
            criteria = q_config.get("criteria", {})
            opts = list(criteria.keys()) if criteria else ["option1", "option2"]
            chosen = random.choice(opts)
            probs = {o: random.uniform(0.01, 0.9) for o in opts}
            probs[chosen] = 0.7 + random.uniform(0, 0.25)
            results[q_name] = {
                "type": "choice",
                "choice": chosen,
                "confidence": probs[chosen],
                "probabilities": probs
            }
        elif q_type == "score":
            results[q_name] = {
                "type": "score",
                "score": random.uniform(0.5, 2.5),
                "confidence": random.uniform(0.7, 0.99)
            }
    return results
    """调用 Jev API（无 Key 时走 mock）"""
    if not JEV_API_KEY:
        # Mock 模式
        return mock_jev_multi(questions)

    headers = {
        "Authorization": f"Bearer {JEV_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "jev-latest",
        "state": state,
        "questions": questions,
    }

    try:
        resp = requests.post(
            f"{JEV_BASE_URL}/systemone",
            json=payload,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("answers", {})
    except Exception as e:
        # API 失败时 fallback 到 mock
        return mock_jev_multi(questions)


# ============ API 路由 ============

@app.post("/api/choice")
def choice(req: ChoiceRequest):
    """Choice 模式：从选项中选一个"""
    questions = {
        "result": {
            "type": "choice",
            "instructions": req.question,
            "criteria": {opt: opt for opt in req.options}
        }
    }
    answers = call_jev(req.state, questions)
    return answers.get("result", {})


@app.post("/api/score")
def score(req: ScoreRequest):
    """Score 模式：打分"""
    questions = {
        "result": {
            "type": "score",
            "instructions": req.question,
            "criteria": req.scale
        }
    }
    answers = call_jev(req.state, questions)
    return answers.get("result", {})


@app.post("/api/noul")
def noul(req: NoulRequest):
    """Noul 模式：是/否判断"""
    questions = {
        "result": {
            "type": "noul",
            "instructions": req.question,
            "criteria": {
                "true": "Yes, it is true",
                "false": "No, it is not true"
            }
        }
    }
    answers = call_jev(req.state, questions)
    result = answers.get("result", {})
    result["passed"] = result.get("noul", 0) >= req.threshold
    result["threshold"] = req.threshold
    return result


@app.post("/api/wechat-polish")
def wechat_polish(req: WechatPolishRequest):
    """微信润色：检查消息合不合适"""
    state = f"接收人：{req.recipient}\n消息内容：{req.message}"

    # 并行问三个问题（Jev 一次调用多个问题）
    questions = {
        "too_rude": {
            "type": "noul",
            "instructions": "这句话语气冲吗？会不会让对方不舒服？",
            "criteria": {
                "true": "语气冲，容易让对方不舒服",
                "false": "语气正常，没问题"
            }
        },
        "risk_score": {
            "type": "score",
            "instructions": "这条消息发出去的社死风险等级？",
            "criteria": [
                "safe: 完全安全",
                "slightly_risky: 有点风险",
                "risky: 风险较高",
                "very_risky: 千万别发"
            ]
        },
        "appropriateness": {
            "type": "choice",
            "instructions": "这条消息在这个场景下合适吗？",
            "criteria": {
                "perfect": "非常合适，直接发",
                "ok": "还行，可以发",
                "needs_polish": "需要润色一下",
                "dont_send": "千万别发"
            }
        }
    }

    answers = call_jev(state, questions)

    results = {
        "too_rude": answers.get("too_rude", {}).get("noul", 0),
        "risk_level": "safe",
        "risk_score": answers.get("risk_score", {}).get("score", 0),
        "appropriateness": answers.get("appropriateness", {}).get("choice", "ok"),
        "should_send": "dont_send" not in answers.get("appropriateness", {}).get("choice", "ok"),
    }

    # 根据 score 映射 risk_level
    score_val = results["risk_score"]
    if score_val < 0.5:
        results["risk_level"] = "safe"
    elif score_val < 1.5:
        results["risk_level"] = "slightly_risky"
    elif score_val < 2.5:
        results["risk_level"] = "risky"
    else:
        results["risk_level"] = "very_risky"

    # 生成建议
    if not results["should_send"]:
        results["feedback"] = f"⚠️ 千万别发！这条给{req.recipient}的消息风险太高了。"
    elif results["too_rude"] > 0.6:
        results["feedback"] = f"💡 这句话语气有点冲，建议委婉一点。"
    elif "needs_polish" in results["appropriateness"]:
        results["feedback"] = f"✨ 意思没问题，但可以润色得更得体一点。"
    else:
        results["feedback"] = f"✅ 没问题，直接发吧！"

    return results


# ============ 前端页面 ============
@app.get("/")
def index():
    return FileResponse("index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
