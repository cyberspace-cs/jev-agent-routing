"""
Jev Web Demo — 后端 API
=========================
FastAPI 后端，调用 Jev API，提供三种决策模式：
- Choice: 从选项中选一个
- Score: 打分
- Noul: 是/否判断
"""

import os
import random
from typing import List, Optional
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

class UTF8JSONResponse(JSONResponse):
    """确保 JSON 响应使用 UTF-8 编码"""
    media_type = "application/json; charset=utf-8"

app = FastAPI(title="Jev Demo", version="0.1.0", default_response_class=UTF8JSONResponse)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ 配置 ============
TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY", "")
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
    role: str = "friend"  # boss/colleague/girlfriend/boyfriend/bestie/bro
    their_last_message: str = ""  # 对方上一句话
    conversation_history: list = []  # 完整对话历史


# ============ Mock 数据 ============
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


# ============ API 调用 ============
def call_jev(state, questions: dict) -> dict:
    """调用 Jev API（无 Key 时走 mock）"""
    if not TYPESAFE_API_KEY:
        return mock_jev_multi(questions)

    try:
        from typesafe_sdk import Choice, Noul, Score, TypeSafeClient
        client = TypeSafeClient()

        sdk_questions = {}
        for q_name, q_config in questions.items():
            q_type = q_config.get("type", "noul")
            instructions = q_config.get("instructions", "")
            criteria = q_config.get("criteria", {})

            if q_type == "choice":
                sdk_questions[q_name] = Choice(instructions=instructions, criteria=criteria)
            elif q_type == "score":
                sdk_questions[q_name] = Score(instructions=instructions, criteria=criteria)
            elif q_type == "noul":
                sdk_questions[q_name] = Noul(instructions=instructions)

        resp = client.system_one(state=state, questions=sdk_questions)

        results = {}
        for q_name in questions.keys():
            ans = resp.answers[q_name]
            q_type = questions[q_name].get("type", "noul")
            if q_type == "choice":
                results[q_name] = {
                    "type": "choice",
                    "choice": ans.choice,
                    "confidence": ans.confidence,
                    "probabilities": ans.probabilities
                }
            elif q_type == "score":
                results[q_name] = {
                    "type": "score",
                    "score": ans.score,
                    "confidence": ans.confidence,
                    "probabilities": ans.probabilities
                }
            elif q_type == "noul":
                results[q_name] = {
                    "type": "noul",
                    "noul": ans.noul
                }
        return results

    except Exception as e:
        print(f"Jev API error: {e}")
        return mock_jev_multi(questions)


# ============ API 路由 ============

@app.post("/api/choice")
def choice(req: ChoiceRequest):
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
    questions = {
        "result": {
            "type": "noul",
            "instructions": req.question,
        }
    }
    answers = call_jev(req.state, questions)
    result = answers.get("result", {})
    result["passed"] = result.get("noul", 0) >= req.threshold
    result["threshold"] = req.threshold
    return result


