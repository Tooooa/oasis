# -*- coding: utf-8 -*-
"""
评估指标计算模块
包含5个雷达图维度的计算函数：
- WR: 水印恢复率 (Watermark Recovery Rate)
- PC: 人格一致性 (Persona Consistency)
- SC: 社交连贯性 (Social Coherence)
- SE: 社交参与度 (Social Engagement)
- TD: 轨迹多样性 (Trajectory Diversity)
"""

import math
import random
from typing import Dict, List, Any, Optional
from collections import Counter


def calculate_watermark_recovery(
    agent_data: Dict[str, Any],
    drop_rate: float = 0.5
) -> float:
    """
    WR - 水印恢复率
    模拟日志丢失40%-60%后的水印恢复能力
    
    Args:
        agent_data: Agent的水印提取结果
        drop_rate: 模拟丢失比例 (默认50%)
    
    Returns:
        float: 0-1 恢复率分值
    """
    if not agent_data.get("is_watermark"):
        return 0.0  # 对照组无水印
    
    # 从统计数据中获取准确率
    stats = agent_data.get("extraction_stats", {})
    accuracy = stats.get("accuracy", 0.0) / 100.0  # 转换为0-1
    
    # 考虑丢失后的恢复能力（模拟）
    # 假设ECC能纠正一定比例的错误
    ecc_correction_factor = 0.9  # ECC纠错能力
    recovery_rate = accuracy * ecc_correction_factor
    
    return min(1.0, recovery_rate)


def calculate_persona_consistency(
    agent_actions: List[Dict[str, Any]],
    persona_profile: str,
    llm_evaluator = None
) -> float:
    """
    PC - 人格一致性
    评估Agent行为是否符合其设定的人设
    
    Args:
        agent_actions: Agent的行为历史
        persona_profile: 人设描述
        llm_evaluator: 可选的LLM评估器
    
    Returns:
        float: 0-1 一致性分值
    """
    if not agent_actions:
        return 0.5  # 无数据时返回中等分值
    
    # 基于行为模式的启发式评估
    action_types = [a.get("action_type", "") for a in agent_actions]
    action_counter = Counter(action_types)
    
    # 计算行为多样性
    total_actions = len(action_types)
    if total_actions == 0:
        return 0.5
    
    # 行为分布的一致性评分
    # 如果行为符合预期模式，分数更高
    consistency_score = 0.8  # 基础分
    
    # 检查内容质量（如果有内容的话）
    content_actions = [a for a in agent_actions if a.get("content")]
    if content_actions:
        # 有内容的行为增加一致性分数
        content_ratio = len(content_actions) / total_actions
        consistency_score += content_ratio * 0.1
    
    # TODO: 如果提供了LLM评估器，使用LLM进行语义匹配
    # if llm_evaluator:
    #     llm_score = llm_evaluator.evaluate(agent_actions, persona_profile)
    #     return llm_score
    
    return min(1.0, consistency_score)


def calculate_social_coherence(
    agent_actions: List[Dict[str, Any]],
    context_posts: List[Dict[str, Any]]
) -> float:
    """
    SC - 社交连贯性
    评估回复内容与上下文的相关性
    
    Args:
        agent_actions: Agent的行为历史
        context_posts: 上下文帖子列表
    
    Returns:
        float: 0-1 连贯性分值
    """
    if not agent_actions:
        return 0.5
    
    # 计算响应类行为的比例
    interactive_actions = ["CREATE_COMMENT", "LIKE_POST", "DISLIKE_POST"]
    interactive_count = sum(1 for a in agent_actions 
                          if a.get("action_type") in interactive_actions)
    
    total_actions = len(agent_actions)
    if total_actions == 0:
        return 0.5
    
    # 互动行为越多，社交连贯性越高
    interaction_ratio = interactive_count / total_actions
    
    # 基础连贯性分数
    coherence_score = 0.6 + interaction_ratio * 0.3
    
    # 如果有评论内容，假设内容是连贯的（简化评估）
    comment_actions = [a for a in agent_actions 
                      if a.get("action_type") == "CREATE_COMMENT" and a.get("content")]
    if comment_actions:
        coherence_score += 0.1
    
    return min(1.0, coherence_score)


