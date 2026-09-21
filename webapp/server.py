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
from fastapi.staticfiles import StaticFiles

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
def call_jev(payload: dict) -> dict:
    """调用 Jev API"""
    if not JEV_API_KEY:
        raise HTTPException(status_code=400, detail="请先设置 JEV_API_KEY 环境变量")
    
    headers = {
        "Authorization": f"Bearer {JEV_API_KEY}",
        "Content-Type": "application/json",
    }
    
    try:
        resp = requests.post(
            f"{JEV_BASE_URL}/decisions",
            json=payload,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=resp.status_code, detail=f"Jev API 错误: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"请求失败: {e}")


# ============ API 路由 ============

@app.post("/api/choice")
def choice(req: ChoiceRequest):
    """Choice 模式：从选项中选一个"""
    payload = {
        "type": "choice",
        "state": req.state,
        "question": req.question,
        "options": req.options,
    }
    return call_jev(payload)


@app.post("/api/score")
def score(req: ScoreRequest):
    """Score 模式：打分"""
    payload = {
        "type": "score",
        "state": req.state,
        "question": req.question,
        "scale": req.scale,
    }
    return call_jev(payload)


@app.post("/api/noul")
def noul(req: NoulRequest):
    """Noul 模式：是/否判断"""
    payload = {
        "type": "noul",
        "state": req.state,
        "question": req.question,
    }
    result = call_jev(payload)
    result["passed"] = result.get("noul", 0) >= req.threshold
    result["threshold"] = req.threshold
    return result


@app.post("/api/wechat-polish")
def wechat_polish(req: WechatPolishRequest):
    """微信润色：检查消息合不合适"""
    state = f"接收人：{req.recipient}\n消息内容：{req.message}"
    
    # 并行问三个问题
    results = {}
    
    # 1. 语气冲不冲
    r1 = call_jev({
        "type": "noul",
        "state": state,
        "question": "这句话语气冲吗？会不会让对方不舒服？",
    })
    results["too_rude"] = r1.get("noul", 0)
    
    # 2. 风险等级
    r2 = call_jev({
        "type": "score",
        "state": state,
        "question": "这条消息发出去的社死风险等级？",
        "scale": ["safe", "slightly_risky", "risky", "very_risky"],
    })
    results["risk_level"] = r2.get("level", "safe")
    results["risk_score"] = r2.get("score", 0)
    
    # 3. 合适程度
    r3 = call_jev({
        "type": "choice",
        "state": state,
        "question": "这条消息在这个场景下合适吗？",
        "options": [
            "perfect: 非常合适，直接发",
            "ok: 还行，可以发",
            "needs_polish: 需要润色一下",
            "dont_send: 千万别发",
        ],
    })
    results["appropriateness"] = r3.get("choice", "ok")
    results["should_send"] = "dont_send" not in results["appropriateness"]
    
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


# 静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
