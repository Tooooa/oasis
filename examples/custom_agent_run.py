"""
自定义少量 Agent 运行示例（带水印）

可配置:
- Agent 数量 (1-10)
- 模拟轮数 (1-20)
- 使用 DeepSeek 或 OpenAI
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig

import oasis
from oasis import ActionType, AgentGraph, LLMAction, SocialAgent, UserInfo
from oasis.watermark import WatermarkManager

# ========== 配置区域 ==========
NUM_AGENTS = 2        # 🔧 修改这里：Agent 数量（1-10）
NUM_ROUNDS = 3        # 🔧 修改这里：模拟轮数（1-20）
USE_DEEPSEEK = True   # 🔧 修改这里：是否使用 DeepSeek（便宜 70%）

# DeepSeek API（如果使用）
DEEPSEEK_API_KEY = "sk-5fa9b50054194880bfa66023555f857d"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
# ==============================


async def run_custom_simulation():
    """运行自定义配置的模拟"""
    
    print("=" * 70)
    print(f"🚀 OASIS 少量 Agent 模拟（带水印）")
    print(f"   Agents: {NUM_AGENTS}")
    print(f"   Rounds: {NUM_ROUNDS}")
    print(f"   LLM: {'DeepSeek' if USE_DEEPSEEK else 'OpenAI'}")
    print("=" * 70)
    
    # 1. 配置 API
    if USE_DEEPSEEK:
        os.environ["OPENAI_API_KEY"] = DEEPSEEK_API_KEY
        os.environ["OPENAI_API_BASE"] = DEEPSEEK_BASE_URL
        print("\n✅ DeepSeek API 已配置")
    else:
        print("\n✅ 使用 OpenAI API")
    
    # 2. 创建水印管理器
    print("\n📋 初始化水印管理器...")
    wm = WatermarkManager(
        enabled=True,
        mode="full",
        bit_stream="11001101",  # 8-bit payload
        config={
            "payload_bit_length": 8,
            "ecc_method": "parity",
            "embedding_strategy": "cyclic"
        }
    )
    print(f"   ✅ Bit stream: {wm.bit_stream}")
    print(f"   📊 需要嵌入: {len(wm.bit_stream)} bits")
    
    # 3. 创建模型
    print("\n📋 创建 LLM 模型...")
    if USE_DEEPSEEK:
        model_config = ChatGPTConfig(
            temperature=0.7, 
            max_tokens=1000,
        )
        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type="deepseek-chat",  # ✅ 使用 DeepSeek 原生模型名
            model_config_dict=model_config.as_dict(),
            url=DEEPSEEK_BASE_URL,
            api_key=DEEPSEEK_API_KEY,
        )
    else:
        model_config = ChatGPTConfig(
            temperature=0.7,
            max_tokens=1000,
        )
        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O_MINI,
            model_config_dict=model_config.as_dict(),
        )
    print(f"   ✅ 模型创建成功")
    
    # 4. 定义可用行为
    available_actions = [
        ActionType.LIKE_POST,
        ActionType.CREATE_POST,
        ActionType.CREATE_COMMENT,
        ActionType.FOLLOW,
        ActionType.REFRESH,
    ]
    print(f"\n📋 可用行为: {[a.value for a in available_actions]}")
    
    # 5. 创建 Agent Graph
    print(f"\n📋 创建 {NUM_AGENTS} 个 Agent...")
    agent_graph = AgentGraph()
    agents = []
    
    for i in range(NUM_AGENTS):
        agent = SocialAgent(
            agent_id=i,
            user_info=UserInfo(
                user_name=f"agent_{i}",
                name=f"Agent {i}",
                description=f"Social agent {i}",
                profile=None,
                recsys_type="reddit",
            ),
            agent_graph=agent_graph,
            model=model,
            available_actions=available_actions,
            watermark_manager=wm,  # 🎯 关键：传递水印管理器
        )
        agent_graph.add_agent(agent)
        agents.append(agent)
        print(f"   ✅ Agent {i} 创建成功（带水印）")
    
    # 6. 初始化环境
    print(f"\n📋 初始化 OASIS 环境...")
    db_path = f"./oasis_custom_{NUM_AGENTS}agents_{NUM_ROUNDS}rounds.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    env = oasis.make(
        agent_graph=agent_graph,
        platform=oasis.DefaultPlatformType.REDDIT,
        database_path=db_path,
    )
    await env.reset()
    print(f"   ✅ 环境初始化完成: {db_path}")
    
    # 7. 估算资源
    print(f"\n📊 资源估算:")
    total_calls = NUM_AGENTS * NUM_ROUNDS * 2  # 两阶段集成
    estimated_tokens = total_calls * 800
    if USE_DEEPSEEK:
        estimated_cost = estimated_tokens * 0.00000025  # DeepSeek 定价
        print(f"   API 调用: {total_calls} 次")
        print(f"   估算 Tokens: ~{estimated_tokens:,}")
        print(f"   估算成本: ${estimated_cost:.4f} (DeepSeek)")
        print(f"   估算时间: {NUM_AGENTS * NUM_ROUNDS * 2} 秒 (约 {(NUM_AGENTS * NUM_ROUNDS * 2) / 60:.1f} 分钟)")
    else:
        estimated_cost = estimated_tokens * 0.000002  # OpenAI GPT-4O-MINI
        print(f"   API 调用: {total_calls} 次")
        print(f"   估算 Tokens: ~{estimated_tokens:,}")
        print(f"   估算成本: ${estimated_cost:.4f} (OpenAI)")
        print(f"   估算时间: {NUM_AGENTS * NUM_ROUNDS * 2} 秒 (约 {(NUM_AGENTS * NUM_ROUNDS * 2) / 60:.1f} 分钟)")
    
    # 8. 运行模拟
    print(f"\n" + "=" * 70)
    print(f"🎬 开始模拟 {NUM_ROUNDS} 轮...")
    print("=" * 70)
    
    import time
    start_time = time.time()
    
    for round_num in range(NUM_ROUNDS):
        print(f"\n📍 Round {round_num + 1}/{NUM_ROUNDS}")
        
        # 所有 Agent 执行 LLM 驱动的行为
        all_actions = {agent: LLMAction() for agent in agents}
        
        try:
            round_start = time.time()
            await env.step(all_actions)
            round_time = time.time() - round_start
            
            # 显示统计
            stats = wm.get_statistics()
            print(f"   ✅ 完成 (耗时: {round_time:.1f}秒)")
            print(f"   📊 水印进度: {stats['current_bit_index']}/{stats['bit_stream_length']} bits")
            print(f"   📊 剩余: {stats['bits_remaining']} bits")
            
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            break
    
    total_time = time.time() - start_time
    
    # 9. 提取和验证
    print(f"\n" + "=" * 70)
    print(f"🔍 提取和验证水印...")
    print("=" * 70)
    
    extracted, stats = wm.extract_watermark_from_log()
    
    print(f"\n📊 提取结果:")
    print(f"   原始比特流: {wm.bit_stream}")
    print(f"   提取比特流: {extracted}")
    print(f"   解码Payload: {stats.get('decoded_payload', 'N/A')}")
    print(f"   成功提取: {stats.get('successful_extractions', 0)} / {stats.get('actions_processed', 0)}")
    print(f"   完整块数: {stats.get('complete_messages', 0)}")
    if stats.get('partial_bits', 0) > 0:
        print(f"   部分提取: {stats.get('partial_bits', 0)} bits {'✅ 已验证' if stats.get('partial_is_valid') else '❌ 不匹配'}")
    print(f"   有效性: {'✅ 有效' if stats.get('valid', False) else '⚠️ 部分失败'}")
    
    # ✅ 使用改进的准确率（来自stats）
    if len(extracted) > 0:
        # 优先使用 WatermarkManager 计算的循环准确率
        accuracy = stats.get('accuracy', 0.0)
        print(f"   循环准确率: {accuracy:.1f}%")
        
        if accuracy == 100 and stats.get('valid', False):
            print(f"\n✅ 水印完整提取并验证成功！")
        elif accuracy >= 90:
            print(f"\n✅ 水印提取准确率高（{accuracy:.1f}%）")
            if stats.get('partial_bits', 0) > 0:
                print(f"   💡 提示: {'部分提取已验证通过' if stats.get('partial_is_valid') else '增加轮数可提取完整水印'}")
        elif accuracy >= 80:
            print(f"\n⚠️  水印提取准确率中等（{accuracy:.1f}%）")
            print(f"   💡 提示: 增加轮数以提高准确率")
        else:
            print(f"\n⚠️  水印提取准确率较低（{accuracy:.1f}%）")
    else:
        print(f"\n❌ 未提取到水印")
    
    # 10. 清理
    await env.close()
    
    # 11. 总结
    print(f"\n" + "=" * 70)
    print(f"📊 运行总结")
    print("=" * 70)
    print(f"✅ 配置:")
    print(f"   - Agent 数量: {NUM_AGENTS}")
    print(f"   - 模拟轮数: {NUM_ROUNDS}")
    print(f"   - LLM: {'DeepSeek' if USE_DEEPSEEK else 'OpenAI'}")
    print(f"\n✅ 性能:")
    print(f"   - 总耗时: {total_time:.1f} 秒 ({total_time / 60:.1f} 分钟)")
    print(f"   - 平均每轮: {total_time / NUM_ROUNDS:.1f} 秒")
    print(f"   - API 调用: {total_calls} 次")
    print(f"\n✅ 输出文件:")
    print(f"   - 数据库: {db_path}")
    print(f"   - 日志: {wm.log_file}")
    print("=" * 70)


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     OASIS 自定义 Agent 运行（带水印）                    ║
    ║                                                          ║
    ║  修改配置:                                               ║
    ║    - NUM_AGENTS: Agent 数量                              ║
    ║    - NUM_ROUNDS: 模拟轮数                                ║
    ║    - USE_DEEPSEEK: 是否使用 DeepSeek                     ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(run_custom_simulation())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n\n❌ 运行失败: {e}")
        import traceback
        traceback.print_exc()
