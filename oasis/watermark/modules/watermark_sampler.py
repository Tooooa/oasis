"""
水印算法模块 (Watermark Sampler)
职责: 包含所有与行为采样相关的算法
"""

import random
import math
import torch
import hmac
import hashlib
import numpy as np


# ==============================================================================
# ================ 上下文密钥生成 (Contextual Key Generation) ================
# ==============================================================================

def generate_contextual_key(history_responses, num_bytes=32):
    """
    根据历史响应(上下文)生成一个确定性的密钥。
    
    Args:
        history_responses (list): 一个包含过去行为描述字符串的列表。
        num_bytes (int): 生成密钥的字节数 (默认32,对应SHA-256)。

    Returns:
        bytes: 生成的密钥。
        
    Example:
        >>> history = ["用户点赞了视频", "用户收藏了视频"]
        >>> key = generate_contextual_key(history)
        >>> len(key)
        32
    """
    if not history_responses:
        # 冷启动: 如果历史为空,使用一个固定的初始字符串
        context_string = "INITIAL_CONTEXT_FOR_AGENT_WATERMARK"
    else:
        # 使用最近的响应作为上下文
        # 这里我们使用最后一个响应,可以根据需要扩展为多个响应的拼接
        context_string = history_responses[-1]
        
    # 使用 SHA-256 哈希函数将上下文字符串转换为固定长度的密钥
    hasher = hashlib.sha256()
    hasher.update(context_string.encode('utf-8'))
    return hasher.digest()[:num_bytes]


# ==============================================================================
# ================ 差分方案水印引擎 (Differential Scheme Watermark Engine) ================
# ==============================================================================

# 伪随机数生成器 (PRG/DRBG)，确保发送方和接收方可以同步随机过程
class DRBG:
    def __init__(self, key, nonce):
        self.key = key
        self.nonce = nonce
        self.counter = 0

    def generate_random_bits(self, n):
        message = self.nonce + self.counter.to_bytes(4, 'big')
        hmac_sha512 = hmac.new(self.key, message, hashlib.sha512).digest()
        self.counter += 1
        
        bits = ''.join(format(byte, '08b') for byte in hmac_sha512)
        return bits[:n]

    def generate_random(self, n):
        # 从比特串生成一个 (0,1) 之间的浮点数
        random_bits = self.generate_random_bits(n)
        random_int = int(random_bits, 2)
        random_float = random_int / (2**n)
        return random_float

# 均匀隐写编码器 (在选定的"箱子"内根据秘密信息选择一项)
# 标准版本 - 与Artifacts实现完全一致
def uni_cyclic_shift_enc(bit_stream, n, PRG, precision=52):
    """
    循环移位均匀隐写编码器 (Artifacts标准版本)
    
    Args:
        bit_stream (str): 要嵌入的比特流
        n (int): 箱子大小
        PRG: 伪随机数生成器
        precision (int): 精度参数
        
    Returns:
        tuple: (选中的索引, 嵌入的比特串)
    """
    if n == 1:
        PRG.generate_random(n=precision)
        return 0, ''
    
    ptr = PRG.generate_random(n=precision)
    R = math.floor(ptr * n)
    
    k = math.floor(math.log2(n))
    t = n - 2**k
    
    # 检查比特流是否足够
    if len(bit_stream) < k:
        # 比特流不够,随机选择但消耗PRG以保持同步
        return R, ''
    
    bits = bit_stream[:k]
    
    # 检查是否需要额外的一位
    if len(bit_stream) < k + 1:
        bits_res = '0'  # 默认值
    else:
        bits_res = bit_stream[k]
    
    idx_sort = lsb_bits2int([int(b) for b in bits])
    
    if idx_sort < 2**k - t:
        return (idx_sort + R) % n, bits
    else:
        return (2 * (idx_sort - (2**k - t)) + (2**k - t) + R + int(bits_res)) % n, bits + bits_res

