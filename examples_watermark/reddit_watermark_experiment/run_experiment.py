# -*- coding: utf-8 -*-
"""
Reddit 水印 Agent 实验主脚本
r/TechFuture 子社区模拟

实验目标：
- 初始化 10 个 Agent（5 水印组 + 5 对照组）
- 在 Reddit 环境中运行 10 个时间步
- 计算 5 个评估维度指标
- 生成雷达图对比

使用方法：
    cd oasis
    python examples/reddit_watermark_experiment/run_experiment.py
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入 OASIS 模块
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig

import oasis
from oasis import ActionType, AgentGraph, LLMAction, ManualAction, SocialAgent, UserInfo
from oasis.watermark import WatermarkManager

# 导入本地模块
from config import EXPERIMENT_CONFIG, API_CONFIG, WATERMARK_CONFIG
from personas import PERSONAS, get_persona_by_index, get_agent_name
from seed_data import SEED_POSTS
from metrics import compute_all_metrics
from visualization import plot_radar_chart, plot_comparison_bar_chart, generate_report


class RedditWatermarkExperiment:
    """Reddit 水印 Agent 实验类"""
    
    def __init__(self):
        self.config = EXPERIMENT_CONFIG
        self.api_config = API_CONFIG
        self.watermark_config = WATERMARK_CONFIG
        
        self.watermark_agents: List[SocialAgent] = []
        self.control_agents: List[SocialAgent] = []
        self.all_agents: List[SocialAgent] = []
        
        self.agent_graph = None
        self.env = None
        self.model = None
        
        # 行为记录
        self.action_history: Dict[int, List[Dict]] = {}  # agent_id -> actions
        self.agent_posts: Dict[int, List[int]] = {}  # agent_id -> post_ids
        
        # 输出目录
        self.output_dir = PROJECT_ROOT / "outputs" / "reddit_exp" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def setup_api(self):
        """配置 API 和模型"""
        print("\n" + "=" * 70)
        print("📋 配置 LLM API...")
        print("=" * 70)
        
        provider = self.api_config.get("provider", "deepseek")
        
        if provider == "deepseek":
            deepseek_cfg = self.api_config.get("deepseek", {})
            api_key = deepseek_cfg.get("api_key") or os.getenv("DEEPSEEK_API_KEY", "")
            base_url = deepseek_cfg.get("base_url", "https://api.deepseek.com")
            model_name = deepseek_cfg.get("model", "deepseek-chat")
            
            os.environ["OPENAI_API_KEY"] = api_key
            os.environ["OPENAI_API_BASE"] = base_url
            
            model_config = ChatGPTConfig(temperature=0.7, max_tokens=1000)
            self.model = ModelFactory.create(
                model_platform=ModelPlatformType.OPENAI,
                model_type=model_name,
                model_config_dict=model_config.as_dict(),
                url=base_url,
                api_key=api_key,
            )
            print(f"✅ DeepSeek API 已配置: {model_name}")
        else:
            openai_cfg = self.api_config.get("openai", {})
            api_key = openai_cfg.get("api_key") or os.getenv("OPENAI_API_KEY", "")
            model_name = openai_cfg.get("model", "gpt-4o-mini")
            
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
            
            model_config = ChatGPTConfig(temperature=0.7, max_tokens=1000)
            self.model = ModelFactory.create(
                model_platform=ModelPlatformType.OPENAI,
                model_type=model_name,
                model_config_dict=model_config.as_dict(),
            )
            print(f"✅ OpenAI API 已配置: {model_name}")
    
    def create_agents(self):
        """创建 10 个 Agent（5 水印 + 5 对照）"""
        print("\n" + "=" * 70)
        print("📋 创建 Agent...")
        print("=" * 70)
        
        self.agent_graph = AgentGraph()
        available_actions = ActionType.get_default_reddit_actions()
        
        num_wm = self.config.get("num_watermark_agents", 5)
        num_ctrl = self.config.get("num_control_agents", 5)
        
        # ========== 创建水印组 Agent ==========
        print("\n🔐 水印组 (Group A):")
        for i in range(num_wm):
            persona = get_persona_by_index(i)
            agent_name = get_agent_name(i, is_watermark=True)
            
            # 水印组：不传 watermark_manager，让 SocialAgent 自动创建独立的
            agent = SocialAgent(
                agent_id=i,
                user_info=UserInfo(
                    user_name=f"wm_{persona['user_name']}",
                    name=agent_name,
                    description=persona['description'],
                    profile=persona['profile'],
                    recsys_type="reddit",
                ),
                agent_graph=self.agent_graph,
                model=self.model,
                available_actions=available_actions,
                # 不传 watermark_manager，自动创建
            )
            
            self.agent_graph.add_agent(agent)
            agent.agent_index = i
            agent.persona_name = persona['name']
            agent.is_watermark = True
            self.watermark_agents.append(agent)
            self.action_history[i] = []
            self.agent_posts[i] = []
            
            if hasattr(agent, 'watermark_manager') and agent.watermark_manager:
                expected_bits = format(i, '08b')
                print(f"   ✅ Agent {i} [{persona['name']}] - 水印启用 (agent_id={i}, bits={expected_bits})")
            else:
                print(f"   ⚠️ Agent {i} [{persona['name']}] - 水印未启用")
        
        # ========== 创建对照组 Agent ==========
        print("\n⚪ 对照组 (Group B):")
        for i in range(num_ctrl):
            agent_id = num_wm + i
            persona = get_persona_by_index(i)  # 使用相同人设
            agent_name = get_agent_name(agent_id, is_watermark=False)
            
            # 对照组：传入 disabled 的 watermark_manager
            disabled_wm = WatermarkManager(enabled=False)
            
            agent = SocialAgent(
                agent_id=agent_id,
                user_info=UserInfo(
                    user_name=f"ctrl_{persona['user_name']}",
                    name=agent_name,
                    description=persona['description'],
                    profile=persona['profile'],
                    recsys_type="reddit",
                ),
                agent_graph=self.agent_graph,
                model=self.model,
                available_actions=available_actions,
                watermark_manager=disabled_wm,  # 禁用水印
            )
            
            self.agent_graph.add_agent(agent)
            agent.agent_index = agent_id
            agent.persona_name = persona['name']
            agent.is_watermark = False
            self.control_agents.append(agent)
            self.action_history[agent_id] = []
            self.agent_posts[agent_id] = []
            
            print(f"   ⚪ Agent {agent_id} [{persona['name']}] - 无水印 (对照组)")
        
        self.all_agents = self.watermark_agents + self.control_agents
        print(f"\n✅ 共创建 {len(self.all_agents)} 个 Agent")
    
    async def setup_environment(self):
        """初始化 OASIS 环境"""
        print("\n" + "=" * 70)
        print("📋 初始化 OASIS 环境...")
        print("=" * 70)
        
        db_path = self.config.get("db_path", str(self.output_dir / "simulation.db"))
        if os.path.exists(db_path):
            os.remove(db_path)
        
        self.env = oasis.make(
            agent_graph=self.agent_graph,
            platform=oasis.DefaultPlatformType.REDDIT,
            database_path=db_path,
        )
        await self.env.reset()
        print(f"✅ 环境初始化完成: {db_path}")
    
    async def seed_initial_content(self):
        """发布种子帖子和初始评论"""
        print("\n" + "=" * 70)
        print("📋 发布种子内容 (r/TechFuture)...")
        print("=" * 70)
        
        # 使用第一个Agent发布种子帖子
        seed_agent = self.all_agents[0]
        
        for idx, post_data in enumerate(SEED_POSTS, start=1):
            content = f"【{post_data['title']}】\n\n{post_data['content']}"
            
            action = {
                seed_agent: ManualAction(
                    action_type=ActionType.CREATE_POST,
                    action_args={"content": content}
                )
            }
            await self.env.step(action)
            print(f"   ✅ 种子帖 {idx}: {post_data['title'][:30]}...")
            
            # 发布初始评论（使用不同Agent）
            for comment_idx, comment in enumerate(post_data.get("initial_comments", [])):
                comment_agent = self.all_agents[(idx + comment_idx) % len(self.all_agents)]
                comment_action = {
                    comment_agent: ManualAction(
                        action_type=ActionType.CREATE_COMMENT,
                        action_args={"post_id": idx, "content": comment["content"]}
                    )
                }
                await self.env.step(comment_action)
            
            await asyncio.sleep(0.2)
        
        print(f"✅ 种子内容发布完成: {len(SEED_POSTS)} 帖子")
    
    async def run_simulation(self):
        """运行模拟"""
        num_steps = self.config.get("num_steps", 10)
        
        print("\n" + "=" * 70)
        print(f"🎬 开始模拟 {num_steps} 个时间步...")
        print("=" * 70)
        
        start_time = time.time()
        
        for step in range(num_steps):
            print(f"\n📍 Step {step + 1}/{num_steps}")
            step_start = time.time()
            
            # 所有 Agent 执行 LLM 驱动的行为
            all_actions = {agent: LLMAction() for agent in self.all_agents}
            
            try:
                await self.env.step(all_actions)
                step_time = time.time() - step_start
                
                # 显示进度
                print(f"   ✅ 完成 (耗时: {step_time:.1f}s)")
                
                # 显示水印组统计
                for agent in self.watermark_agents:
                    if hasattr(agent, 'watermark_manager') and agent.watermark_manager:
                        stats = agent.watermark_manager.get_statistics()
                        print(f"      WM-{agent.agent_index}: {stats['current_bit_index']}/{stats['bit_stream_length']} bits")
                
            except Exception as e:
                print(f"   ❌ 错误: {e}")
                import traceback
                traceback.print_exc()
        
        total_time = time.time() - start_time
        print(f"\n✅ 模拟完成: 总耗时 {total_time:.1f}s ({total_time/60:.1f} 分钟)")
    
    def collect_actions_from_db(self):
        """从数据库中收集所有Agent的行为数据"""
        import sqlite3
        
        db_path = self.config.get("db_path", str(self.output_dir / "simulation.db"))
        
        print("\n" + "=" * 70)
        print("📊 从数据库收集行为数据...")
        print("=" * 70)
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取所有帖子
            cursor.execute("SELECT * FROM post")
            posts = cursor.fetchall()
            print(f"   帖子总数: {len(posts)}")
            
            # 获取所有评论
            cursor.execute("SELECT * FROM comment")
            comments = cursor.fetchall()
            print(f"   评论总数: {len(comments)}")
            
            # 获取所有点赞/踩
            cursor.execute("SELECT * FROM like")
            likes = cursor.fetchall()
            print(f"   点赞/踩总数: {len(likes)}")
            
            # 为每个Agent收集行为
            for agent in self.all_agents:
                agent_id = agent.agent_index
                user_id = agent_id + 1  # 数据库中user_id从1开始
                
                actions = []
                agent_post_ids = []
                
                # 收集发帖行为
                for post in posts:
                    if post['user_id'] == user_id:
                        actions.append({
                            "action_type": "CREATE_POST",
                            "agent_id": agent_id,
                            "post_id": post['post_id'],
                            "content": post['content'][:100] if post['content'] else "",
                            "created_at": post['created_at']
                        })
                        agent_post_ids.append(post['post_id'])
                
                # 收集评论行为
                for comment in comments:
                    if comment['user_id'] == user_id:
                        actions.append({
                            "action_type": "CREATE_COMMENT",
                            "agent_id": agent_id,
                            "post_id": comment['post_id'],
                            "content": comment['content'][:100] if comment['content'] else "",
                            "created_at": comment['created_at']
                        })
                
                # 收集点赞/踩行为
                for like in likes:
                    if like['user_id'] == user_id:
                        action_type = "LIKE_POST" if like.get('like_type', 1) == 1 else "DISLIKE_POST"
                        actions.append({
                            "action_type": action_type,
                            "agent_id": agent_id,
                            "post_id": like['post_id'],
                            "created_at": like['created_at']
                        })
                
                self.action_history[agent_id] = actions
                self.agent_posts[agent_id] = agent_post_ids
                
                print(f"   Agent {agent_id}: {len(actions)} 行为, {len(agent_post_ids)} 帖子")
            
            conn.close()
            print(f"✅ 行为数据收集完成")
            
        except Exception as e:
            print(f"⚠️ 数据库读取失败: {e}")
            import traceback
            traceback.print_exc()
    
    def extract_watermarks(self):
        """提取和验证水印"""
        print("\n" + "=" * 70)
        print("🔍 提取水印...")
        print("=" * 70)
        
        results = []
        
        for agent in self.watermark_agents:
            if not (hasattr(agent, 'watermark_manager') and agent.watermark_manager):
                continue
            
            wm = agent.watermark_manager
            extracted, stats = wm.extract_watermark_from_log()
            
            result = {
                "agent_id": agent.agent_index,
                "persona": agent.persona_name,
                "is_watermark": True,
                "original_bits": wm.bit_stream,
                "extracted_bits": extracted,
                "extraction_stats": stats,
                "actions": self.action_history.get(agent.agent_index, []),
                "posts": self.agent_posts.get(agent.agent_index, []),
                "persona_profile": PERSONAS[agent.agent_index % 5]['profile']
            }
            results.append(result)
            
            # 验证
            decoded = stats.get('decoded_payload', '')
            accuracy = stats.get('accuracy', 0)
            
            if decoded and len(decoded) >= 8:
                extracted_id = int(decoded[:8], 2)
                match = "✅" if extracted_id == agent.agent_index else "❌"
                print(f"   Agent {agent.agent_index} [{agent.persona_name}]: {match} 识别为 {extracted_id} (准确率: {accuracy:.1f}%)")
            else:
                print(f"   Agent {agent.agent_index} [{agent.persona_name}]: ⚠️ 提取不完整 ({len(extracted)} bits)")
        
        return results
    
    def collect_control_data(self) -> List[Dict]:
        """收集对照组数据"""
        results = []
        for agent in self.control_agents:
            result = {
                "agent_id": agent.agent_index,
                "persona": agent.persona_name,
                "is_watermark": False,
                "actions": self.action_history.get(agent.agent_index, []),
                "posts": self.agent_posts.get(agent.agent_index, []),
                "persona_profile": PERSONAS[agent.agent_index % 5]['profile']
            }
            results.append(result)
        return results
    
    def compute_metrics(self, watermark_data: List[Dict], control_data: List[Dict]) -> Dict:
        """计算评估指标"""
        print("\n" + "=" * 70)
        print("📊 计算评估指标...")
        print("=" * 70)
        
        all_actions = []
        for agent_id, actions in self.action_history.items():
            all_actions.extend(actions)
        
        metrics = compute_all_metrics(watermark_data, control_data, all_actions)
        
        print("\n水印组指标:")
        for k, v in metrics['watermark'].items():
            print(f"   {k}: {v:.3f}")
        
        print("\n对照组指标:")
        for k, v in metrics['control'].items():
            print(f"   {k}: {v:.3f}")
        
        return metrics
    
    def generate_visualizations(self, metrics: Dict):
        """生成可视化图表"""
        print("\n" + "=" * 70)
        print("📈 生成可视化...")
        print("=" * 70)
        
        output_dir = str(self.output_dir)
        
        # 生成雷达图
        radar_path = str(self.output_dir / "radar_chart.png")
        plot_radar_chart(
            metrics['watermark'],
            metrics['control'],
            title="r/TechFuture 水印Agent评估",
            save_path=radar_path
        )
        
        # 生成柱状图
        bar_path = str(self.output_dir / "bar_chart.png")
        plot_comparison_bar_chart(
            metrics['watermark'],
            metrics['control'],
            save_path=bar_path
        )
        
        # 保存指标数据
        metrics_path = self.output_dir / "metrics.json"
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        print(f"✅ 指标数据已保存: {metrics_path}")
    
    async def run(self):
        """运行完整实验"""
        print("\n" + "=" * 70)
        print("🚀 Reddit 水印 Agent 实验")
        print("   r/TechFuture 子社区模拟")
        print("=" * 70)
        print(f"   水印组: {self.config.get('num_watermark_agents', 5)} 个 Agent")
        print(f"   对照组: {self.config.get('num_control_agents', 5)} 个 Agent")
        print(f"   时间步: {self.config.get('num_steps', 10)} 步")
        print(f"   输出目录: {self.output_dir}")
        print("=" * 70)
        
        try:
            # 1. 配置 API
            self.setup_api()
            
            # 2. 创建 Agent
            self.create_agents()
            
            # 3. 初始化环境
            await self.setup_environment()
            
            # 4. 发布种子内容
            await self.seed_initial_content()
            
            # 5. 运行模拟
            await self.run_simulation()
            
            # 6. 从数据库收集行为数据
            self.collect_actions_from_db()
            
            # 7. 提取水印
            watermark_data = self.extract_watermarks()
            control_data = self.collect_control_data()
            
            # 8. 计算指标
            metrics = self.compute_metrics(watermark_data, control_data)
            
            # 8. 生成可视化
            self.generate_visualizations(metrics)
            
            # 9. 清理
            await self.env.close()
            
            print("\n" + "=" * 70)
            print("✨ 实验完成!")
            print("=" * 70)
            print(f"   输出目录: {self.output_dir}")
            print(f"   雷达图: {self.output_dir / 'radar_chart.png'}")
            print(f"   柱状图: {self.output_dir / 'bar_chart.png'}")
            print(f"   指标数据: {self.output_dir / 'metrics.json'}")
            print("=" * 70)
            
            return metrics
            
        except Exception as e:
            print(f"\n❌ 实验失败: {e}")
            import traceback
            traceback.print_exc()
            raise


async def main():
    """主函数"""
    experiment = RedditWatermarkExperiment()
    await experiment.run()


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║     Reddit 水印 Agent 实验                                       ║
    ║     r/TechFuture 子社区模拟                                      ║
    ║                                                                  ║
    ║     5 水印组 Agent + 5 对照组 Agent                              ║
    ║     评估维度: WR / PC / SC / SE / TD                             ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n\n❌ 运行失败: {e}")
        import traceback
        traceback.print_exc()
