# 测试脚本 - 验证水印功能

## 📋 文件说明

| 文件 | 说明 | 运行时间 | 需要环境 |
|------|------|----------|----------|
| `test_watermark_only.py` | 水印逻辑单元测试 | ~30 秒 | 无需 OASIS |
| `test_end_to_end.py` | 端到端集成测试 | ~3 分钟 | 需要 OASIS |

## 🧪 测试类型

### 1. 水印逻辑测试（快速）

```bash
python test_watermark_only.py
```

**测试内容**：
- ✅ WatermarkManager 初始化
- ✅ 比特流嵌入
- ✅ ECC 编码/解码
- ✅ 水印提取
- ✅ 准确率验证

**优点**：
- 快速（30 秒内完成）
- 不需要 API 调用
- 不需要完整 OASIS 环境
- 适合 CI/CD

---

### 2. 端到端测试（完整）

```bash
python test_end_to_end.py
```

**测试内容**：
- ✅ OASIS 环境初始化
- ✅ Agent 创建和水印配置
- ✅ 多轮模拟执行
- ✅ 日志记录
- ✅ 水印提取和验证
- ✅ 数据库写入

**优点**：
- 完整流程验证
- 真实环境测试
- 发现集成问题

## 🚀 运行测试

### 运行所有测试

```bash
# 快速测试
python test_watermark_only.py

# 完整测试（需要 API key）
python test_end_to_end.py
```

### 查看测试结果

测试通过会显示：

```
✅ 测试 1: WatermarkManager 初始化 - 通过
✅ 测试 2: 比特流嵌入 - 通过
✅ 测试 3: ECC 编码 - 通过
✅ 测试 4: 水印提取 - 通过
✅ 测试 5: 准确率验证 - 通过

🎉 所有测试通过！
```

测试失败会显示：

```
❌ 测试 3: ECC 编码 - 失败
   期望: 000000001
   实际: 000000000
   
详细错误信息...
```

## 🔍 调试测试

### 启用详细日志

```python
# 在测试文件开头添加
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 单独运行某个测试

```python
# 在 test_watermark_only.py 中
if __name__ == "__main__":
    # 注释掉其他测试，只运行需要的
    test_watermark_embedding()
    # test_watermark_extraction()
    # test_ecc_encoding()
```

## 📊 测试覆盖率

### test_watermark_only.py

- [x] WatermarkManager 初始化
- [x] Parity ECC 编码/解码
- [x] Hamming ECC 编码/解码
- [x] 差分水印采样
- [x] 比特流循环
- [x] 日志记录
- [x] 统计计算

### test_end_to_end.py

- [x] OASIS 环境创建
- [x] Agent 水印集成
- [x] 多轮模拟
- [x] LLM 调用
- [x] 水印提取
- [x] 数据库操作
- [x] 文件清理

## 💡 测试最佳实践

### 1. 开发时频繁运行快速测试

```bash
# 每次修改代码后
python test_watermark_only.py
```

### 2. 提交前运行完整测试

```bash
# Git commit 前
python test_end_to_end.py
```

### 3. CI/CD 集成

```yaml
# .github/workflows/test.yml
- name: Run watermark tests
  run: |
    python examples_watermark/03_testing/test_watermark_only.py
    python examples_watermark/03_testing/test_end_to_end.py
```

## 🐛 常见问题

### Q: test_watermark_only.py 失败

**A**: 检查 `oasis/watermark/` 模块是否正常导入。

### Q: test_end_to_end.py 超时

**A**: 检查 API key 是否配置正确，网络是否正常。

### Q: 准确率不是 100%

**A**: 这是正常的，差分水印有概率性。准确率 > 90% 即为合格。

## 📚 相关文档

- [水印验证报告](../../docs/watermark/zh/reports/端到端水印验证报告.md)
- [集成完成报告](../../docs/watermark/zh/reports/AgentMark集成完成报告.md)
