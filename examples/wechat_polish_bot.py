"""
微信助手 — 低情商救星（Jev 版）
=================================
用法：你想发什么话，先发给它，它帮你判断合不合适、怎么改更好。

功能：
1. 语气判断：这句话会不会让人不舒服？
2. 风险等级：发出去会不会社死？
3. 改写建议：怎么说更得体？

灵感来源：Jev + 微信 = 治好低情商
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jev import JevClient


class WechatPolishBot:
    """
    微信消息润色助手 — 低情商救星
    
    用法：
        bot = WechatPolishBot(jev)
        
        # 你想发的话
        your_draft = "你怎么又迟到了？是不是没把约会当回事？"
        
        result = bot.check_message(your_draft)
        print(result["feedback"])
        # → "这句话有点冲，建议改成：'路上顺利吗？我有点担心你'"
    """
    
    def __init__(self, jev_client: JevClient):
        self.jev = jev_client
    
    def check_message(self, message: str, recipient: str = "朋友") -> dict:
        """
        检查一条微信消息发出去合不合适
        
        Args:
            message: 你想发的消息草稿
            recipient: 接收人（朋友/老板/暗恋对象/客户）
        """
        
        # 1. 判断语气会不会冲
        rude_result = self.jev.noul(
            context=f"接收人：{recipient}\n消息内容：{message}",
            question="这句话语气冲吗？会不会让对方不舒服？",
            threshold=0.6,
        )
        
        # 2. 风险等级
        risk_result = self.jev.score(
            context=f"接收人：{recipient}\n消息内容：{message}",
            question="这条消息发出去的社死风险等级？",
            scale=["safe", "slightly_risky", "risky", "very_risky"],
        )
        
        # 3. 场景匹配度
        appropriateness = self.jev.choice(
            context=f"接收人：{recipient}\n消息：{message}",
            question="这条消息在这个场景下合适吗？",
            options=[
                "perfect: 非常合适，直接发",
                "ok: 还行，可以发",
                "needs_polish: 需要润色一下",
                "dont_send: 千万别发",
            ],
        )
        
        return {
            "message": message,
            "recipient": recipient,
            "tone_too_rude": rude_result.passed,
            "rude_probability": rude_result.probability,
            "risk_level": risk_result.level,
            "appropriateness": appropriateness.choice,
            "should_send": "dont_send" not in appropriateness.choice,
            "feedback": self._generate_feedback(
                message, recipient, rude_result, risk_result, appropriateness
            ),
        }
    
    def _generate_feedback(self, message, recipient, rude, risk, appropriateness) -> str:
        """生成反馈建议"""
        
        if "dont_send" in appropriateness.choice:
            return f"⚠️ 千万别发！这条给{recipient}的消息风险太高了。"
        
        if rude.passed:
            return f"💡 这句话语气有点冲，建议委婉一点，{recipient}可能会不舒服。"
        
        if "needs_polish" in appropriateness.choice:
            return f"✨ 意思没问题，但可以润色得更得体一点。"
        
        return f"✅ 没问题，直接发吧！这条消息给{recipient}很合适。"
    
    def suggest_rephrase(self, message: str, recipient: str = "朋友") -> str:
        """建议改写（需要 LLM 配合，这里先返回结构）"""
        
        # 先让 Jev 判断方向
        direction = self.jev.choice(
            context=f"原消息：{message}\n接收人：{recipient}",
            question="应该往哪个方向改？",
            options=[
                "softer: 语气更柔和",
                "more_formal: 更正式一点",
                "warmer: 更温暖真诚",
                "shorter: 更简洁",
            ],
        )
        
        return f"建议方向：{direction.choice}（具体改写需要 LLM 配合）"


def main():
    print("=" * 60)
    print("💬 微信低情商救星 — Jev 版")
    print("=" * 60)
    print()
    print("输入你想发的微信消息，我帮你看看合不合适。")
    print("输入 q 退出。")
    print()
    
    jev = JevClient(api_key=os.getenv("JEV_API_KEY"))
    bot = WechatPolishBot(jev)
    
    while True:
        recipient = input("\n发给谁？（朋友/老板/暗恋对象/客户，默认朋友）：").strip()
        recipient = recipient or "朋友"
        
        message = input("你想发什么？：").strip()
        if message.lower() == "q":
            break
        
        print("\n🔍 分析中...")
        result = bot.check_message(message, recipient)
        
        print(f"\n📊 结果：")
        print(f"   语气太冲：{'是' if result['tone_too_rude'] else '否'}（{result['rude_probability']:.0%}）")
        print(f"   风险等级：{result['risk_level']}")
        print(f"   合适程度：{result['appropriateness']}")
        print(f"\n💬 建议：{result['feedback']}")
        
        if not result["should_send"]:
            suggestion = bot.suggest_rephrase(message, recipient)
            print(f"   {suggestion}")


if __name__ == "__main__":
    main()
