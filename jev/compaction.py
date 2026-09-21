"""
Jev Context Compaction — 上下文压缩
======================================
参考腾讯技术工程《一万字 Jev 工程实践》和 fast-jev-compaction 的思路：

不做"大模型总结历史"，而是用 Jev 对每个工具调用做窄判断：
  - keepCall: 这个工具调用本身还重要吗？
  - keepResult: 这个工具结果全文还需要保留吗？

三种动作：
  - keep:        完整保留调用和结果
  - drop_result: 只保留调用，截断结果
  - drop_call:   调用和结果一起删除

核心原则：
  - 用户文本和助手文本不改写（保留原始事实）
  - 只处理 tool_use / tool_result 配对
  - 首条消息和最近 N 条 pinned 保护，不参与删除
  - 先削弱细节，再删除内容；先处理旧消息，再处理最近消息
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
import json


# ============ 数据结构 ============

@dataclass
class ToolCall:
    """配对后的工具调用对象"""
    id: str                # 内部短 ID，如 t1, t2
    tool_use_id: str       # 原始 tool_use id
    tool_name: str         # 工具名
    tool_input: dict      # 工具输入
    call_index: int       # 调用所在消息位置
    result_index: int     # 结果所在消息位置
    result_chars: int      # 结果字符数
    is_error: bool         # 是否失败
    pinned: bool = False # 是否固定保留


@dataclass
class CompactDecision:
    """压缩决策结果"""
    call_id: str
    tool_name: str
    action: str            # keep / drop_result / drop_call
    reason: str
    keep_call: float       # keepCall 概率
    keep_result: float     # keepResult 概率


# ============ 主类 ============

class JevCompactor:
    """
    上下文压缩器 — 用 Jev 判断工具历史保留价值
    
    用法：
        compactor = JevCompactor(jev_client)
        
        # messages 是标准 OpenAI / Claude 消息列表
        result = compactor.compact(messages, keep_threshold=0.5)
        
        print(f"压缩前: {result['chars_before']} 字符")
        print(f"压缩后: {result['chars_after']} 字符")
        print(f"压缩率: {result['compression_ratio']:.1%}")
    """
    
    DEFAULT_KEEP_THRESHOLD = 0.5
    DEFAULT_PRESERVE_RECENT = 6
    DEFAULT_MAX_STATE_TOKENS = 25000
    
    def __init__(
        self,
        asker: Callable,  # Jev 调用函数，传入 questions dict，返回 answers dict
        keep_threshold: float = DEFAULT_KEEP_THRESHOLD,
        preserve_recent: int = DEFAULT_PRESERVE_RECENT,
        max_state_tokens: int = DEFAULT_MAX_STATE_TOKENS,
    ):
        self.asker = asker  # 可替换：真实 Jev / 本地 mock / LLM 适配器
        self.keep_threshold = keep_threshold
        self.preserve_recent = preserve_recent
        self.max_state_tokens = max_state_tokens
    
    # ---- 第 1 步：收集并配对工具调用 ----
    
    def collect_tool_calls(self, messages: List[dict]) -> List[ToolCall]:
        """
        从消息列表中收集 tool_use 和 tool_result，并按 tool_use_id 配对
        
        pinned 规则：
          - 第 0 条消息（首条）
          - 最近 preserve_recent 条消息
        """
        calls: List[ToolCall] = []
        by_tool_use_id: Dict[str, ToolCall] = {}
        total = len(messages)
        
        def is_pinned(index: int) -> bool:
            return index == 0 or index >= total - self.preserve_recent
        
        for msg_idx, message in enumerate(messages):
            content = message.get("content", [])
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            
            for item in content:
                # tool_use
                if item.get("type") == "tool_use":
                    call = ToolCall(
                        id=f"t{len(calls) + 1}",
                        tool_use_id=item.get("id", ""),
                        tool_name=item.get("name", "unknown"),
                        tool_input=item.get("input", {}),
                        call_index=msg_idx,
                        result_index=-1,
                        result_chars=0,
                        is_error=False,
                        pinned=is_pinned(msg_idx),
                    )
                    calls.append(call)
                    by_tool_use_id[call.tool_use_id] = call
                
                # tool_result
                elif item.get("type") == "tool_result":
                    tool_use_id = item.get("tool_use_id", "")
                    if tool_use_id in by_tool_use_id:
                        call = by_tool_use_id[tool_use_id]
                        call.result_index = msg_idx
                        result_content = item.get("content", "")
                        if isinstance(result_content, list):
                            result_content = json.dumps(result_content, ensure_ascii=False)
                        call.result_chars = len(str(result_content))
                        call.is_error = item.get("is_error", False)
        
        return calls
    
    # ---- 第 2 步：构造判断用 state（不发完整结果）----
    
    def build_state(self, messages: List[dict], calls: List[ToolCall]) -> dict:
        """
        构造给 Jev 看的 state。
        
        关键：不把完整工具结果发给 Jev，只发短摘要：
          - "ok, 4213 chars (omitted)"
          - "error, 830 chars (omitted)"
        """
        entries = []
        
        for call in calls:
            # 结果摘要（不发全文）
            if call.is_error:
                note = f"error, {call.result_chars} chars (omitted)"
            else:
                note = f"ok, {call.result_chars} chars (omitted)"
            
            # 工具输入截断
            input_str = json.dumps(call.tool_input, ensure_ascii=False)
            if len(input_str) > 200:
                input_str = input_str[:200] + "..."
            
            entries.append({
                "id": call.id,
                "tool": call.tool_name,
                "input": input_str,
                "result": note,
                "is_error": call.is_error,
                "pinned": call.pinned,
            })
        
        return {
            "goal": self._extract_goal(messages),
            "history_entries": entries,
        }
    
    def _extract_goal(self, messages: List[dict]) -> str:
        """从首条用户消息提取目标"""
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, list):
                    content = " ".join(
                        c.get("text", "") for c in content if isinstance(c, dict)
                    )
                text = str(content).strip()
                if text:
                    return text[:500]
        return ""
    
    # ---- 第 3 步：构造问题（两个 Noul）----
    
    def questions_for(self, call: ToolCall) -> Dict[str, dict]:
        """
        对每个工具调用问两个独立的 Noul 问题。
        
        原则：一个问题只做一个判断，不要混合。
        """
        input_str = json.dumps(call.tool_input, ensure_ascii=False)
        if len(input_str) > 200:
            input_str = input_str[:200] + "..."
        
        result_note = (
            f"error, {call.result_chars} chars"
            if call.is_error
            else f"ok, {call.result_chars} chars"
        )
        summary = f"{call.tool_name} input={input_str} result={result_note}"
        
        return {
            f"call_{call.id}": {
                "type": "noul",
                "question": (
                    f"Does knowing that this tool call was made, "
                    f"with its inputs, still matter for the rest of the task?\n"
                    f"Tool call: {summary}"
                ),
            },
            f"result_{call.id}": {
                "type": "noul",
                "question": (
                    f"Does the full content of this tool result still need to be kept, "
                    f"or can it be dropped/truncated?\n"
                    f"Tool call: {summary}"
                ),
            },
        }
    
    # ---- 第 4 步：决策 ----
    
    def decide(self, call: ToolCall, answers: dict) -> CompactDecision:
        """
        根据 keepCall / keepResult 概率决定动作：
        
          - keep:        keepResult >= threshold → 完整保留
          - drop_result: keepResult < threshold 且 keepCall >= threshold → 保留调用，截断结果
          - drop_call:   两者都低 → 都删除
        """
        if call.pinned:
            return CompactDecision(
                call_id=call.id,
                tool_name=call.tool_name,
                action="keep",
                reason="pinned",
                keep_call=1.0,
                keep_result=1.0,
            )
        
        keep_call = answers.get(f"call_{call.id}", {}).get("noul", 0)
        keep_result = answers.get(f"result_{call.id}", {}).get("noul", 0)
        
        if keep_result >= self.keep_threshold:
            action = "keep"
            reason = "kept"
        elif keep_call >= self.keep_threshold:
            action = "drop_result"
            reason = "call_kept_result_dropped"
        else:
            action = "drop_call"
            reason = "both_low"
        
        return CompactDecision(
            call_id=call.id,
            tool_name=call.tool_name,
            action=action,
            reason=reason,
            keep_call=keep_call,
            keep_result=keep_result,
        )
    
    # ---- 主流程 ----
    
    def compact(self, messages: List[dict]) -> dict:
        """
        主流程：压缩上下文
        
        Returns:
            {
                "decisions": [CompactDecision, ...],
                "chars_before": int,
                "chars_after": int,
                "compression_ratio": float,
                "kept_count": int,
                "dropped_result_count": int,
                "dropped_call_count": int,
            }
        """
        # 1. 收集配对
        calls = self.collect_tool_calls(messages)
        candidates = [c for c in calls if not c.pinned]
        
        # 2. 计算原始字符数
        chars_before = sum(
            len(json.dumps(m, ensure_ascii=False)) for m in messages
        )
        
        # 3. 构造 state
        state = self.build_state(messages, calls)
        
        # 4. 构造所有问题（批量并行）
        all_questions = {}
        for call in candidates:
            all_questions.update(self.questions_for(call))
        
        # 5. 调用 asker（真实 Jev 或 mock）
        answers = self.asker(state, all_questions) if all_questions else {}
        
        # 6. 逐个决策
        decisions = []
        for call in calls:
            decision = self.decide(call, answers)
            decisions.append(decision)
        
        # 7. 统计
        kept = sum(1 for d in decisions if d.action == "keep")
        dropped_result = sum(1 for d in decisions if d.action == "drop_result")
        dropped_call = sum(1 for d in decisions if d.action == "drop_call")
        
        # 估算压缩后字符数
        chars_after = self._estimate_chars_after(messages, calls, decisions)
        
        return {
            "decisions": decisions,
            "chars_before": chars_before,
            "chars_after": chars_after,
            "compression_ratio": 1 - chars_after / max(chars_before, 1),
            "kept_count": kept,
            "dropped_result_count": dropped_result,
            "dropped_call_count": dropped_call,
            "state_used": state,
        }
    
    def _estimate_chars_after(
        self,
        messages: List[dict],
        calls: List[ToolCall],
        decisions: List[CompactDecision],
    ) -> int:
        """估算压缩后字符数（简化版：删除的调用/结果按 0 计，截断的按 10% 计）"""
        decision_map = {d.call_id: d for d in decisions}
        total = 0
        
        for call in calls:
            d = decision_map.get(call.id)
            if not d:
                continue
            if d.action == "keep":
                total += call.result_chars
            elif d.action == "drop_result":
                total += max(call.result_chars * 0.1, 200)
            # drop_call: 0
        
        # 加上非工具消息的字符（用户/助手文本不改写）
        for msg in messages:
            if msg.get("role") in ("user", "assistant"):
                content = msg.get("content", "")
                if isinstance(content, str):
                    total += len(content)
        
        return int(total)


# ============ 示例 asker（本地 mock，离线测试用）============

def heuristic_asker(state: dict, questions: dict) -> dict:
    """
    本地启发式 asker（离线演示用）。
    真实环境请替换为 Jev API 调用。
    
    规则：
      - error 结果 → keepResult 高（重要证据）
      - 长结果 → keepResult 低（容易过期）
      - list_dir 类调用 → keepCall 中等，keepResult 低
      - read_file/execute_command 失败 → keepResult 高
    """
    answers = {}
    for key, q in questions.items():
        text = q.get("question", "").lower()
        
        if "still matter" in text or "still need" in text:
            # keepCall / keepResult 判断
            if "error" in text:
                val = 0.85
            elif "list_dir" in text or "listdir" in text:
                val = 0.3
            elif "read_file" in text or "readfile" in text:
                val = 0.6
            elif "execute_command" in text:
                val = 0.7
            else:
                val = 0.5
            
            # 结果类问题，长结果降低保留概率
            if "full content" in text:
                if "4213" in text or "long" in text:
                    val *= 0.4
                if "error" in text:
                    val = max(val, 0.8)
            
            answers[key] = {"noul": val}
    
    return answers


def real_jev_asker(jev_client, base_url: str = "https://api.typesafe.ai/v1"):
    """
    真实 Jev API asker 工厂。
    
    用法：
        asker = real_jev_asker(jev_client)
        compactor = JevCompactor(asker=asker)
    """
    import requests
    
    def asker(state: dict, questions: dict) -> dict:
        # 批量调用：一个 state，多个问题
        payload = {
            "state": state,
            "questions": questions,
        }
        resp = jev_client._post("/decisions/batch", payload)
        return resp.get("answers", {})
    
    return asker
