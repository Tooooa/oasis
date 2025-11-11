# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
"""
OASIS Watermark Integration Example

This example demonstrates how to integrate agent watermarking into OASIS.
It shows both lightweight (simple) and full (advanced) integration modes.
"""

import asyncio
import os
import sys
from pathlib import Path

# 修复路径：从 examples_watermark/02_advanced/ 回到项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

import oasis
from oasis import (ActionType, AgentGraph, LLMAction, ManualAction,
                   SocialAgent, UserInfo)
from oasis.watermark import WatermarkManager


async def example_lightweight_watermark():
    """
    Example 1: Lightweight Watermark Integration
    
    This mode only requires minimal changes - the WatermarkManager
    automatically tracks and logs watermarked actions.
    """
    print("=" * 70)
    print("Example 1: Lightweight Watermark Integration")
    print("=" * 70)
    
    # Step 1: Initialize watermark manager
    watermark_manager = WatermarkManager(
        enabled=True,
        mode="lightweight"  # Simple probability modification
    )
    
    print(f"✅ Watermark Manager initialized")
    print(f"   - Bit stream length: {len(watermark_manager.bit_stream)}")
    print(f"   - Delta: {watermark_manager.delta}")
    print(f"   - Gamma: {watermark_manager.gamma}")
    
    # Step 2: Create LLM model
    openai_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )
    
    # Step 3: Define available actions
    available_actions = [
        ActionType.LIKE_POST,
        ActionType.CREATE_POST,
        ActionType.CREATE_COMMENT,
        ActionType.FOLLOW,
        ActionType.REFRESH,
    ]
    
    # Step 4: Create agent graph
    agent_graph = AgentGraph()
    
    # Step 5: Create agents with watermark manager
    agents = []
    for i in range(3):  # Create 3 agents
        agent = SocialAgent(
            agent_id=i,
            user_info=UserInfo(
                user_name=f"agent_{i}",
                name=f"Agent {i}",
                description=f"Test agent {i} with watermark",
                profile=None,
                recsys_type="reddit",
            ),
            agent_graph=agent_graph,
            model=openai_model,
            available_actions=available_actions,
            watermark_manager=watermark_manager,  # 🎯 Key integration point
        )
        agent_graph.add_agent(agent)
        agents.append(agent)
        print(f"✅ Created Agent {i} with watermark enabled")
    
    # Step 6: Setup environment
    project_root = Path(__file__).parent.parent.parent
    db_path = str(project_root / "outputs" / "databases" / "current" / "test_watermark_lightweight.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    env = oasis.make(
        agent_graph=agent_graph,
        platform=oasis.DefaultPlatformType.REDDIT,
        database_path=db_path,
    )
    
    await env.reset()
    print("✅ Environment initialized")
    
    # Step 7: Run simulation with watermarked actions
    print("\n" + "-" * 70)
    print("Running simulation (5 rounds)...")
    print("-" * 70)
    
    for round_num in range(5):
        print(f"\n📍 Round {round_num + 1}/5")
        
        # Let all agents take LLM-driven actions
        all_agents_actions = {
            agent: LLMAction()
            for agent in agents
        }
        
        await env.step(all_agents_actions)
        
        # Print watermark statistics
        stats = watermark_manager.get_statistics()
        print(f"   Bits embedded: {stats['current_bit_index']}/{stats['bit_stream_length']}")
        print(f"   Bits remaining: {stats['bits_remaining']}")
    
    # Step 8: Show results
    print("\n" + "=" * 70)
    print("Simulation Complete!")
    print("=" * 70)
    
    final_stats = watermark_manager.get_statistics()
    print(f"Total bits embedded: {final_stats['current_bit_index']}")
    print(f"Database saved to: {db_path}")
    print(f"Watermark log saved to: ./log/watermark-*.log")
    
    await env.close()
    print("\n✅ Example completed successfully!")


