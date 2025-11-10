"""
Prompt 工具模块 (Prompt Utilities)
职责: 提供与生成 LLM Prompt 相关的格式化工具
"""


def format_behaviors_list(behaviors):
    """
    将行为列表格式化为字符串
    
    Args:
        behaviors (list): 行为列表
        
    Returns:
        str: 格式化后的行为列表字符串
        
    Example:
        >>> behaviors = ["点赞", "收藏", "转发"]
        >>> format_behaviors_list(behaviors)
        '- 点赞\\n- 收藏\\n- 转发'
    """
    return "\n".join([f"- {behavior}" for behavior in behaviors])


def generate_behaviors_example(behaviors):
    """
    生成行为概率的示例JSON字符串
    
    Args:
        behaviors (list): 行为列表
        
    Returns:
        str: 示例JSON字符串
        
    Example:
        >>> behaviors = ["点赞", "收藏", "转发"]
        >>> generate_behaviors_example(behaviors)
        '{ "点赞": <点赞的概率>, "收藏": <收藏的概率>, "转发": <转发的概率> }'
    """
    example_dict = {behavior: f"<{behavior}的概率>" for behavior in behaviors}
    return "{ " + ", ".join([f'"{k}": {v}' for k, v in example_dict.items()]) + " }"
