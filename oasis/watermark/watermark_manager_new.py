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
    # Try to import from relative path first
    agentmark_path = Path(__file__).parent / "modules"
    if agentmark_path.exists():
        sys.path.insert(0, str(agentmark_path.parent.parent.parent.parent / "AgentMark" / "new_code"))
    
    from modules.watermark_sampler import (
        sample_behavior_differential,
        differential_based_decoder,
        generate_contextual_key
    )
    from modules.coding_utils import encode_payload, decode_message
    
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
        log_level: str = "INFO"
    ):
        """Initialize WatermarkManager"""
        self.enabled = enabled and AGENTMARK_AVAILABLE
        self.mode = mode
        
        if not AGENTMARK_AVAILABLE and enabled:
            print("⚠️ Watermark requested but AgentMark not available. Disabling watermark.")
            self.enabled = False
        
        # Default configuration
        self.config = config or {
            "payload_bit_length": 8,
            "ecc_method": "parity",
            "embedding_strategy": "cyclic"
        }
        
        # Bit stream management
        if bit_stream:
            self.bit_stream = self._prepare_bit_stream(bit_stream)
        else:
            # Default: encode a simple message
            self.bit_stream = self._prepare_bit_stream("11001101")
        
        self.bit_index = 0
        self.bits_embedded_history = []
        
        # Context management
        self.history_responses = []
        
        # Logging setup
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = os.path.join(log_dir, f"watermark-{timestamp}.log")
        
        # Setup logger
        self.logger = logging.getLogger(f"watermark-{timestamp}")
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
            self.logger.info("WatermarkManager Initialized")
            self.logger.info("=" * 70)
            self.logger.info(f"Mode: {self.mode}")
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
            # Call AgentMark's differential watermark sampler
            selected_behavior, target_list, bits_embedded, context_used = \
                sample_behavior_differential(
                    probabilities=probabilities,
                    bit_stream=self.bit_stream,
                    bit_index=self.bit_index,
                    context_for_key=context_for_key,
                    round_num=round_num
                )
            
            # Update bit index
            self.bit_index += bits_embedded
            
            # Handle cyclic embedding
            if self.bit_index >= len(self.bit_stream):
                if self.config.get("embedding_strategy") == "cyclic":
                    self.bit_index = self.bit_index % len(self.bit_stream)
                    self.logger.info(f"Bit stream cycled. Reset to index {self.bit_index}")
            
            # Log the watermarked action
            self.log_watermark_action(
                round_num=round_num,
                probabilities=probabilities,
                selected_behavior=selected_behavior,
                target_list=target_list,
                bits_embedded=bits_embedded,
                context_for_key=context_used
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
        context_for_key: str
    ):
        """Log watermarked action details"""
        log_entry = {
            "round_num": round_num,
            "probabilities_watermark": probabilities,
            "selected_behavior_watermark": selected_behavior,
            "target_list": target_list,
            "bits_embedded": bits_embedded,
            "context_for_key": context_for_key,
            "bit_index": self.bit_index
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
                for line in f:
                    if '"round_num":' in line and '"probabilities_watermark":' in line:
                        # Extract JSON from log line
                        json_start = line.find('{')
                        if json_start != -1:
                            json_str = line[json_start:]
                            try:
                                data = json.loads(json_str)
                                round_data_list.append(data)
                            except json.JSONDecodeError:
                                continue
            
            # Extract bits from each round
            for round_data in round_data_list:
                bits = differential_based_decoder(
                    probabilities=round_data['probabilities_watermark'],
                    selected_behavior=round_data['selected_behavior_watermark'],
                    context_for_key=round_data['context_for_key'],
                    round_num=round_data['round_num']
                )
                extracted_bits.append(bits)
            
            extracted_bit_stream = "".join(extracted_bits)
            
            # Decode with ECC
            result = decode_message(extracted_bit_stream, self.config)
            
            stats = {
                "rounds_parsed": len(round_data_list),
                "extracted_bit_stream": extracted_bit_stream,
                "decoded_payload": result['decoded_payload'],
                "valid": result['valid'],
                "corrected": result['corrected'],
                "ecc_method": result['ecc_method']
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
