# AgentMark 水印集成文档

> **OASIS × AgentMark 水印技术集成**  
> 为 OASIS 社交模拟平台集成差分水印技术，实现 Agent 行为追踪与验证

---

## 📚 文档导航

### 快速开始
- **[快速开始指南](01-快速开始指南.md)** - 5分钟上手水印功能
- **[使用教程](02-使用教程.md)** - 完整的使用说明和示例

### 深入理解  
- **[集成架构](03-集成架构.md)** - 技术架构和设计决策
- **[API 参考](04-API参考.md)** - 完整的 API 文档

### 开发参考
- **[开发报告](05-开发报告.md)** - 集成过程的完整记录
- **[故障排查](06-故障排查.md)** - 常见问题和解决方案

---

## 🎯 项目概述

### 什么是 AgentMark？

AgentMark 是一种**差分水印技术**，通过在 LLM 生成的行为概率分布中嵌入秘密信息，实现：

- ✅ **Agent 身份追踪** - 每个 Agent 可嵌入唯一 ID
- ✅ **行为验证** - 验证行为是否由特定 Agent 产生
- ✅ **隐蔽性强** - 不影响 Agent 的自然行为
- ✅ **鲁棒性高** - 支持错误纠正码（ECC）

### 集成特点

| 特性 | 说明 |
|------|------|
| 🔌 **非侵入式** | 不改变 OASIS 核心代码，可选启用 |
| 🎨 **双模式** | 共享水印 / 独立水印两种模式 |
| 🔧 **灵活配置** | JSON 配置文件，支持多种参数 |
| 📊 **自动日志** | 完整的嵌入和提取日志 |
| ✅ **完整验证** | 端到端的水印验证流程 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/camel-ai/oasis.git
cd oasis

# 安装依赖
pip install -e .
```

### 2. 配置 API

```bash
# 复制配置模板
cp config.json.template config.json

# 编辑配置文件，填入 API Key
# 支持: OpenAI / DeepSeek
```

### 3. 运行示例

```bash
# 基础示例（2 Agent，8 轮）
python examples_watermark/01_basic/custom_agent_run.py

# 完整演示（3 Agent，5 轮，自定义 payload）
python examples_watermark/02_advanced/full_integration.py
```

### 4. 查看结果

```bash
# 数据库
outputs/databases/current/simulation.db

# 日志
outputs/logs/watermark/2025-11/watermark-agent0-*.log
```

---

## 📊 资源需求

### 最小配置
- **CPU**: 2核 2.0 GHz
- **内存**: 2-4 GB
- **网络**: 稳定的 API 连接
- **成本**: $0.006-0.05 (取决于 Agent 数和轮数)

### 推荐配置
- **CPU**: 4核 2.5 GHz+
- **内存**: 8 GB
- **API**: DeepSeek (便宜 70%)

---

## 🏗️ 项目结构

```
oasis/
├── oasis/
│   └── watermark/              # 水印核心模块
│       ├── watermark_manager.py
│       └── modules/
│
├── examples_watermark/         # 水印示例
│   ├── 01_basic/              # 基础示例
│   ├── 02_advanced/           # 高级示例
│   └── 03_testing/            # 测试脚本
│
├── outputs/                   # 输出目录
│   ├── logs/watermark/        # 水印日志
│   └── databases/             # 数据库
│
└── docs/watermark/            # 文档
    └── zh/                    # 中文文档
```

---

## 📖 文档说明

### 文档组织

所有水印相关文档已整理到 `docs/watermark/zh/` 目录：

1. **快速开始指南** - 5分钟快速入门
2. **使用教程** - 详细的使用说明
3. **集成架构** - 技术架构和设计
4. **API 参考** - 完整的 API 文档
5. **开发报告** - 历史开发记录
6. **故障排查** - 问题解决方案

### 历史文档归档

原有的分散文档已整合并归档到 `05-开发报告.md`：

- AgentMark集成完成报告.md
- AgentMark集成策略总结.md
- DeepSeek使用说明.md
- 端到端水印验证报告.md
- 等...

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](../../../CONTRIBUTING.md)

---

## 📝 许可证

Apache License 2.0 - 详见 [LICENSE](../../../LICENSE)

---

## 🔗 相关链接

- [OASIS 主项目](https://github.com/camel-ai/oasis)
- [AgentMark 论文](https://arxiv.org/abs/2411.11581)
- [CAMEL-AI](https://www.camel-ai.org/)
