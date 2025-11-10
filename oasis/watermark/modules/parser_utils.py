"""
响应解析工具模块 (Parser Utilities)
职责: 从 LLM 响应中解析结构化数据
"""

import re
import json


def extract_probabilities(response_text, behaviors):
    """
    从API响应文本中提取行为概率数据
    
    支持两种解析策略:
    1. JSON解析: 优先尝试从响应中提取第一个JSON对象并解析
    2. 正则回退: 如果JSON解析失败,使用正则表达式逐个匹配行为概率
    
    Args:
        response_text (str): API响应的文本内容
        behaviors (list): 行为类型列表
        
    Returns:
        dict: 包含各个行为概率的字典,如果提取失败返回None
        
    Example:
        >>> response = '根据场景分析,概率为 {"点赞": 0.3, "收藏": 0.2, "转发": 0.5}'
        >>> behaviors = ["点赞", "收藏", "转发"]
        >>> extract_probabilities(response, behaviors)
        {'点赞': 0.3, '收藏': 0.2, '转发': 0.5}
    """
    # 策略1: 尝试从响应中提取第一个 JSON 对象并解析（更鲁棒）
    try:
        # 查找第一个花括号包围的 JSON 片段
        m = re.search(r"\{[\s\S]*?\}", response_text)
        if m:
            json_text = m.group(0)
            # 有时模型会使用单引号，尽量处理成合法的 JSON
            json_text_fixed = json_text.replace("'", '"')
            parsed = json.loads(json_text_fixed)
            # 检查是否包含所有行为键
            if all(b in parsed for b in behaviors):
                return {b: float(parsed[b]) for b in behaviors}
    except Exception:
        # 解析失败，继续尝试正则回退
        pass

    # 策略2: 使用行为逐个匹配的正则
    pattern_parts = []
    for behavior in behaviors:
        pattern_parts.append(r'"' + re.escape(behavior) + r'"\s*:\s*([0-9]*\.?[0-9]+)')

    probability_pattern = r'\{[\s\S]*' + r'.*'.join(pattern_parts) + r'[\s\S]*\}'
    match = re.search(probability_pattern, response_text)
    if match:
        return {
            behavior: float(match.group(i + 1))
            for i, behavior in enumerate(behaviors)
        }

    return None
