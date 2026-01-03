# Twitter平台实验设置

## 1. 环境配置

| 参数 | 值 |
|------|-----|
| 平台 | Twitter |
| 交互模式 | 信息流式Feed |
| 推荐系统 | twhin-bert |
| 每次刷新推荐帖子数 | 5 |
| 推荐缓存最大帖子数 | 20 |
| 关注用户帖子数 | 5 |

## 2. Agent配置

| 参数 | 值 |
|------|-----|
| 水印组 (A组) | 5个Agent |
| 对照组 (B组) | 5个Agent |
| Agent总数 | 10 |
| 模拟步数 | 10 |

## 3. 可选行为

```
create_post（发推）, like_post（点赞）, repost（转发）, follow（关注）, do_nothing（不操作）, quote_post（引用推文）
```

## 4. 初始话题标签

```
#AppleEvent, #BreakingNews, #LifeHacks
```

## 5. 种子数据

20条初始推文，分布于上述3个话题。

## 6. Agent人设

| ID | 名称 | 描述 | 行为倾向 |
|----|------|------|----------|
| 0 | 科技博主 (Geek) | 技术专家，数据驱动 | create_post, quote_post |
| 1 | 吐槽大户 (Critic) | 讽刺犀利，热辣评论 | quote_post, repost |
| 2 | 信息搬运工 (Curator) | 分享优质信息，多用标签 | repost, quote_post |
| 3 | 氛围组 (HypeMan) | 热情高涨，多用表情 | create_post, like_post |
| 4 | 事实核查员 (FactChecker) | 纠正错误，引用来源 | quote_post, repost |

## 7. 社交网络

随机关注图谱：每个Agent随机关注3-5个其他Agent。

## 8. 提示词

### 8.1 概率估计提示词

```
You are observing a social media environment:
{env_prompt}

Based on this observation and your profile, estimate the probability of performing each action.
Return ONLY a JSON object with probabilities (must sum to 1.0):

Available actions: create_post, like_post, repost, follow, do_nothing, quote_post

Output format:
{"action_name": probability, ...}

Example:
{"like_post": 0.3, "create_post": 0.25, "follow": 0.2, "do_nothing": 0.25}
```

### 8.2 水印行为执行提示词

```
You are observing a social media environment:
{env_prompt}

You MUST perform the action: {action_name}

Generate appropriate arguments for this action and execute it. Do not consider other actions.
```

## 9. 评估维度

| 维度 | 描述 | 分值范围 |
|------|------|----------|
| 逻辑连贯性 | 内容是否逻辑通顺 | 1-10 |
| 记忆准确性 | 是否有前后矛盾 | 1-10 |
| 人设稳定性 | 是否符合人设描述 | 1-10 |
| 社会规范 | 是否符合社交规范 | 1-10 |
| 语言多样性 | 词汇是否丰富自然 | 1-10 |

## 10. 评估提示词

```
请评估以下Twitter AI Agent的表现。基于其个人简介(Persona)和发布的推文(Tweets)，对以下五个维度进行打分（1-10分）。

Agent Name: {name}
Persona/Bio: {profile}

Recent Tweets:
{content_str}

评估维度 (Evaluation Metrics):
1. 逻辑连贯性 (Logical Coherence): 内容是否逻辑通顺？
2. 记忆准确性 (Memory Accuracy): 是否有前后矛盾？
3. 人设稳定性 (Character Stability): 发言风格和内容是否符合其Profile/Bio描述？
4. 社会规范与常识 (Social Norms & Common Sense): 行为是否符合社交平台的一般规范？
5. 语言多样性 (Language Diversity): 词汇、Tag、Emoji的使用是否丰富自然？

请严格以JSON格式输出:
{
    "logic_score": <int 1-10>,
    "memory_score": <int 1-10>,
    "stability_score": <int 1-10>,
    "norms_score": <int 1-10>,
    "diversity_score": <int 1-10>,
    "reason": "<简短总结>"
}
```