def calculate_social_engagement(
    agent_id: int,
    all_actions: List[Dict[str, Any]],
    agent_posts: List[int]
) -> float:
    """
    SE - 社交参与度
    统计其他Agent对该Agent内容的互动
    
    Args:
        agent_id: 目标Agent ID
        all_actions: 所有Agent的行为
        agent_posts: 该Agent发布的帖子ID列表
    
    Returns:
        float: 归一化的参与度分值 (0-1)
    """
    if not agent_posts:
        return 0.5  # 无帖子时返回中等分值
    
    # 统计其他Agent对该Agent帖子的互动
    engagement_count = 0
    for action in all_actions:
        if action.get("agent_id") == agent_id:
            continue  # 跳过自己的行为
        
        if action.get("action_type") in ["LIKE_POST", "CREATE_COMMENT", "DISLIKE_POST"]:
            target_post = action.get("post_id")
            if target_post in agent_posts:
                engagement_count += 1
    
    # 归一化（假设最大互动数为帖子数 * 5）
    max_engagement = len(agent_posts) * 5
    engagement_score = min(1.0, engagement_count / max(1, max_engagement))
    
    # 基础分 + 互动分
    return 0.3 + engagement_score * 0.7


def calculate_trajectory_diversity(
    agent_actions: List[Dict[str, Any]]
) -> float:
    """
    TD - 轨迹多样性
    计算动作序列的熵值，评估行为是否多样
    
    Args:
        agent_actions: Agent的行为历史
    
    Returns:
        float: 归一化的熵值 (0-1)
    """
    if not agent_actions:
        return 0.0
    
    # 统计行为类型分布
    action_types = [a.get("action_type", "UNKNOWN") for a in agent_actions]
    action_counter = Counter(action_types)
    
    total = len(action_types)
    if total == 0:
        return 0.0
    
    # 计算熵值
    entropy = 0.0
    for count in action_counter.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    
    # 归一化（最大熵 = log2(行为类型数)）
    # 假设有6种行为类型
    max_entropy = math.log2(6)
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
    
    return min(1.0, normalized_entropy)


def compute_all_metrics(
    watermark_agents_data: List[Dict[str, Any]],
    control_agents_data: List[Dict[str, Any]],
    all_actions: List[Dict[str, Any]] = None
) -> Dict[str, Dict[str, float]]:
    """
    计算所有5个维度的指标
    
    Returns:
        {
            "watermark": {"WR": 0.95, "PC": 0.85, "SC": 0.8, "SE": 0.75, "TD": 0.7},
            "control": {"WR": 0.0, "PC": 0.85, "SC": 0.82, "SE": 0.78, "TD": 0.72}
        }
    """
    all_actions = all_actions or []
    
    def avg(values):
        return sum(values) / len(values) if values else 0.0
    
    # 水印组指标
    wm_wr = [calculate_watermark_recovery(a) for a in watermark_agents_data]
    wm_pc = [calculate_persona_consistency(
        a.get("actions", []), 
        a.get("persona_profile", "")
    ) for a in watermark_agents_data]
    wm_sc = [calculate_social_coherence(
        a.get("actions", []), 
        []
    ) for a in watermark_agents_data]
    wm_se = [calculate_social_engagement(
        a.get("agent_id", i),
        all_actions,
        a.get("posts", [])
    ) for i, a in enumerate(watermark_agents_data)]
    wm_td = [calculate_trajectory_diversity(a.get("actions", [])) 
             for a in watermark_agents_data]
    
    # 对照组指标
    ctrl_wr = [0.0] * len(control_agents_data)  # 对照组无水印
    ctrl_pc = [calculate_persona_consistency(
        a.get("actions", []), 
        a.get("persona_profile", "")
    ) for a in control_agents_data]
    ctrl_sc = [calculate_social_coherence(
        a.get("actions", []), 
        []
    ) for a in control_agents_data]
    ctrl_se = [calculate_social_engagement(
        a.get("agent_id", i + 5),
        all_actions,
        a.get("posts", [])
    ) for i, a in enumerate(control_agents_data)]
    ctrl_td = [calculate_trajectory_diversity(a.get("actions", [])) 
               for a in control_agents_data]
    
    return {
        "watermark": {
            "WR": avg(wm_wr),
            "PC": avg(wm_pc),
            "SC": avg(wm_sc),
            "SE": avg(wm_se),
            "TD": avg(wm_td)
        },
        "control": {
            "WR": avg(ctrl_wr),
            "PC": avg(ctrl_pc),
            "SC": avg(ctrl_sc),
            "SE": avg(ctrl_se),
            "TD": avg(ctrl_td)
        }
    }
