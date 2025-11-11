# 🚀 使用 DeepSeek API 运行水印测试

## 概述

现在你可以使用 **DeepSeek API** 替代 OpenAI API 来测试 SocialAgent 的水印集成。

---

## 📁 可用的测试脚本

### 1. **快速测试** (推荐)

```bash
python examples/quick_test_deepseek.py
```

**特点**:
- ✅ 只执行 1 轮测试
- ✅ 快速验证集成是否工作
- ✅ 约 10-20 秒完成
- ✅ 自动提取和验证水印

**适用场景**: 快速验证 DeepSeek API 配置和基本功能

---

### 2. **完整测试**

```bash
python examples/test_socialagent_watermark_deepseek.py
```

**特点**:
- ✅ 执行 5 轮完整测试
- ✅ 测试带水印和无水印两种模式
- ✅ 完整的统计和验证
- ⏰ 约 1-2 分钟完成

**适用场景**: 完整的集成验证和性能测试

---

## 🔑 API 配置

### 方式 1: 使用脚本内置配置 (默认)

脚本已经包含 DeepSeek API 密钥：
```python
DEEPSEEK_API_KEY = "sk-5fa9b50054194880bfa66023555f857d"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
```

**无需额外配置，直接运行即可！**

---

### 方式 2: 使用环境变量

```bash
# PowerShell
$env:OPENAI_API_KEY = "your-deepseek-key"
$env:OPENAI_API_BASE = "https://api.deepseek.com"

# 然后运行测试
python examples/quick_test_deepseek.py
```

---

## 📊 预期输出

### 快速测试成功示例:

```
🚀 快速测试: SocialAgent + DeepSeek + Watermark

✅ DeepSeek API 已配置
✅ WatermarkManager: 110011011
✅ Model: DeepSeek
✅ SocialAgent 创建成功 (带水印)

📝 执行 1 轮测试...
✅ 执行成功!
   Response: I performed a like_post action with post_id: 123...

🔍 提取水印...
   原始: 110011011
   提取: 110011011
   准确率: 100.00%

🎉 测试完成!
```

---

## 🎯 DeepSeek 优势

相比 OpenAI:

| 方面 | OpenAI | DeepSeek |
|------|---------|----------|
| **价格** | 高 | **低 70%+** |
| **速度** | 一般 | **更快** |
| **中文支持** | 一般 | **原生支持** |
| **API 兼容性** | 原生 | OpenAI 兼容 |

---

## 🔧 技术实现

### CAMEL 如何支持 DeepSeek?

```python
# DeepSeek 使用 OpenAI 兼容接口
model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,  # 使用 OpenAI 平台类型
    model_type=ModelType.GPT_4O_MINI,         # 任意兼容的模型类型
    url=DEEPSEEK_BASE_URL,                     # 🎯 关键：自定义 base URL
    api_key=DEEPSEEK_API_KEY,                  # 🎯 关键：DeepSeek API 密钥
)
```

**原理**: DeepSeek API 完全兼容 OpenAI 的接口格式，只需要修改 base URL 和 API key。

---

## 📝 代码示例

### 最小化示例

```python
import os
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

from oasis import SocialAgent, UserInfo
from oasis.social_platform import Channel
from oasis.watermark import WatermarkManager

# 1. 配置 DeepSeek
os.environ["OPENAI_API_KEY"] = "your-deepseek-key"
os.environ["OPENAI_API_BASE"] = "https://api.deepseek.com"

# 2. 创建水印管理器
wm = WatermarkManager(
    enabled=True,
    bit_stream="11001101",
    config={"payload_bit_length": 8}
)

# 3. 创建 DeepSeek 模型
model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_4O_MINI,
    url="https://api.deepseek.com",
    api_key="your-deepseek-key",
)

# 4. 创建 Agent（带水印）
agent = SocialAgent(
    agent_id=1,
    user_info=UserInfo(name="User"),
    channel=Channel(),
    model=model,
    watermark_manager=wm,  # 🎯 集成水印
)

# 5. 执行行为（自动嵌入水印）
response = await agent.perform_action_by_llm()

# 6. 提取验证
extracted, stats = wm.extract_watermark_from_log()
print(f"准确率: {stats['extraction_accuracy']:.2%}")
```

---

## 🚨 常见问题

### Q1: 如何获取 DeepSeek API Key?

访问 [DeepSeek Platform](https://platform.deepseek.com/) 注册并获取 API Key。

---

### Q2: 报错 "Missing or empty required API keys"?

**解决方案**:
1. 检查 API Key 是否正确
2. 确认 `OPENAI_API_KEY` 环境变量已设置
3. 或直接使用脚本内置的 API Key

---

### Q3: DeepSeek 支持哪些模型?

DeepSeek 主要模型:
- `deepseek-chat` (推荐)
- `deepseek-coder`

**注意**: 在 CAMEL 中使用 `ModelType.GPT_4O_MINI` 或类似类型即可，实际模型由 base URL 决定。

---

### Q4: 性能和 OpenAI 有差异吗?

**水印集成完全兼容**，差异主要在:
- 响应速度：DeepSeek 可能更快
- 输出质量：两者相近
- 成本：DeepSeek 便宜 70%+

---

## 📦 下一步

1. **运行快速测试**:
   ```bash
   python examples/quick_test_deepseek.py
   ```

2. **运行完整测试**:
   ```bash
   python examples/test_socialagent_watermark_deepseek.py
   ```

3. **集成到你的代码**:
   - 参考上面的最小化示例
   - 只需修改 model 创建部分
   - 其他代码保持不变

---

## ✅ 总结

- ✅ **零修改**: SocialAgent 代码无需改动
- ✅ **完全兼容**: 水印功能正常工作
- ✅ **成本更低**: DeepSeek 便宜 70%+
- ✅ **开箱即用**: 脚本已包含配置

**立即试试**: `python examples/quick_test_deepseek.py` 🚀
