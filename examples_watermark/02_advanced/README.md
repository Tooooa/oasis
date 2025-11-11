# 高级示例 - 完整集成演示

## 📋 文件说明

| 文件 | 说明 | 推荐场景 |
|------|------|----------|
| `full_integration.py` | 完整集成演示 | 学习水印原理 |
| `deepseek_demo.py` | DeepSeek 专用演示 | 成本优化 |
| `integration_example.py` | 多种集成模式 | 高级用法探索 |

## 🎯 使用场景

### 1. 学习水印原理

```bash
python full_integration.py
```

**适合**：
- 第一次接触水印技术
- 想理解嵌入-提取流程
- 教学演示

**特点**：
- 共享水印管理器
- 详细的步骤说明
- 完整的验证流程

---

### 2. 使用 DeepSeek 降低成本

```bash
python deepseek_demo.py
```

**适合**：
- 需要大量实验
- 预算有限
- 快速原型开发

**优势**：
- 比 OpenAI 便宜 70%
- API 响应速度快
- 支持中文优化

---

### 3. 探索不同集成模式

```bash
python integration_example.py
```

**适合**：
- 需要自定义水印配置
- 测试不同 ECC 方法
- 研究水印鲁棒性

**功能**：
- 轻量级模式
- 完整模式
- 自定义 payload

## 📖 代码结构

### full_integration.py

```
1. 初始化 WatermarkManager（共享模式）
2. 创建 3 个 Agent，使用同一个管理器
3. 运行 5 轮模拟
4. 提取并验证水印
5. 显示详细统计
```

### deepseek_demo.py

```
1. 配置 DeepSeek API
2. 优化 temperature 和 max_tokens
3. 运行水印嵌入
4. 性能和成本统计
```

### integration_example.py

```
1. 轻量级集成示例
2. 完整集成示例
3. 简化示例
4. 对比不同模式
```

## 💡 提示

### 修改 payload

在脚本中找到：

```python
payload = "11001101"  # 8-bit payload
```

改为你想嵌入的消息（必须是二进制字符串）。

### 调整 ECC 方法

```python
watermark_config = {
    "ecc_method": "parity",  # 或 "hamming"
}
```

### 更改模拟规模

```python
num_rounds = 5  # 改为你需要的轮数
for i in range(3):  # 改为你需要的 Agent 数量
```

## 📊 性能对比

| 示例 | Agent | 轮数 | 时间 | OpenAI 成本 | DeepSeek 成本 |
|------|-------|------|------|-------------|---------------|
| full_integration | 3 | 5 | 5 min | $0.05 | $0.01 |
| deepseek_demo | 2 | 8 | 3 min | - | $0.008 |
| integration_example | 3 | 3 | 2 min | $0.03 | $0.006 |
