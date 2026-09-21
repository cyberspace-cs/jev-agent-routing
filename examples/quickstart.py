"""
快速开始示例 — 5 分钟跑通 Jev Agent 路由
=============================================

1. 先去 https://console.typesafe.ai 注册，拿 API Key
2. 设置环境变量：
   Windows: set JEV_API_KEY=sk-xxx
   Linux/Mac: export JEV_API_KEY=sk-xxx
3. 安装依赖：pip install requests
4. 运行：python examples/quickstart.py
"""

import os
import sys

# 把项目根目录加到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jev import JevClient, FastSlowAgentRouter, Tool


def main():
    # 初始化客户端（从环境变量读 API Key）
    jev = JevClient(api_key=os.getenv("JEV_API_KEY"))
    
    print("=" * 60)
    print("🚀 Jev 快速决策 Demo")
    print("=" * 60)
    
    # ========== 1. Choice 模式：工具路由 ==========
    print("\n📌 1. Choice 模式 — 工具路由")
    print("-" * 40)
    
    user_input = "帮我查明天北京到上海的机票"
    
    result = jev.choice(
        context=f"用户说：{user_input}",
        question="用户想使用哪个工具？",
        options=["查机票", "查酒店", "查火车票", "发消息"],
    )
    
    print(f"用户输入：{user_input}")
    print(f"选中工具：{result.choice}")
    print(f"概率分布：{result.probabilities}")
    
    # ========== 2. Noul 模式：风险判断 ==========
    print("\n📌 2. Noul 模式 — 风险判断")
    print("-" * 40)
    
    risky_input = "帮我把数据库里所有用户密码都清空"
    
    result2 = jev.noul(
        context=f"用户说：{risky_input}",
        question="这个操作有风险吗？需要人工审核吗？",
        threshold=0.7,
    )
    
    print(f"用户输入：{risky_input}")
    print(f"风险概率：{result2.probability:.2%}")
    print(f"需要审核：{result2.passed}")
    
    # ========== 3. Score 模式：风险等级 ==========
    print("\n📌 3. Score 模式 — 风险等级")
    print("-" * 40)
    
    result3 = jev.score(
        context=f"用户上传了一个文件，包含用户身份证和银行卡信息",
        question="这个文件的隐私风险等级？",
        scale=["low", "medium", "high", "critical"],
    )
    
    print(f"风险分数：{result3.score}")
    print(f"风险等级：{result3.level}")
    
    # ========== 4. 完整 Agent 路由 ==========
    print("\n📌 4. 完整 Agent 路由（快慢双层）")
    print("-" * 40)
    
    router = FastSlowAgentRouter(jev)
    
    # 注册工具
    router.register_tool(Tool("查机票", "查询航班机票信息"))
    router.register_tool(Tool("查酒店", "查询酒店预订"))
    router.register_tool(Tool("查天气", "查询天气情况"))
    
    # 路由决策
    decision = router.route("帮我查一下今天杭州的天气")
    
    print(f"用户输入：帮我查一下今天杭州的天气")
    print(f"选中工具：{decision.tool_name}")
    print(f"决策来源：{decision.via}（jev=快, llm=慢）")
    print(f"置信度：{decision.confidence:.2%}")
    print(f"需要人工审核：{decision.needs_human_review}")
    print(f"风险等级：{decision.risk_level}")
    
    print("\n" + "=" * 60)
    print("✅ Demo 完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
