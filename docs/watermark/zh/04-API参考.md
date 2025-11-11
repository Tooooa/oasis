# API 参考 - 完整接口文档

> **完整文档**: OASIS AgentMark 水印模块所有 API  
> **适合**: 开发者、集成人员

---

## 📋 目录

1. [WatermarkManager](#watermarkmanager)
2. [WatermarkSampler](#watermarksampler)
3. [ECCFactory](#eccfactory)
4. [AgentSimulator](#agentsimulator)
5. [工具函数](#工具函数)
6. [配置项](#配置项)

---

## WatermarkManager

**路径**: `oasis.watermark.WatermarkManager`

主要的水印管理类，负责整个水印生命周期。

### 类定义

```python
class WatermarkManager:
    """
    水印管理器
    
    管理水印的嵌入、提取和验证流程
    """
```

### 构造函数

```python
def __init__(
    self,
    enabled: bool = True,
    bit_stream: str = "11001101",
    delta: float = 2.0,
    gamma: float = 0.25,
    ecc_type: str = "parity",
    log_dir: str = "outputs/logs/watermark",
    agent_id: Optional[int] = None
)
```

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | `bool` | `True` | 是否启用水印功能 |
| `bit_stream` | `str` | `"11001101"` | 要嵌入的原始 bit 流（payload） |
| `delta` | `float` | `2.0` | 差分采样的偏移强度 |
| `gamma` | `float` | `0.25` | Softmax 的平滑系数 |
| `ecc_type` | `str` | `"parity"` | ECC 编码类型（"parity"） |
| `log_dir` | `str` | `"outputs/logs/watermark"` | 日志文件保存目录 |
| `agent_id` | `Optional[int]` | `None` | Agent ID（用于日志文件命名） |

**返回**: `WatermarkManager` 实例

**示例**:

```python
from oasis.watermark import WatermarkManager

# 基础用法
watermark_mgr = WatermarkManager()

# 自定义配置
watermark_mgr = WatermarkManager(
    enabled=True,
    bit_stream="11110000",
    delta=2.5,
    gamma=0.30,
    ecc_type="parity",
    log_dir="my_logs/watermark",
    agent_id=0
)

# 禁用水印
watermark_mgr = WatermarkManager(enabled=False)
```

---

### 方法: sample_behavior_watermark

嵌入水印并采样行为。

```python
def sample_behavior_watermark(
    self,
    probabilities: Dict[str, float],
    round_num: int,
    context_for_key: str = ""
) -> Tuple[str, List[str], str, str]
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `probabilities` | `Dict[str, float]` | 行为概率分布，如 `{"create_post": 0.45, "like": 0.35}` |
| `round_num` | `int` | 当前轮次编号（从 0 开始） |
| `context_for_key` | `str` | 上下文字符串（用于生成密钥，当前未使用） |

**返回**: `Tuple[str, List[str], str, str]`

- `selected_behavior` (`str`): 选中的行为
- `targets` (`List[str]`): 行为目标列表（当前返回空列表）
- `embedded_bit` (`str`): 嵌入的 bit 值（"0" 或 "1"，如果跳过则为 ""）
- `context_for_key` (`str`): 返回的上下文（与输入相同）

**示例**:

```python
# 行为概率分布
probabilities = {
    "create_post": 0.45,
    "like_post": 0.35,
    "comment": 0.20
}

# 采样行为（自动嵌入水印）
behavior, targets, bit, context = watermark_mgr.sample_behavior_watermark(
    probabilities=probabilities,
    round_num=0,
    context_for_key="user_context"
)

print(f"Selected behavior: {behavior}")  # e.g., "create_post"
print(f"Embedded bit: {bit}")            # e.g., "1"
```

**注意事项**:

- 如果 `enabled=False`，直接返回概率最高的行为，不嵌入水印
- 如果概率分布太集中（前两个差距 > 10%），会跳过嵌入
- 自动记录日志到 `log_dir/watermark-agent{id}-{timestamp}.log`

---

### 方法: extract_and_verify_watermark

从日志文件提取并验证水印。

```python
def extract_and_verify_watermark(
    self,
    log_file: str
) -> Dict[str, Any]
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `log_file` | `str` | 日志文件路径 |

**返回**: `Dict[str, Any]`

```python
{
    "original_payload": str,     # 原始 payload
    "decoded_payload": str,      # 解码后的 payload
    "match": bool,               # payload 是否匹配
    "parity_check": str,         # "passed" 或 "failed"
    "embedding_rate": float,     # 嵌入率 (0.0-1.0)
    "total_rounds": int,         # 总轮数
    "embedded_count": int,       # 嵌入成功次数
    "skipped_count": int         # 跳过次数
}
```

**示例**:

```python
# 提取并验证
log_file = "outputs/logs/watermark/2025-11/watermark-agent0-20251111-143052.log"
result = watermark_mgr.extract_and_verify_watermark(log_file)

print(f"Original payload: {result['original_payload']}")
print(f"Decoded payload:  {result['decoded_payload']}")
print(f"Match: {result['match']}")
print(f"Parity check: {result['parity_check']}")
print(f"Embedding rate: {result['embedding_rate']:.1%}")

# 验证成功的条件
if result['match'] and result['parity_check'] == 'passed':
    print("✅ WATERMARK VERIFIED!")
else:
    print("❌ VERIFICATION FAILED")
```

---

### 方法: flush_logs

强制刷新日志缓冲区到文件。

```python
def flush_logs(self) -> None
```

**参数**: 无

**返回**: `None`

**示例**:

```python
# 在关键点刷新日志
for round_num in range(10):
    watermark_mgr.sample_behavior_watermark(...)
    
    if round_num % 5 == 0:
        watermark_mgr.flush_logs()  # 每 5 轮刷新一次

# 实验结束时刷新
watermark_mgr.flush_logs()
```

---

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `enabled` | `bool` | 是否启用水印 |
| `bit_stream` | `str` | ECC 编码后的 bit 流 |
| `original_payload` | `str` | 原始 payload |
| `current_bit_index` | `int` | 当前嵌入位置 |
| `delta` | `float` | 偏移强度 |
| `gamma` | `float` | 平滑系数 |
| `log_file` | `str` | 日志文件路径 |
| `stats` | `Dict` | 统计信息 |

**示例**:

```python
# 访问属性
print(f"Enabled: {watermark_mgr.enabled}")
print(f"Bit stream: {watermark_mgr.bit_stream}")
print(f"Current index: {watermark_mgr.current_bit_index}")

# 查看统计
print(f"Stats: {watermark_mgr.stats}")
```

---

## WatermarkSampler

**路径**: `oasis.watermark.watermark_sampler`

实现差分水印采样算法。

### 函数: differential_based_recombination

```python
def differential_based_recombination(
    sorted_behaviors: List[Tuple[str, float]],
    bit: str,
    delta: float = 2.0,
    gamma: float = 0.25
) -> Tuple[str, List[float]]
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `sorted_behaviors` | `List[Tuple[str, float]]` | 排序后的行为列表 `[(behavior, prob), ...]` |
| `bit` | `str` | 要嵌入的 bit（"0" 或 "1"） |
| `delta` | `float` | 偏移强度（默认 2.0） |
| `gamma` | `float` | 平滑系数（默认 0.25） |

**返回**: `Tuple[str, List[float]]`

- `selected_behavior` (`str`): 选中的行为
- `updated_probabilities` (`List[float]`): 更新后的概率分布

**示例**:

```python
from oasis.watermark.watermark_sampler import differential_based_recombination

# 排序后的行为
sorted_behaviors = [
    ("create_post", 0.45),
    ("like_post", 0.35),
    ("comment", 0.20)
]

# 嵌入 bit = "1"
behavior, probs = differential_based_recombination(
    sorted_behaviors=sorted_behaviors,
    bit="1",
    delta=2.0,
    gamma=0.25
)

print(f"Selected: {behavior}")
print(f"Updated probs: {probs}")
```

---

## ECCFactory

**路径**: `oasis.watermark.coding_utils.ECCFactory`

ECC 编码/解码工厂类。

### 方法: create

创建 ECC 编码器/解码器。

```python
@classmethod
def create(cls, ecc_type: str) -> object
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `ecc_type` | `str` | ECC 类型（"parity"） |

**返回**: ECC 编码器/解码器对象

**示例**:

```python
from oasis.watermark.coding_utils import ECCFactory

# 创建 Parity ECC
ecc = ECCFactory.create("parity")

# 编码
encoded = ecc.encode("11001101")
print(f"Encoded: {encoded}")  # "110011011"

# 解码
decoded, valid = ecc.decode(encoded)
print(f"Decoded: {decoded}")  # "11001101"
print(f"Valid: {valid}")      # True
```

---

### 方法: register

注册新的 ECC 方法。

```python
@classmethod
def register(cls, name: str, ecc_class: Type) -> None
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | ECC 方法名称 |
| `ecc_class` | `Type` | ECC 类 |

**返回**: `None`

**示例**:

```python
from oasis.watermark.coding_utils import ECCFactory

# 自定义 ECC
class CustomECC:
    @staticmethod
    def encode(payload: str) -> str:
        # 你的编码逻辑
        return payload + "0"
    
    @staticmethod
    def decode(encoded: str) -> Tuple[str, bool]:
        # 你的解码逻辑
        return encoded[:-1], True

# 注册
ECCFactory.register("custom", CustomECC)

# 使用
watermark_mgr = WatermarkManager(ecc_type="custom")
```

---

## AgentSimulator

**路径**: `oasis.watermark.agent_simulator.AgentSimulator`

LLM 行为模拟器。

### 构造函数

```python
def __init__(self, model: object)
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `model` | `object` | LLM 模型实例 |

**返回**: `AgentSimulator` 实例

**示例**:

```python
from oasis.watermark.agent_simulator import AgentSimulator
from oasis.inference import ModelFactory, ModelPlatformType

# 创建 LLM 模型
model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type="gpt-4o-mini"
)

# 创建模拟器
simulator = AgentSimulator(model)
```

---

### 方法: generate_behavior_probabilities

生成行为概率分布。

```python
def generate_behavior_probabilities(
    self,
    context: str,
    available_actions: List[str]
) -> Dict[str, float]
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `context` | `str` | 上下文信息 |
| `available_actions` | `List[str]` | 可用行为列表 |

**返回**: `Dict[str, float]` - 行为概率分布

**示例**:

```python
# 上下文
context = "User is browsing their feed"

# 可用行为
actions = ["create_post", "like_post", "comment", "share"]

# 生成概率
probabilities = simulator.generate_behavior_probabilities(
    context=context,
    available_actions=actions
)

print(probabilities)
# {"create_post": 0.35, "like_post": 0.40, "comment": 0.15, "share": 0.10}
```

---

## 工具函数

### parity_encode

Parity 编码。

```python
def parity_encode(payload: str) -> str
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `payload` | `str` | 原始 bit 流 |

**返回**: `str` - 编码后的 bit 流（payload + parity bit）

**示例**:

```python
from oasis.watermark.coding_utils import parity_encode

encoded = parity_encode("11001101")
print(encoded)  # "110011011" (添加了 parity bit "1")
```

---

### parity_decode

Parity 解码。

```python
def parity_decode(encoded: str) -> Tuple[str, bool]
```

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `encoded` | `str` | 编码后的 bit 流 |

**返回**: `Tuple[str, bool]`

- `payload` (`str`): 解码后的 payload
- `valid` (`bool`): 校验是否通过

**示例**:

```python
from oasis.watermark.coding_utils import parity_decode

# 正确的编码
payload, valid = parity_decode("110011011")
print(f"Payload: {payload}")  # "11001101"
print(f"Valid: {valid}")      # True

# 错误的编码（bit 翻转）
payload, valid = parity_decode("110011001")
print(f"Payload: {payload}")  # "11001100"
print(f"Valid: {valid}")      # False
```

---

### can_embed_watermark

检查概率分布是否适合嵌入水印。

```python
def can_embed_watermark(
    probabilities: Dict[str, float],
    threshold: float = 0.10
) -> bool
```

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `probabilities` | `Dict[str, float]` | - | 行为概率分布 |
| `threshold` | `float` | `0.10` | 前两个概率的最大差距 |

**返回**: `bool` - 是否可以嵌入

**示例**:

```python
from oasis.watermark.utils import can_embed_watermark

# 可以嵌入
probs1 = {"create_post": 0.45, "like": 0.38, "comment": 0.17}
print(can_embed_watermark(probs1))  # True (0.45-0.38=0.07 < 0.10)

# 无法嵌入
probs2 = {"create_post": 0.92, "like": 0.05, "comment": 0.03}
print(can_embed_watermark(probs2))  # False (0.92-0.05=0.87 > 0.10)
```

---

## 配置项

### 环境变量

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `OPENAI_API_KEY` | `str` | OpenAI API Key |
| `DEEPSEEK_API_KEY` | `str` | DeepSeek API Key |
| `WATERMARK_ENABLED` | `bool` | 是否启用水印（"true"/"false"） |
| `WATERMARK_BIT_STREAM` | `str` | 默认 bit stream |
| `WATERMARK_DELTA` | `float` | 默认 delta 值 |
| `WATERMARK_GAMMA` | `float` | 默认 gamma 值 |
| `WATERMARK_LOG_DIR` | `str` | 日志目录 |

**示例**:

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY = "sk-xxx"
$env:WATERMARK_ENABLED = "true"
$env:WATERMARK_BIT_STREAM = "11110000"

# Linux/Mac
export DEEPSEEK_API_KEY="sk-xxx"
export WATERMARK_ENABLED=true
export WATERMARK_BIT_STREAM="11110000"
```

---

### 配置文件 (config.json)

```json
{
  "model": {
    "platform": "openai",
    "type": "deepseek-chat",
    "url": "https://api.deepseek.com",
    "api_key": "sk-xxx"
  },
  "watermark": {
    "enabled": true,
    "bit_stream": "11001101",
    "delta": 2.0,
    "gamma": 0.25,
    "ecc_type": "parity",
    "log_dir": "outputs/logs/watermark"
  },
  "database": {
    "path": "outputs/databases/current/oasis.db"
  }
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `model.platform` | `str` | LLM 平台（"openai", "anthropic"） |
| `model.type` | `str` | 模型类型（"gpt-4o-mini", "deepseek-chat"） |
| `model.url` | `str` | API URL（可选，用于自定义端点） |
| `model.api_key` | `str` | API Key |
| `watermark.enabled` | `bool` | 是否启用水印 |
| `watermark.bit_stream` | `str` | 原始 payload |
| `watermark.delta` | `float` | 偏移强度 |
| `watermark.gamma` | `float` | 平滑系数 |
| `watermark.ecc_type` | `str` | ECC 类型 |
| `watermark.log_dir` | `str` | 日志目录 |
| `database.path` | `str` | 数据库文件路径 |

---

## 完整示例

### 基础使用

```python
from oasis.watermark import WatermarkManager
from oasis.social_agent import SocialAgent

# 1. 创建水印管理器
watermark_mgr = WatermarkManager(
    enabled=True,
    bit_stream="11001101",
    delta=2.0,
    gamma=0.25,
    agent_id=0
)

# 2. 创建 Agent
agent = SocialAgent(
    agent_id=0,
    watermark_manager=watermark_mgr
)

# 3. 运行模拟
for round_num in range(10):
    agent.perform_action()

# 4. 验证水印
result = watermark_mgr.extract_and_verify_watermark(
    log_file=watermark_mgr.log_file
)

print(f"Verification: {result['match']}")
```

---

### 高级配置

```python
import json
from pathlib import Path
from oasis.watermark import WatermarkManager

# 1. 读取配置文件
config_path = Path("config.json")
with open(config_path) as f:
    config = json.load(f)

# 2. 创建水印管理器（使用配置）
watermark_config = config.get("watermark", {})
watermark_mgr = WatermarkManager(
    enabled=watermark_config.get("enabled", True),
    bit_stream=watermark_config.get("bit_stream", "11001101"),
    delta=watermark_config.get("delta", 2.0),
    gamma=watermark_config.get("gamma", 0.25),
    ecc_type=watermark_config.get("ecc_type", "parity"),
    log_dir=watermark_config.get("log_dir", "outputs/logs/watermark"),
    agent_id=0
)

# 3. 创建 Agent 并运行
# ...
```

---

### 多 Agent 实验

```python
from oasis.watermark import WatermarkManager
from oasis.social_agent import SocialAgent

# 创建多个 Agent，每个有独立水印
agents = []
for i in range(10):
    watermark_mgr = WatermarkManager(
        enabled=True,
        bit_stream=format(i, '08b'),  # 嵌入 Agent ID
        log_dir="outputs/logs/watermark",
        agent_id=i
    )
    
    agent = SocialAgent(
        agent_id=i,
        watermark_manager=watermark_mgr
    )
    agents.append(agent)

# 运行模拟
for round_num in range(10):
    for agent in agents:
        agent.perform_action()
    print(f"Round {round_num + 1} completed")

# 验证每个 Agent 的水印
for i, agent in enumerate(agents):
    result = agent.watermark_manager.extract_and_verify_watermark(
        log_file=agent.watermark_manager.log_file
    )
    print(f"Agent {i}: {'✅' if result['match'] else '❌'}")
```

---

## 错误处理

### 异常类型

| 异常 | 说明 | 处理方法 |
|------|------|----------|
| `FileNotFoundError` | 配置文件或日志文件不存在 | 检查文件路径 |
| `ValueError` | 参数值无效（如 delta < 0） | 检查参数范围 |
| `KeyError` | 配置项缺失 | 提供默认值或完整配置 |
| `json.JSONDecodeError` | JSON 解析失败 | 检查 JSON 格式 |

### 错误处理示例

```python
from oasis.watermark import WatermarkManager
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # 创建水印管理器
    watermark_mgr = WatermarkManager(
        enabled=True,
        bit_stream="11001101",
        delta=2.0,
        gamma=0.25
    )
    
    # 运行模拟
    for round_num in range(10):
        try:
            # 生成行为
            probabilities = {"create_post": 0.45, "like": 0.35, "comment": 0.20}
            behavior, _, bit, _ = watermark_mgr.sample_behavior_watermark(
                probabilities=probabilities,
                round_num=round_num
            )
            logger.info(f"Round {round_num}: {behavior} (bit={bit})")
        
        except Exception as e:
            logger.error(f"Round {round_num} failed: {e}")
            continue
    
    # 验证水印
    result = watermark_mgr.extract_and_verify_watermark(
        log_file=watermark_mgr.log_file
    )
    
    if result['match']:
        logger.info("✅ Watermark verified successfully")
    else:
        logger.warning("❌ Watermark verification failed")

except Exception as e:
    logger.critical(f"Fatal error: {e}")
    raise
```

---

## 参考资料

- **快速开始**: `01-快速开始指南.md`
- **使用教程**: `02-使用教程.md`
- **集成架构**: `03-集成架构.md`
- **开发报告**: `05-开发报告.md`
- **故障排查**: `06-故障排查.md`

---

**最后更新**: 2025年11月11日
