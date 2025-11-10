"""
AgentMark 模块包
将复杂的水印实验代码拆分为清晰的模块
"""

from .agent_simulator import get_behavior_probabilities, get_behavior_description
from .watermark_sampler import (
    sample_behavior, 
    sample_behavior_watermark,
    sample_behavior_watermark_uncertainty,
    sample_behavior_differential
)
from .experiment_logger import (
    initialize_log_file, 
    log_round_results, 
    log_long_responses,
    log_summary, 
    calculate_statistics,
    print_statistics
)
from .prompt_utils import format_behaviors_list, generate_behaviors_example
from .parser_utils import extract_probabilities

__all__ = [
    # 模型交互
    'get_behavior_probabilities',
    'get_behavior_description',
    
    # 水印采样
    'sample_behavior',
    'sample_behavior_watermark',
    'sample_behavior_watermark_uncertainty',
    'sample_behavior_differential',
    
    # 日志记录
    'initialize_log_file',
    'log_round_results',
    'log_long_responses',
    'log_summary',
    'calculate_statistics',
    'print_statistics',
    
    # Prompt工具
    'format_behaviors_list',
    'generate_behaviors_example',
    
    # 解析工具
    'extract_probabilities',
]
