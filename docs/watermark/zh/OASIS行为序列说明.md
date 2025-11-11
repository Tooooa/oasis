# OASIS 行为序列说明

> **重要**: 关于 OASIS 可用行为序列的设计和使用

---

## 核心结论

### ❌ **行为序列不会动态变化**

OASIS 的 `available_actions` 是在 **Agent 初始化时固定的**，在整个模拟过程中**不会根据上下文动态调整**。

```python
# Agent 创建时确定行为序列
agent = SocialAgent(
    agent_id=0,
    available_actions=[...]  # 固定的行为列表
)

# 之后模拟过程中，这个列表不会改变
```

---

## 源码分析

### 1. 初始化时确定

**文件**: `oasis/social_agent/agent.py` (第 114-132 行)

```python
if not available_actions:
    # 未指定：使用平台的所有行为
    self.action_tools = self.env.action.get_openai_function_list()
else:
    # 已指定：只使用指定的行为
    self.action_tools = [
        tool for tool in all_tools if tool.func.__name__ in [
            a.value if isinstance(a, ActionType) else a
            for a in available_actions
        ]
    ]
```

**说明**:
- `self.action_tools` 在 `__init__()` 中赋值
- 之后不再修改
- 每轮模拟都使用相同的行为列表

---

### 2. 行为采样时使用

**文件**: `oasis/social_agent/agent.py` (第 184-185 行)

```python
async def _query_behavior_probabilities(self, env_prompt: str) -> dict:
    """生成行为概率分布"""
    # 获取所有可用行为
    available_actions = [tool.func.__name__ for tool in self.action_tools]
    actions_str = ", ".join(available_actions)
    
    # 构造 prompt，让 LLM 估计概率
    prompt = f"""...
    Available actions: {actions_str}
    ..."""
```

**说明**:
- 每次调用时都使用初始化时的 `self.action_tools`
- 不会根据环境状态动态过滤行为

---

## OASIS 原始示例

### Twitter 默认行为 (6个)

**文件**: `oasis/social_platform/typing.py` (第 52-59 行)

```python
@classmethod
def get_default_twitter_actions(cls):
    return [
        cls.CREATE_POST,
        cls.LIKE_POST,
        cls.REPOST,
        cls.FOLLOW,
        cls.DO_NOTHING,
        cls.QUOTE_POST,
    ]
```

**使用示例**: `examples/twitter_simulation_openai.py`

```python
available_actions = ActionType.get_default_twitter_actions()

agent_graph = await generate_twitter_agent_graph(
    profile_path="...",
    model=openai_model,
    available_actions=available_actions,  # 固定的 6 个行为
)
```

---

### Reddit 默认行为 (13个)

**文件**: `oasis/social_platform/typing.py` (第 61-75 行)

```python
@classmethod
def get_default_reddit_actions(cls):
    return [
        cls.LIKE_POST,
        cls.DISLIKE_POST,
        cls.CREATE_POST,
        cls.CREATE_COMMENT,
        cls.LIKE_COMMENT,
        cls.DISLIKE_COMMENT,
        cls.SEARCH_POSTS,
        cls.SEARCH_USER,
        cls.TREND,
        cls.REFRESH,
        cls.DO_NOTHING,
        cls.FOLLOW,
        cls.MUTE,
    ]
```

---

## 我们的脚本修正

### 修改前（自定义 14 个行为）

```python
available_actions = [
    ActionType.LIKE_POST,
    ActionType.UNLIKE_POST,      # ❌ 不在 Reddit 默认列表
    ActionType.DISLIKE_POST,
    ActionType.CREATE_POST,
    ActionType.CREATE_COMMENT,
    ActionType.REPOST,            # ❌ Twitter 特有
    ActionType.QUOTE_POST,        # ❌ Twitter 特有
    ActionType.FOLLOW,
    ActionType.UNFOLLOW,          # ❌ 不在默认列表
    ActionType.MUTE,
    ActionType.UNMUTE,            # ❌ 不在默认列表
    ActionType.SEARCH_USER,
    ActionType.SEARCH_POSTS,
    ActionType.REFRESH,
]
# ❌ 缺少 DO_NOTHING
```

**问题**:
1. 混合了 Twitter 和 Reddit 行为
2. 包含不在默认列表的行为（`UNLIKE_POST`, `UNFOLLOW`, `UNMUTE`）
3. 缺少 `DO_NOTHING`（Agent 无法选择不活动）

---

### 修改后（使用 Reddit 默认）

```python
# ✅ 使用 OASIS 原始 Reddit 默认行为
available_actions = ActionType.get_default_reddit_actions()
```

**好处**:
1. ✅ 与 OASIS 原始设计一致
2. ✅ 包含 `DO_NOTHING`
3. ✅ 行为列表经过 OASIS 团队验证
4. ✅ LLM 对这些行为有更好的理解

---

## 为什么行为不动态变化？

### 1. 设计简化

动态调整行为序列会增加复杂度：
- 需要维护状态机
- 需要上下文感知逻辑
- 增加调试难度

