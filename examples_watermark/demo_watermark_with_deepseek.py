"""
完整的 OASIS + AgentMark 水印演示
使用 DeepSeek API 进行真实的社交模拟

这个示例展示了：
1. 使用 DeepSeek LLM 生成行为概率
2. 通过差分水印方案嵌入水印
3. 完整的社交模拟流程
4. 水印提取和验证
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from openai import AsyncOpenAI

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from oasis.watermark import WatermarkManager


# ========== 配置加载 ==========
def load_config(config_path: str = None) -> dict:
    """加载配置文件"""
    search_paths = [
        config_path,
        "./config.json",
        "../config.json",
        str(Path(__file__).parent.parent / "config.json"),
    ]
    
    for path in search_paths:
        if path and os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  配置文件加载失败: {e}")
    
    # 默认配置
    return {
        "deepseek": {
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat"
        }
    }


CONFIG = load_config()
DEEPSEEK_CONFIG = CONFIG.get("deepseek", {})
DEEPSEEK_API_KEY = DEEPSEEK_CONFIG.get("api_key", "")
DEEPSEEK_BASE_URL = DEEPSEEK_CONFIG.get("base_url", "https://api.deepseek.com")
DEEPSEEK_MODEL = DEEPSEEK_CONFIG.get("model", "deepseek-chat")


class WatermarkedSocialAgent:
    """
    带水印的社交Agent模拟器
    
    这个类模拟了一个真实的社交Agent，包括：
    - 使用LLM生成行为概率
    - 通过WatermarkManager嵌入水印
    - 记录完整的交互历史
    """
    
    def __init__(
        self,
        agent_id: int,
        name: str,
        profile: str,
        watermark_manager: WatermarkManager = None,
        api_key: str = DEEPSEEK_API_KEY,
        base_url: str = DEEPSEEK_BASE_URL,
        model: str = DEEPSEEK_MODEL
    ):
        self.agent_id = agent_id
        self.name = name
        self.profile = profile
        self.watermark_manager = watermark_manager
        
        # 初始化 DeepSeek 客户端
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        
        # 历史记录
        self.history_events = []
        self.history_responses = []
        self.round_num = 0
    
    async def get_behavior_probabilities(
        self,
        event: str,
        behaviors: list[str]
    ) -> dict[str, float]:
        """
        使用 DeepSeek LLM 生成行为概率
        
        Args:
            event: 当前事件描述
            behaviors: 可选行为列表
            
        Returns:
            dict: 行为到概率的映射
        """
        # 构造 prompt
        behaviors_str = ", ".join([f'"{b}"' for b in behaviors])
        behaviors_example = "{" + ", ".join([f'"{b}": 0.xx' for b in behaviors]) + "}"
        
        prompt = f"""任务：根据以下事件，计算用户{self.name}可能的行为概率值，并确保所有概率值的总和为1。

用户画像：{self.profile}

事件描述：
{event}

行为列表：
{behaviors_str}

归一化规则：
1. 计算每种行为的原始概率值。
2. 将所有行为的原始概率值相加，得到总和。
3. 将每种行为的原始概率值除以总和，得到归一化后的概率值。

