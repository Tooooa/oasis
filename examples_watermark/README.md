# OASIS 水印集成示例

本目录包含 AgentMark 水印技术在 OASIS 平台的集成示例。

## 📂 目录结构

```
examples_watermark/
├── 01_basic/          # 基础示例，适合快速入门
├── 02_advanced/       # 高级示例，完整功能演示
└── 03_testing/        # 测试脚本，验证水印功能
```

## 🚀 快速开始

### 方式 1: 运行基础示例（推荐新手）

```bash
# 1. 确保配置文件存在
cd examples_watermark
cp ../config.json ./config_watermark.json

# 2. 编辑配置（可选）
# 修改 config_watermark.json 中的 num_agents, num_rounds 等

# 3. 运行示例
python 01_basic/custom_agent_run.py
```

**特点**：
- ✅ 独立 Agent 水印架构
- ✅ 每个 Agent 嵌入自己的 agent_id
- ✅ 自动提取和验证
- ✅ 详细统计报告

---

### 方式 2: 运行完整集成示例

```bash
python 02_advanced/full_integration.py
```

**特点**：
- ✅ 共享水印管理器演示
- ✅ 完整的嵌入-提取-验证流程
- ✅ 适合学习水印原理

---

### 方式 3: 测试水印功能

```bash
# 单独测试水印逻辑（不需要完整 OASIS 环境）
python 03_testing/test_watermark_only.py

# 端到端测试（包含 OASIS 环境）
python 03_testing/test_end_to_end.py
```

---

## 📖 示例说明

### 01_basic/ - 基础示例

| 文件 | 说明 | 适用场景 |
|------|------|----------|
| `custom_agent_run.py` | 自定义配置运行 | 实际实验研究 |

**配置方式**：
- 从 `config_watermark.json` 读取配置
- 支持 DeepSeek + OpenAI 双 LLM
- 可调整 Agent 数量和轮数

---

### 02_advanced/ - 高级示例

| 文件 | 说明 | 适用场景 |
|------|------|----------|
| `full_integration.py` | 完整集成演示 | 学习水印原理 |
| `deepseek_demo.py` | DeepSeek 专用演示 | 成本优化 |
| `integration_example.py` | 多种集成模式 | 高级用法 |

**特点**：
- 详细的步骤说明
- 完整的统计和验证
- 适合教学演示

---

### 03_testing/ - 测试脚本

| 文件 | 说明 | 运行时间 |
|------|------|----------|
| `test_watermark_only.py` | 水印逻辑测试 | ~30 秒 |
| `test_end_to_end.py` | 端到端测试 | ~3 分钟 |

**用途**：
- 验证水印功能正常
- 快速测试代码改动
- CI/CD 集成测试

---

## ⚙️ 配置文件

### config_watermark.json 示例

```json
{
    "api_provider": "deepseek",
    "deepseek": {
        "api_key": "your-api-key",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat"
    },
    "num_agents": 2,
    "num_rounds": 8,
    "watermark_enabled": true,
    "watermark_config": {
        "payload_bit_length": 8,
        "ecc_method": "parity",
        "embedding_strategy": "cyclic"
    },
    "log_dir": "../outputs/logs/watermark",
    "database_path": "../outputs/databases/current/simulation.db"
}
```

---

## 📊 输出说明

运行示例后，会生成以下文件：

```
outputs/
├── logs/
│   └── watermark/
│       └── 2025-11/
│           ├── watermark-agent0-*.log  # Agent 0 的水印日志
│           └── watermark-agent1-*.log  # Agent 1 的水印日志
│
└── databases/
    └── current/
        └── simulation.db               # 模拟数据库
```

---

## 🔍 查看结果

### 查看水印提取结果

运行完成后，终端会显示：

```
🤖 Agent 0 - 水印提取
======================================================================
📊 提取结果:
   Agent索引(整数): 0
   原始比特流: 000000001 (长度: 9)
   提取比特流: 000000001 (长度: 9)
   识别的agent_id: 0 (binary: 00000000)
   ✅ Agent ID 匹配！

📈 比特位准确度:
   - 匹配度: 100.0%
   ✅ 完美匹配
```

### 查看数据库

```python
import sqlite3
conn = sqlite3.connect('../outputs/databases/current/simulation.db')
cursor = conn.cursor()

# 查看 Agent 行为
cursor.execute("SELECT * FROM actions LIMIT 10")
for row in cursor.fetchall():
    print(row)
```

### 分析日志

```python
# 读取水印日志
log_file = '../outputs/logs/watermark/2025-11/watermark-agent0-*.log'
with open(log_file, 'r', encoding='utf-8') as f:
    for line in f:
        print(line.strip())
```

---

## 💡 使用技巧

### 1. 快速测试（2 Agent, 3 轮）

```json
{
    "num_agents": 2,
    "num_rounds": 3
}
```
**预计**: 1-2 分钟，成本 < $0.01

### 2. 完整验证（5 Agent, 10 轮）

```json
{
    "num_agents": 5,
    "num_rounds": 10
}
```
**预计**: 5-8 分钟，成本 ~$0.02

### 3. 切换到 OpenAI

```json
{
    "api_provider": "openai",
    "openai": {
        "api_key": "sk-your-key",
        "model": "gpt-4o-mini"
    }
}
```

---

## 📚 相关文档

- [水印集成指南](../docs/watermark/zh/02-集成指南.md)
- [快速开始](../docs/watermark/zh/01-快速开始.md)
- [API 参考](../docs/watermark/zh/03-API参考.md)

---

## ❓ 常见问题

### Q: 如何修改 Agent 数量？
**A**: 编辑 `config_watermark.json`，修改 `num_agents` 字段。

### Q: 如何使用 DeepSeek 节省成本？
**A**: 设置 `"api_provider": "deepseek"`，比 OpenAI 便宜约 70%。

### Q: 日志文件在哪里？
**A**: 在 `../outputs/logs/watermark/2025-11/` 目录下。

### Q: 如何清理旧文件？
**A**: 运行 `python ../scripts/cleanup.py`

---

## 🤝 贡献

欢迎提交问题和改进建议！

## 📄 许可

Apache License 2.0 - 详见 [LICENSE](../LICENSE)
