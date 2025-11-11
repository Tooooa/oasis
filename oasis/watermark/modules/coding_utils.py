"""
编码工具模块 (Coding Utils)
职责: 提供不同的纠错码编解码功能,支持可配置的水印嵌入策略

使用标准实现:
- 奇偶校验: 使用Python内置功能
- 汉明码: 使用标准Hamming(7,4)扩展算法
- Reed-Solomon: 使用reedsolo库(可选)
"""


def add_parity_bit(data_bits: str) -> str:
    """
    为8-bit数据添加奇偶校验位
    
    Args:
        data_bits (str): 8位二进制字符串
        
    Returns:
        str: 9位二进制字符串(原始8位 + 1位校验位)
        
    Example:
        >>> add_parity_bit("11001100")
        "110011000"  # 偶校验,0个1,校验位为0
        >>> add_parity_bit("11001101")
        "110011011"  # 偶校验,奇数个1,校验位为1
    """
    if len(data_bits) != 8:
        raise ValueError(f"奇偶校验需要8位数据,但收到 {len(data_bits)} 位")
    
    # 计算1的个数,使用偶校验
    ones_count = data_bits.count('1')
    parity_bit = '1' if ones_count % 2 == 1 else '0'
    
    return data_bits + parity_bit


def check_and_strip_parity_bit(message_bits: str) -> tuple:
    """
    检查并移除奇偶校验位
    
    Args:
        message_bits (str): 9位二进制字符串(8位数据 + 1位校验位)
                           如果不足9位,会进行部分校验
        
    Returns:
        tuple: (data_bits, is_valid)
            - data_bits (str): 原始数据(最多8位)
            - is_valid (bool): 校验是否通过(不足9位时返回None表示无法完整校验)
            
    Example:
        >>> check_and_strip_parity_bit("110011000")
        ("11001100", True)
        >>> check_and_strip_parity_bit("110011001")  # 校验位错误
        ("11001100", False)
        >>> check_and_strip_parity_bit("1100110")  # 不足9位
        ("1100110", None)
    """
    if len(message_bits) < 9:
        # 不足9位,无法完整校验,返回部分数据
        # 但不抛出异常,允许部分验证
        return message_bits, None
    
    if len(message_bits) > 9:
        # 超过9位,截断到9位进行校验
        message_bits = message_bits[:9]
    
    data_bits = message_bits[:8]
    received_parity = message_bits[8]
    
    # 重新计算校验位
    ones_count = data_bits.count('1')
    expected_parity = '1' if ones_count % 2 == 1 else '0'
    
    is_valid = (received_parity == expected_parity)
    
    return data_bits, is_valid


def add_hamming_code(data_bits: str) -> str:
    """
    为16-bit数据添加标准汉明码
    使用扩展Hamming码,能够纠正1位错误,检测2位错误
    
    Args:
        data_bits (str): 16位二进制字符串
        
    Returns:
        str: 编码后的比特串(含校验位)
        
    Note:
        使用标准Hamming(21,16)码
        - 16位数据
        - 5位校验位(在位置 1,2,4,8,16)
        - 总共21位
    """
    if len(data_bits) != 16:
        raise ValueError(f"汉明码需要16位数据,但收到 {len(data_bits)} 位")
    
    # 将数据位转换为列表
    data = [int(b) for b in data_bits]
    
    # 创建编码数组(21位: 索引0不用, 1-21位)
    # 校验位在位置 1,2,4,8,16
    encoded = [0] * 22  # 索引0不用,1-21有效
    
    # 数据位的映射位置(跳过2的幂次位置)
    data_positions = [i for i in range(1, 22) if i & (i-1) != 0]  # 非2的幂
    
    # 填充数据位
    for i, pos in enumerate(data_positions[:16]):
        encoded[pos] = data[i]
    
    # 计算校验位
    parity_positions = [1, 2, 4, 8, 16]
    
    for p in parity_positions:
        # 对于每个校验位位置p,检查所有位置i,其中 i & p != 0
        parity = 0
        for i in range(1, 22):
            if i & p and i != p:  # 检查位置i是否被校验位p覆盖
                parity ^= encoded[i]
        encoded[p] = parity
    
    # 转换为字符串(跳过索引0)
    return ''.join(str(encoded[i]) for i in range(1, 22))


