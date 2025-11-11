# 🗺️ WatermarkManager 集成到 SocialAgent 路线图

**目标**: 将 WatermarkManager 深度集成到 `SocialAgent` 类，实现自动化水印嵌入

**完成时间估计**: 2-3 小时

---

## 📋 当前状态分析

### ✅ 已完成
1. **WatermarkManager 核心功能** (100%)
   - 差分水印采样
   - ECC 编码/解码
   - 日志记录和提取
   - 循环嵌入策略

2. **Demo 验证** (100%)
   - `demo_watermark_with_deepseek.py` 成功运行
   - 10轮嵌入 27 bits，验证 100%

3. **基础集成支持** (100%)
   - `SocialAgent.__init__` 已有 `watermark_manager` 参数
   - 简单的日志记录已实现（lines 161-173）

### 🔧 需要改进
1. **当前集成不完整**
   - 只在 `perform_action_by_llm()` 中记录 bit
   - 没有真正修改行为概率
   - 没有使用差分水印采样

2. **缺少概率获取机制**
   - LLM 直接调用工具，没有暴露行为概率
   - 无法执行差分水印嵌入

---

## 🎯 集成策略

### 方案选择：**深度集成 + 概率拦截**

**核心思路**:
1. 在 LLM 决策前获取行为概率分布
2. 使用 WatermarkManager 修改概率（差分水印）
3. 基于修改后的概率让 LLM 采样
4. 自动记录水印日志

---

## 📝 实施步骤

### 阶段 1: 分析和准备 (30分钟)

#### 1.1 深入理解 ChatAgent.astep()
- [ ] 阅读 `camel/agents/chat_agent.py` 的 `astep()` 方法
- [ ] 理解工具调用流程
- [ ] 确定概率获取点

**关键问题**:
- ❓ LLM 如何选择工具？
- ❓ 能否获取所有可用工具的概率分布？
- ❓ 能否在选择前修改概率？

#### 1.2 设计拦截机制
- [ ] 设计概率提取方法
- [ ] 设计概率修改注入点
- [ ] 规划向后兼容性

---

### 阶段 2: 实现核心集成 (60-90分钟)

#### 2.1 修改 `SocialAgent.perform_action_by_llm()`

**目标**: 在 LLM 决策前拦截并修改概率

```python
async def perform_action_by_llm(self):
    # 1. 获取环境观察
    env_prompt = await self.env.to_text_prompt()
    
    # 2. 构造 user 消息
    user_msg = BaseMessage.make_user_message(...)
    
    # 🎯 3. 水印集成点：拦截概率
    if self.watermark_manager and self.watermark_manager.enabled:
        # 3.1 获取 LLM 对所有工具的概率分布
        probabilities = await self._get_action_probabilities(user_msg)
        
        # 3.2 使用水印采样修改概率
        selected_action, target_list, bits_embedded, context = \
            self.watermark_manager.sample_behavior_watermark(
                probabilities=probabilities,
                round_num=self.watermark_manager.stats['rounds_completed'],
                context_for_key=self._build_context()
            )
        
        # 3.3 强制执行选定的行为
        response = await self._execute_forced_action(selected_action, user_msg)
    else:
        # 无水印：正常流程
        response = await self.astep(user_msg)
    
    # 4. 处理响应
    for tool_call in response.info['tool_calls']:
        ...
```

#### 2.2 实现辅助方法

**方法 1**: `_get_action_probabilities()`
```python
async def _get_action_probabilities(self, user_msg: BaseMessage) -> dict[str, float]:
    """
    获取 LLM 对所有可用工具的概率分布
    
    实现方式:
    1. 调用 LLM 生成 logprobs
    2. 提取工具选择的 token 概率
    3. 归一化成概率分布
    
    Returns:
        dict: {"like_post": 0.3, "create_comment": 0.25, ...}
    """
    # TODO: 根据 CAMEL 的 API 实现
    pass
```

**方法 2**: `_build_context()`
```python
def _build_context(self) -> str:
    """
    构建上下文密钥字符串
    
    使用最近 3 个行为作为上下文
    Returns:
        str: "like_post||create_comment||follow"
    """
    window_size = 3
    if not hasattr(self, '_action_history'):
        self._action_history = []
    
    recent_actions = self._action_history[-window_size:]
    return "||".join(recent_actions) if recent_actions else ""
```

**方法 3**: `_execute_forced_action()`
```python
async def _execute_forced_action(
    self, 
    action_name: str, 
    user_msg: BaseMessage
) -> Any:
    """
    强制执行指定的行为（跳过 LLM 决策）
    
    Args:
        action_name: 要执行的行为名称
        user_msg: 原始用户消息
        
    Returns:
        执行结果
    """
    # 找到对应的工具
    for tool in self.action_tools:
        if tool.func.__name__ == action_name:
            # 构造参数（可能需要 LLM 生成）
            args = await self._generate_action_args(action_name, user_msg)
            
            # 执行工具
            result = await tool.func(**args)
            
            # 更新历史
            if not hasattr(self, '_action_history'):
                self._action_history = []
            self._action_history.append(action_name)
            
            return result
    
    raise ValueError(f"Action {action_name} not found")
```

#### 2.3 处理边界情况
- [ ] 水印比特用尽时的处理
- [ ] 概率获取失败的回退机制
- [ ] 兼容非 LLM 行为（ManualAction）

