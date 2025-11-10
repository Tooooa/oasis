"""
实验日志模块 (Experiment Logger)
职责: 负责所有与文件写入和统计计算相关的任务
"""


def initialize_log_file(log_path, round_idx, total_rounds, verbose_log_path=None, enable_verbose=False):
    """
    初始化日志文件，写入实验轮次的标题头
    
    Args:
        log_path (str): 日志文件路径
        round_idx (int): 当前实验轮次索引 (从0开始)
        total_rounds (int): 总实验轮次数
        verbose_log_path (str, optional): 详细日志文件路径
        enable_verbose (bool, optional): 是否开启详细日志
    """
    mode = 'w' if round_idx == 0 else 'a'
    with open(log_path, mode, encoding='utf-8') as f:
        f.write(f"\n\n{'='*30} 第 {round_idx + 1}/{total_rounds} 轮实验 {'='*30}\n\n")

    if enable_verbose and verbose_log_path:
        verbose_mode = 'w' if round_idx == 0 else 'a'
        with open(verbose_log_path, verbose_mode, encoding='utf-8') as vf:
            vf.write(f"\n\n{'='*30} 第 {round_idx + 1}/{total_rounds} 轮实验 - 详细日志 {'='*30}\n\n")


def log_round_results(log_path, round_idx, round_data):
    """
    将单次循环的数据格式化并追加到日志文件
    
    Args:
        log_path (str): 日志文件路径
        round_idx (int): 当前视频轮次 (从1开始)
        round_data (dict): 包含单次循环所有数据的字典
    """
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"{round_idx}:\n")
        f.write(f"  event_watermark: {round_data['event_watermark']}\n")
        f.write(f"  BEHAVIOR_TYPES: {round_data['BEHAVIOR_TYPES']}\n")
        f.write(f"  time_cost: {round_data['time_cost']}\n")
        f.write(f"  probabilities_baseline: {round_data['probabilities_baseline']}\n")
        f.write(f"  selected_behavior_baseline: {round_data['selected_behavior_baseline']}\n")
        f.write(f"  probabilities_watermark: {round_data['probabilities_watermark']}\n")
        f.write(f"  selected_behavior_watermark: {round_data['selected_behavior_watermark']}\n")
        f.write(f"  target_behavior_list: {round_data['target_behavior_list']}\n")
        f.write(f"  behaviors_match: {round_data['behaviors_match']}\n")
        f.write(f"  watermark_hit: {round_data['watermark_hit']}\n")
        f.write(f"  baseline_hit_target: {round_data['baseline_hit_target']}\n")
        
        # 如果有差分引擎特有的数据，也记录下来
        if 'num_bits_embedded' in round_data:
            f.write(f"  num_bits_embedded: {round_data['num_bits_embedded']}\n")
        if 'bit_index' in round_data:
            f.write(f"  bit_index: {round_data['bit_index']}\n")
        if 'context_for_key' in round_data:
            f.write(f"  context_for_key: {round_data['context_for_key']}\n")
        
        f.write("\n")


def log_long_responses(verbose_log_path, long_responses, enable_verbose=False):
    """
    记录详细的 API 响应内容
    
    Args:
        verbose_log_path (str): 详细日志文件路径
        long_responses (dict): 包含所有长响应的字典
        enable_verbose (bool, optional): 是否开启详细日志
    """
    if not enable_verbose or not verbose_log_path:
        return

    with open(verbose_log_path, 'a', encoding='utf-8') as f:
        f.write("=== 详细响应 ===\n\n")
        for key, value in long_responses.items():
            f.write(f"{key}:\n{value}\n\n")


