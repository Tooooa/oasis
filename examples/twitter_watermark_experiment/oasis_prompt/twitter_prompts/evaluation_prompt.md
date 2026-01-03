# LLM Evaluation Prompt

**Purpose**: This prompt is sent to DeepSeek API to evaluate each agent's performance on 5 dimensions based on their persona and generated tweets.

**Used In**: `evaluate_metrics_llm.py`

---

## Prompt Template

```
请评估以下Twitter AI Agent的表现。基于其个人简介(Persona)和发布的推文(Tweets)，对以下五个维度进行打分（1-10分）。

Agent Name: {name}
Persona/Bio: {profile}

Recent Tweets:
{content_str}

评估维度 (Evaluation Metrics):
1. 逻辑连贯性 (Logical Coherence): 内容是否逻辑通顺？
2. 记忆准确性 (Memory Accuracy): 是否有前后矛盾？(如果没有足够上下文判断矛盾，给高分)
3. 人设稳定性 (Character Stability): 发言风格和内容是否符合其Profile/Bio描述？
4. 社会规范与常识 (Social Norms & Common Sense): 行为是否符合社交平台的一般规范？
5. 语言多样性 (Language Diversity): 词汇、Tag、Emoji的使用是否丰富自然？

请严格以JSON格式输出，不要包含Markdown formatting (```json ... ```)，直接输出JSON字符串:
{
    "logic_score": <int 1-10>,
    "memory_score": <int 1-10>,
    "stability_score": <int 1-10>,
    "norms_score": <int 1-10>,
    "diversity_score": <int 1-10>,
    "reason": "<short summary>"
}
```

---

## System Message

```
You are an expert social media agent evaluator.
```

---

## Variable Descriptions

| Variable | Description |
|----------|-------------|
| `{name}` | Agent's display name (e.g., "Geek_wm_0") |
| `{profile}` | Agent's persona/bio from `personas.py` |
| `{content_str}` | Up to 20 recent tweets, formatted as bullet list |

---

## Output Format

The LLM returns a JSON object with scores (1-10) for each dimension:

```json
{
    "logic_score": 8,
    "memory_score": 9,
    "stability_score": 7,
    "norms_score": 8,
    "diversity_score": 6,
    "reason": "Agent maintains consistent tech-focused persona with data-driven analysis."
}
```

---

## Evaluation Dimensions Explained

| Dimension | Chinese | What It Measures |
|-----------|---------|------------------|
| Logic Coherence | 逻辑连贯性 | Are tweets logically consistent? |
| Memory Accuracy | 记忆准确性 | Does agent contradict itself over time? |
| Character Stability | 人设稳定性 | Does behavior match assigned persona? |
| Social Norms | 社会规范与常识 | Is content appropriate for social media? |
| Language Diversity | 语言多样性 | Variety in vocabulary, hashtags, emojis? |