# 差分重组模块 (核心创新点：水平切割)
# V2: 使用稳定排序来处理概率相等的情况
def differential_based_recombination(prob, indices):
    bins = []
    
    # ========================== 使用稳定排序 ==========================
    # torch.argsort 返回一个索引张量，该张量可以对输入张量进行排序。
    # stable=True 确保了当 prob 中的值相等时，对应的索引将保持其原始顺序。
    # 这是保证编解码同步的关键！
    sorted_order_indices = torch.argsort(prob, stable=True, descending=False)
    
    # 使用这个确定性的顺序来重新排列 prob 和 indices
    prob = prob[sorted_order_indices]
    indices = indices[sorted_order_indices]
    # ==================================================================

    mask = prob > 0
    prob_nonzero = prob[mask]
    indices_nonzero = indices[mask]
 
    diff = torch.cat((prob_nonzero[:1], torch.diff(prob_nonzero, n=1)))
    n = len(prob_nonzero)

    weights = torch.arange(n, 0, -1, device = prob.device) 
    diff_positive = diff > 0

    prob_new = diff[diff_positive] * weights[diff_positive] 
    bins = torch.arange(n, device = prob.device)[diff_positive]

    return indices_nonzero, bins, prob_new

# 差分编码器 (引擎总装)
def differential_based_encoder(prob, indices, bit_stream, bit_index, PRG, precision = 52, **kwargs):
    indices_nonzero, bins, prob_new = differential_based_recombination(prob, indices)
    if prob_new.sum() == 0: # 避免除以0的错误
        # 如果所有概率都一样，随机选择一个
        random_idx = int(PRG.generate_random(precision) * len(indices))
        return indices[random_idx].view(1,1), 0

    prob_new = prob_new/prob_new.sum()

    random_p = PRG.generate_random(n = precision)
    cdf = torch.cumsum(prob_new, dim=0)
    bin_indice_idx = torch.searchsorted(cdf, random_p).item()
    
    selected_bin_start_index = bins[bin_indice_idx]
    bin_content = indices_nonzero[selected_bin_start_index:]

    idx, bits = uni_cyclic_shift_enc(bit_stream=bit_stream[bit_index:], n = len(bin_content), PRG = PRG, precision=precision)
    
    num = len(bits)
    prev = bin_content[idx].view(1,1)

    return prev, num


# ==============================================================================
# ================ 基础采样算法 ================
# ==============================================================================

def sample_behavior(probabilities, seed=None, round_num=0):
    """
    根据概率从行为列表中随机选择一个行为 (无水印版本)
    
    Args:
        probabilities (dict): 行为及其对应的概率字典
        seed (int, optional): 随机数种子，用于确保结果可复现
        round_num (int, optional): 当前轮数，用于在固定种子的基础上引入变化
        
    Returns:
        str: 选中的行为
        
    Example:
        >>> probs = {"点赞": 0.3, "收藏": 0.2, "转发": 0.5}
        >>> sample_behavior(probs, seed=42, round_num=1)
        '转发'
    """
    # 设置随机数种子
    if seed is not None:
        # 将种子和轮数结合，创建新的种子
        combined_seed = seed + round_num
        random.seed(combined_seed)
    
    # 获取行为列表和对应的概率列表
    behaviors = list(probabilities.keys())
    probs = list(probabilities.values())
    
    # 确保概率和为1
    total = sum(probs)
    if total != 1.0:
        probs = [p/total for p in probs]
    
    # 使用random.choices进行加权随机选择
    # k=1 表示只选择一个元素，weights参数指定每个元素的权重（概率）
    selected_behavior = random.choices(behaviors, weights=probs, k=1)[0]
    
    return selected_behavior


# ==============================================================================
# ================ 传统水印采样算法 ================
# ==============================================================================

