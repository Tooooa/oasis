# LLM Evaluation Prompt (Reddit)

**Purpose**: This prompt is sent to DeepSeek API to evaluate each agent's performance on 5 dimensions based on their persona and generated posts/comments.

**Used In**: `evaluate_metrics_llm.py`

---

## System Message

```
你是专业的社交媒体行为评估专家。
```

---

## Prompt Template

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

请以JSON格式输出，格式如下:
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

---

## Variable Descriptions

| Variable | Description |
|----------|-------------|
| `{user_name}` | Agent's username (e.g., "wm_tech_geek_expert") |
| `{profile}` | Agent's bio from database |
| `{content_str}` | Up to 20 posts/comments, formatted as "[Post] content" or "[Comment] content" |

---

## Output Format

The LLM returns a JSON object with scores (1-10) and reasons for each dimension:

```json
{
    "logic_score": 8,
    "logic_reason": "内容逻辑清晰，论点有条理",
    "memory_score": 9,
    "memory_reason": "未发现前后矛盾",
    "stability_score": 7,
    "stability_reason": "基本符合技术专家人设",
    "norms_score": 8,
    "norms_reason": "表达得体，符合社区规范",
    "diversity_score": 6,
    "diversity_reason": "词汇较为技术化，句式变化一般",
    "overall_comment": "整体表现良好，技术分析到位"
}
```

---

## Evaluation Dimensions Explained

| Dimension | Chinese | What It Measures |
|-----------|---------|------------------|
| Logic Coherence | 逻辑连贯性 | Are posts/comments logically consistent? |
| Memory Accuracy | 记忆准确性 | Does agent contradict itself over time? |
| Character Stability | 人设稳定性 | Does behavior match assigned persona? |
| Social Norms | 社会规范与常识 | Is content appropriate for the community? |
| Language Diversity | 语言多样性 | Variety in vocabulary and sentence structure? |
