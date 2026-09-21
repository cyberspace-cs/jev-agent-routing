"""
Jev Decision Client — DIY Agent 决策层
=========================================
基于 TypeSafe AI Jev API 的快速决策客户端。

三种决策模式：
1. choice   — 从候选中选一个
2. noul     — 返回事件发生的概率（0-1）
3. score    — 在有序区间打分（低/中/高，1-10分等）

官网：https://console.typesafe.ai
"""

import os
from dataclasses import dataclass
from typing import List, Literal, Optional

import requests


@dataclass
class ChoiceResult:
    """choice 模式返回结果"""
    choice: str           # 选中的选项
    choice_index: int     # 选中的索引（0-based）
    probabilities: dict   # 所有选项的概率分布


@dataclass
class NoulResult:
    """noul 模式返回结果"""
    probability: float    # 0-1 之间的概率
    threshold: float     # 你设置的阈值
    passed: bool         # 是否超过阈值


@dataclass
class ScoreResult:
    """score 模式返回结果"""
    score: float          # 分数值
    level: str            # 映射后的等级（low/medium/high 等）
    raw: dict             # 原始返回


class JevClient:
    """
    Jev 快速决策客户端
    
    用法：
        client = JevClient(api_key="...")
        
        # 1. 选择模式：工具路由
        result = client.choice(
            context="用户说：帮我查北京到上海的机票",
            question="用户想使用哪个工具？",
            options=["查机票", "查酒店", "查火车", "发消息"]
        )
        print(result.choice)  # "查机票"
        
        # 2. Noul 模式：要不要人工审核？
        result = client.noul(
            context="用户说：帮我删一下数据库里所有用户的密码",
            question="这个操作需要人工审核吗？",
            threshold=0.7
        )
        print(result.passed)  # True（概率 > 0.7）
        
        # 3. Score 模式：风险等级打分
        result = client.score(
            context="用户上传了一个文件，包含个人信息",
            question="这个内容的隐私风险等级是多少？",
            scale=["low", "medium", "high", "critical"]
        )
        print(result.level)  # "high"
    """
    
    BASE_URL = "https://api.typesafe.ai/v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 10,
    ):
        self.api_key = api_key or os.getenv("JEV_API_KEY")
        if not self.api_key:
            raise ValueError(
                "需要提供 Jev API Key。"
                "去 https://console.typesafe.ai 注册，送 $5 额度。"
                "设置环境变量 JEV_API_KEY 或直接传入。"
            )
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })
    
    def choice(
        self,
        context: str,
        question: str,
        options: List[str],
    ) -> ChoiceResult:
        """
        从候选选项中选择一个
        
        Args:
            context: 上下文信息（state）
            question: 要回答的问题
            options: 候选选项列表
        
        Returns:
            ChoiceResult 包含选中项和概率分布
        """
        payload = {
            "type": "choice",
            "context": context,
            "question": question,
            "options": options,
        }
        resp = self._post("/decisions", payload)
        return ChoiceResult(
            choice=resp["choice"],
            choice_index=options.index(resp["choice"]),
            probabilities=resp.get("probabilities", {}),
        )
    
    def noul(
        self,
        context: str,
        question: str,
        threshold: float = 0.5,
    ) -> NoulResult:
        """
        返回某件事发生的概率
        
        Args:
            context: 上下文信息
            question: 是/否 类问题
            threshold: 判定阈值，概率超过则 passed=True
        
        Returns:
            NoulResult 包含概率和是否通过阈值
        """
        payload = {
            "type": "noul",
            "context": context,
            "question": question,
        }
        resp = self._post("/decisions", payload)
        prob = resp.get("probability", 0.0)
        return NoulResult(
            probability=prob,
            threshold=threshold,
            passed=prob >= threshold,
        )
    
    def score(
        self,
        context: str,
        question: str,
        scale: List[str] = None,
    ) -> ScoreResult:
        """
        在有序区间打分
        
        Args:
            context: 上下文信息
            question: 评分问题
            scale: 有序等级列表，如 ["low", "medium", "high", "critical"]
        
        Returns:
            ScoreResult 包含分数和等级
        """
        scale = scale or ["low", "medium", "high"]
        payload = {
            "type": "score",
            "context": context,
            "question": question,
            "scale": scale,
        }
        resp = self._post("/decisions", payload)
        return ScoreResult(
            score=resp.get("score", 0.0),
            level=resp.get("level", scale[0]),
            raw=resp,
        )
    
    def multi_decision(
        self,
        context: str,
        questions: List[dict],
    ) -> List[dict]:
        """
        一次提交多个问题，并行决策
        
        适合：一次上下文，多个判断
        例如：同时判断「用哪个工具」+「要不要审核」+「风险等级」
        """
        payload = {
            "type": "batch",
            "context": context,
            "questions": questions,
        }
        resp = self._post("/decisions/batch", payload)
        return resp.get("results", [])
    
    def _post(self, path: str, payload: dict) -> dict:
        """发送请求并处理错误"""
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 401:
                raise ValueError("API Key 无效，去 https://console.typesafe.ai 重新获取")
            elif resp.status_code == 429:
                raise RuntimeError("额度用完了，去官网充值")
            else:
                raise RuntimeError(f"Jev API 错误: {e}")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("无法连接到 Jev API，检查网络")
