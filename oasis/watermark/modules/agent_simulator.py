"""
模型交互模块 (Agent Simulator)
职责: 封装所有与大模型 API 交互的逻辑
"""

from .prompt_utils import format_behaviors_list, generate_behaviors_example
from .parser_utils import extract_probabilities


def get_behavior_probabilities(client, model, role_config, event, behaviors, probability_template):
    """
    根据事件获取各个行为的概率分布
    
    Args:
        client: OpenAI 客户端实例
        model: 使用的模型名称
        role_config: 角色配置信息 (包含 name, profile, system_prompt)
        event: 格式化后的视频事件文本
        behaviors: 行为类型列表，如 ['点赞', '收藏', '转发', ...]
        probability_template: 概率计算的 prompt 模板
    
    Returns:
        tuple: (probabilities_dict, raw_response_text)
            - probabilities_dict: 概率字典，如 {'点赞': 0.3, '收藏': 0.2, ...}
            - raw_response_text: API 返回的原始响应文本
    """
    name = role_config['name']
    profile = role_config['profile']
    
    # 构建概率计算的 prompt
    probability_prompt = probability_template.format(
        name=name,
        event=event,
        behaviors=format_behaviors_list(behaviors),
        behaviors_example=generate_behaviors_example(behaviors)
    )
    
    print("概率计算的 prompt:")
    print(probability_prompt)
    
    # 调用 API 获取行为概率
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system", 
                "content": role_config["system_prompt"].format(name=name, profile=profile)
            },
            {
                "role": "user", 
                "content": probability_prompt
            }
        ]
    )
    
    # 获取响应文本
    response_text = response.choices[0].message.content
    print("\n概率响应:")
    print(response_text)
    
    # 提取概率数据
    probabilities = extract_probabilities(response_text, behaviors)
    
    if probabilities:
        print("\n提取的概率数据:")
        print(probabilities)
    else:
        print("\n警告: 未能成功提取概率数据")
    
    return probabilities, response_text


def get_behavior_description(client, model, role_config, event, behavior, behavior_template):
    """
    根据事件和选定的行为，获取该行为的详细描述
    
    Args:
        client: OpenAI 客户端实例
        model: 使用的模型名称
        role_config: 角色配置信息
        event: 格式化后的视频事件文本
        behavior: 选定的行为，如 "点赞"
        behavior_template: 行为描述的 prompt 模板
    
    Returns:
        str: 模型生成的行为描述文本
    """
    name = role_config['name']
    profile = role_config['profile']
    
    # 构建行为描述的 prompt
    behavior_prompt = behavior_template.format(
        name=name,
        event=event,
        behavior=behavior
    )
    
    print(f"\n行为描述的 prompt (行为: {behavior}):")
    print(behavior_prompt)
    
    # 调用 API 获取行为描述
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system", 
                "content": role_config["system_prompt"].format(name=name, profile=profile)
            },
            {
                "role": "user", 
                "content": behavior_prompt
            }
        ]
    )
    
    behavior_description = response.choices[0].message.content
    print("\n行为描述:")
    print(behavior_description)
    
    return behavior_description
