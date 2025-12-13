# OASIS 水印集成示例

本目录包含 AgentMark 水印技术在 OASIS 平台的集成示例与测试脚本。

## 目录结构

```
examples_watermark/
├── 01_basic/          # 基础示例（在 OASIS 环境中运行）
└── 02_testing/        # 测试脚本（快速验证水印模块）
```

## 快速开始

### 方式 1：运行基础示例（会调用 LLM API）

```bash
cd examples_watermark
cp ../config.json ./config_watermark.json
python 01_basic/custom_agent_run.py
```

### 方式 2：测试水印模块（不需要 API / 不跑 OASIS 环境）

```bash
python 02_testing/test_watermark_only.py
```

## 示例说明

### 01_basic/ - 基础示例

| 文件 | 说明 |
|------|------|
| `custom_agent_run.py` | 基础运行脚本（创建 Agent + OASIS 环境 + 多轮模拟 + 提取验证） |
| `custom_agent_run_with_profile.py` | 使用真实 profile 的运行脚本（更贴近真实用户画像） |

> 说明：当前集成使用“两阶段”水印策略，每轮每个 Agent 大致会有 2 次 LLM 调用（先取行为概率分布，再执行选定行为）。

### 02_testing/ - 测试脚本

| 文件 | 说明 |
|------|------|
| `test_watermark_only.py` | 仅测试 `WatermarkManager` 的嵌入/日志/提取/校验逻辑（快速回归） |

## 配置文件

默认从以下路径按优先级读取配置（脚本内也会给出默认值）：

1. `./config_watermark.json`（当前工作目录）
2. `../config.json`（项目根目录）

配置示例结构见 `docs/watermark/zh/02-使用教程.md`。

## 输出说明

运行示例会生成：

- 数据库：`outputs/databases/current/*.db`
- 水印日志：`outputs/logs/watermark/<YYYY-MM>/*.log`（或脚本配置的 `log_dir`）

## 相关文档

- `docs/watermark/zh/01-快速开始指南.md`
- `docs/watermark/zh/02-使用教程.md`
- `docs/watermark/zh/03-集成架构.md`
- `docs/watermark/zh/04-API参考.md`