def sample_behavior_watermark(probabilities, seed=None, round_num=0, prob_bias=0.5, ratio=0.5, BEHAVIOR_TYPES=[]):
    """
    根据概率从行为列表中随机选择一个行为，并对部分行为增加概率偏置 (旧的概率偏置水印)
    
    Args:
        probabilities (dict): 行为及其对应的概率字典
        seed (int, optional): 随机数种子，用于确保结果可复现
        round_num (int, optional): 当前轮数，用于在固定种子的基础上引入变化
        prob_bias (float, optional): 概率偏置，用于调整概率
        ratio (float, optional): 行为概率偏置比例, 0-1, 控制我们在BEHAVIOR_TYPES中增加prob_bias的范围
        BEHAVIOR_TYPES (list, optional): 行为类型列表

    Returns:
        tuple: (选中的行为, 被增加概率偏置的行为列表)
        
    Example:
        >>> probs = {"点赞": 0.3, "收藏": 0.2, "转发": 0.5}
        >>> behavior, biased_list = sample_behavior_watermark(probs, seed=42, round_num=1, prob_bias=0.5, ratio=0.5, BEHAVIOR_TYPES=['点赞', '收藏', '转发'])
        >>> print(f"选中行为: {behavior}, 增加偏置的行为: {biased_list}")
    """
    # 行为数量
    behavior_num = len(BEHAVIOR_TYPES)
    
    # 设置随机数种子
    if seed is not None:
        # 将种子和轮数结合，创建新的种子
        combined_seed = seed + round_num
        random.seed(combined_seed)
    
    # 根据combined_seed和ratio来划分需要增加prob_bias的行为
    # 计算需要增加偏置的行为数量
    biased_count = int(behavior_num * ratio)
    # 随机选择需要增加偏置的行为
    add_logits_behavior_list = random.sample(BEHAVIOR_TYPES, biased_count)
    
    # 获取行为列表和对应的概率列表
    behaviors = list(probabilities.keys())
    probs = list(probabilities.values())
    
    # 对选中的行为增加概率偏置
    modified_probs = []
    for behavior, prob in zip(behaviors, probs):
        if behavior in add_logits_behavior_list:
            modified_probs.append(prob + prob_bias)
        else:
            modified_probs.append(prob)
    
    # 确保概率和为1
    total = sum(modified_probs)
    if total != 1.0:
        modified_probs = [p/total for p in modified_probs]
    
    # 使用random.choices进行加权随机选择
    selected_behavior_watermark = random.choices(behaviors, weights=modified_probs, k=1)[0]
    
    return selected_behavior_watermark, add_logits_behavior_list


def sample_behavior_watermark_uncertainty(probabilities, seed=None, round_num=0, prob_bias=0.5, ratio=0.5, BEHAVIOR_TYPES=[], uncertainty_threshold=0.5):
    """
    根据概率从行为列表中随机选择一个行为，并对部分行为增加概率偏置，同时判断行为的不确定性
    
    Args:
        probabilities (dict): 行为及其对应的概率字典
        seed (int, optional): 随机数种子，用于确保结果可复现
        round_num (int, optional): 当前轮数，用于在固定种子的基础上引入变化
        prob_bias (float, optional): 概率偏置，用于调整概率
        ratio (float, optional): 行为概率偏置比例, 0-1, 控制我们在BEHAVIOR_TYPES中增加prob_bias的范围
        BEHAVIOR_TYPES (list, optional): 行为类型列表
        uncertainty_threshold (float, optional): 不确定性阈值，超过此值则认为行为不稳定

    Returns:
        tuple: (选中的行为, 被增加概率偏置的行为列表, 是否采用水印)
        
    Example:
        >>> probs = {"点赞": 0.3, "收藏": 0.2, "转发": 0.5}
        >>> behavior, biased_list, is_stable = sample_behavior_watermark_uncertainty(
        ...     probs, seed=42, round_num=1, prob_bias=0.5, ratio=0.5,
        ...     BEHAVIOR_TYPES=['点赞', '收藏', '转发'], uncertainty_threshold=0.5
        ... )
        >>> print(f"选中行为: {behavior}, 增加偏置的行为: {biased_list}, 是否稳定: {is_stable}")
    """
    # 行为数量
    behavior_num = len(BEHAVIOR_TYPES)
    
    # 设置随机数种子
    if seed is not None:
        # 将种子和轮数结合，创建新的种子
        combined_seed = seed + round_num
        random.seed(combined_seed)
    
    # 根据combined_seed和ratio来划分需要增加prob_bias的行为
    # 计算需要增加偏置的行为数量
    biased_count = int(behavior_num * ratio)
    # 随机选择需要增加偏置的行为
    add_logits_behavior_list = random.sample(BEHAVIOR_TYPES, biased_count)
    
    # 获取行为列表和对应的概率列表
    behaviors = list(probabilities.keys())
    probs = list(probabilities.values())
    
    # 记录原始概率，用于后续比较
    original_probs = probs.copy()
    
    # 对选中的行为增加概率偏置
    modified_probs = []
    for behavior, prob in zip(behaviors, probs):
        if behavior in add_logits_behavior_list:
            modified_probs.append(prob + prob_bias)
        else:
            modified_probs.append(prob)
    
    # 确保概率和为1
    total = sum(modified_probs)
    if total != 1.0:
        modified_probs = [p/total for p in modified_probs]
    
    # 使用random.choices进行加权随机选择
    selected_behavior_watermark = random.choices(behaviors, weights=modified_probs, k=1)[0]
    
    # 计算不确定性
    # NOTE 方法1: 计算修改后的最大概率与次大概率的差值
    # 通过对概率排序,取最大和次大概率的差值,差值越大说明最大概率越显著,不确定性越小
    # 例如: 如果最大概率0.8,次大概率0.1,差值0.7,说明最大概率很显著,选择很确定
    sorted_probs = sorted(modified_probs, reverse=True)
    max_prob_diff = sorted_probs[0] - sorted_probs[1]
    
    # NOTE 方法2: 计算原始概率和修改后概率的最大变化量
    # 通过计算修改前后概率的变化量,变化越大说明水印影响越大,不确定性越大
    # 例如: 如果某行为原始概率0.2,修改后0.7,变化量0.5,说明水印影响很大,选择不确定
    prob_changes = [abs(m - o) for m, o in zip(modified_probs, original_probs)]
    max_prob_change = max(prob_changes)
    
    # NOTE 方法3: 计算信息熵
    # 通过计算概率分布的信息熵来衡量不确定性,熵越大说明概率分布越均匀,不确定性越大
    # 例如: 如果概率分布均匀[0.33,0.33,0.34],熵接近1,说明选择很不确定
    # 如果概率分布集中[0.9,0.05,0.05],熵接近0,说明选择很确定
    entropy = -sum(p * math.log2(p) if p > 0 else 0 for p in modified_probs)
    normalized_entropy = entropy / math.log2(len(behaviors))  # 归一化熵
    
    # 综合不确定性度量（可以根据需要调整这个计算方式）
    uncertainty = (
        (1 - max_prob_diff) +  # 最大概率差越小，不确定性越大
        max_prob_change +      # 概率变化越大，不确定性越大
        normalized_entropy     # 熵越大，不确定性越大
    ) / 3
    
    # 判断是否采用水印, uncertainty越小,说明不确定性越小,越可能采用水印
    is_stable = uncertainty < uncertainty_threshold
    
    return selected_behavior_watermark, add_logits_behavior_list, is_stable, uncertainty


