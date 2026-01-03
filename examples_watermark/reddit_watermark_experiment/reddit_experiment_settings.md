# Reddit平台实验设置

## 1. 环境配置

| 参数 | 值 |
|------|-----|
| 平台 | Reddit |
| 子版块 | r/TechFuture |
| 交互模式 | 论坛式 |
| 推荐系统 | reddit |

## 2. Agent配置

| 参数 | 值 |
|------|-----|
| 水印组 (A组) | 5个Agent |
| 对照组 (B组) | 5个Agent |
| Agent总数 | 10 |
| 模拟步数 | 10 |

## 3. 可选行为

```
create_post（发帖）, create_comment（评论）, like_post（点赞）, dislike_post（踩）, like_comment（评论点赞）, dislike_comment（评论踩）, search_posts（搜索帖子）, search_user（搜索用户）, trend（查看趋势）, refresh（刷新）, do_nothing（不操作）, follow（关注）, mute（屏蔽）
```

## 4. Agent人设

| ID | 名称 | 描述 | 行为倾向 |
|----|------|------|----------|
| 0 | 技术专家 (Geek) | 深度分析，技术术语 | create_post, create_comment |
| 1 | 批评者 (Critic) | 犀利质疑，逻辑分析 | create_comment, dislike_post |
| 2 | 热心人 (Helper) | 温暖鼓励，多用表情 | like_post, create_comment |
| 3 | 潮流追踪者 (Influencer) | 追踪热点，轻松对话 | create_post, refresh |
| 4 | 事实核查员 (FactChecker) | 中立客观，引用来源 | create_comment |

## 5. 水印配置

| 参数 | 值 |
|------|-----|
| 启用状态 | True |
| 水印方案 | 差分方案 (Differential Scheme) |
| 纠错方法 | parity (奇偶校验) |
| 嵌入策略 | cyclic (循环嵌入) |
| 上下文窗口 | 3 (最近3个行为作为PRG种子) |

## 6. 提示词

### 6.1 概率估计提示词

```
You are observing a social media environment:
{env_prompt}

Based on this observation and your profile, estimate the probability of performing each action.
Return ONLY a JSON object with probabilities (must sum to 1.0):

Available actions: like_post, dislike_post, create_post, create_comment, like_comment, dislike_comment, search_posts, search_user, trend, refresh, do_nothing, follow, mute

Output format:
{"action_name": probability, ...}

Example:
{"like_post": 0.3, "create_comment": 0.25, "follow": 0.2, "refresh": 0.25}
```

### 6.2 水印行为执行提示词

```
You are observing a social media environment:
{env_prompt}

You MUST perform the action: {action_name}

Generate appropriate arguments for this action and execute it. Do not consider other actions.
```

## 7. 评估维度

| 维度 | 描述 | 分值范围 |
|------|------|----------|
| 逻辑连贯性 | 内容是否逻辑通顺 | 1-10 |
| 记忆准确性 | 是否有前后矛盾 | 1-10 |
| 人设稳定性 | 是否符合人设描述 | 1-10 |
| 社会规范 | 是否符合社交规范 | 1-10 |
| 语言多样性 | 词汇是否丰富自然 | 1-10 |

## 8. 评估提示词

```
请评估以下社交媒体Agent的表现。基于其个人简介和发布的内容，对以下五个维度进行打分（1-10分）并给出简短理由。

Agent信息:
Name: {user_name}
Profile/Bio: {profile}

Agent发布的内容样本:
{content_str}

评估维度:
1. 逻辑连贯性 (Logical Coherence): 内容是否逻辑通顺？
2. 记忆准确性 (Memory Accuracy): 是否有前后矛盾？
3. 人设稳定性 (Character Stability): 是否符合其Profile描述？
4. 社会规范与常识 (Social Norms & Common Sense): 是否符合一般的社会规范和常识？
5. 语言多样性 (Language Diversity): 词汇和句式是否丰富？

请以JSON格式输出:
{
    "logic_score": 0,
    "logic_reason": "...",
    "memory_score": 0,
    "memory_reason": "...",
    "stability_score": 0,
    "stability_reason": "...",
    "norms_score": 0,
    "norms_reason": "...",
    "diversity_score": 0,
    "diversity_reason": "...",
    "overall_comment": "..."
}
```
