# API 参考（以当前代码为准）

本文件描述 `oasis/watermark` 目录下**实际存在**且可用的接口（以代码实现为准），用于集成与调用。

---

## WatermarkManager

**路径**：`oasis.watermark.WatermarkManager`（实现文件：`oasis/watermark/watermark_manager.py`）

水印的统一入口，负责：

- 将 payload bit-stream（可选 ECC 编码）按轮次嵌入到“行为选择”过程中
- 记录每轮的嵌入日志
- 从日志中提取 bit-stream 并解码/校验

### 构造函数

```python
def __init__(
    self,
    enabled: bool = True,
    mode: str = "lightweight",
    config: Optional[Dict[str, Any]] = None,
    bit_stream: Optional[str] = None,
    log_dir: str = "./log",
    log_level: str = "INFO",
    agent_id: Optional[int] = None,
)
```

**要点**：

- `enabled`：启用/禁用水印（且依赖 `oasis/watermark/modules/*` 是否可导入）。
- `config`：水印配置字典（常用字段：`payload_bit_length`、`ecc_method`、`embedding_strategy`）。
- `bit_stream`：要嵌入的 payload（二进制字符串）。不提供时：
  - 若提供 `agent_id`：默认嵌入 `agent_id` 的 8-bit 二进制；
  - 否则：默认嵌入 `"11001101"`（并按 `config` 做 ECC 编码）。
- `log_dir`：日志输出目录（注意：默认是 `./log`，不是 `outputs/logs/...`）。
- `mode`：集成/示例标签（当前实现主要用于记录与展示，不影响核心算法分支）。

---

### 方法：sample_behavior_watermark

将水印嵌入到行为选择中，并返回被选中的行为。

```python
def sample_behavior_watermark(
    self,
    probabilities: Dict[str, float],
    round_num: int,
    context_for_key: str = "",
) -> Tuple[str, List[str], int, str]
```

**参数**：

- `probabilities`：LLM 生成的“行为→概率”分布（需可归一化）。
- `round_num`：当前轮次编号（会参与 PRG 同步，编码/解码必须一致）。
- `context_for_key`：上下文字符串（会参与密钥生成；建议与日志一致）。

**返回**：

- `selected_behavior`：最终选中的行为名
- `target_list`：本轮“箱子/bin”的目标行为列表（用于检测/分析）
- `bits_embedded`：本轮实际嵌入的 bit 数（`int`，可能为 0）
- `context_used`：实际用于密钥生成的上下文

**注意**：

- `enabled=False` 或水印模块不可用时，会走降级逻辑（随机按权重采样），并返回 `bits_embedded=0`。

---

### 方法：extract_watermark_from_log

从日志文件中提取并解码水印。

```python
def extract_watermark_from_log(
    self,
    log_path: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]
```

**返回**：

- `extracted_bit_stream`：从各轮解码拼接得到的“原始编码 bit-stream”
- `stats`：统计与校验信息（字段随实现更新，常用包括：`decoded_payload`、`valid`、`accuracy`、`ecc_method`、`error` 等）

---

### 其他常用方法

- `get_statistics()`：返回当前嵌入进度、日志文件路径等统计。
- `reset()`：重置 bit 索引与统计信息。

---

## 配置（与示例脚本一致）

项目根目录的 `config.json.template` 提供了推荐结构（用于 `examples_watermark/01_basic/*`）：

- API：`api_provider`、`deepseek.*`、`openai.*`
- 模拟：`num_agents`、`num_rounds`、`platform`
- 水印：`watermark_enabled`、`watermark_config`、`log_dir`
- 数据库：`database_path`

具体字段含义参考：`config.json.template`。

---

## 参考资料

- `docs/watermark/zh/01-快速开始指南.md`
- `docs/watermark/zh/02-集成架构.md`
- `docs/watermark/zh/OASIS行为序列说明.md`