async def example_manual_watermark():
    """
    Example 2: Manual Watermark with Predefined Actions
    
    This example shows how to manually control watermarked actions.
    """
    print("\n\n" + "=" * 70)
    print("Example 2: Manual Watermark with Predefined Actions")
    print("=" * 70)
    
    # Initialize watermark manager
    watermark_manager = WatermarkManager(enabled=True, mode="lightweight")
    
    # Create simple agent
    openai_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )
    
    agent_graph = AgentGraph()
    agent = SocialAgent(
        agent_id=0,
        user_info=UserInfo(
            user_name="manual_agent",
            name="Manual Agent",
            description="Agent with manual watermarked actions",
            profile=None,
            recsys_type="reddit",
        ),
        agent_graph=agent_graph,
        model=openai_model,
        available_actions=[ActionType.CREATE_POST, ActionType.LIKE_POST],
        watermark_manager=watermark_manager,
    )
    agent_graph.add_agent(agent)
    
    # Setup environment
    project_root = Path(__file__).parent.parent.parent
    db_path = str(project_root / "outputs" / "databases" / "current" / "test_watermark_manual.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    
    env = oasis.make(
        agent_graph=agent_graph,
        platform=oasis.DefaultPlatformType.REDDIT,
        database_path=db_path,
    )
    
    await env.reset()
    
    # Manually define a sequence of actions with watermark tracking
    print("\nExecuting manual action sequence with watermark tracking...")
    
    actions_sequence = [
        ("CREATE_POST", "Hello, this is a watermarked post!"),
        ("CREATE_POST", "Another watermarked message!"),
        ("CREATE_POST", "Testing watermark embedding..."),
    ]
    
    for i, (action_type, content) in enumerate(actions_sequence, 1):
        print(f"\n📍 Action {i}/{len(actions_sequence)}: {action_type}")
        
        # Get next watermark bit
        bit = watermark_manager.get_next_bit()
        print(f"   Embedding bit: {bit}")
        
        # Execute action
        action = {
            agent: ManualAction(
                action_type=ActionType.CREATE_POST,
                action_args={"content": content}
            )
        }
        
        await env.step(action)
        
        # Log watermarked action
        watermark_manager.log_action(
            agent_id=agent.social_agent_id,
            action_name=action_type,
            action_args={"content": content},
            bit=bit
        )
        
        print(f"   ✅ Action logged with watermark bit '{bit}'")
    
    print("\n" + "=" * 70)
    print("Manual watermark example completed!")
    print("=" * 70)
    
    stats = watermark_manager.get_statistics()
    print(f"Total bits embedded: {stats['current_bit_index']}")
    print(f"Database: {db_path}")
    
    await env.close()


async def example_watermark_extraction():
    """
    Example 3: Watermark Extraction (Placeholder)
    
    This shows how you would extract watermarks from logs.
    """
    print("\n\n" + "=" * 70)
    print("Example 3: Watermark Extraction (Placeholder)")
    print("=" * 70)
    
    watermark_manager = WatermarkManager(enabled=True)
    
    # Find latest watermark log
    project_root = Path(__file__).parent.parent.parent
    log_dir = str(project_root / "outputs" / "logs" / "watermark" / "2025-11")
    if os.path.exists(log_dir):
        log_files = [
            f for f in os.listdir(log_dir) 
            if f.startswith("watermark-") and f.endswith(".log")
        ]
        
        if log_files:
            latest_log = max(
                log_files,
                key=lambda f: os.path.getmtime(os.path.join(log_dir, f))
            )
            log_path = os.path.join(log_dir, latest_log)
            
            print(f"📄 Extracting watermark from: {log_path}")
            
            # TODO: Implement extraction using your log_parser module
            extracted_bits, stats = watermark_manager.extract_watermark_from_log(
                log_path
            )
            
            print(f"Extracted bits: {extracted_bits}")
            print(f"Statistics: {stats}")
        else:
            print("⚠️  No watermark log files found")
    else:
        print("⚠️  Log directory not found")


async def main():
    """Run all examples."""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║           OASIS Agent Watermark Integration Examples            ║
    ║                                                                  ║
    ║  This demo shows how to integrate agent watermarking into       ║
    ║  OASIS platform for steganographic message embedding.           ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Run examples
    try:
        # Example 1: Lightweight integration
        await example_lightweight_watermark()
        
        # Example 2: Manual watermark control
        await example_manual_watermark()
        
        # Example 3: Watermark extraction
        await example_watermark_extraction()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
    
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                      Examples Completed!                         ║
    ║                                                                  ║
    ║  Next steps:                                                     ║
    ║  1. Copy your watermark modules to oasis/watermark/modules/     ║
    ║  2. Update config.json with your settings                       ║
    ║  3. Implement full encoder/decoder integration                  ║
    ║  4. Run your experiments!                                       ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    asyncio.run(main())
