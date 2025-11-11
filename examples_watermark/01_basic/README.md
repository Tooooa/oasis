# 基础示例 - 自定义 Agent 运行

## 📋 文件说明

- `custom_agent_run.py` - 带水印的自定义 Agent 运行脚本

## 🚀 快速开始

```bash
# 1. 配置 API（如果还没有）
cd ..
cp ../config.json ./config_watermark.json
# 编辑 config_watermark.json

# 2. 运行
cd 01_basic
python custom_agent_run.py
```

## ⚙️ 配置参数

在 `../config_watermark.json` 中修改：

```json
{
    "num_agents": 2,        // Agent 数量（推荐 2-10）
    "num_rounds": 8,        // 模拟轮数（推荐 3-20）
    "api_provider": "deepseek"  // "deepseek" 或 "openai"
}
```

## 📊 输出结果

运行后会显示：

1. **实时进度**：每轮的执行状态
2. **水印提取**：每个 Agent 的独立水印
3. **统计信息**：准确率、成本、耗时等
4. **文件输出**：
   - 数据库: `../../outputs/databases/current/simulation.db`
   - 日志: `../../outputs/logs/watermark/2025-11/`

## 💡 特点

- ✅ **独立水印**：每个 Agent 有独立的 WatermarkManager
- ✅ **自动识别**：嵌入和提取 agent_id
- ✅ **灵活配置**：通过 JSON 配置，无需改代码
- ✅ **详细统计**：比特位准确度、ECC 验证等
