# -*- coding: utf-8 -*-
"""
Reddit 水印 Agent 实验配置
r/TechFuture 子社区模拟
"""

import os
import json
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# ========== 加载项目配置文件 ==========
def load_project_config():
    """从项目根目录加载 config.json"""
    config_path = PROJECT_ROOT / "config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 加载配置文件失败: {e}")
    return {}

_project_config = load_project_config()

# ========== 实验配置 ==========
EXPERIMENT_CONFIG = {
    "platform": "reddit",
    "num_steps": 10,                    # 时间步数
    "num_watermark_agents": 5,          # 水印组 Agent 数量
    "num_control_agents": 5,            # 对照组 Agent 数量
    "db_path": str(PROJECT_ROOT / "outputs" / "databases" / "reddit_watermark_exp.db"),
    "log_dir": str(PROJECT_ROOT / "outputs" / "logs" / "reddit_exp"),
}

# ========== API 配置 (优先从 config.json 读取) ==========
_deepseek_cfg = _project_config.get("deepseek", {})
API_CONFIG = {
    "provider": _project_config.get("api_provider", "deepseek"),
    "deepseek": {
        "api_key": _deepseek_cfg.get("api_key") or os.getenv("DEEPSEEK_API_KEY", ""),
        "base_url": _deepseek_cfg.get("base_url", "https://api.deepseek.com"),
        "model": _deepseek_cfg.get("model", "deepseek-chat")
    },
    "openai": {
        "api_key": _project_config.get("openai", {}).get("api_key") or os.getenv("OPENAI_API_KEY", ""),
        "model": _project_config.get("openai", {}).get("model", "gpt-4o-mini")
    }
}

# ========== 水印配置 ==========
WATERMARK_CONFIG = {
    "enabled": True,
    "mode": "lightweight",
    "ecc_method": "parity",
    "embedding_strategy": "cyclic",
    "delta": 0.1,
    "gamma": 0.3,
}

# ========== Reddit 可用行为类型 ==========
AVAILABLE_ACTIONS = [
    "CREATE_POST",       # 发帖
    "CREATE_COMMENT",    # 评论
    "LIKE_POST",         # 点赞
    "DISLIKE_POST",      # 踩
    "REFRESH",           # 刷新
    "DO_NOTHING",        # 不做任何事
]