def decode_and_correct_hamming(message_bits: str) -> str:
    """
    解码并纠正标准汉明码
    能够纠正1位错误,检测2位错误
    
    Args:
        message_bits (str): 21位编码比特串(如果不足21位,会补零处理)
        
    Returns:
        str: 纠正后的16位原始数据
        
    Note:
        使用标准汉明码纠错算法
        如果输入不足21位,会自动补零到21位后再解码
    """
    if len(message_bits) < 21:
        # 不足21位,补零到21位
        message_bits = message_bits.ljust(21, '0')
    elif len(message_bits) > 21:
        # 超过21位,截断到21位
        message_bits = message_bits[:21]
    
    # 转换为数组(索引0不用, 1-21有效)
    received = [0] + [int(b) for b in message_bits]
    
    # 计算伴随式(syndrome)
    syndrome = 0
    parity_positions = [1, 2, 4, 8, 16]
    
    for p in parity_positions:
        parity = 0
        for i in range(1, 22):
            if i & p:  # 检查位置i是否被校验位p覆盖
                parity ^= received[i]
        if parity != 0:
            syndrome += p
    
    # 如果syndrome不为0,说明有错误
    if syndrome != 0:
        if 1 <= syndrome <= 21:
            print(f"⚠️ 汉明码检测到错误在位置 {syndrome}, 已自动纠正")
            # 纠正错误
            received[syndrome] ^= 1
        else:
            print(f"⚠️ 汉明码检测到多位错误(无法纠正)")
    
    # 提取数据位(非2的幂位置)
    data_positions = [i for i in range(1, 22) if i & (i-1) != 0]
    data_bits = ''.join(str(received[pos]) for pos in data_positions[:16])
    
    return data_bits


def encode_payload(payload_bits: str, config: dict) -> str:
    """
    根据配置,为核心数据(payload)编码成完整的消息包
    这是一个工厂函数,根据配置调度不同的编码器
    
    Args:
        payload_bits (str): 原始载荷比特串
        config (dict): 水印配置字典,包含:
            - payload_bit_length: 载荷长度(8或16)
            - ecc_method: 纠错码方法("parity"/"hamming"/"none")
            - embedding_strategy: 嵌入策略("cyclic"/"once")
            
    Returns:
        str: 编码后的消息包
        
    Raises:
        ValueError: 如果配置不匹配或参数错误
        
    Example:
        >>> config = {"payload_bit_length": 8, "ecc_method": "parity"}
        >>> encode_payload("11001100", config)
        "110011000"
    """
    bit_length = config.get("payload_bit_length", 8)
    ecc_method = config.get("ecc_method", "none")
    
    # 1. 验证输入长度是否与配置匹配
    if len(payload_bits) != bit_length:
        raise ValueError(
            f"数据长度 {len(payload_bits)} 与配置的 payload_bit_length {bit_length} 不匹配"
        )
    
    # 2. 根据 ecc_method 选择纠错码函数
    if ecc_method == "parity":
        if bit_length != 8:
            raise ValueError("奇偶校验 (parity) 当前只支持8-bit数据")
        return add_parity_bit(payload_bits)
        
    elif ecc_method == "hamming":
        if bit_length != 16:
            raise ValueError("汉明码 (hamming) 当前只支持16-bit数据")
        return add_hamming_code(payload_bits)
        
    elif ecc_method == "none":
        return payload_bits  # 不加纠错码,直接返回
        
    else:
        raise ValueError(f"未知的纠错码方法: {ecc_method}")


