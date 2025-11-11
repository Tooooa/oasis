"""
使用真实 Profile 的 Agent 运行示例（带水印）

特点：
- ✅ 使用 OASIS 原生的真实用户 profile
- ✅ 每个 Agent 独立的水印管理器
- ✅ 支持配置文件加载
- ✅ 完整的嵌入-提取-验证流程

配置方式:
1. 复制 config.json.template 为 config.json
2. 填入你的 API 配置
3. 运行此脚本
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# 修复路径：从 examples_watermark/01_basic/ 回到项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig

import oasis
from oasis import ActionType, AgentGraph, LLMAction, SocialAgent
from oasis.watermark import WatermarkManager


# ========== 从配置文件加载 ==========
def load_config(config_path: str = None) -> dict:
    """
    加载配置文件
    优先级: 指定路径 > 相对于项目根目录的 config.json
    """
    # 计算项目根目录 (oasis/)
    project_root = Path(__file__).parent.parent.parent
    
    # 尝试的配置文件路径列表
    search_paths = [
        config_path,
        "./config_watermark.json",
        str(project_root / "config.json"),
        str(Path(__file__).parent.parent / "config_watermark.json"),
    ]
    
    for path in search_paths:
        if path and os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ 已加载配置文件: {path}")
                return config
            except Exception as e:
                print(f"⚠️  配置文件 {path} 加载失败: {e}")
    
    # 返回默认配置
    print("⚠️  未找到配置文件，使用默认配置")
    return {
        "api_provider": "deepseek",
        "deepseek": {
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat"
        },
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini"
        },
        "num_agents": 3,
        "num_rounds": 10,
        "agent_profile": {
            "enabled": True,
            "profile_path": "./data/reddit/user_data_36.json"
        },
        "watermark_enabled": True,
        "watermark_config": {
            "payload_bit_length": 8,
            "ecc_method": "parity",
            "embedding_strategy": "cyclic"
        },
        "log_dir": str(Path(__file__).parent.parent.parent / "outputs" / "logs" / "watermark"),
        "database_path": str(Path(__file__).parent.parent.parent / "outputs" / "databases" / "current" / "simulation.db")
    }


# 加载配置
CONFIG = load_config()
# ==============================


async def create_watermarked_agents_from_profile(
    profile_path: str,
    model,
    available_actions: list[ActionType],
    num_agents: int = None,
    watermark_enabled: bool = True,
    log_dir: str = "./log"
) -> tuple[AgentGraph, list[SocialAgent]]:
    """
    使用真实 profile 创建带水印的 Agent
    
    核心策略：
    1. 手动加载 JSON profile（只加载需要的数量）
    2. 使用 OASIS 的 UserInfo 和 SocialAgent 类创建 Agent
    3. 为每个 Agent 添加独立的 WatermarkManager
    
    Args:
        profile_path: profile JSON 文件路径
        model: LLM 模型
        available_actions: 可用行为列表
        num_agents: 使用的 Agent 数量（None=全部）
        watermark_enabled: 是否启用水印
        log_dir: 水印日志目录
        
    Returns:
        agent_graph: AgentGraph 对象
        agents: Agent 列表（包含独立水印）
    """
    print(f"\n📋 使用真实 Profile 创建 Agent...")
    print(f"   Profile 文件: {profile_path}")
    
    # Step 1: 加载 profile JSON
    with open(profile_path, "r", encoding='utf-8') as file:
        agent_info = json.load(file)
    
    total_profiles = len(agent_info)
    agents_to_create = num_agents if num_agents else total_profiles
    
    print(f"   📊 JSON 中共有 {total_profiles} 个 Profile")
    print(f"   🎯 将创建 {agents_to_create} 个 Agent")
    
    # Step 2: 创建 AgentGraph 和 Agent
    agent_graph = AgentGraph()
    agents = []
    
    async def process_agent(idx):
        # 构建 profile 结构（与 OASIS 原生格式一致）
        profile = {
            "nodes": [],
            "edges": [],
            "other_info": {
                "user_profile": agent_info[idx]["persona"],
                "mbti": agent_info[idx]["mbti"],
                "gender": agent_info[idx]["gender"],
                "age": agent_info[idx]["age"],
                "country": agent_info[idx]["country"]
            }
        }
        
        user_info = oasis.UserInfo(
            name=agent_info[idx]["username"],
            description=agent_info[idx]["bio"],
            profile=profile,
            recsys_type="reddit",
        )
        
        agent = SocialAgent(
            agent_id=idx,
            user_info=user_info,
            agent_graph=agent_graph,
            model=model,
            available_actions=available_actions,
        )
        
        # ✅ Agent 在创建时已经自动创建了独立的 WatermarkManager
        # 保存整数索引用于后续验证
        agent.agent_index = idx
        
        # 添加到 agent_graph
        agent_graph.add_agent(agent)
        
        return agent
    
    # 并发创建所有需要的 Agent
    tasks = [process_agent(i) for i in range(agents_to_create)]
    agents = await asyncio.gather(*tasks)
    
    print(f"   ✅ 成功创建 {len(agents)} 个 Agent")
    
    # Step 3: 显示 Agent 信息
    for agent in agents:
        user_info = agent.user_info
        profile_info = user_info.profile.get("other_info", {}) if user_info.profile else {}
        
        # 验证水印管理器
        if hasattr(agent, 'watermark_manager') and agent.watermark_manager is not None:
            expected_bits = format(agent.agent_index, '08b')
            print(f"   ✅ Agent {agent.agent_index}: {user_info.name}")
            print(f"      - 水印: 独立嵌入 agent_id={agent.agent_index} (binary={expected_bits})")
            print(f"      - Bio: {user_info.description[:60]}...")
            print(f"      - Profile: {profile_info.get('age')}岁, "
                  f"{profile_info.get('gender')}, "
                  f"MBTI={profile_info.get('mbti')}, "
                  f"{profile_info.get('country')}")
        else:
            print(f"   ⚪ Agent {agent.agent_index}: {user_info.name} (水印未启用)")
    
    return agent_graph, agents


async def run_custom_simulation():
    """运行使用真实 Profile 的模拟"""
    
    # 读取配置
    api_provider = CONFIG.get("api_provider", "deepseek")
    num_agents = CONFIG.get("num_agents", 3)
    num_rounds = CONFIG.get("num_rounds", 10)
    use_deepseek = api_provider == "deepseek"
    
    # Profile 配置
    agent_profile_config = CONFIG.get("agent_profile", {})
    profile_enabled = agent_profile_config.get("enabled", True)
    profile_path = agent_profile_config.get("profile_path", "./data/reddit/user_data_36.json")
    
    print("=" * 70)
    print(f"🚀 OASIS 真实 Profile Agent 模拟（带水印）")
    print(f"   Agents: {num_agents}")
    print(f"   Rounds: {num_rounds}")
    print(f"   LLM: {api_provider.upper()}")
    print(f"   Profile: {'✅ 真实用户数据' if profile_enabled else '❌ 简化数据'}")
    print("=" * 70)
    
    # 1. 配置 API
    if use_deepseek:
        deepseek_config = CONFIG.get("deepseek", {})
        os.environ["OPENAI_API_KEY"] = deepseek_config.get("api_key", "")
        os.environ["OPENAI_API_BASE"] = deepseek_config.get("base_url", "https://api.deepseek.com")
        print(f"\n✅ DeepSeek API 已配置")
        print(f"   Base URL: {deepseek_config.get('base_url')}")
    else:
        openai_config = CONFIG.get("openai", {})
        if openai_config.get("api_key"):
            os.environ["OPENAI_API_KEY"] = openai_config.get("api_key")
        print(f"\n✅ OpenAI API 已配置")
    
    # 2. 水印配置
    watermark_enabled = CONFIG.get("watermark_enabled", True)
    watermark_config = CONFIG.get("watermark_config", {})
    log_dir = CONFIG.get("log_dir", "./log")
    
    if watermark_enabled:
        print(f"\n📋 水印配置:")
        print(f"   ✅ 独立 Agent 水印架构")
        print(f"   📊 每个 Agent 嵌入自己的 agent_id (8-bit)")
        print(f"   🔐 ECC 方法: {watermark_config.get('ecc_method', 'parity')}")
        print(f"   📁 日志目录: {log_dir}")
    
    # 3. 创建模型
    print(f"\n📋 创建 LLM 模型...")
    if use_deepseek:
        deepseek_config = CONFIG.get("deepseek", {})
        model_config = ChatGPTConfig(
            temperature=0.7, 
            max_tokens=1000,
        )
        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=deepseek_config.get("model", "deepseek-chat"),
            model_config_dict=model_config.as_dict(),
            url=deepseek_config.get("base_url", "https://api.deepseek.com"),
            api_key=deepseek_config.get("api_key", ""),
        )
        print(f"   ✅ DeepSeek 模型: {deepseek_config.get('model', 'deepseek-chat')}")
    else:
        openai_config = CONFIG.get("openai", {})
        model_config = ChatGPTConfig(
            temperature=0.7,
            max_tokens=1000,
        )
        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=openai_config.get("model", ModelType.GPT_4O_MINI),
            model_config_dict=model_config.as_dict(),
        )
    print(f"   ✅ 模型创建成功")
    
    # 4. 定义可用行为（使用 OASIS 默认 Reddit 行为列表）
    available_actions = ActionType.get_default_reddit_actions()
    
    print(f"\n📋 可用行为: {[a.value for a in available_actions]}")
    print(f"   ✅ 共 {len(available_actions)} 种行为可供选择")
    print(f"   ℹ️  行为序列在模拟过程中保持不变（OASIS 原始设计）")
    
    # 5. 创建 Agent Graph（使用真实 Profile）⭐
    # 计算绝对路径
    project_root = Path(__file__).parent.parent.parent
    abs_profile_path = str(project_root / profile_path)
    
    agent_graph, agents = await create_watermarked_agents_from_profile(
        profile_path=abs_profile_path,
        model=model,
        available_actions=available_actions,
        num_agents=num_agents,
        watermark_enabled=watermark_enabled,
        log_dir=log_dir
    )
    
    print(f"\n✅ 成功创建 {len(agents)} 个带水印的 Agent")
    
    # 6. 初始化环境
    print(f"\n📋 初始化 OASIS 环境...")
    db_path = CONFIG.get("database_path", f"./oasis_profile_{num_agents}agents_{num_rounds}rounds.db")
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
    total_calls = num_agents * num_rounds * 2  # 两阶段集成
    estimated_tokens = total_calls * 800
    if use_deepseek:
        estimated_cost = estimated_tokens * 0.00000025  # DeepSeek 定价
        print(f"   API 调用: {total_calls} 次")
        print(f"   估算 Tokens: ~{estimated_tokens:,}")
        print(f"   估算成本: ${estimated_cost:.4f} (DeepSeek)")
        print(f"   估算时间: {num_agents * num_rounds * 2} 秒 (约 {(num_agents * num_rounds * 2) / 60:.1f} 分钟)")
    else:
        estimated_cost = estimated_tokens * 0.000002  # OpenAI GPT-4O-MINI
        print(f"   API 调用: {total_calls} 次")
        print(f"   估算 Tokens: ~{estimated_tokens:,}")
        print(f"   估算成本: ${estimated_cost:.4f} (OpenAI)")
        print(f"   估算时间: {num_agents * num_rounds * 2} 秒 (约 {(num_agents * num_rounds * 2) / 60:.1f} 分钟)")
    
    # 8. 运行模拟
    print(f"\n" + "=" * 70)
    print(f"🎬 开始模拟 {num_rounds} 轮...")
    print("=" * 70)
    
    import time
    start_time = time.time()
    
    for round_num in range(num_rounds):
        print(f"\n📍 Round {round_num + 1}/{num_rounds}")
        
        # 所有 Agent 执行 LLM 驱动的行为
        all_actions = {agent: LLMAction() for agent in agents}
        
        try:
            round_start = time.time()
            await env.step(all_actions)
            round_time = time.time() - round_start
            
            # ✅ 显示每个Agent的独立统计
            print(f"   ✅ 完成 (耗时: {round_time:.1f}秒)")
            for agent in agents:
                if hasattr(agent, 'watermark_manager') and agent.watermark_manager is not None:
                    stats = agent.watermark_manager.get_statistics()
                    print(f"      {agent.user_info.name} (Agent {agent.agent_index}): "
                          f"{stats['current_bit_index']}/{stats['bit_stream_length']} bits "
                          f"(剩余: {stats['bits_remaining']})")
            
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            break
    
    total_time = time.time() - start_time
    
    # 9. ✅ 独立提取和验证每个Agent的水印
    print(f"\n" + "=" * 70)
    print(f"🔍 提取和验证每个Agent的独立水印...")
    print("=" * 70)
    
    for agent in agents:
        if not (hasattr(agent, 'watermark_manager') and agent.watermark_manager is not None):
            print(f"\n⚠️ {agent.user_info.name} (Agent {agent.agent_index}): 未启用水印")
            continue
        
        wm = agent.watermark_manager
        print(f"\n{'=' * 70}")
        print(f"🤖 {agent.user_info.name} (Agent {agent.agent_index}) - 水印提取")
        print(f"{'=' * 70}")
        
        extracted, stats = wm.extract_watermark_from_log()
        
        print(f"\n📊 提取结果:")
        print(f"   Username: {agent.user_info.name}")
        print(f"   Agent索引: {agent.agent_index}")
        print(f"   Agent UUID: {agent.social_agent_id}")
        print(f"   原始比特流: {wm.bit_stream} (长度: {len(wm.bit_stream)})")
        print(f"   提取比特流: {extracted} (长度: {len(extracted)})")
        print(f"   解码Payload: {stats.get('decoded_payload', 'N/A')}")
        
        # ✅ 识别agent_id：从解码的payload中提取前8位
        if stats.get('decoded_payload'):
            decoded_payload = stats.get('decoded_payload', '')
            if len(decoded_payload) >= 8:
                extracted_agent_id_bits = decoded_payload[:8]
                extracted_agent_id = int(extracted_agent_id_bits, 2)
                print(f"   识别的agent_id: {extracted_agent_id} (binary: {extracted_agent_id_bits})")
                
                if extracted_agent_id == agent.agent_index:
                    print(f"   ✅ Agent ID 匹配！")
                else:
                    print(f"   ❌ Agent ID 不匹配! (期望: {agent.agent_index})")
            else:
                print(f"   ⚠️ Payload不足8位，无法识别agent_id")
        
        # ✅ 更准确的统计描述
        total_rounds = stats.get('actions_processed', 0)
        embedded_rounds = stats.get('successful_extractions', 0)
        skipped_rounds = total_rounds - embedded_rounds
        
        print(f"\n📊 嵌入统计:")
        print(f"   总轮数: {total_rounds}")
        print(f"   有效嵌入轮数: {embedded_rounds} (成功嵌入水印)")
        if skipped_rounds > 0:
            print(f"   跳过轮数: {skipped_rounds} (概率分布太集中，无法嵌入)")
        print(f"   完整块数: {stats.get('complete_messages', 0)}")
        if stats.get('partial_bits', 0) > 0:
            print(f"   部分嵌入: {stats.get('partial_bits', 0)} bits "
                  f"{'✅ ECC验证通过' if stats.get('partial_is_valid') else '⚠️ ECC验证失败(不足完整块)'}")
        
        # ✅ 使用改进的准确率（来自stats）
        if len(extracted) > 0:
            accuracy = stats.get('accuracy', 0.0)
            original_length = len(wm.bit_stream)
            extracted_length = len(extracted)
            
            print(f"\n📈 比特位准确度:")
            print(f"   - 匹配度: {accuracy:.1f}%")
            print(f"   - 原始长度: {original_length} bits")
            print(f"   - 提取长度: {extracted_length} bits")
            
            if accuracy < 100:
                mismatches = []
                for i, bit in enumerate(extracted):
                    expected_bit = wm.bit_stream[i % len(wm.bit_stream)]
                    if bit != expected_bit:
                        mismatches.append((i, bit, expected_bit))
                
                if mismatches:
                    print(f"   ⚠️ 发现 {len(mismatches)} 个不匹配的bit:")
                    for pos, actual, expected in mismatches[:5]:
                        print(f"      位置{pos}: 提取='{actual}' vs 原始='{expected}'")
                    if len(mismatches) > 5:
                        print(f"      ... 还有 {len(mismatches) - 5} 个不匹配")
            else:
                print(f"   ✅ 完美匹配: 提取的每一位都与原始bit_stream循环一致")
            
            print(f"\n🔐 ECC验证状态:")
            complete_messages = stats.get('complete_messages', 0)
            failed_validations = stats.get('failed_validations', 0)
            partial_bits = stats.get('partial_bits', 0)
            
            if stats.get('valid', False):
                if complete_messages > 0 and failed_validations == 0:
                    print(f"   - 状态: ✅ 完全有效")
                    print(f"   - 说明: {complete_messages} 个完整块全部通过ECC校验")
                else:
                    print(f"   - 状态: ✅ 验证成功")
                    print(f"   - 说明: {complete_messages - failed_validations}/{complete_messages} 个完整块通过ECC校验")
                
                if partial_bits > 0:
                    partial_valid = stats.get('partial_is_valid', False)
                    if partial_valid:
                        print(f"   - 部分块: {partial_bits} bits 验证成功")
                    else:
                        print(f"   - 部分块: {partial_bits} bits 未验证（不影响结果）")
            else:
                if complete_messages == 0:
                    print(f"   - 状态: ❌ 无法验证")
                    print(f"   - 说明: 提取的比特数不足一个完整块")
                    print(f"   - 提示: 需要至少 9 bits（含ECC）才能验证")
                else:
                    print(f"   - 状态: ❌ 验证失败")
                    print(f"   - 说明: {complete_messages} 个完整块中有 {failed_validations} 个验证失败")
            
            if accuracy == 100 and stats.get('valid', False):
                print(f"\n✅ {agent.user_info.name} 水印完整提取并验证成功！")
            elif accuracy >= 90:
                print(f"\n✅ {agent.user_info.name} 比特位准确度高（{accuracy:.1f}%）")
                if stats.get('partial_bits', 0) > 0:
                    print(f"   💡 提示: 增加模拟轮数可嵌入完整水印块，通过ECC验证")
            elif accuracy >= 80:
                print(f"\n⚠️ {agent.user_info.name} 水印提取准确率中等（{accuracy:.1f}%）")
                print(f"   💡 提示: 增加轮数以提高准确率")
            else:
                print(f"\n⚠️ {agent.user_info.name} 水印提取准确率较低（{accuracy:.1f}%）")
        else:
            print(f"\n❌ {agent.user_info.name} 未提取到水印")
    
    # 10. 清理
    await env.close()
    
    # 11. 总结
    print(f"\n" + "=" * 70)
    print(f"📊 运行总结")
    print("=" * 70)
    print(f"✅ 配置:")
    print(f"   - Agent 数量: {num_agents} (使用真实 Profile)")
    print(f"   - 模拟轮数: {num_rounds}")
    print(f"   - LLM: {api_provider.upper()}")
    
    # 显示 Agent 信息
    print(f"\n✅ Agent 信息:")
    for agent in agents:
        user_info = agent.user_info
        profile_info = user_info.profile.get("other_info", {}) if user_info.profile else {}
        print(f"   - Agent {agent.agent_index}: {user_info.name}")
        print(f"     {profile_info.get('age')}岁 {profile_info.get('gender')}, "
              f"MBTI={profile_info.get('mbti')}, {profile_info.get('country')}")
        if profile_info.get('user_profile'):
            persona_preview = profile_info['user_profile'][:100]
            print(f"     Persona: {persona_preview}...")
    
    print(f"\n✅ 性能:")
    print(f"   - 总耗时: {total_time:.1f} 秒 ({total_time / 60:.1f} 分钟)")
    print(f"   - 平均每轮: {total_time / num_rounds:.1f} 秒")
    print(f"   - API 调用: {total_calls} 次")
    print(f"\n✅ 输出文件:")
    print(f"   - 数据库: {db_path}")
    
    # ✅ 显示每个agent的日志文件
    for agent in agents:
        if hasattr(agent, 'watermark_manager') and agent.watermark_manager is not None:
            print(f"   - {agent.user_info.name} (Agent {agent.agent_index}) 日志: {agent.watermark_manager.log_file}")
    
    print("=" * 70)


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     OASIS 真实 Profile Agent 运行（带水印）             ║
    ║                                                          ║
    ║  特点:                                                   ║
    ║    ✅ 使用 OASIS 原生真实用户 Profile                   ║
    ║    ✅ 每个 Agent 独立水印管理器                         ║
    ║    ✅ 支持 DeepSeek / OpenAI 双 LLM                     ║
    ║    ✅ 完整的嵌入-提取-验证流程                          ║
    ║                                                          ║
    ║  修改配置:                                               ║
    ║    编辑 config.json 或 config_watermark.json            ║
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
