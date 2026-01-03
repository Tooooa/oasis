
import os
import sys
import json
import sqlite3
import asyncio
from pathlib import Path
from openai import AsyncOpenAI
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_config(config_path: str = None) -> dict:
    """Load configuration file"""
    search_paths = [
        config_path,
        "./config.json",
        "../../config.json", # Since we are in examples/reddit_watermark_experiment
        "../config.json",
        str(Path(__file__).parent.parent.parent / "config.json"),
    ]
    
    for path in search_paths:
        if path and os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Config load failed: {e}")
    
    return {}

CONFIG = load_config()
DEEPSEEK_CONFIG = CONFIG.get("deepseek", {})
DEEPSEEK_API_KEY = DEEPSEEK_CONFIG.get("api_key", os.getenv("DEEPSEEK_API_KEY", ""))
DEEPSEEK_BASE_URL = DEEPSEEK_CONFIG.get("base_url", "https://api.deepseek.com")
DEEPSEEK_MODEL = DEEPSEEK_CONFIG.get("model", "deepseek-chat")

DATABASE_PATH = Path(__file__).parent.parent.parent / "outputs" / "databases" / "reddit_watermark_exp.db"

class AgentEvaluator:
    def __init__(self, db_path: str):
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
            # We need to map user table to agent concept. In schema provided earlier:
            # CREATE TABLE user (user_id INTEGER PRIMARY KEY, ...)
            # CREATE TABLE agent (agent_id INTEGER PRIMARY KEY, ...)
            # Wait, let's double check the schema. The schema output showed `user` table has `agent_id` FK?
            # No, `group_messages` has `sender_id REFERENCES user(agent_id)`.
            # Let's assume 'agent' table exists or 'user' table is what we want.
            # Re-checking schema dump...
            # The previous tool output showed `CREATE TABLE user ...` and `CREATE TABLE group_members ... agent_id`.
            # Let's check if there is an `agent` table. The previous output didn't explicitly show `CREATE TABLE agent` but it might have been truncated?
            # Actually, `CREATE TABLE `chat_group` ...` was shown.
            # Let's assume there is a `user` table that holds agent info, or an `agent` table.
            # The schema usually has a `user` table for all entities.
            # I will query `sqlite_master` to be sure if I need to.
            # But let's try `SELECT * FROM user` first.
            cursor.execute("SELECT * FROM user")
            agents = [dict(row) for row in cursor.fetchall()]
            return agents
        finally:
            conn.close()

    def get_agent_content(self, user_id: int, limit: int = 20) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        content_list = []
        try:
            cursor = conn.cursor()
            # Fetch Posts
            cursor.execute("SELECT content FROM post WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
            posts = [row['content'] for row in cursor.fetchall()]
            content_list.extend([f"[Post] {p}" for p in posts])
            
            # Fetch Comments
            cursor.execute("SELECT content FROM comment WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
            comments = [row['content'] for row in cursor.fetchall()]
            content_list.extend([f"[Comment] {c}" for c in comments])
            
            return content_list
        finally:
            conn.close()

    async def evaluate_agent(self, agent: Dict[str, Any], content: List[str]) -> Dict[str, Any]:
        if not content:
            return {
                "agent_id": agent.get('user_id'),
                "name": agent.get('user_name'),
                "error": "No content found"
            }

        content_str = "\n".join(content[:20]) # Limit to 20 items to fit context
        profile = agent.get('bio', 'No profile available') # Assuming 'bio' column exists, check schema later if needed.

        prompt = f"""
请评估以下社交媒体Agent的表现。基于其个人简介和发布的内容，对以下五个维度进行打分（1-10分）并给出简短理由。

Agent信息:
Name: {agent.get('user_name', 'Unknown')}
Profile/Bio: {profile}

Agent发布的内容样本:
{content_str}

评估维度:
1. 逻辑连贯性 (Logical Coherence): 内容是否逻辑通顺？
2. 记忆准确性 (Memory Accuracy): 是否有前后矛盾？
3. 人设稳定性 (Character Stability): 是否符合其Profile描述？
4. 社会规范与常识 (Social Norms & Common Sense): 是否符合一般的社会规范和常识？
5. 语言多样性 (Language Diversity): 词汇和句式是否丰富？

请以JSON格式输出，格式如下:
{{
    "logic_score": 0,
    "logic_reason": "...",
    "memory_score": 0,
    "memory_reason": "...",
    "stability_score": 0,
    "stability_reason": "...",
    "norms_score": 0,
    "norms_reason": "...",
    "diversity_score": 0,
    "diversity_reason": "...",
    "overall_comment": "..."
}}
"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是专业的社交媒体行为评估专家。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            result_json = response.choices[0].message.content
            return json.loads(result_json)
        except Exception as e:
            print(f"Error evaluating agent {agent.get('user_name', 'Unknown')}: {e}")
            return {"error": str(e)}

    async def run(self):
        print(f"Connecting to database: {self.db_path}")
        if not self.db_path.exists():
            print(f"❌ Database not found at {self.db_path}")
            return

        cols = self.get_db_columns('user')
        print(f"User table columns: {cols}")

        agents = self.get_agents()
        print(f"Found {len(agents)} agents.")
        
        results = []
        for agent in agents:
            user_id = agent.get('user_id') or agent.get('agent_id') # Handle potential column name differences
            if user_id is None:
                continue
                
            name = agent.get('user_name') or agent.get('name', f"User {user_id}")
            print(f"\nEvaluating Agent: {name} (ID: {user_id})...")
            
            content = self.get_agent_content(user_id)
            print(f"  - Found {len(content)} items of content.")
            
            if not content:
                print("  - Skipping (No content)")
                continue
                
            eval_result = await self.evaluate_agent(agent, content)
            
            # Merge identity info
            complete_result = {
                "user_id": user_id,
                "name": name,
                "evaluation": eval_result
            }
            results.append(complete_result)
            print("  - Evaluation complete.")
            
            # Print simple summary
            if "error" not in eval_result:
                print(f"    Logic: {eval_result.get('logic_score')}, Stable: {eval_result.get('stability_score')}")

        # Save to file
        output_file = Path(__file__).parent / "evaluation_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n[OK] All evaluations saved to {output_file}")

    def get_db_columns(self, table_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        return columns

if __name__ == "__main__":
    evaluator = AgentEvaluator(DATABASE_PATH)
    asyncio.run(evaluator.run())