def log_summary(log_path, stats, round_idx, total_duration, epoch_num):
    """
    将最终的统计结果写入日志
    
    Args:
        log_path (str): 日志文件路径
        stats (dict): 统计数据字典，包含各种指标
    """
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write("=== 统计信息 ===\n")
        f.write(f"第 {round_idx + 1} 轮总耗时: {total_duration:.2f}秒\n")
        f.write(f"第 {round_idx + 1} 轮平均每次循环耗时: {(total_duration/epoch_num):.2f}秒\n\n")
        f.write(f"第 {round_idx + 1} 轮行为不同的次数: {stats['different_behavior_count']}/{stats['total_rounds']}\n")
        f.write(f"第 {round_idx + 1} 轮行为不同的比例: {stats['different_behavior_ratio']:.2f}%\n")
        f.write(f"第 {round_idx + 1} 轮水印行为命中次数: {stats['watermark_hit_count']}\n")
        f.write(f"第 {round_idx + 1} 轮水印行为命中比例: {stats['watermark_hit_ratio']:.2f}%\n")
        f.write(f"第 {round_idx + 1} 轮原始行为命中次数: {stats['original_hit_count']}\n")
        f.write(f"第 {round_idx + 1} 轮原始行为命中比例: {stats['original_hit_ratio']:.2f}%\n")

        # 如果有差分引擎相关的统计，也记录
        if 'total_bits_embedded' in stats:
            f.write(f"第 {round_idx + 1} 轮总共嵌入比特数: {stats['total_bits_embedded']}\n")
        if 'bit_stream_usage' in stats:
            f.write(f"第 {round_idx + 1} 轮比特流使用率: {stats['bit_stream_usage']:.2f}%\n")

        f.write("\n")


def calculate_statistics(all_rounds_data, epoch_num):
    """
    接收所有轮次的数据，计算出命中率、差异率等统计指标
    
    Args:
        all_rounds_data (list): 所有轮次的数据列表
        epoch_num (int): 总循环次数
        
    Returns:
        dict: 包含各种统计指标的字典
    """
    different_behavior_count = 0
    watermark_hit_count = 0
    original_hit_count = 0
    total_bits_embedded = 0
    
    for round_data in all_rounds_data:
        # 统计行为是否不同
        if not round_data["behaviors_match"]:
            different_behavior_count += 1
        
        # 统计水印命中
        if round_data["watermark_hit"]:
            watermark_hit_count += 1
        
        # 统计基准行为命中目标列表
        if round_data.get("baseline_hit_target", round_data.get("original_hit", False)):
            original_hit_count += 1
        
        # 如果有差分引擎的数据，统计嵌入的比特数
        if 'num_bits_embedded' in round_data:
            total_bits_embedded += round_data['num_bits_embedded']
    
    # 计算比例
    stats = {
        'total_rounds': epoch_num,
        'different_behavior_count': different_behavior_count,
        'different_behavior_ratio': (different_behavior_count / epoch_num) * 100 if epoch_num > 0 else 0,
        'watermark_hit_count': watermark_hit_count,
        'watermark_hit_ratio': (watermark_hit_count / epoch_num) * 100 if epoch_num > 0 else 0,
        'original_hit_count': original_hit_count,
        'original_hit_ratio': (original_hit_count / epoch_num) * 100 if epoch_num > 0 else 0,
    }
    
    # 如果使用了差分引擎，添加相关统计
    if total_bits_embedded > 0:
        stats['total_bits_embedded'] = total_bits_embedded
    
    return stats


def print_statistics(stats, round_idx, total_duration, epoch_num):
    """
    在控制台打印统计信息
    
    Args:
        stats (dict): 统计数据字典
        round_idx (int): 当前实验轮次索引 (从0开始)
        total_duration (float): 总耗时（秒）
        epoch_num (int): 每轮的循环次数
    """
    print(f"\n第 {round_idx + 1} 轮总耗时: {total_duration:.2f}秒")
    print(f"第 {round_idx + 1} 轮平均每次循环耗时: {(total_duration/epoch_num):.2f}秒")
    print(f"\n第 {round_idx + 1} 轮行为不同的次数: {stats['different_behavior_count']}/{stats['total_rounds']}")
    print(f"第 {round_idx + 1} 轮行为不同的比例: {stats['different_behavior_ratio']:.2f}%")
    print(f"第 {round_idx + 1} 轮水印行为命中次数: {stats['watermark_hit_count']}")
    print(f"第 {round_idx + 1} 轮水印行为命中比例: {stats['watermark_hit_ratio']:.2f}%")
    print(f"第 {round_idx + 1} 轮原始行为命中次数: {stats['original_hit_count']}")
    print(f"第 {round_idx + 1} 轮原始行为命中比例: {stats['original_hit_ratio']:.2f}%")
    
    # 如果有差分引擎数据，也打印
    if 'total_bits_embedded' in stats:
        print(f"第 {round_idx + 1} 轮总共嵌入比特数: {stats['total_bits_embedded']}")
