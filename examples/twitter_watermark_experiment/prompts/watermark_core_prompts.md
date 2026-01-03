# Watermark Core Prompts

This file contains the prompts used in the **watermark embedding** process.
These are the core prompts for the probability-based action selection mechanism.

---

## 1. Action Probability Estimation Prompt

**Purpose**: Ask LLM to estimate probability distribution over all available actions based on current social media context.

**Location in Code**: `oasis/social_agent/agent.py` → `_get_action_probabilities()` method

**When Used**: Every time a watermarked agent needs to make a decision (Phase 1 of two-phase approach)

```text
You are observing a social media environment:
{env_prompt}

Based on this observation and your profile, estimate the probability of performing each action.
Return ONLY a JSON object with probabilities (must sum to 1.0):

Available actions: {actions_str}

Output format:
{"action_name": probability, ...}

Example:
{"like_post": 0.3, "create_comment": 0.25, "follow": 0.2, "refresh": 0.25}
```

### Variables
| Variable | Description |
|----------|-------------|
| `{env_prompt}` | Current feed content, posts, and social context |
| `{actions_str}` | Comma-separated list of available actions (e.g., "like_post, create_comment, follow, refresh") |

### Expected Output
```json
{"like_post": 0.35, "create_comment": 0.25, "follow": 0.15, "refresh": 0.25}
```

---

## 2. Watermarked Action Execution Prompt

**Purpose**: Force LLM to execute a specific action (selected by watermark algorithm) with appropriate arguments.

**Location in Code**: `oasis/social_agent/agent.py` → `_execute_watermarked_action()` method

**When Used**: After watermark sampling selects an action (Phase 3 of two-phase approach)

```text
You are observing a social media environment:
{env_prompt}

You MUST perform the action: {action_name}

Generate appropriate arguments for this action and execute it. Do not consider other actions.
```

### Variables
| Variable | Description |
|----------|-------------|
| `{env_prompt}` | Current feed content and context |
| `{action_name}` | The action selected by watermark (e.g., "like_post") |

---

## 3. Normal Mode Action Prompt (No Watermark)

**Purpose**: Let LLM freely choose and execute actions when watermark is disabled.

**Location in Code**: `oasis/social_agent/agent.py` → `perform_action_by_llm()` method

```text
Please perform social media actions after observing the platform environments. 
Notice that don't limit your actions for example to just like the posts. 
Here is your social media environment: {env_prompt}
```

---

## Watermark Process Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Watermarked Agent                        │
├─────────────────────────────────────────────────────────────┤
│ Phase 1: Probability Estimation                             │
│   └── LLM Call with Prompt #1                               │
│   └── Output: {"like": 0.3, "comment": 0.4, "follow": 0.3}  │
│                                                             │
│ Phase 2: Watermark Sampling                                 │
│   └── Differential-based encoder                            │
│   └── Embed secret bits into action selection               │
│   └── Output: "comment" (watermark-selected)                │
│                                                             │
│ Phase 3: Action Execution                                   │
│   └── LLM Call with Prompt #2                               │
│   └── Execute "comment" with generated arguments            │
└─────────────────────────────────────────────────────────────┘
```

---

## Recommended Paper Placement

| Section | Usage |
|---------|-------|
| **Method / Methodology** | Full prompt text with explanation |
| **Appendix** | If space is limited, place full prompts here |
| **Implementation Details** | Reference to prompts with summary |