@app.post("/api/wechat-polish")
def wechat_polish(req: WechatPolishRequest):
    # 关系映射
    role_relations = {
        "boss": "老板-下属",
        "colleague": "同事-同事",
        "girlfriend": "情侣-女友",
        "boyfriend": "情侣-男友",
        "bestie": "闺蜜-闺蜜",
        "bro": "兄弟-兄弟",
        "friend": "朋友-朋友"
    }
    relation = role_relations.get(req.role, "朋友-朋友")

    # 构建对话上下文
    me_said = req.conversation_history[-5:] if req.conversation_history else []
    they_said = [req.their_last_message] if req.their_last_message else []

    state = {
        "dialogue": {
            "me_said": me_said,
            "they_said": they_said,
            "their_latest": req.their_last_message,
            "relation": relation,
            "my_reply": req.message
        }
    }

    # 根据不同角色调整分析维度
    role_specific_questions = {
        "boss": {
            "professionalism": {
                "type": "score",
                "instructions": "这句话在老板看来够不够专业？会不会显得不成熟？",
                "criteria": ["很不专业", "不太专业", "还行", "很专业"]
            },
            "too_aggressive": {
                "type": "noul",
                "instructions": "这句话会不会显得我在顶嘴或甩锅？"
            }
        },
        "girlfriend": {
            "emotion_understanding": {
                "type": "score",
                "instructions": "这句话有没有接住她的情绪？会不会显得很敷衍？",
                "criteria": ["完全没接住", "有点敷衍", "还行", "很懂她"]
            },
            "too_cold": {
                "type": "noul",
                "instructions": "这句话会不会显得太冷淡了？"
            }
        },
        "bestie": {
            "enough_gossip": {
                "type": "noul",
                "instructions": "这句话够不够闺蜜感？会不会太正经了？"
            }
        },
        "bro": {
            "too_serious": {
                "type": "noul",
                "instructions": "这句话会不会太正经了？兄弟之间应该更随意一点。"
            }
        }
    }

    # 基础问题（所有角色通用）
    questions = {
        "too_rude": {
            "type": "noul",
            "instructions": "这句话语气冲吗？会不会让对方不舒服？",
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
            "instructions": "结合对话上下文，这条消息在这个场景下合适吗？",
            "criteria": {
                "perfect": "非常合适，直接发",
                "ok": "还行，可以发",
                "needs_polish": "需要润色一下",
                "dont_send": "千万别发"
            }
        }
    }

    # 加入角色特定问题
    if req.role in role_specific_questions:
        questions.update(role_specific_questions[req.role])

    answers = call_jev(state, questions)

    results = {
        "too_rude": answers.get("too_rude", {}).get("noul", 0),
        "risk_level": "safe",
        "risk_score": answers.get("risk_score", {}).get("score", 0),
        "appropriateness": answers.get("appropriateness", {}).get("choice", "ok"),
        "should_send": "dont_send" not in answers.get("appropriateness", {}).get("choice", "ok"),
    }

    # 加入角色特定分析结果
    if req.role == "boss" and "professionalism" in answers:
        results["professionalism"] = answers["professionalism"].get("score", 0)
    if req.role == "girlfriend" and "emotion_understanding" in answers:
        results["emotion_understanding"] = answers["emotion_understanding"].get("score", 0)

    score_val = results["risk_score"]
    if score_val < 0.5:
        results["risk_level"] = "safe"
    elif score_val < 1.5:
        results["risk_level"] = "slightly_risky"
    elif score_val < 2.5:
        results["risk_level"] = "risky"
    else:
        results["risk_level"] = "very_risky"

    # 生成更灵活的反馈
    suggested_replies = {
        "boss": [
            "好的老板，我马上处理。",
            "收到，我今天下班前给您。",
            "抱歉老板，我调整一下，稍后发您。"
        ],
        "girlfriend": [
            "怎么了宝？我在呢。",
            "抱抱，别生气啦，我错了嘛。",
            "想你啦，你在干嘛呀？"
        ],
        "boyfriend": [
            "咋了？",
            "行吧，听你的。",
            "知道了。"
        ],
        "colleague": [
            "收到，我这边没问题。",
            "好的，我们对齐一下时间。",
            "抱歉，我马上改。"
        ],
        "bestie": [
            "啊啊啊怎么了！快说！",
            "我跟你说！！！",
            "真的假的？？？"
        ],
        "bro": [
            "咋了兄弟？",
            "行，上号。",
            "喝！老地方。"
        ]
    }

    if not results["should_send"]:
        results["feedback"] = f"⚠️ 千万别发！这条给{req.recipient}的消息风险太高了。"
    elif req.role == "boss":
        if results.get("professionalism", 0) < 1.5:
            results["feedback"] = "💡 这句话在老板看来不够专业，建议更正式一点。"
        elif results["too_rude"] > 0.6:
            results["feedback"] = "💡 语气有点冲，别在老板面前顶嘴。"
        else:
            results["feedback"] = "✅ 没问题，很得体。"
    elif req.role == "girlfriend":
        if results.get("emotion_understanding", 0) < 1.5:
            results["feedback"] = "💡 没接住她的情绪！先共情，再讲道理。"
        elif results["too_rude"] > 0.6:
            results["feedback"] = "💡 语气太冲了！对女友要温柔。"
        else:
            results["feedback"] = "✅ 可以，挺懂她的。"
    elif results["too_rude"] > 0.6:
        results["feedback"] = f"💡 这句话语气有点冲，建议委婉一点。"
    elif "needs_polish" in results["appropriateness"]:
        results["feedback"] = f"✨ 意思没问题，但可以润色得更自然一点。"
    else:
        results["feedback"] = f"✅ 没问题，直接发吧！"

    results["suggested_replies"] = suggested_replies.get(req.role, ["好的，收到。", "没问题。"])

    return results


# ============ 分析对方话语 ============
class AnalyzeThemRequest(BaseModel):
    their_message: str
    recipient: str = "朋友"
    role: str = "friend"
    conversation_history: list = []

