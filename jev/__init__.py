"""
Jev Agent Routing — DIY 决策层
=================================
快速决策 + LLM 兜底的快慢双层架构

模块：
- client:     Jev API 客户端（choice/noul/score 三种模式）
- router:     快慢双层 Agent 路由器 + 模型路由器
- agent:      完整 DIY Agent 实现
- compaction: 上下文压缩（fast-jev-compaction 风格）
"""

from .client import JevClient, ChoiceResult, NoulResult, ScoreResult
from .router import FastSlowAgentRouter, ModelRouter, Tool, RouteDecision
from .agent import DIYAgent, AgentResponse
from .compaction import JevCompactor, ToolCall, CompactDecision

__version__ = "0.2.0"
__all__ = [
    "JevClient",
    "ChoiceResult",
    "NoulResult",
    "ScoreResult",
    "FastSlowAgentRouter",
    "ModelRouter",
    "Tool",
    "RouteDecision",
    "DIYAgent",
    "AgentResponse",
    "JevCompactor",
    "ToolCall",
    "CompactDecision",
]
