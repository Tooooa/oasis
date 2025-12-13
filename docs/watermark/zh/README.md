# AgentMark 水印集成文档

> **OASIS × AgentMark 水印技术集成**  
> 为 OASIS 社交模拟平台集成差分水印技术，实现 Agent 行为追踪与验证

---

## 文档导航

### 快速开始
- **[快速开始指南](01-快速开始指南.md)** - 最短路径验证水印
- **[环境配置](00-环境配置.md)** - Python/conda/DeepSeek 配置与运行

### 深入理解
- **[集成架构](02-集成架构.md)** - 实际集成链路与数据流
- **[API 参考](03-API参考.md)** - 以当前代码为准的接口说明

### 说明
- **[OASIS行为序列说明](OASIS行为序列说明.md)** - 行为集合固定性说明

---

## 项目概述

AgentMark 是一种差分水印技术：在 LLM 生成的“行为概率分布”里嵌入 payload，从而实现 Agent 身份追踪与行为验证。

集成特点：

| 特性 | 说明 |
|------|------|
| 非侵入式 | 不需要改动平台/环境核心逻辑（在 Agent 决策处插入） |
| Agent 级追踪 | 默认每个 Agent 独立水印（常用 `agent_id` 作为 payload） |
| 自动日志 | 记录每轮嵌入所需的可复现信息，支持离线提取与校验 |
| ECC 支持 | 支持 `parity` / `hamming` 等纠错码（见配置与代码实现） |

---

## 快速验证（水印是否工作）

### 1) 安装

在项目根目录（`oasis/`）：

```bash
pip install -e .
```

### 2) 配置 API

复制模板并填入 API key：

```bash
cp config.json.template config.json
```

### 3) 运行真实 OASIS + 水印验证

```bash
python examples_watermark/01_basic/custom_agent_run_with_profile.py
```

运行完成后，脚本会在结尾输出每个 Agent 的水印提取/校验结果（例如 `Agent ID 匹配` / `valid: True`）。

### 4) 产物位置

- 数据库：`outputs/databases/current/*.db`
- 水印日志：`outputs/logs/watermark/<YYYY-MM>/*.log`（或配置中的 `log_dir`）

---

## 示例目录（当前仓库）

```
oasis/
├── oasis/watermark/                 # 水印模块实现
├── examples_watermark/              # 可运行示例与测试
│   ├── 01_basic/                    # 真实 OASIS 环境示例（会调用 LLM API）
│   └── 02_testing/                  # 水印模块快速回归（不需要 API）
└── docs/watermark/zh/               # 中文文档
```
