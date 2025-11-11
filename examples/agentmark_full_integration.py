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
OASIS AgentMark Integration Example - Full Implementation

This example demonstrates the complete integration of AgentMark watermarking
into OASIS social simulation platform.

Features:
- Differential watermark embedding
- Error correction codes (Parity)
- Context-based key generation  
- Automatic logging and extraction
- Statistics and validation
"""

import asyncio
import os
import sys

# Add parent directory to path to import oasis module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

import oasis
from oasis import (ActionType, AgentGraph, LLMAction, SocialAgent, UserInfo)
from oasis.watermark import WatermarkManager


async def example_full_watermark_integration():
    """
    Complete AgentMark Integration Example
    
    This demonstrates how to use the WatermarkManager with OASIS agents
    to embed secret messages into agent behaviors.
    """
    print("=" * 80)
    print("OASIS + AgentMark: Complete Integration Example")
    print("=" * 80)
    
    # ==================== Step 1: Initialize Watermark Manager ====================
    print("\n📋 Step 1: Initializing Watermark Manager...")
    
    watermark_config = {
        "payload_bit_length": 8,
        "ecc_method": "parity",  # Use parity check for error detection
        "embedding_strategy": "cyclic"  # Cycle through message
    }
    
    # Custom message to embed
    payload = "11001101"  # 8-bit payload (will become 9-bit with parity)
    
    watermark_manager = WatermarkManager(
        enabled=True,
        mode="full",  # Use full differential watermark mode
        config=watermark_config,
        bit_stream=payload,
        log_dir="./log"
    )
    
    print(f"✅ WatermarkManager initialized")
    print(f"   Payload: {payload}")
    print(f"   Bit stream length: {len(watermark_manager.bit_stream)}")
    print(f"   ECC method: {watermark_config['ecc_method']}")
    print(f"   Log file: {watermark_manager.log_file}")
    
    # ==================== Step 2: Create LLM Model ====================
    print("\n📋 Step 2: Creating LLM Model...")
    
    openai_model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )
    
    print(f"✅ Model created: GPT-4O-MINI")
    
    # ==================== Step 3: Define Available Actions ====================
    print("\n📋 Step 3: Defining Available Actions...")
    
    available_actions = [
        ActionType.LIKE_POST,
        ActionType.CREATE_POST,
        ActionType.CREATE_COMMENT,
        ActionType.FOLLOW,
        ActionType.REFRESH,
    ]
    
    print(f"✅ Available actions: {[a.value for a in available_actions]}")
    
    # ==================== Step 4: Create Agent Graph ====================
    print("\n📋 Step 4: Creating Agent Graph...")
    
    agent_graph = AgentGraph()
    
    # ==================== Step 5: Create Agents with Watermark ====================
    print("\n📋 Step 5: Creating Watermarked Agents...")
    
    agents = []
    for i in range(3):
        agent = SocialAgent(
            agent_id=i,
            user_info=UserInfo(
                user_name=f"agent_{i}",
                name=f"Agent {i}",
                description=f"Social agent {i} with AgentMark watermark enabled",
                profile=None,
                recsys_type="reddit",
            ),
            agent_graph=agent_graph,
            model=openai_model,
            available_actions=available_actions,
            # 🎯 KEY INTEGRATION POINT: Pass watermark manager
            watermark_manager=watermark_manager,
        )
        agent_graph.add_agent(agent)
        agents.append(agent)
        print(f"   ✅ Created Agent {i} with watermark")
    
    # ==================== Step 6: Setup Environment ====================
    print("\n📋 Step 6: Setting up OASIS Environment...")
    
    db_path = "./oasis_agentmark_integration.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    env = oasis.make(
        agent_graph=agent_graph,
        platform=oasis.DefaultPlatformType.REDDIT,
        database_path=db_path,
    )
    
    await env.reset()
    print(f"✅ Environment initialized: {db_path}")
    
    # ==================== Step 7: Run Simulation ====================
    print("\n" + "=" * 80)
    print("🎬 Running Simulation with Watermark Embedding...")
    print("=" * 80)
    
    num_rounds = 5
    
    for round_num in range(num_rounds):
        print(f"\n📍 Round {round_num + 1}/{num_rounds}")
        print("-" * 80)
        
        # All agents take LLM-driven actions
        # Watermark is automatically embedded during action selection
        all_agents_actions = {
            agent: LLMAction()
            for agent in agents
        }
        
        await env.step(all_agents_actions)
        
        # Show watermark statistics after each round
        stats = watermark_manager.get_statistics()
        print(f"   Bits embedded: {stats['current_bit_index']}/{stats['bit_stream_length']}")
        print(f"   Bits remaining: {stats['bits_remaining']}")
        print(f"   Watermarked actions: {stats['watermarked_actions']}")
        
        # Update statistics
        watermark_manager.stats["rounds_completed"] += 1
    
    # ==================== Step 8: Show Results ====================
    print("\n" + "=" * 80)
    print("📊 Simulation Complete - Statistics")
    print("=" * 80)
    
    final_stats = watermark_manager.get_statistics()
    print(f"✅ Total rounds: {final_stats['rounds_completed']}")
    print(f"✅ Total watermarked actions: {final_stats['watermarked_actions']}")
    print(f"✅ Total bits embedded: {final_stats['bits_embedded']}")
    print(f"✅ Database: {db_path}")
    print(f"✅ Watermark log: {final_stats['log_file']}")
    
    # ==================== Step 9: Extract and Verify Watermark ====================
    print("\n" + "=" * 80)
    print("🔍 Extracting and Verifying Watermark...")
    print("=" * 80)
    
    extracted_bits, extraction_stats = watermark_manager.extract_watermark_from_log()
    
    print(f"📋 Extraction Results:")
    print(f"   Rounds parsed: {extraction_stats['rounds_parsed']}")
    print(f"   Extracted bit stream: {extraction_stats['extracted_bit_stream']}")
    print(f"   Decoded payload: {extraction_stats['decoded_payload']}")
    print(f"   Valid: {extraction_stats['valid']}")
    print(f"   Corrected: {extraction_stats['corrected']}")
    print(f"   ECC method: {extraction_stats['ecc_method']}")
    
    # Verify payload matches original
    print(f"\n🔍 Verification:")
    print(f"   Original payload: {payload}")
    print(f"   Decoded payload:  {extraction_stats['decoded_payload']}")
    
    if extraction_stats['decoded_payload'] == payload and extraction_stats['valid']:
        print(f"   ✅ WATERMARK VERIFIED SUCCESSFULLY!")
        print(f"   🎉 AgentMark integration is working correctly!")
    else:
        print(f"   ❌ Verification failed")
        if not extraction_stats['valid']:
            print(f"   ⚠️  Parity check failed - data may be corrupted")
    
    # ==================== Cleanup ====================
    await env.close()
    
    print("\n" + "=" * 80)
    print("✅ Example completed successfully!")
    print("=" * 80)
    print(f"\n📖 Next steps:")
    print(f"   1. Check the watermark log: {final_stats['log_file']}")
    print(f"   2. Inspect the database: {db_path}")
    print(f"   3. Try different payloads and ECC methods")
    print(f"   4. Integrate into your own OASIS applications")


async def example_simple_watermark():
    """
    Simplified example showing the minimal integration
    """
    print("\n\n" + "=" * 80)
    print("Simplified Example: Minimal Watermark Integration")
    print("=" * 80)
    
    # Create watermark manager
    wm = WatermarkManager(enabled=True)
    
    # Simulate behavior sampling with watermark
    probabilities = {
        "like_post": 0.3,
        "create_post": 0.2,
        "create_comment": 0.5
    }
    
    print(f"\n📋 Original probabilities:")
    for action, prob in probabilities.items():
        print(f"   {action}: {prob}")
    
    # Sample with watermark
    selected, targets, bits, ctx = wm.sample_behavior_watermark(
        probabilities=probabilities,
        round_num=0,
        context_for_key=""
    )
    
    print(f"\n✅ Watermark sampling result:")
    print(f"   Selected behavior: {selected}")
    print(f"   Target list: {targets}")
    print(f"   Bits embedded: {bits}")
    print(f"   Context used: '{ctx}' (empty for first round)")
    
    # Show statistics
    stats = wm.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"   Bit index: {stats['current_bit_index']}")
    print(f"   Bits remaining: {stats['bits_remaining']}")


async def main():
    """Run all examples"""
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║        OASIS + AgentMark: Complete Integration Examples             ║
    ║                                                                      ║
    ║  This demo shows the full integration of AgentMark watermarking     ║
    ║  technology into OASIS social simulation platform.                  ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Run full integration example
        await example_full_watermark_integration()
        
        # Run simplified example
        await example_simple_watermark()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
    
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                      All Examples Completed!                         ║
    ║                                                                      ║
    ║  📖 Documentation:                                                   ║
    ║     - Integration Guide: docs/AgentMark集成完成报告.md               ║
    ║     - Integration Strategy: docs/AgentMark集成策略总结.md            ║
    ║                                                                      ║
    ║  🔧 Key Features Demonstrated:                                       ║
    ║     ✅ Differential watermark embedding                              ║
    ║     ✅ Error correction codes (Parity)                               ║
    ║     ✅ Context-based key generation                                  ║
    ║     ✅ Automatic logging and extraction                              ║
    ║     ✅ Statistics and validation                                     ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    asyncio.run(main())
