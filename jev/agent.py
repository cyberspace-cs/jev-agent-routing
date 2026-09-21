"""
DIY Agent — 完整快慢双层架构
=================================
System 1 (Jev 快决策) + System 2 (LLM 慢推理)

功能：
- 工具路由（Jev 选工具）
- 风险审核（Jev 判断要不要确认）
- 模型路由（Jev 选便宜还是贵模型）
- LLM 兜底（复杂问题走大模型）
"""

import os
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .client import JevClient


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    handler: Callable = None
    risk_level: str = "low"  # low/medium/high


@dataclass
class AgentResponse:
    """Agent 响应"""
    success: bool
    output: str
    via: str  # "jev_fast" / "llm_slow"
    tool_used: Optional[str] = None
    needs_confirmation: bool = False


class DIYAgent:
    """
    完整 DIY Agent — 快慢双层架构
    
    用法：
        agent = DIYAgent(
            jev_client=jev,
            llm_func=my_llm,
        )
        
        agent.register_tool(Tool("查机票", "查航班", flight_handler))
        agent.register_tool(Tool("查酒店", "订酒店", hotel_handler))
        
        response = agent.run("帮我查北京到上海的机票")
        print(response.output)
    """
    
    def __init__(
        self,
        jev_client: JevClient,
        llm_func: Optional[Callable] = None,
        confidence_threshold: float = 0.8,
    ):
        self.jev = jev_client
        self.llm = llm_func
        self.confidence_threshold = confidence_threshold
        self.tools: Dict[str, Tool] = {}
        self.conversation_history: List[dict] = []
    
    def register_tool(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool
    
    def run(self, user_input: str) -> AgentResponse:
        """
        完整 Agent 执行流程：
        1. Jev 快速判断：这是简单问题还是复杂问题？
        2. 简单问题 → Jev 选工具 → 执行
        3. 复杂问题 → 走 LLM 推理
        4. 高风险操作 → 问用户确认
        """
        
        # 第一步：Jev 判断复杂度
        complexity = self.jev.choice(
            context=f"用户问题：{user_input}",
            question="这个问题的复杂度？",
            options=[
                "simple: 简单直接，查信息/算东西/选选项",
                "medium: 需要一些推理，但不复杂",
                "complex: 复杂推理/写代码/创作/开放式问题",
            ]
        )
        
        complexity_text = complexity.choice.lower()
        
        # 简单问题 → 走快路径
        if "simple" in complexity_text or "medium" in complexity_text:
            return self._fast_path(user_input)
        
        # 复杂问题 → 走慢路径
        return self._slow_path(user_input)
    
    def _fast_path(self, user_input: str) -> AgentResponse:
        """快路径：Jev 选工具，直接执行"""
        
        # 1. Jev 选工具
        tool_names = list(self.tools.keys())
        tool_options = [f"{t.name}: {t.description}" for t in self.tools.values()]
        
        if not tool_options:
            return self._slow_path(user_input)
        
        tool_result = self.jev.choice(
            context=f"用户说：{user_input}",
            question="应该用哪个工具？",
            options=tool_options,
        )
        
        # 解析工具名
        tool_name = tool_result.choice.split(":")[0].strip()
        if tool_name not in self.tools:
            tool_name = tool_names[0]
        
        tool = self.tools[tool_name]
        
        # 2. 检查风险等级
        if tool.risk_level in ("high", "critical"):
            # 高风险，问用户确认
            confirm_result = self.jev.noul(
                context=f"用户要执行操作：{tool_name}（{tool.description}）",
                question="这个操作有风险吗？需要用户确认吗？",
                threshold=0.7,
            )
            if confirm_result.passed:
                return AgentResponse(
                    success=False,
                    output=f"⚠️ 这个操作有风险，需要你确认：是否执行 {tool_name}？",
                    via="jev_fast",
                    tool_used=tool_name,
                    needs_confirmation=True,
                )
        
        # 3. 执行工具
        try:
            if tool.handler:
                result = tool.handler(user_input)
            else:
                result = f"[模拟执行] 使用 {tool_name}：{user_input}"
            
            return AgentResponse(
                success=True,
                output=result,
                via="jev_fast",
                tool_used=tool_name,
            )
        except Exception as e:
            # 执行失败，走 LLM 兜底
            return self._slow_path(user_input, error=str(e))
    
    def _slow_path(self, user_input: str, error: str = None) -> AgentResponse:
        """慢路径：走 LLM 推理"""
        
        if not self.llm:
            return AgentResponse(
                success=False,
                output="这个问题比较复杂，需要 LLM 来处理，但没有配置 LLM 函数。",
                via="none",
            )
        
        # 构造上下文
        context = f"对话历史：{self.conversation_history[-5:]}\n"
        if error:
            context += f"之前出错了：{error}\n"
        context += f"用户问题：{user_input}"
        
        # 调用 LLM
        result = self.llm(context)
        
        # 更新对话历史
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": result})
        
        return AgentResponse(
            success=True,
            output=result,
            via="llm_slow",
        )
