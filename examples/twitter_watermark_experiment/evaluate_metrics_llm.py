# -*- coding: utf-8 -*-
"""
LLM-based Evaluation Script for Twitter Experiment
Evaluates agents on 5 dimensions using DeepSeek
"""

import os
import sys
import json
import sqlite3
import asyncio
import numpy as np
from pathlib import Path
from openai import AsyncOpenAI
from typing import List, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load Config
from config import API_CONFIG, EXPERIMENT_CONFIG

# Configuration
DEEPSEEK_API_KEY = API_CONFIG["deepseek"]["api_key"] or os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = API_CONFIG["deepseek"]["base_url"]
DEEPSEEK_MODEL = API_CONFIG["deepseek"]["model"]

# Determine DB Path (find the latest experiment output)
OUTPUT_BASE_DIR = PROJECT_ROOT / "outputs" / "twitter_exp"
# Find latest subdirectory
if OUTPUT_BASE_DIR.exists():
    latest_dir = max([d for d in OUTPUT_BASE_DIR.iterdir() if d.is_dir()], key=os.path.getmtime, default=None)
    if latest_dir:
        DATABASE_PATH = latest_dir / "simulation.db"
        OUTPUT_DIR = latest_dir
    else:
        print("❌ No experiment data found.")
        sys.exit(1)
else:
    print("❌ No experiment data found.")
    sys.exit(1)

class AgentEvaluator:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
        self.model = DEEPSEEK_MODEL

    def get_agents(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            # In OASIS, 'user' table stores agent info
            cursor.execute("SELECT * FROM user")
            agents = [dict(row) for row in cursor.fetchall()]
            return agents
        finally:
            conn.close()

    def get_agent_content(self, user_id: int, limit: int = 30) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        content_list = []
        try:
            cursor = conn.cursor()
            # Fetch Posts (Twitter uses post table for tweets, reposts, quotes)
            cursor.execute("SELECT content, quote_content FROM post WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
            posts = cursor.fetchall()
            
            for p in posts:
                text = p['content']
                if p['quote_content']:
                    text += f" [Quote: {p['quote_content']}]"
                if text:
                    content_list.append(text)
            
            return content_list
        finally:
            conn.close()

    async def evaluate_agent(self, agent: Dict[str, Any], content: List[str]) -> Dict[str, Any]:
        if not content:
            return {
                "user_id": agent.get('user_id'),
                "error": "No content"
            }

        content_str = "\n".join([f"- {c}" for c in content[:20]])
        profile = agent.get('bio', 'No profile available')
        name = agent.get('name', 'Unknown')

        prompt = f"""
请评估以下Twitter AI Agent的表现。基于其个人简介(Persona)和发布的推文(Tweets)，对以下五个维度进行打分（1-10分）。

Agent Name: {name}
Persona/Bio: {profile}

Recent Tweets:
{content_str}

评估维度 (Evaluation Metrics):
1. 逻辑连贯性 (Logical Coherence): 内容是否逻辑通顺？
2. 记忆准确性 (Memory Accuracy): 是否有前后矛盾？(如果没有足够上下文判断矛盾，给高分)
3. 人设稳定性 (Character Stability): 发言风格和内容是否符合其Profile/Bio描述？
4. 社会规范与常识 (Social Norms & Common Sense): 行为是否符合社交平台的一般规范？
5. 语言多样性 (Language Diversity): 词汇、Tag、Emoji的使用是否丰富自然？

请严格以JSON格式输出，不要包含Markdown formatting (```json ... ```)，直接输出JSON字符串:
{{
    "logic_score": <int 1-10>,
    "memory_score": <int 1-10>,
    "stability_score": <int 1-10>,
    "norms_score": <int 1-10>,
    "diversity_score": <int 1-10>,
    "reason": "<short summary>"
}}
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert social media agent evaluator."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            result_json = response.choices[0].message.content
            return json.loads(result_json)
        except Exception as e:
            print(f"Error evaluating agent {name}: {e}")
            return {"error": str(e)}

    async def run(self):
        print(f"📂 Reading Database: {self.db_path}")
        if not self.db_path.exists():
            print("❌ Database file not found.")
            return

        agents = self.get_agents()
        print(f"   Found {len(agents)} agents.")
        
        results = []
        
        # We need to distinguish Watermark vs Control based on ID or Name
        # In our script: Watermark = 0-4, Control = 5-9.
        # Agent ID in DB matches loop index (0-9).
        
        print("\n🚀 Starting Evaluation with DeepSeek...")
        
        for agent in agents:
            user_id = agent.get('user_id')
            name = agent.get('name')
            
            # Determine Group
            # ID 0-4 (Watermark), 5-9 (Control)
            # note: user_id might be 0-indexed or equal to agent_id
            group = "Watermark" if user_id <= 4 else "Control"
            
            print(f"   Evaluating Agent {user_id} ({name}) [{group}]...")
            
            content = self.get_agent_content(user_id)
            if not content:
                print("      ⚠️ No content found.")
                continue
                
            eval_result = await self.evaluate_agent(agent, content)
            
            if "error" not in eval_result:
                complete_result = {
                    "user_id": user_id,
                    "name": name,
                    "group": group,
                    "metrics": eval_result
                }
                results.append(complete_result)
                print(f"      ✅ Score: L={eval_result['logic_score']}, S={eval_result['stability_score']}")
            else:
                print(f"      ❌ Evaluation Failed: {eval_result['error']}")

        # Save Results
        output_file = OUTPUT_DIR / "evaluation_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f"\n✅ Evaluation Saved: {output_file}")
        
        return results, output_file

if __name__ == "__main__":
    evaluator = AgentEvaluator(DATABASE_PATH)
    asyncio.run(evaluator.run())