# ==============================================================================
# ================ 差分水印采样算法 ================
# ==============================================================================

def sample_behavior_differential(probabilities, bit_stream, bit_index, context_for_key=None, history_responses=None, seed=None, round_num=0):
    """
    使用差分方案引擎来选择行为，并嵌入秘密信息 (新的差分水印方案)
    这是新引擎的适配器函数，支持基于上下文动态生成密钥。

    Args:
        probabilities (dict): 行为及其对应的概率字典.
        bit_stream (str): 要嵌入的秘密信息比特流.
        bit_index (int): 当前比特流的起始索引.
        context_for_key (str, optional): 明确的上下文字符串,用于密钥生成(推荐使用).
        history_responses (list, optional): [已弃用] 历史响应列表,仅当context_for_key为None时使用.
        seed (int, optional): 随机数种子 (备用，当前实现使用上下文密钥).
        round_num (int, optional): 当前轮数.

    Returns:
        tuple: (选中的行为, 用于检测的目标行为列表, 本次嵌入的比特数, 实际使用的context_for_key)
        
    Example:
        >>> probs = {"点赞": 0.3, "收藏": 0.2, "转发": 0.5}
        >>> context = "response1||response2"
        >>> behavior, targets, bits, ctx = sample_behavior_differential(probs, "10110", 0, context_for_key=context, round_num=1)
        >>> print(f"选中: {behavior}, 目标列表: {targets}, 嵌入比特数: {bits}")
    """
    # --- 1. 数据格式转换 (将输入适配新引擎) ---
    # 确保行为顺序固定，以便索引保持一致
    behaviors = sorted(probabilities.keys())
    probs_list = [probabilities[b] for b in behaviors]
    
    # 转换为PyTorch Tensors
    device = 'cuda' if torch.cuda.is_available() else 'cpu'  # 自动检测设备
    probs_tensor = torch.tensor(probs_list, dtype=torch.float32, device=device)
    indices_tensor = torch.arange(len(behaviors), device=device)
    
    # --- 2. 初始化PRG (基于上下文动态生成密钥) ---
    # 决定使用哪个上下文:优先使用context_for_key,否则从history_responses构建
    if context_for_key is not None:
        # 使用明确提供的上下文字符串
        context_used = context_for_key
    else:
        # 向后兼容:从history_responses构建上下文
        if history_responses is None:
            history_responses = []
        # 使用滑动窗口(最近3个响应)构建上下文
        window_size = 3
        recent_responses = history_responses[-window_size:] if len(history_responses) > 0 else []
        context_used = "||".join(recent_responses) if recent_responses else ""
    
    # === 新方法: 基于明确上下文字符串的密钥 ===
    key = generate_contextual_key([context_used])  # 传入列表以兼容原函数
    # nonce 使用轮数，确保每轮生成不同的随机序列
    nonce = str(round_num).encode('utf-8') 
    
    # === 旧方法: 基于预共享种子的静态密钥 (保留作为备注) ===
    # 如果未来需要回退到静态密钥方案，可以取消下面的注释:
    # if seed is None:
    #     seed = 42
    # combined_seed_str = str(seed)
    # round_num_str = str(round_num)
    # key = combined_seed_str.encode('utf-8')
    # nonce = round_num_str.encode('utf-8')
    
    PRG = DRBG(key, nonce)

    # --- 3. 调用新引擎核心 ---
    selected_idx_tensor, num_bits_embedded = differential_based_encoder(
        prob=probs_tensor,
        indices=indices_tensor,
        bit_stream=bit_stream,
        bit_index=bit_index,
        PRG=PRG
    )
    selected_idx = selected_idx_tensor.item()
    
    # --- 4. 转换输出并生成用于检测的"目标列表" ---
    # 将选中的索引ID转换回行为字符串
    selected_behavior = behaviors[selected_idx]
    
    # 为了让检测器(detect_watermark.py)能工作，我们需要重新计算出当时被选中的是哪个"箱子"(bin)。
    # 检测器需要知道"目标范围"是什么。
    PRG_for_detection = DRBG(key, nonce)  # 使用完全相同的参数重新创建一个PRG
    
    indices_nonzero, bins, prob_new = differential_based_recombination(probs_tensor, indices_tensor)
    prob_new = prob_new / prob_new.sum()
    
    random_p = PRG_for_detection.generate_random(n=52)
    cdf = torch.cumsum(prob_new, dim=0)
    bin_indice_idx = torch.searchsorted(cdf, random_p).item()
    
    selected_bin_start_index = bins[bin_indice_idx]
    bin_content_indices = indices_nonzero[selected_bin_start_index:]
    
    # 这就是等效于旧引擎"绿名单"的"目标列表"
    target_behavior_list = [behaviors[i] for i in bin_content_indices]
    
    return selected_behavior, target_behavior_list, num_bits_embedded, context_used


