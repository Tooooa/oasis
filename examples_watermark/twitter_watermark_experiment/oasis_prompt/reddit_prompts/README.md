# Reddit Watermark Experiment Prompts

This folder contains all prompts used in the Reddit Watermark Experiment (r/TechFuture simulation).

## Files

| File | Purpose |
|------|---------|
| `agent_personas.md` | Agent behavior prompts (5 personas) |
| `evaluation_prompt.md` | LLM evaluation prompt for scoring agents |

## Usage

- **Agent Personas**: Loaded by `run_experiment.py` to define how each agent behaves on the simulated Reddit platform.
- **Evaluation Prompt**: Used by `evaluate_metrics_llm.py` to call DeepSeek API and score agents on 5 dimensions.
