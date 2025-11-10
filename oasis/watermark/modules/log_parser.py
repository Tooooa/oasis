"""
日志解析模块 (Log Parser)
职责: 解析实验日志文件,提取嵌入和解码所需的数据
"""

import re
import yaml


def parse_log_files(log_path, verbose_log_path=None):
    """
    解析简略和详细日志文件,并将它们的数据合并。

    Args:
        log_path (str): 简略日志文件路径 (watermark_log.txt)
        verbose_log_path (str, optional): 详细日志文件路径 (watermark_verbose.log)

    Returns:
        list: 一个字典列表,每个字典代表一轮的数据。
        
    Example:
        >>> rounds = parse_log_files('log/watermark_log.txt', 'log/watermark_verbose.log')
        >>> print(f"解析了 {len(rounds)} 轮数据")
        >>> print(f"第1轮选择的水印行为: {rounds[0]['selected_behavior_watermark']}")
    """
    # --- 1. 解析简略日志 ---
    print(f"📖 正在解析简略日志: {log_path}")
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            log_content = f.read()
    except FileNotFoundError:
        print(f"❌ 错误: 找不到日志文件 {log_path}")
        return []

    rounds_data = {}
    
    # 使用正则表达式找到每个轮次的块
    # 匹配格式: "数字:\n  key: value\n  key: value..."
    round_blocks = re.findall(r'^(\d+):\n((?:  .*\n)+)', log_content, re.MULTILINE)

    for round_num_str, block_content in round_blocks:
        round_num = int(round_num_str)
        data = {}
        lines = block_content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                value = value.strip()
                
                # 使用 PyYAML 来安全地解析字典和列表字符串
                try:
                    parsed_value = yaml.safe_load(value)
                    data[key.strip()] = parsed_value
                except yaml.YAMLError:
                    # 如果无法解析为YAML,保留原始字符串
                    data[key.strip()] = value
                    
        rounds_data[round_num] = data
    
    print(f"✓ 从简略日志中解析了 {len(rounds_data)} 轮数据")
        
    # --- 2. 解析详细日志以获取 behavior_response_watermark ---
    if verbose_log_path:
        print(f"📖 正在解析详细日志: {verbose_log_path}")
        
        try:
            with open(verbose_log_path, 'r', encoding='utf-8') as f:
                verbose_content = f.read()
        except FileNotFoundError:
            print(f"⚠️ 警告: 找不到详细日志文件 {verbose_log_path},将跳过行为描述解析")
            verbose_content = ""

        if verbose_content:
            # 正则表达式匹配 round_X_behavior_response_watermark: 及其后的内容
            # 匹配格式: "round_数字_behavior_response_watermark:\n> 行为类型:..."
            response_blocks = re.findall(
                r'round_(\d+)_behavior_response_watermark:\n((?:>.*\n?)+)', 
                verbose_content
            )
            
            for round_num_str, response_text in response_blocks:
                round_num = int(round_num_str)
                if round_num in rounds_data:
                    # 将多行带 '>' 的描述合并成一个字符串
                    cleaned_response = re.sub(r'>\s*', '', response_text).strip()
                    rounds_data[round_num]['behavior_response_watermark'] = cleaned_response
            
            print(f"✓ 从详细日志中提取了 {len(response_blocks)} 个行为描述")
    
    # --- 3. 转换为有序列表 ---
    sorted_rounds_list = [rounds_data[i] for i in sorted(rounds_data.keys())]
    
    print(f"✅ 日志解析完成,共 {len(sorted_rounds_list)} 轮数据")
    
    return sorted_rounds_list


def validate_round_data(round_data, round_num):
    """
    验证单轮数据的完整性
    
    Args:
        round_data (dict): 单轮数据字典
        round_num (int): 轮次编号(用于错误提示)
        
    Returns:
        tuple: (is_valid, missing_keys)
        
    Example:
        >>> valid, missing = validate_round_data(rounds[0], 1)
        >>> if not valid:
        ...     print(f"第1轮数据缺失字段: {missing}")
    """
    required_keys = [
        'probabilities_watermark',
        'selected_behavior_watermark',
        'behavior_response_watermark'
    ]
    
    missing_keys = []
    for key in required_keys:
        if key not in round_data or round_data[key] is None:
            missing_keys.append(key)
    
    is_valid = len(missing_keys) == 0
    
    if not is_valid:
        print(f"⚠️ 警告: 第 {round_num} 轮数据不完整,缺失字段: {missing_keys}")
    
    return is_valid, missing_keys


def extract_statistics_from_log(log_path):
    """
    从简略日志中提取统计信息
    
    Args:
        log_path (str): 简略日志文件路径
        
    Returns:
        dict: 统计信息字典,包含总耗时、命中率、嵌入比特数等
        
    Example:
        >>> stats = extract_statistics_from_log('log/watermark_log.txt')
        >>> print(f"水印命中率: {stats['watermark_hit_rate']}%")
    """
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            log_content = f.read()
    except FileNotFoundError:
        print(f"❌ 错误: 找不到日志文件 {log_path}")
        return {}
    
    stats = {}
    
    # 提取统计信息
    patterns = {
        'total_time': r'第 \d+ 轮总耗时: ([\d.]+)秒',
        'avg_time': r'第 \d+ 轮平均每次循环耗时: ([\d.]+)秒',
        'behavior_diff_rate': r'第 \d+ 轮行为不同的比例: ([\d.]+)%',
        'watermark_hit_rate': r'第 \d+ 轮水印行为命中比例: ([\d.]+)%',
        'original_hit_rate': r'第 \d+ 轮原始行为命中比例: ([\d.]+)%',
        'total_bits_embedded': r'第 \d+ 轮总共嵌入比特数: (\d+)',
        'bit_usage_rate': r'第 \d+ 轮比特流使用率: ([\d.]+)%',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, log_content)
        if match:
            value = match.group(1)
            # 尝试转换为数字
            try:
                if '.' in value:
                    stats[key] = float(value)
                else:
                    stats[key] = int(value)
            except ValueError:
                stats[key] = value
    
    return stats