### 2. LLM 限制

LLM 生成概率时需要固定的行为集合：
- 每次 prompt 都包含完整行为列表
- LLM 需要对每个行为都给出概率估计
- 动态行为会导致 prompt 不一致

### 3. 水印兼容性

差分水印算法要求：
- 固定数量的行为选项
- 稳定的概率分布
- 动态行为会破坏水印嵌入

---

## 最佳实践

### 1. 使用平台默认行为

```python
# ✅ 推荐：使用默认行为
if platform == "twitter":
    available_actions = ActionType.get_default_twitter_actions()
elif platform == "reddit":
    available_actions = ActionType.get_default_reddit_actions()
```

### 2. 自定义行为时的注意事项

如果需要自定义：

```python
# ✅ 保持行为数量合理（5-15 个）
# ✅ 包含 DO_NOTHING
# ✅ 确保平台支持所有行为
# ✅ 不混合不同平台的行为

available_actions = [
    ActionType.CREATE_POST,
    ActionType.LIKE_POST,
    ActionType.COMMENT,
    ActionType.FOLLOW,
    ActionType.DO_NOTHING,  # 必须包含
]
```

### 3. 验证行为有效性

```python
# Agent 初始化时会自动验证
# 不支持的行为会输出警告：
# "Action xxx is not supported. Supported actions are: ..."
```

---

## 对水印的影响

### 行为数量与水印质量

| 行为数量 | 概率分布 | 水印质量 | 建议 |
|---------|---------|---------|------|
| 2-4 个 | 很平滑 | 优秀 | ✅ 最佳 |
| 5-10 个 | 平滑 | 良好 | ✅ 推荐 |
| 11-15 个 | 较平滑 | 中等 | ⚠️ 可用 |
| 16+ 个 | 集中 | 较差 | ❌ 不推荐 |

**原因**:
- 行为越多，LLM 给出的概率越集中在少数几个
- 概率分布太集中会导致无法嵌入水印（前两个概率差距 > 10%）

### Reddit 默认行为 (13个) 的影响

```python
# 13 个行为 → 概率分布相对分散
# 平均概率：1/13 ≈ 7.7%

# 实际分布（示例）：
{
    "create_post": 0.25,     # 高
    "like_post": 0.20,       # 高
    "refresh": 0.15,         # 中
    "search_posts": 0.10,    # 中
    "follow": 0.08,          # 低
    "do_nothing": 0.05,      # 低
    ... (其他行为)
}

# ✅ 前两个差距：0.25 - 0.20 = 0.05 < 0.10
# ✅ 可以成功嵌入水印
```

---

## 常见问题

### Q1: 能否根据上下文过滤行为？

**A**: 原始 OASIS 不支持，但可以通过以下方式实现：

```python
# 方案 1: 在 LLM prompt 中提示
prompt = f"""
Context: {env_prompt}

Note: Currently you cannot create a post because you just posted.
Please choose from other actions.

Available actions: {actions_str}
"""

# 方案 2: 后处理（不推荐，会影响水印）
if just_posted:
    # 手动排除 CREATE_POST
    filtered_actions = [a for a in available_actions if a != ActionType.CREATE_POST]
```

⚠️ **注意**: 动态过滤会影响水印嵌入质量！

---

### Q2: DO_NOTHING 的作用？

**A**: 非常重要！

1. **避免过度活跃**: Agent 可以选择不执行任何操作
2. **更真实**: 模拟人类用户的"观察"行为
3. **水印质量**: 增加行为选项的多样性

```python
# ❌ 没有 DO_NOTHING
# Agent 必须执行某个操作，即使不合适

# ✅ 有 DO_NOTHING
# Agent 可以选择观察，等待更好的时机
```

---

### Q3: 如何选择 Twitter 还是 Reddit 行为？

**A**: 根据平台类型

```python
# 创建环境时指定平台
env = oasis.make(
    agent_graph=agent_graph,
    platform=oasis.DefaultPlatformType.REDDIT,  # 或 TWITTER
    database_path=db_path,
)

# 行为列表应匹配平台
if platform == oasis.DefaultPlatformType.REDDIT:
    available_actions = ActionType.get_default_reddit_actions()
elif platform == oasis.DefaultPlatformType.TWITTER:
    available_actions = ActionType.get_default_twitter_actions()
```

---

## 总结

| 要点 | 说明 |
|------|------|
| **固定性** | 行为序列在 Agent 创建时确定，模拟过程中不变 |
| **推荐** | 使用 `get_default_twitter_actions()` 或 `get_default_reddit_actions()` |
| **DO_NOTHING** | 必须包含，提供"不活动"选项 |
| **行为数量** | 建议 5-15 个，太多会影响水印质量 |
| **平台匹配** | 行为列表应与平台类型一致 |

---

**最后更新**: 2025年11月11日  
**相关文件**: 
- `oasis/social_agent/agent.py`
- `oasis/social_platform/typing.py`
- `examples_watermark/01_basic/custom_agent_run.py`