# ==============================================================================
# ================ 差分水印解码算法 (Differential Watermark Decoder) ================
# ==============================================================================

def lsb_bits2int(bits):
    """
    将比特列表转换为整数 (LSB优先)
    
    Args:
        bits (list): 比特列表,如 [1, 0, 1] 表示二进制 101 (LSB在前)
        
    Returns:
        int: 对应的整数值
        
    Example:
        >>> lsb_bits2int([1, 0, 1])  # LSB: 1*1 + 0*2 + 1*4 = 5
        5
    """
    result = 0
    for i, bit in enumerate(bits):
        result += bit * (2 ** i)
    return result


def lsb_int2bits(num, length):
    """
    将整数转换为比特列表 (LSB优先)
    
    Args:
        num (int): 要转换的整数
        length (int): 比特列表长度
        
    Returns:
        list: 比特列表 (LSB在前)
        
    Example:
        >>> lsb_int2bits(5, 3)  # 5 = 101(二进制) -> [1, 0, 1] (LSB在前)
        [1, 0, 1]
    """
    bits = []
    for _ in range(length):
        bits.append(num % 2)
        num //= 2
    return bits


def uni_cyclic_shift_dec(idx, n, PRG, precision=52):
    """
    均匀循环移位解码器 (Artifacts标准版本)
    与编码器uni_cyclic_shift_enc对应,从选中的索引中提取秘密比特。
    
    必须与编码器的PRG调用顺序完全一致!
    
    Args:
        idx (int): 选中的索引位置 (在箱子内的相对位置)
        n (int): 箱子大小
        PRG: 伪随机数生成器
        precision (int): 精度参数
        
    Returns:
        str: 提取的比特串
    """
    if n == 1:
        PRG.generate_random(n=precision)
        return ''
    
    # 必须与编码器一样,先生成R
    ptr = PRG.generate_random(n=precision)
    R = math.floor(ptr * n)
    
    k = math.floor(math.log2(n))
    t = n - 2**k
    
    # 反向循环移位
    idx_sort = (idx - R) % n
    
    if idx_sort < 2**k - t:
        bits = lsb_int2bits(idx_sort, k)
        bits = "".join([str(_) for _ in bits])
        return bits
    else:
        s1 = idx_sort - 2**k + t
        s_last = s1 % 2
        
        bits = lsb_int2bits((s1 - s_last) // 2 + 2**k - t, k)
        bits = "".join([str(_) for _ in bits])
        
        if s_last == 0:
            return bits + '0'
        else:
            return bits + '1'


def differential_based_decoder(probabilities, selected_behavior, context_for_key=None, history_responses=None, round_num=0):
    """
    差分水印解码器 - 从选中的行为中提取嵌入的秘密比特
    
    Args:
        probabilities (dict): 行为及其对应的概率字典
        selected_behavior (str): 实际选中的行为
        context_for_key (str, optional): 明确的上下文字符串,用于密钥生成(推荐从日志读取)
        history_responses (list, optional): [已弃用] 历史响应列表,仅当context_for_key为None时使用
        round_num (int): 当前轮数 (必须与编码时一致)
        
    Returns:
        str: 提取的比特串
        
    Example:
        >>> probs = {"点赞": 0.3, "收藏": 0.2, "转发": 0.5}
        >>> context = "response1||response2"
        >>> bits = differential_based_decoder(probs, "转发", context_for_key=context, round_num=1)
        >>> print(f"提取的比特: {bits}")
    """
    # --- 1. 数据格式转换 ---
    behaviors = sorted(probabilities.keys())
    probs_list = [probabilities[b] for b in behaviors]
    
    # 转换为PyTorch Tensors
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    probs_tensor = torch.tensor(probs_list, dtype=torch.float32, device=device)
    indices_tensor = torch.arange(len(behaviors), device=device)
    
    # 找到选中行为的索引
    try:
        selected_idx = behaviors.index(selected_behavior)
    except ValueError:
        print(f"⚠️ 警告: 选中的行为 '{selected_behavior}' 不在行为列表中")
        return ''
    
    prev_tensor = torch.tensor([selected_idx], device=device)
    
    # --- 2. 初始化PRG (必须与编码时完全一致) ---
    # 决定使用哪个上下文:优先使用context_for_key
    if context_for_key is not None:
        context_used = context_for_key
    else:
        # 向后兼容:从history_responses构建
        if history_responses is None:
            history_responses = []
        window_size = 3
        recent_responses = history_responses[-window_size:] if len(history_responses) > 0 else []
        context_used = "||".join(recent_responses) if recent_responses else ""
    
    key = generate_contextual_key([context_used])
    nonce = str(round_num).encode('utf-8')
    PRG = DRBG(key, nonce)
    
    # --- 3. 概率重组 (与编码器相同) ---
    indices_nonzero, bins, prob_new = differential_based_recombination(probs_tensor, indices_tensor)
    
    if prob_new.sum() == 0:
        return ''
    
    prob_new = prob_new / prob_new.sum()
    
    # --- 4. 箱子采样 (与编码器相同) ---
    random_p = PRG.generate_random(n=52)
    cdf = torch.cumsum(prob_new, dim=0)
    bin_indice_idx = torch.searchsorted(cdf, random_p).item()
    
    selected_bin_start_index = bins[bin_indice_idx]
    bin_content = indices_nonzero[selected_bin_start_index:]
    
    # --- 5. 均匀隐写解码 ---
    # 找到选中索引在箱子中的位置
    try:
        idx_in_bin = (bin_content == prev_tensor.item()).nonzero().item()
    except (RuntimeError, ValueError):
        # 如果选中的行为不在箱子中,说明出错了
        print(f"⚠️ 警告: 选中的行为不在预期的箱子中,无法解码")
        return ''
    
    # 使用循环移位解码器提取比特
    bits = uni_cyclic_shift_dec(idx=idx_in_bin, n=len(bin_content), PRG=PRG, precision=52)
    
    return bits
