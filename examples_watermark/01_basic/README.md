# 基础示例 - 在 OASIS 环境中运行水印

本目录包含“真实 OASIS 环境 + LLM API 调用 + 水印嵌入/提取验证”的基础脚本。

## 文件说明

- `custom_agent_run.py`：最小可跑版本（按配置创建若干 Agent，跑多轮模拟，结束后提取并验证每个 Agent 的水印）。
- `custom_agent_run_with_profile.py`：使用真实 profile JSON 创建 Agent（更贴近真实用户画像的实验流程）。

## 运行

```bash
cd examples_watermark
cp ../config.json ./config_watermark.json
python 01_basic/custom_agent_run.py
```

或：

```bash
python 01_basic/custom_agent_run_with_profile.py
```

## 输出

- 数据库：`outputs/databases/current/*.db`
- 水印日志：`outputs/logs/watermark/<YYYY-MM>/*.log`（或脚本配置的 `log_dir`）