输出格式：
请以以下格式输出结果：{behaviors_example}，并确保所有概率值的总和为1。
只输出JSON格式的结果，不要有其他文字。"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"你是{self.name}。{self.profile}"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
            )
            
            content = response.choices[0].message.content.strip()
            print(f"\n🤖 LLM返回的概率: {content}")
            
            # 提取 JSON
            if '{' in content and '}' in content:
                start = content.find('{')
                end = content.rfind('}') + 1
                json_str = content[start:end]
                probabilities = json.loads(json_str)
                
                # 归一化
                total = sum(probabilities.values())
                if total > 0:
                    probabilities = {k: v/total for k, v in probabilities.items()}
                
                return probabilities
            else:
                print(f"⚠️ 无法解析LLM返回，使用默认均匀分布")
                return {b: 1.0/len(behaviors) for b in behaviors}
                
        except Exception as e:
            print(f"❌ LLM调用失败: {e}")
            # 返回均匀分布作为后备
            return {b: 1.0/len(behaviors) for b in behaviors}
    
    async def perform_action(
        self,
        event: str,
        behaviors: list[str]
    ) -> dict:
        """
        执行一次完整的行为决策流程
        
        Args:
            event: 当前事件
            behaviors: 可选行为列表
            
        Returns:
            dict: 包含选择的行为、嵌入的比特等信息
        """
        print(f"\n{'='*60}")
        print(f"📹 轮次 {self.round_num}: {self.name} 的行为决策")
        print(f"{'='*60}")
        print(f"事件: {event}")
        
        # 1. 从 LLM 获取行为概率
        probabilities = await self.get_behavior_probabilities(event, behaviors)
        print(f"\n📊 原始概率分布:")
        for behavior, prob in probabilities.items():
            print(f"  - {behavior}: {prob:.4f}")
        
        # 2. 如果启用水印，使用水印采样
        if self.watermark_manager and self.watermark_manager.enabled:
            # 构造上下文（最近3个响应）
            window_size = 3
            recent_responses = self.history_responses[-window_size:] if self.history_responses else []
            context_for_key = "||".join(recent_responses) if recent_responses else ""
            
            # 水印采样
            selected_behavior, target_list, bits_embedded, context_used = \
                self.watermark_manager.sample_behavior_watermark(
                    probabilities=probabilities,
                    round_num=self.round_num,
                    context_for_key=context_for_key
                )
            
            print(f"\n🔐 水印嵌入:")
            print(f"  - 选择的行为: {selected_behavior}")
            print(f"  - 嵌入比特数: {bits_embedded}")
            print(f"  - 目标列表: {target_list}")
            print(f"  - 当前比特索引: {self.watermark_manager.bit_index}")
            
        else:
            # 无水印：简单随机采样
            import random
            selected_behavior = random.choices(
                list(probabilities.keys()),
                weights=list(probabilities.values()),
                k=1
            )[0]
            bits_embedded = 0
            target_list = []
            
            print(f"\n⚪ 无水印选择: {selected_behavior}")
        
        # 3. 更新历史
        self.history_events.append(event)
        self.history_responses.append(selected_behavior)
        self.round_num += 1
        
        return {
            "round_num": self.round_num - 1,
            "event": event,
            "probabilities": probabilities,
            "selected_behavior": selected_behavior,
            "bits_embedded": bits_embedded,
            "target_list": target_list
        }


