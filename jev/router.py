"""
Agent 快慢路由层 — Jev 决策 + LLM 兜底
=========================================
架构：
    用户输入
       ↓
    Jev 快决策（90% 简单问题在这里搞定）
       ↓ 不确定/复杂问题
    LLM 慢推理（10% 兜底）

效果：快 10 倍，便宜 10 倍
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .client import JevClient, ChoiceResult, NoulResult


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    handler: Callable = None  # 实际执行函数


@dataclass
class RouteDecision:
    """路由决策结果"""
    tool_name: str
    confidence: float
    needs_human_review: bool
    risk_level: str
    via: str  # "jev" or "llm"


class FastSlowAgentRouter:
    """
    快慢双层 Agent 路由器
    
    三层决策：
    1. 工具选择（Jev choice）— 该用哪个工具
    2. 风险判断（Jev noul）— 要不要人工审核
    3. 风险等级（Jev score）— 高/中/低风险
    
    只有 Jev 不确定时，才 fallback 到 LLM。
    
    用法：
        router = FastSlowAgentRouter(jev_client, llm_fallback_func)
        
        # 注册工具
        router.register_tool(Tool("查机票", "查询航班机票", flight_handler))
        router.register_tool(Tool("查酒店", "查询酒店预订", hotel_handler))
        
        # 路由
        decision = router.route("帮我查明天北京到上海的机票")
        print(decision.tool_name)  # "查机票"
    """
    
    def __init__(
        self,
        jev_client: JevClient,
        llm_fallback: Optional[Callable] = None,
        confidence_threshold: float = 0.8,
    ):
        self.jev = jev_client
        self.llm_fallback = llm_fallback
        self.confidence_threshold = confidence_threshold
        self.tools: Dict[str, Tool] = {}
    
    def register_tool(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool
    
    def route(self, user_input: str) -> RouteDecision:
        """
        完整路由流程：
        1. Jev 选工具
        2. Jev 判断要不要审核
        3. Jev 打风险等级
        4. 任何一步不确定 → fallback LLM
        """
        
        # 第一步：选工具
        tool_result = self._select_tool(user_input)
        via = "jev"
        
        # 置信度不够，走 LLM
        if tool_result.max_confidence < self.confidence_threshold:
            if self.llm_fallback:
                tool_name = self.llm_fallback(user_input, list(self.tools.keys()))
                via = "llm"
            else:
                tool_name = tool_result.best_tool
        else:
            tool_name = tool_result.best_tool
        
        # 第二步：判断要不要人工审核
        review_result = self.jev.noul(
            context=f"用户输入：{user_input}\n选中工具：{tool_name}",
            question="这个操作有风险吗？需要人工审核吗？",
            threshold=0.7,
        )
        needs_review = review_result.passed
        
        # 第三步：风险等级打分
        risk_result = self.jev.score(
            context=f"用户输入：{user_input}\n操作：{tool_name}",
            question="这个操作的风险等级？",
            scale=["low", "medium", "high", "critical"],
        )
        
        return RouteDecision(
            tool_name=tool_name,
            confidence=tool_result.max_confidence,
            needs_human_review=needs_review,
            risk_level=risk_result.level,
            via=via,
        )
    
    def _select_tool(self, user_input: str) -> "_ToolSelection":
        """用 Jev 选工具"""
        tool_names = list(self.tools.keys())
        tool_descs = [f"{t.name}: {t.description}" for t in self.tools.values()]
        
        result = self.jev.choice(
            context=f"用户说：{user_input}",
            question="应该用哪个工具来处理？",
            options=tool_descs,
        )
        
        # 从概率分布找最大置信度
        probs = result.probabilities
        best_desc = result.choice
        max_conf = probs.get(best_desc, 0.9)  # 默认高置信
        
        # 从 description 提取 tool name
        best_tool_name = best_desc.split(":")[0].strip()
        if best_tool_name not in self.tools:
            best_tool_name = tool_names[0]
        
        return _ToolSelection(
            best_tool=best_tool_name,
            max_confidence=max_conf,
        )


@dataclass
class _ToolSelection:
    best_tool: str
    max_confidence: float


class ModelRouter:
    """
    模型路由器 — Jev 决定用便宜模型还是贵模型
    
    简单问题 → 小模型（便宜）
    复杂问题 → 大模型（贵）
    
    示例：
        router = ModelRouter(jev)
        model = router.pick_model("写个 hello world")
        print(model)  # "qwen-7b"（便宜）
        
        model = router.pick_model("设计一个分布式微服务架构")
        print(model)  # "gpt-4o"（贵）
    """
    
    def __init__(self, jev_client: JevClient):
        self.jev = jev_client
    
    def pick_model(self, user_query: str) -> str:
        """根据问题复杂度选模型"""
        result = self.jev.choice(
            context=f"用户问题：{user_query}",
            question="这个问题需要哪个级别的模型来处理？",
            options=[
                "simple: 简单问题，用便宜小模型就行",
                "medium: 中等复杂度，用中等模型",
                "complex: 复杂推理/代码/架构，用大模型",
            ],
        )
        
        choice = result.choice.lower()
        if "simple" in choice:
            return "qwen-7b"
        elif "medium" in choice:
            return "qwen-72b"
        else:
            return "gpt-4o"
    
    def should_human_review(self, tool_name: str, input_data: str) -> bool:
        """判断工具调用要不要人工确认"""
        result = self.jev.noul(
            context=f"工具：{tool_name}\n输入：{input_data}",
            question="这个工具调用有风险吗？需要人工确认吗？",
            threshold=0.8,
        )
        return result.passed
