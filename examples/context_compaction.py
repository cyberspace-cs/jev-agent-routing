"""
上下文压缩 Demo — 修复订单导出超时的会话
==========================================
参考腾讯技术工程 fast-jev-compaction 的样本会话。

四个工具调用：
  t1 list_dir        长目录树      → drop_result（调用有用，全文无用）
  t2 read_file       orderExport.ts → keep（含 getAuthToken，和鉴权约束相关）
  t3 execute_command 测试失败      → keep（含超时和 authorization header）
  t4 read_file        legacy 文件   → drop_call（和当前任务无关）
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jev.compaction import JevCompactor, heuristic_asker


# 模拟一个修复 bug 的会话
SAMPLE_MESSAGES = [
    # 首条用户消息（pinned）
    {
        "role": "user",
        "content": "订单导出测试超时了，帮我修复。注意不要破坏鉴权。",
    },
    # 助手调用 list_dir
    {
        "role": "assistant",
        "content": [
            {"type": "text", "text": "我先看看项目结构。"},
            {"type": "tool_use", "id": "toolu_001", "name": "list_dir",
             "input": {"path": "/repo/src/services"}},
        ],
    },
    # list_dir 返回长目录树
    {
        "role": "user",
        "content": [
            {"type": "tool_result", "tool_use_id": "toolu_001", "is_error": False,
             "content": "orderExport.ts\norderImport.ts\nauthHelper.ts\nutils/\nlegacy/\n..." + "x" * 4000},
        ],
    },
    # 助手 read_file orderExport.ts
    {
        "role": "assistant",
        "content": [
            {"type": "tool_use", "id": "toolu_002", "name": "read_file",
             "input": {"path": "/repo/src/services/orderExport.ts"}},
        ],
    },
    # read_file 返回文件内容（含 getAuthToken）
    {
        "role": "user",
        "content": [
            {"type": "tool_result", "tool_use_id": "toolu_002", "is_error": False,
             "content": "export async function exportOrders() {\n  const token = getAuthToken();\n  // ...\n}"},
        ],
    },
    # 助手跑测试
    {
        "role": "assistant",
        "content": [
            {"type": "tool_use", "id": "toolu_003", "name": "execute_command",
             "input": {"command": "npm test -- order-export"}},
        ],
    },
    # 测试失败（关键证据）
    {
        "role": "user",
        "content": [
            {"type": "tool_result", "tool_use_id": "toolu_003", "is_error": True,
             "content": "FAIL order-export.test.ts\nError: Timeout of 5000ms exceeded\n  at exportOrders (/repo/src/services/orderExport.ts:42:19)\nExpected authorization header to be preserved."},
        ],
    },
    # 助手读了一个无关的 legacy 文件
    {
        "role": "assistant",
        "content": [
            {"type": "tool_use", "id": "toolu_004", "name": "read_file",
             "input": {"path": "/repo/src/legacy/reportPrinter.ts"}},
        ],
    },
    {
        "role": "user",
        "content": [
            {"type": "tool_result", "tool_use_id": "toolu_004", "is_error": False,
             "content": "// legacy code, unrelated to order export\n..."},
        ],
    },
]


def main():
    print("=" * 70)
    print("🧹 Jev Context Compaction Demo")
    print("=" * 70)
    print()
    
    # 用本地启发式 asker（离线可跑）
    # 真实环境替换为 real_jev_asker(jev_client)
    compactor = JevCompactor(
        asker=heuristic_asker,
        keep_threshold=0.5,
        preserve_recent=6,
    )
    
    result = compactor.compact(SAMPLE_MESSAGES)
    
    # 打印决策表
    print("📊 决策结果：")
    print(f"{'ID':<5} {'工具':<18} {'动作':<14} {'keepCall':<10} {'keepResult':<12}")
    print("-" * 70)
    for d in result["decisions"]:
        print(f"{d.call_id:<5} {d.tool_name:<18} {d.action:<14} "
              f"{d.keep_call:<10.2f} {d.keep_result:<12.2f}")
    
    print()
    print("📈 压缩统计：")
    print(f"   压缩前字符数：{result['chars_before']}")
    print(f"   压缩后字符数：{result['chars_after']}")
    print(f"   压缩率：      {result['compression_ratio']:.1%}")
    print(f"   完整保留：    {result['kept_count']} 个")
    print(f"   截断结果：    {result['dropped_result_count']} 个")
    print(f"   调用删除：    {result['dropped_call_count']} 个")
    print()
    print("💡 说明：")
    print("   - list_dir 的长目录树 → drop_result（可重跑，不需要全文）")
    print("   - orderExport.ts → keep（含 getAuthToken，和鉴权约束相关）")
    print("   - 测试失败日志 → keep（含超时和 authorization header）")
    print("   - legacy 文件 → drop_call（和当前任务无关）")


if __name__ == "__main__":
    main()