async def run_simulation():
    """运行完整的水印社交模拟"""
    
    print("\n" + "="*60)
    print("🎬 OASIS + AgentMark 水印社交模拟演示")
    print("="*60)
    print("使用 DeepSeek API 进行真实的 LLM 交互")
    print("="*60)
    
    # 1. 初始化 WatermarkManager
    log_dir = Path(__file__).parent.parent / "test_log" / "deepseek_demo"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    payload = "11001101"  # 8-bit 载荷
    wm = WatermarkManager(
        enabled=True,
        mode="lightweight",
        bit_stream=payload,
        log_dir=str(log_dir),
        config={
            "payload_bit_length": 8,
            "ecc_method": "parity",
            "embedding_strategy": "cyclic"
        }
    )
    
    print(f"\n✅ WatermarkManager 初始化成功")
    print(f"  - 原始载荷: {payload} (8 bits)")
    print(f"  - 编码后比特流: {wm.bit_stream} ({len(wm.bit_stream)} bits)")
    print(f"  - ECC方法: parity (奇偶校验)")
    print(f"  - 日志目录: {log_dir}")
    print(f"  - 日志文件: {wm.log_file}")
    
    # 2. 创建带水印的 Agent
    agent = WatermarkedSocialAgent(
        agent_id=1,
        name="张三",
        profile="一个活跃的社交媒体用户,喜欢浏览、收藏、转发和评论各类内容",
        watermark_manager=wm
    )
    
    print(f"\n✅ Agent 创建成功: {agent.name}")
    
    # 3. 定义模拟场景
    # 使用6种行为类型，与原始AgentMark保持一致，每轮可嵌入 log2(6) ≈ 2.58 bits
    behaviors = ["点赞", "评论", "转发", "收藏", "浏览", "下载"]
    
    events = [
        "看到一个有趣的科技新闻视频",
        "朋友分享了一篇美食推荐文章",
        "热门话题讨论：人工智能的未来",
        "看到一个感人的故事视频",
        "发现一个实用的生活小技巧",
        "音乐推荐：最新流行歌曲",
        "看到一条有争议的社会新闻",
        "朋友发布了旅行照片",
        "发现一个有趣的梗图",
        "看到一篇深度技术文章",
    ]
    
    # 4. 运行模拟
    print(f"\n{'='*60}")
    print(f"🚀 开始模拟 {len(events)} 轮社交行为")
    print(f"{'='*60}")
    
    results = []
    for event in events:
        result = await agent.perform_action(event, behaviors)
        results.append(result)
        
        # 等待一小段时间，避免API限流
        await asyncio.sleep(0.5)
    
    # 5. 显示统计信息
    stats = wm.get_statistics()
    print(f"\n{'='*60}")
    print(f"📊 模拟统计")
    print(f"{'='*60}")
    print(f"总轮次: {stats['rounds_completed']}")
    print(f"水印动作数: {stats['watermarked_actions']}")
    print(f"嵌入比特数: {stats['bits_embedded']}")
    print(f"当前比特索引: {stats['current_bit_index']}")
    print(f"比特流长度: {stats['bit_stream_length']}")
    print(f"循环次数: {stats.get('cycles', 0)}")
    
    # 6. 提取水印
    print(f"\n{'='*60}")
    print(f"🔍 从日志中提取水印")
    print(f"{'='*60}")
    
    extracted_bits, extract_stats = wm.extract_watermark_from_log()
    
    print(f"\n✅ 提取完成:")
    print(f"  - 提取的比特流: {extracted_bits} ({len(extracted_bits)} bits)")
    print(f"  - 处理的动作数: {extract_stats.get('actions_processed', 0)}")
    print(f"  - 成功提取数: {extract_stats.get('successful_extractions', 0)}")
    
    # 显示连续校验信息
    num_messages = extract_stats.get('num_messages', 0)
    complete_messages = extract_stats.get('complete_messages', 0)
    partial_bits = extract_stats.get('partial_bits', 0)
    
    if num_messages > 0:
        print(f"\n📦 连续校验信息:")
        print(f"  - 完整消息数: {complete_messages}")
        if partial_bits > 0:
            print(f"  - 部分消息位: {partial_bits} bits")
        print(f"  - 总消息数: {num_messages}")
        
        failed_validations = extract_stats.get('failed_validations', 0)
        total_corrections = extract_stats.get('total_corrections', 0)
        
        print(f"  - 验证通过: {num_messages - failed_validations}/{num_messages}")
        if failed_validations > 0:
            print(f"  - ⚠️ 验证失败: {failed_validations}")
        if total_corrections > 0:
            print(f"  - ✓ 纠错次数: {total_corrections}")
    
    decoded_payload = extract_stats.get('decoded_payload', '')
    if decoded_payload:
        print(f"\n  - 解码的载荷: {decoded_payload} ({len(decoded_payload)} bits)")
        print(f"  - 验证状态: {'✅ 通过' if extract_stats.get('valid') else '❌ 失败'}")
    
    if extract_stats.get('error'):
        print(f"  - ⚠️ 提取错误: {extract_stats['error']}")
    
    # 7. 验证结果  
    print(f"\n{'='*60}")
    print(f"🔍 水印验证结果")
    print(f"{'='*60}")
    
    decoded_payload = extract_stats.get('decoded_payload', '')
    num_messages = extract_stats.get('num_messages', 0)
    complete_messages = extract_stats.get('complete_messages', 0)
    
    # 原始payload（8-bit，不含ECC）
    original_payload = payload  # "11001101"
    
    # 检查是否是循环嵌入 - 按照原始代码的逻辑验证
    if num_messages > 0:
        print(f"\n💫 检测到循环嵌入:")
        print(f"  - 核心payload: {original_payload} ({len(original_payload)} bits)")
        print(f"  - 编码后消息: {wm.bit_stream} ({len(wm.bit_stream)} bits, 含ECC)")
        print(f"  - 解码后长度: {len(decoded_payload)} bits")
        
        # 只验证完整的payload倍数部分（忽略余数）
        payload_len = len(original_payload)
        num_complete_payloads = len(decoded_payload) // payload_len
        
        print(f"  - 完整payload数: {num_complete_payloads}")
        
        if num_complete_payloads > 0:
            all_match = True
            
            for i in range(num_complete_payloads):
                start = i * payload_len
                end = start + payload_len
                segment = decoded_payload[start:end]
                
                # 对于循环嵌入，每个payload段都应该匹配原始payload
                matches = sum(1 for j in range(len(segment)) if segment[j] == original_payload[j])
                match_rate = matches / len(segment) * 100 if len(segment) > 0 else 0
                
                status = "✅" if match_rate == 100 else "❌"
                print(f"  Payload循环 {i+1}: {status} 匹配度 {match_rate:.1f}%")
                
                if match_rate < 100:
                    all_match = False
                    print(f"    期望: {original_payload}")
                    print(f"    实际: {segment}")
            
            # 显示余数信息（但不验证）
            remainder = len(decoded_payload) % payload_len
            if remainder > 0:
                print(f"  ⚠️ 余数部分: {remainder} bits (不验证)")
            
            if all_match:
                print(f"\n🎉 成功! 所有 {num_complete_payloads} 个完整payload都匹配!")
                print(f"✓ 水印嵌入和提取流程验证通过")
            else:
                print(f"\n⚠️ 部分payload不匹配，可能存在以下原因:")
                print(f"  - PRG随机性差异")
                print(f"  - 上下文密钥不一致")
                print(f"  - 解码参数不同步")
    
    if extract_stats.get('error'):
        error_msg = extract_stats.get('error')
        if 'Failed' in error_msg and 'validations' in error_msg:
            print(f"\n⚠️ 校验警告: {error_msg}")
            print(f"  说明: 部分消息块未通过校验，可能存在比特错误")
        elif 'partial' in error_msg.lower() or '部分' in error_msg:
            print(f"\n⚠️ 部分提取: {error_msg}")
            print(f"\n📊 部分验证:")
            print(f"  - 提取长度: {len(extracted_bits)}/{len(wm.bit_stream)} bits ({len(extracted_bits)/len(wm.bit_stream)*100:.1f}%)")
            print(f"  - 期望比特流: {wm.bit_stream}")
            print(f"  - 实际比特流: {extracted_bits}")
            
            # 计算前缀匹配度
            min_len = min(len(extracted_bits), len(wm.bit_stream))
            if min_len > 0:
                matching_bits = sum(1 for i in range(min_len) if extracted_bits[i] == wm.bit_stream[i])
                match_rate = matching_bits / min_len * 100
                print(f"\n✅ 前 {min_len} 位匹配度: {matching_bits}/{min_len} ({match_rate:.1f}%)")
                
                if match_rate >= 80:
                    print(f"🎉 匹配度 >= 80%，水印嵌入基本成功!")
                elif match_rate >= 60:
                    print(f"⚠️ 匹配度 >= 60%，部分成功，建议增加轮次")
                else:
                    print(f"❌ 匹配度 < 60%，可能存在问题")
            
            # 部分载荷验证
            if decoded_payload:
                print(f"\n📝 载荷验证:")
                print(f"  - 原始载荷: {payload}")
                print(f"  - 解码载荷: {decoded_payload}")
                
                # 计算载荷匹配度
                min_payload_len = min(len(decoded_payload), len(payload))
                if min_payload_len > 0:
                    matching_payload = sum(1 for i in range(min_payload_len) if decoded_payload[i] == payload[i])
                    payload_match = matching_payload / min_payload_len * 100
                    print(f"  - 载荷匹配度: {matching_payload}/{min_payload_len} ({payload_match:.1f}%)")
                    
                    if payload_match >= 80:
                        print(f"  ✅ 载荷匹配度良好!")
        else:
            print(f"❌ 提取错误: {error_msg}")
    else:
        # 完整提取的情况
        if extracted_bits == wm.bit_stream:
            print(f"🎉 完美匹配! 提取的比特流与编码后的比特流完全一致!")
            print(f"  - 比特流: {extracted_bits}")
        else:
            print(f"⚠️ 比特流不完全一致")
            print(f"  - 期望: {wm.bit_stream}")
            print(f"  - 实际: {extracted_bits}")
            
            # 计算匹配度
            min_len = min(len(extracted_bits), len(wm.bit_stream))
            if min_len > 0:
                matching = sum(1 for i in range(min_len) if extracted_bits[i] == wm.bit_stream[i])
                print(f"  - 匹配度: {matching}/{min_len} ({matching/min_len*100:.1f}%)")
        
        if decoded_payload == payload:
            print(f"🎉 载荷验证成功! 解码的载荷与原始载荷完全一致!")
            print(f"  - 载荷: {decoded_payload}")
        elif decoded_payload:
            print(f"⚠️ 载荷不一致")
            print(f"  - 原始载荷: {payload}")
            print(f"  - 解码载荷: {decoded_payload}")
            
            # 计算载荷匹配度
            min_len = min(len(decoded_payload), len(payload))
            if min_len > 0:
                matching = sum(1 for i in range(min_len) if decoded_payload[i] == payload[i])
                print(f"  - 匹配度: {matching}/{min_len} ({matching/min_len*100:.1f}%)")
    
    print(f"\n{'='*60}")
    print(f"✨ 演示完成!")
    print(f"{'='*60}")
    print(f"日志文件保存在: {wm.log_file}")
    print(f"您可以查看日志文件了解详细的水印嵌入过程")
    
    return results, stats, extract_stats


if __name__ == "__main__":
    print("\n" + "="*60)
    print("⚠️  注意: 这个演示需要访问 DeepSeek API")
    print("="*60)
    print(f"API Key: {DEEPSEEK_API_KEY[:20]}...")
    print(f"Base URL: {DEEPSEEK_BASE_URL}")
    print(f"Model: {DEEPSEEK_MODEL}")
    print("="*60)
    
    confirm = input("\n是否继续运行演示? (y/n): ")
    if confirm.lower() != 'y':
        print("演示已取消")
        sys.exit(0)
    
    # 运行异步模拟
    asyncio.run(run_simulation())