@app.post("/api/analyze-them")
def analyze_them(req: AnalyzeThemRequest):
    """分析对方说的话：意图、情绪、真实想法"""
    role_relations = {
        "boss": "老板-下属",
        "colleague": "同事-同事",
        "girlfriend": "情侣-女友",
        "boyfriend": "情侣-男友",
        "bestie": "闺蜜-闺蜜",
        "bro": "兄弟-兄弟",
        "friend": "朋友-朋友"
    }
    relation = role_relations.get(req.role, "朋友-朋友")

    state = {
        "dialogue": {
            "me_said": req.conversation_history[-5:] if req.conversation_history else [],
            "they_said": [req.their_message],
            "their_latest": req.their_message,
            "relation": relation,
        }
    }

    questions = {
        "their_intent": {
            "type": "choice",
            "instructions": "对方这句话的真实意图是什么？",
            "criteria": {
                "normal_chat": "正常聊天/陈述",
                "test_water": "在试探你态度",
                "dissatisfied": "对你有点不满/生气",
                "need_help": "需要你帮忙/做事",
                "want_comfort": "需要安慰/情绪支持",
                "warning": "在警告/提醒你"
            }
        },
        "their_emotion": {
            "type": "score",
            "instructions": "对方这句话的情绪强度？",
            "criteria": ["很平静", "有点情绪", "情绪明显", "情绪很激动"]
        },
        "is_test": {
            "type": "noul",
            "instructions": "这句话是不是在考验你/给你送命题？"
        }
    }

    answers = call_jev(state, questions)

    intent_map = {
        "normal_chat": "正常聊天",
        "test_water": "在试探你态度",
        "dissatisfied": "对你有点不满",
        "need_help": "需要你帮忙",
        "want_comfort": "需要安慰",
        "warning": "在警告你"
    }

    emotion_val = answers.get("their_emotion", {}).get("score", 0)
    if emotion_val < 1.0:
        emotion_level = "很平静"
    elif emotion_val < 2.0:
        emotion_level = "有点情绪"
    elif emotion_val < 3.0:
        emotion_level = "情绪明显"
    else:
        emotion_level = "情绪很激动"

    intent_key = answers.get("their_intent", {}).get("choice", "normal_chat")

    # 生成建议
    if answers.get("is_test", {}).get("noul", 0) > 0.6:
        suggestion = "⚠️ 这是送命题！千万小心回答！"
    elif intent_key == "dissatisfied":
        suggestion = "💡 对方有点不满，先道歉再解释"
    elif intent_key == "need_help":
        suggestion = "💡 对方需要你做事，尽快回应"
    elif intent_key == "want_comfort":
        suggestion = "💡 对方需要安慰，先共情"
    elif intent_key == "warning":
        suggestion = "⚠️ 对方在警告你，别再犯同样的错"
    elif emotion_val > 2.0:
        suggestion = "💡 对方情绪激动，别硬碰硬"
    else:
        suggestion = "✅ 正常对话，正常回应就好"

    # 返回详细的概率数据
    intent_probs = answers.get("their_intent", {}).get("probabilities", {})
    # 把英文 key 翻成中文
    intent_probs_cn = {}
    for k, v in intent_probs.items():
        intent_probs_cn[intent_map.get(k, k)] = v

    # 生成建议回复
    reply_templates = {
        "boss": [
            "收到，我马上看一下，下午给您反馈。",
            "好的老板，我今天下班前给您。",
            "抱歉老板，我调整一下，稍后发您。"
        ],
        "girlfriend": [
            "怎么了宝？我在呢。",
            "抱抱，别生气啦，我错了嘛。",
            "想你啦，你在干嘛呀？"
        ],
        "boyfriend": [
            "咋了？",
            "行吧，听你的。",
            "知道了。"
        ],
        "colleague": [
            "收到，我这边没问题。",
            "好的，我们对齐一下时间。",
            "抱歉，我马上改。"
        ],
        "bestie": [
            "啊啊啊怎么了！快说！",
            "我跟你说！！！",
            "真的假的？？？"
        ],
        "bro": [
            "咋了兄弟？",
            "行，上号。",
            "喝！老地方。"
        ],
        "friend": [
            "好的，收到。",
            "没问题。",
            "行，听你的。"
        ]
    }

    suggested_replies = reply_templates.get(req.role, reply_templates["friend"])

    return {
        "intent": intent_map.get(intent_key, intent_key),
        "intent_probabilities": intent_probs_cn,
        "emotion_level": emotion_level,
        "emotion_score_percent": round(emotion_val / 3 * 100),
        "is_test": answers.get("is_test", {}).get("noul", 0),
        "is_test_percent": round(answers.get("is_test", {}).get("noul", 0) * 100),
        "suggestion": suggestion,
        "suggested_replies": suggested_replies
    }


# ============ 前端页面 ============
@app.get("/")
def index():
    return FileResponse("index.html")

@app.get("/chat.html")
def chat():
    return FileResponse("chat.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
