# -*- coding: utf-8 -*-
"""
Experiment Configuration
"""

import os

EXPERIMENT_CONFIG = {
    "num_watermark_agents": 5,
    "num_control_agents": 5,
    "num_steps": 10,  # Simulation steps
    "max_words": 140, # Twitter-like constraint
    "db_path": None,  # Will be set dynamically in run_experiment.py
}

API_CONFIG = {
    "provider": "deepseek",
    "deepseek": {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
        "api_key": os.getenv("DEEPSEEK_API_KEY", "your-deepseek-api-key-here")
    }
}

WATERMARK_CONFIG = {
    "algorithm": "K-Cycle-Watermark",
    "vocab_size": 32000,
    "gamma": 0.5,
    "delta": 2.0,
    "hash_key": 15485863,
}