---

### 阶段 3: 测试和验证 (45分钟)

#### 3.1 创建集成测试

**文件**: `examples/test_socialagent_watermark.py`

```python
async def test_socialagent_watermark():
    """测试 SocialAgent 的水印集成"""
    
    # 1. 初始化水印管理器
    wm = WatermarkManager(
        enabled=True,
        mode="full",
        bit_stream="11001101",
        config={
            "payload_bit_length": 8,
            "ecc_method": "parity",
            "embedding_strategy": "cyclic"
        }
    )
    
    # 2. 创建带水印的 Agent
    agent = SocialAgent(
        agent_id=0,
        user_info=UserInfo(...),
        watermark_manager=wm,
        ...
    )
    
    # 3. 模拟多轮行为
    for i in range(10):
        await agent.perform_action_by_llm()
    
    # 4. 验证水印
    extracted, stats = wm.extract_watermark_from_log()
    
    assert stats['valid'] == True
    assert extracted == wm.bit_stream
    print("✅ 集成测试通过!")
```

#### 3.2 运行现有示例
- [ ] 运行 `examples/quick_start.py` (加水印)
- [ ] 运行 `examples/agentmark_full_integration.py`
- [ ] 验证所有测试通过

#### 3.3 性能测试
- [ ] 测量水印嵌入延迟
- [ ] 验证 LLM 调用次数没有显著增加
- [ ] 检查日志文件大小

---

### 阶段 4: 文档和收尾 (30分钟)

#### 4.1 更新文档
- [ ] 更新 `README.md`
- [ ] 添加集成说明到 `docs/`
- [ ] 更新代码注释

#### 4.2 代码清理
- [ ] 移除旧的临时集成代码（lines 161-173）
- [ ] 统一日志格式
- [ ] 添加类型提示

---

## 🚨 潜在挑战和解决方案

### 挑战 1: CAMEL 框架不暴露工具概率

**问题**: CAMEL 的 `astep()` 可能不返回工具选择的概率分布

**解决方案 A** (理想):
- 修改 CAMEL 源码，添加概率返回
- 贡献回上游项目

**解决方案 B** (实用):
- 使用 `logprobs` 参数获取 token 概率
- 解析 function calling 的概率分布

**解决方案 C** (回退):
- 让 LLM 先返回 JSON 格式的概率分布
- 再用水印修改并重新采样

### 挑战 2: 强制执行行为需要参数生成

**问题**: 水印只决定**哪个**行为，不决定**参数**

**解决方案**:
- 仍然调用 LLM，但限制工具选择
- 提示词：`"You must use the ${action_name} action. Generate appropriate arguments."`

### 挑战 3: 上下文密钥的可复现性

**问题**: 行为历史在重新运行时可能不同

**解决方案**:
- 使用确定性的行为序列
- 从日志中精确还原上下文

---

## 📊 验收标准

### 必须达成 (Must Have)
- ✅ `SocialAgent` 自动使用水印采样
- ✅ 不需要修改用户代码
- ✅ 100% 提取准确率
- ✅ 向后兼容（无水印时正常工作）

### 应该达成 (Should Have)
- ✅ 性能开销 < 20%
- ✅ 详细的集成文档
- ✅ 完整的测试覆盖

### 可以达成 (Nice to Have)
- 可视化工具
- 多 Agent 水印独立性
- 水印强度可配置

---

## 🔄 迭代计划

### 版本 1.0 (本次实现)
- 基础深度集成
- 单 Agent 验证
- 核心文档

### 版本 1.1 (未来)
- 多 Agent 独立水印
- 性能优化
- 可视化面板

### 版本 2.0 (未来)
- 自适应水印强度
- 对抗性攻击防御
- 水印检测 API

---

## ✅ 行动检查清单

### 开始前
- [ ] 激活 conda 环境: `conda activate oasis`
- [ ] 确认当前分支: `feature/integrate-agentmark`
- [ ] 备份重要文件

### 实施中
- [ ] 阶段 1: 分析 ✅
- [ ] 阶段 2: 实现核心功能
- [ ] 阶段 3: 测试验证
- [ ] 阶段 4: 文档完善

### 完成后
- [ ] 运行所有测试
- [ ] 提交代码
- [ ] 更新完成报告

---

## 📞 需要决策的问题

### 问题 1: 概率获取方式
**选项**:
- A) 修改 CAMEL 源码 (高质量，高成本)
- B) 使用 logprobs 解析 (中等质量，中等成本)
- C) 两次 LLM 调用 (低质量，低成本)

**建议**: 先尝试 B，失败则用 C

### 问题 2: 是否修改 OASIS 核心
**选项**:
- A) 修改 `agent.py` (深度集成)
- B) 继承 `SocialAgent` (非侵入)

**建议**: A (已有 watermark_manager 参数，符合设计)

### 问题 3: 测试覆盖范围
**选项**:
- A) 只测试水印相关功能
- B) 回归测试所有 OASIS 功能

**建议**: A + 部分 B (运行核心示例)

---

## 🎯 成功指标

1. **功能完整性**: 所有水印功能正常工作
2. **准确性**: 提取准确率 100%
3. **性能**: 延迟增加 < 20%
4. **兼容性**: 不破坏现有代码
5. **可维护性**: 代码清晰，文档完善

---

**准备好开始了吗？** 

让我们从阶段 1 开始！🚀
