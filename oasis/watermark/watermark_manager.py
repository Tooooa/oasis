# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
"""
WatermarkManager - Agent Watermark Integration for OASIS

This module provides a plug-and-play watermark manager that integrates
AgentMark watermarking technology into OASIS social simulation platform.

Features:
- Non-invasive integration (no core code modification)
- Supports lightweight and full modes  
- Automatic logging and tracking
- Error correction code support (none/parity/hamming)
- Context-based key generation
"""

import logging
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Import AgentMark modules
# We expect AgentMark modules to be in the workspace or in PYTHONPATH
try:
    # Try to import from relative path (within oasis.watermark.modules)
    from .modules.watermark_sampler import (
        sample_behavior_differential,
        differential_based_decoder,
        generate_contextual_key
    )
    from .modules.coding_utils import encode_payload, decode_message
    
    AGENTMARK_AVAILABLE = True
except ImportError as e:
    AGENTMARK_AVAILABLE = False
    print(f"⚠️ Warning: AgentMark modules not found. Watermark features will be disabled.")
    print(f"   Error: {e}")
    print(f"   Please ensure AgentMark code is in PYTHONPATH or in the workspace.")


class WatermarkManager:
    """
    Watermark Manager for OASIS Social Agents
    
    This class manages the watermarking process for social agents, including:
    - Bit stream management
    - Watermark embedding via probability distribution modification
    - Logging and statistics
    - Watermark extraction and verification
    
    Args:
        enabled (bool): Whether watermarking is enabled
        mode (str): Watermark mode ("lightweight" or "full")
        config (dict): Watermark configuration dictionary
        bit_stream (str, optional): Custom bit stream to embed
        log_dir (str): Directory for log files
        
    Example:
        >>> wm = WatermarkManager(enabled=True, mode="lightweight")
        >>> # In agent action: modify probabilities based on watermark bit
        >>> selected, targets, bits, ctx = wm.sample_behavior_watermark(
        ...     probabilities={"like": 0.3, "share": 0.7},
        ...     round_num=0,
        ...     context=""
        ... )
    """
    
    def __init__(
        self,
        enabled: bool = True,
        mode: str = "lightweight",
        config: Optional[Dict[str, Any]] = None,
        bit_stream: Optional[str] = None,
        log_dir: str = "./log",
        log_level: str = "INFO",
        agent_id: Optional[int] = None
    ):
        """
        Initialize WatermarkManager
        
        Args:
            agent_id: Unique identifier for the agent. If provided, this WatermarkManager
                     becomes an independent tracing unit for that specific agent.
        """
        self.enabled = enabled and AGENTMARK_AVAILABLE
        self.mode = mode
        self.agent_id = agent_id  # 🎯 新增: 独立的agent标识
        
        if not AGENTMARK_AVAILABLE and enabled:
            print("⚠️ Watermark requested but AgentMark not available. Disabling watermark.")
            self.enabled = False
        
        # Default configuration
        self.config = config or {
            "payload_bit_length": 8,
            "ecc_method": "parity",
            "embedding_strategy": "cyclic"
        }
        
        # Bit stream management - 如果提供了agent_id，则编码agent_id作为水印
        if bit_stream:
            self.bit_stream = self._prepare_bit_stream(bit_stream)
        elif agent_id is not None:
            # 🎯 新增: 使用agent_id作为水印内容 (8-bit可表示0-255的agent)
            agent_bits = format(agent_id, '08b')  # 转为8位二进制
            self.bit_stream = self._prepare_bit_stream(agent_bits)
        else:
            # Default: encode a simple message
            self.bit_stream = self._prepare_bit_stream("11001101")
        
        self.bit_index = 0
        self.bits_embedded_history = []
        
        # Context management
        self.history_responses = []
        
        # Logging setup
        self.log_dir = os.path.abspath(log_dir)  # Convert to absolute path
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Include microseconds to avoid logger/log-file collisions when multiple
        # WatermarkManager instances are created within the same second.
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        # 🎯 新增: 日志文件名包含agent_id
        if agent_id is not None:
            self.log_file = os.path.join(self.log_dir, f"watermark-agent{agent_id}-{timestamp}.log")
            logger_name = f"watermark-agent{agent_id}-{timestamp}"
        else:
            self.log_file = os.path.join(self.log_dir, f"watermark-{timestamp}.log")
            logger_name = f"watermark-{timestamp}"
        
        # Setup logger
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        if not self.logger.handlers:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(getattr(logging, log_level.upper()))
            formatter = logging.Formatter(
                "%(levelname)s - %(asctime)s - %(name)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Statistics
        self.stats = {
            "total_actions": 0,
            "watermarked_actions": 0,
            "bits_embedded": 0,
            "rounds_completed": 0
        }
        
        if self.enabled:
            self.logger.info("=" * 70)
            if agent_id is not None:
                self.logger.info(f"WatermarkManager Initialized (Agent {agent_id})")
            else:
                self.logger.info("WatermarkManager Initialized")
            self.logger.info("=" * 70)
            if agent_id is not None:
                self.logger.info(f"Agent ID: {agent_id}")
                self.logger.info(f"Agent ID (binary): {format(agent_id, '08b')}")
            self.logger.info(f"Mode: {self.mode}")
            self.logger.info(f"Bit stream: {self.bit_stream}")
            self.logger.info(f"Bit stream length: {len(self.bit_stream)}")
            self.logger.info(f"Config: {json.dumps(self.config, indent=2)}")
            self.logger.info(f"Log file: {self.log_file}")
            self.logger.info("=" * 70)
    
    def _prepare_bit_stream(self, payload: str) -> str:
        """
        Prepare bit stream with error correction encoding
        
        Args:
            payload (str): Original payload bits
            
        Returns:
            str: Encoded bit stream with ECC
        """
        if not AGENTMARK_AVAILABLE:
            return payload
        
        return encode_payload(payload, self.config)
    
    def sample_behavior_watermark(
        self,
        probabilities: Dict[str, float],
        round_num: int,
        context_for_key: str = ""
    ) -> Tuple[str, List[str], int, str]:
        """
        Sample behavior with watermark embedding (differential scheme)
        
        This is the core integration point where watermark bits are embedded
        into the agent's action selection process.
        
        Args:
            probabilities (dict): Behavior probabilities from LLM
            round_num (int): Current round number
            context_for_key (str): Context string for key generation
            
        Returns:
            tuple: (selected_behavior, target_list, bits_embedded, context_used)
            
        Example:
            >>> probs = {"like": 0.3, "comment": 0.2, "share": 0.5}
            >>> behavior, targets, bits, ctx = wm.sample_behavior_watermark(
            ...     probabilities=probs,
            ...     round_num=0,
            ...     context_for_key=""
            ... )
        """
        if not self.enabled or not AGENTMARK_AVAILABLE:
            # Fallback: simple random selection without watermark
            import random
            selected = random.choices(
                list(probabilities.keys()),
                weights=list(probabilities.values()),
                k=1
            )[0]
            return selected, [], 0, context_for_key
        
        try:
            # Prepare bit stream for cyclic embedding
            # For cyclic strategy, extend the bit stream to avoid boundary issues
            if self.config.get("embedding_strategy") == "cyclic":
                # Estimate max bits that could be embedded: log2(6) ≈ 2.58 bits/round
                # Extend to cover at least 2 full cycles beyond current position
                extended_length = self.bit_index + len(self.bit_stream) * 2
                num_repeats = (extended_length // len(self.bit_stream)) + 1
                effective_bit_stream = self.bit_stream * num_repeats
                effective_bit_index = self.bit_index
            else:
                # Sequential strategy: use original bit stream
                effective_bit_stream = self.bit_stream
                effective_bit_index = self.bit_index
            
            # Call AgentMark's differential watermark sampler
            selected_behavior, target_list, bits_embedded, context_used = \
                sample_behavior_differential(
                    probabilities=probabilities,
                    bit_stream=effective_bit_stream,
                    bit_index=effective_bit_index,
                    context_for_key=context_for_key,
                    round_num=round_num
                )
            
            # Record the bit_index BEFORE embedding (for logging)
            bit_index_before = self.bit_index
            
            # Update bit index
            old_bit_index = self.bit_index
            self.bit_index += bits_embedded
            
            # Handle cyclic embedding
            if self.bit_index >= len(self.bit_stream):
                if self.config.get("embedding_strategy") == "cyclic":
                    self.bit_index = self.bit_index % len(self.bit_stream)
                    self.logger.info(f"Bit stream cycled. Reset from {old_bit_index} to {self.bit_index}")
                    self.stats["cycles"] = self.stats.get("cycles", 0) + 1
            
            # Log the watermarked action (AFTER updating bit_index so it shows correct state)
            self.log_watermark_action(
                round_num=round_num,
                probabilities=probabilities,
                selected_behavior=selected_behavior,
                target_list=target_list,
                bits_embedded=bits_embedded,
                context_for_key=context_used,
                bit_index_before=bit_index_before  # 记录嵌入前的索引
            )
            
            # Update statistics
            self.stats["watermarked_actions"] += 1
            self.stats["bits_embedded"] += bits_embedded
            
            return selected_behavior, target_list, bits_embedded, context_used
            
        except Exception as e:
            self.logger.error(f"Error in watermark sampling: {e}", exc_info=True)
            # Fallback
            import random
            selected = random.choices(
                list(probabilities.keys()),
                weights=list(probabilities.values()),
                k=1
            )[0]
            return selected, [], 0, context_for_key
    
    def log_watermark_action(
        self,
        round_num: int,
        probabilities: Dict[str, float],
        selected_behavior: str,
        target_list: List[str],
        bits_embedded: int,
        context_for_key: str,
        bit_index_before: int = None
    ):
        """Log watermarked action details"""
        log_entry = {
            "round_num": round_num,
            "probabilities_watermark": probabilities,
            "selected_behavior_watermark": selected_behavior,
            "target_list": target_list,
            "bits_embedded": bits_embedded,
            "context_for_key": context_for_key,
            "bit_index": bit_index_before if bit_index_before is not None else self.bit_index  # 记录嵌入前的索引
        }
        
        self.logger.info(f"Round {round_num}: {json.dumps(log_entry, indent=2)}")
        self.bits_embedded_history.append(bits_embedded)
    
    def get_next_bit(self) -> str:
        """
        Get the next bit from bit stream (for manual control)
        
        Returns:
            str: Next bit ('0' or '1')
        """
        if not self.enabled:
            return '0'
        
        if self.bit_index >= len(self.bit_stream):
            if self.config.get("embedding_strategy") == "cyclic":
                self.bit_index = 0
            else:
                return '0'
        
        bit = self.bit_stream[self.bit_index]
        self.bit_index += 1
        return bit
    
    def log_action(
        self,
        agent_id: int,
        action_name: str,
        action_args: Dict[str, Any],
        bit: str
    ):
        """
        Log action with watermark bit (for manual watermarking)
        
        Args:
            agent_id (int): Agent ID
            action_name (str): Action name
            action_args (dict): Action arguments
            bit (str): Watermark bit embedded
        """
        if not self.enabled:
            return
        
        log_entry = {
            "agent_id": agent_id,
            "action_name": action_name,
            "action_args": action_args,
            "watermark_bit": bit,
            "bit_index": self.bit_index - 1
        }
        
        self.logger.info(f"Action: {json.dumps(log_entry)}")
        self.stats["total_actions"] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get watermark statistics
        
        Returns:
            dict: Statistics dictionary
        """
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "bit_stream_length": len(self.bit_stream),
            "current_bit_index": self.bit_index,
            "bits_remaining": len(self.bit_stream) - self.bit_index,
            "total_actions": self.stats["total_actions"],
            "watermarked_actions": self.stats["watermarked_actions"],
            "bits_embedded": self.stats["bits_embedded"],
            "rounds_completed": self.stats["rounds_completed"],
            "cycles": self.stats.get("cycles", 0),
            "log_file": self.log_file
        }
    
    def extract_watermark_from_log(
        self,
        log_path: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Extract watermark from log file
        
        Args:
            log_path (str, optional): Path to log file. If None, use current log.
            
        Returns:
            tuple: (extracted_bits, statistics)
        """
        if not self.enabled or not AGENTMARK_AVAILABLE:
            return "", {"error": "Watermark not enabled or AgentMark not available"}
        
        if log_path is None:
            log_path = self.log_file
        
        try:
            # Parse log file
            extracted_bits = []
            round_data_list = []
            
            with open(log_path, 'r') as f:
                content = f.read()
            
            # Parse multi-line JSON from log
            # Look for "Round X: {" patterns and extract the JSON
            lines = content.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i]
                if 'Round ' in line and ': {' in line:
                    # Found start of JSON block
                    json_start = line.find('{')
                    if json_start != -1:
                        # Collect all lines until we find the closing }
                        json_lines = [line[json_start:]]
                        i += 1
                        brace_count = 1
                        while i < len(lines) and brace_count > 0:
                            current_line = lines[i]
                            json_lines.append(current_line)
                            brace_count += current_line.count('{') - current_line.count('}')
                            i += 1
                            if brace_count == 0:
                                break
                        
                        # Parse the collected JSON
                        json_str = '\n'.join(json_lines)
                        try:
                            data = json.loads(json_str)
                            round_data_list.append(data)
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Failed to parse JSON: {e}")
                            pass
                else:
                    i += 1
            
            # Extract bits from each round
            for round_data in round_data_list:
                # Only extract from rounds that actually embedded bits
                bits_embedded = round_data.get('bits_embedded', 0)
                if bits_embedded > 0:
                    bits = differential_based_decoder(
                        probabilities=round_data['probabilities_watermark'],
                        selected_behavior=round_data['selected_behavior_watermark'],
                        context_for_key=round_data['context_for_key'],
                        round_num=round_data['round_num']
                    )
                    extracted_bits.append(bits)
            
            extracted_bit_stream = "".join(extracted_bits)
            
            # Calculate expected length based on config
            payload_length = self.config.get('payload_bit_length', 8)
            ecc_method = self.config.get('ecc_method', 'none')
            
            if ecc_method == 'parity':
                expected_length = payload_length + 1  # 8 + 1 = 9
            elif ecc_method == 'hamming':
                expected_length = 21  # Hamming(21,16)
            else:
                expected_length = payload_length
            
            # 按编码长度分块连续解码（循环校验）
            num_messages = len(extracted_bit_stream) // expected_length
            remainder = len(extracted_bit_stream) % expected_length
            
            if num_messages == 0 and remainder > 0:
                # 不足一个完整块，进行部分解码
                self.logger.warning(f"Extracted only {len(extracted_bit_stream)} bits, expected {expected_length}, performing partial decode")
                result = decode_message(extracted_bit_stream, self.config)
                decoded_payloads = [result.get('decoded_payload', '')]
                validation_results = [result]
                total_corrections = 0
                failed_validations = 1 if not result.get('valid') else 0
                partial_is_valid = False  # 初始化为False（不足一个完整块）
            else:
                # 有完整的块，进行连续解码
                self.logger.info(f"Decoding {num_messages} complete messages ({expected_length} bits each)")
                if remainder > 0:
                    self.logger.warning(f"Remaining {remainder} bits will be decoded as partial message")
                
                decoded_payloads = []
                validation_results = []
                total_corrections = 0
                failed_validations = 0
                
                # 解码所有完整块
                for i in range(num_messages):
                    start_idx = i * expected_length
                    end_idx = start_idx + expected_length
                    encoded_message = extracted_bit_stream[start_idx:end_idx]
                    
                    result = decode_message(encoded_message, self.config)
                    decoded_payloads.append(result.get('decoded_payload', ''))
                    validation_results.append(result)
                    
                    if result.get('corrected', False):
                        total_corrections += 1
                    if not result.get('valid'):
                        failed_validations += 1
                
                # 如果有余数，解码最后一个不完整的块
                partial_is_valid = None  # 默认为None,只有当存在余数时才会被设置
                if remainder > 0:
                    partial_is_valid = False  # 初始化为False
                    partial_message = extracted_bit_stream[num_messages * expected_length:]
                    result = decode_message(partial_message, self.config)
                    decoded_payloads.append(result.get('decoded_payload', ''))
                    validation_results.append(result)
                    
                    # ✅ 改进的余数验证逻辑：与原始 bit_stream 的循环匹配
                    # 计算余数应该对应原始比特流的哪个位置
                    total_embedded_bits = num_messages * payload_length + len(result.get('decoded_payload', ''))
                    expected_partial_position = (total_embedded_bits - len(result.get('decoded_payload', ''))) % len(self.bit_stream)
                    
                    # 提取原始比特流中对应的部分
                    expected_partial = ""
                    for i in range(len(result.get('decoded_payload', ''))):
                        expected_partial += self.bit_stream[(expected_partial_position + i) % len(self.bit_stream)]
                    
                    # 比较提取的部分与期望的部分
                    if result.get('decoded_payload', '') == expected_partial:
                        partial_is_valid = True
                        self.logger.info(f"✅ Partial bits validated: {result.get('decoded_payload', '')} matches expected {expected_partial}")
                    else:
                        # ⚠️ 部分块不匹配时只记录警告，不计入验证失败
                        # 只要至少有一个完整块验证成功即可
                        self.logger.warning(f"⚠️ Partial bits mismatch: got {result.get('decoded_payload', '')}, expected {expected_partial} (不影响验证结果)")
            
            decoded_bit_stream = "".join(decoded_payloads)
            
            # ✅ 改进的准确率计算：用提取的原始bit与bit_stream循环比较
            # 注意: extracted_bit_stream是带ECC的原始提取，应该与bit_stream(也带ECC)比对
            original_bits = self.bit_stream
            accuracy = 0.0
            if extracted_bit_stream:
                # 循环比较，支持超出原始长度的情况
                matches = 0
                for i, bit in enumerate(extracted_bit_stream):
                    expected_bit = original_bits[i % len(original_bits)]
                    if bit == expected_bit:
                        matches += 1
                accuracy = matches / len(extracted_bit_stream) * 100
            
            # ✅ 改进的验证逻辑：
            # - 如果有完整块 (num_messages > 0)，只要至少有一个完整块验证成功就算通过
            # - 如果没有完整块 (num_messages == 0)，则必须部分块验证成功
            # - 部分块的失败不影响整体验证结果（只要有完整块通过）
            
            # 计算完整块的失败数（只计算完整块的验证失败）
            complete_blocks_failed = sum(1 for i, result in enumerate(validation_results[:num_messages]) if not result.get('valid'))
            
            # 验证是否通过的条件：
            # 1. 如果有完整块，至少有一个完整块验证成功（即不是所有完整块都失败）
            # 2. 如果没有完整块，则不足一个完整块无法验证，返回 False
            is_valid = num_messages > 0 and complete_blocks_failed < num_messages
            
            # 错误信息只报告完整块的失败
            error_msg = None
            if num_messages == 0:
                error_msg = f"提取的 {len(extracted_bit_stream)} bits 不足一个完整块 ({expected_length} bits)"
            elif complete_blocks_failed > 0:
                error_msg = f"{num_messages} 个完整块中有 {complete_blocks_failed} 个验证失败"
            
            stats = {
                "actions_processed": len(round_data_list),
                "successful_extractions": len([b for b in extracted_bits if b]),
                "extracted_bit_stream": extracted_bit_stream,
                "decoded_payload": decoded_bit_stream,  # 所有解码后的payload拼接
                "num_messages": num_messages + (1 if remainder > 0 else 0),
                "complete_messages": num_messages,
                "partial_bits": remainder,
                "partial_is_valid": partial_is_valid if remainder > 0 else None,
                "total_corrections": total_corrections,
                "failed_validations": complete_blocks_failed,  # 只记录完整块的失败数
                "valid": is_valid,  # ✅ 新逻辑：至少有一个完整块验证成功
                "corrected": total_corrections > 0,
                "accuracy": accuracy,  # ✅ 新增准确率字段
                "ecc_method": self.config.get('ecc_method', 'none'),
                "error": error_msg
            }
            
            self.logger.info("=" * 70)
            self.logger.info("Watermark Extraction Complete")
            self.logger.info("=" * 70)
            self.logger.info(f"Statistics: {json.dumps(stats, indent=2)}")
            
            return extracted_bit_stream, stats
            
        except Exception as e:
            self.logger.error(f"Error extracting watermark: {e}", exc_info=True)
            return "", {"error": str(e)}
    
    def update_context(self, response: str):
        """
        Update history context with new response
        
        Args:
            response (str): New response to add to history
        """
        self.history_responses.append(response)
        
        # Keep only recent history (sliding window)
        window_size = 3
        if len(self.history_responses) > window_size:
            self.history_responses = self.history_responses[-window_size:]
    
    def get_context_for_key(self) -> str:
        """
        Get context string for key generation
        
        Returns:
            str: Context string (concatenated recent responses)
        """
        if not self.history_responses:
            return ""
        
        return "||".join(self.history_responses)
    
    def reset(self):
        """Reset watermark manager state"""
        self.bit_index = 0
        self.history_responses = []
        self.bits_embedded_history = []
        self.stats = {
            "total_actions": 0,
            "watermarked_actions": 0,
            "bits_embedded": 0,
            "rounds_completed": 0
        }
        
        if self.enabled:
            self.logger.info("WatermarkManager reset")
    
    def __repr__(self) -> str:
        return f"WatermarkManager(enabled={self.enabled}, mode={self.mode}, bits={len(self.bit_stream)})"