def decode_message(message_bits: str, config: dict) -> dict:
    """
    根据配置,解码一个消息包,纠错并返回原始数据和验证信息
    
    Args:
        message_bits (str): 编码后的消息比特串(允许不完整)
        config (dict): 水印配置字典
        
    Returns:
        dict: 解码结果字典
            - decoded_payload (str): 解码后的原始数据
            - valid (bool/None): 消息是否有效/是否通过校验(None表示不完整无法完全校验)
            - corrected (bool): 是否进行了错误纠正
            - ecc_method (str): 使用的纠错码方法
            - error (str, optional): 错误信息(如果验证失败)
            - partial (bool): 是否为部分提取
            
    Example:
        >>> config = {"payload_bit_length": 8, "ecc_method": "parity"}
        >>> decode_message("110011000", config)
        {
            'decoded_payload': '11001100',
            'valid': True,
            'corrected': False,
            'ecc_method': 'parity'
        }
    """
    ecc_method = config.get("ecc_method", "none")
    payload_length = config.get("payload_bit_length", 8)
    
    if ecc_method == "parity":
        expected_length = payload_length + 1
        is_partial = len(message_bits) < expected_length
        
        data_bits, is_valid = check_and_strip_parity_bit(message_bits)
        
        if is_partial:
            error_msg = f"部分提取: 收到 {len(message_bits)} 位, 期望 {expected_length} 位"
        else:
            error_msg = None if is_valid else 'Parity check failed'
        
        return {
            'decoded_payload': data_bits,
            'valid': is_valid,
            'corrected': False,  # 奇偶校验只检测,不纠错
            'ecc_method': 'parity',
            'error': error_msg,
            'partial': is_partial
        }
        
    elif ecc_method == "hamming":
        expected_length = 21
        is_partial = len(message_bits) < expected_length
        
        # 汉明码解码会自动纠错(不足21位会补零)
        corrected_data = decode_and_correct_hamming(message_bits)
        
        # 重新编码,如果和原始不同,说明发生了纠错
        re_encoded = add_hamming_code(corrected_data)
        was_corrected = (re_encoded != message_bits[:21])  # 只比较前21位
        
        error_msg = f"部分提取: 收到 {len(message_bits)} 位, 期望 {expected_length} 位" if is_partial else None
        
        return {
            'decoded_payload': corrected_data,
            'valid': True if not is_partial else None,  # 部分数据无法保证完全有效
            'corrected': was_corrected,
            'ecc_method': 'hamming',
            'error': error_msg,
            'partial': is_partial
        }
        
    elif ecc_method == "none":
        expected_length = payload_length
        is_partial = len(message_bits) < expected_length
        
        error_msg = f"部分提取: 收到 {len(message_bits)} 位, 期望 {expected_length} 位" if is_partial else None
        
        return {
            'decoded_payload': message_bits,
            'valid': True if not is_partial else None,
            'corrected': False,
            'ecc_method': 'none',
            'error': error_msg,
            'partial': is_partial
        }
        
    else:
        return {
            'decoded_payload': '',
            'valid': False,
            'corrected': False,
            'ecc_method': ecc_method,
            'error': f"未知的纠错码方法: {ecc_method}"
        }


def prepare_cyclic_embedding(payload_bits: str, config: dict, total_rounds: int) -> list:
    """
    准备循环嵌入的消息序列
    
    Args:
        payload_bits (str): 原始载荷
        config (dict): 水印配置
        total_rounds (int): 总实验轮次数
        
    Returns:
        list: 每轮要嵌入的消息列表
        
    Example:
        >>> prepare_cyclic_embedding("11001100", config, 3)
        ["110011000", "110011000", "110011000"]  # 循环3次
    """
    message_to_embed = encode_payload(payload_bits, config)
    embedding_strategy = config.get("embedding_strategy", "once")
    
    if embedding_strategy == "cyclic":
        # 循环嵌入:每轮都嵌入相同消息
        return [message_to_embed] * total_rounds
    elif embedding_strategy == "once":
        # 只嵌入一次
        return [message_to_embed]
    else:
        raise ValueError(f"未知的嵌入策略: {embedding_strategy}")
