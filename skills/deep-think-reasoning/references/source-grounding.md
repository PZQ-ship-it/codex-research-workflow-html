# Source Grounding For Deep Think Reasoning

Use this file when explaining the design rationale behind the skill or when updating the workflow.

## Public Deep Think Signals

Google's public materials describe Gemini Deep Think as an enhanced reasoning mode, but do not disclose the full proprietary implementation. Treat these as design signals, not a clone specification.

- Google Blog, "Gemini 2.5: Deep Think is now rolling out" states that Deep Think uses extended parallel thinking, generates many ideas at once, revises or combines ideas over time, and benefits from longer inference or "thinking time": https://blog.google/products-and-platforms/products/gemini/gemini-2-5-deep-think/
- Google DeepMind's Gemini 2.5 Deep Think model card describes it as using parallel thinking and reinforcement learning to test multiple hypotheses at once, with multimodal input and long context: https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-2-5-Deep-Think-Model-Card.pdf
- The Gemini 2.5 technical report says Deep Think produces multiple hypotheses and critiques them before the final answer: https://storage.googleapis.com/deepmind-media/gemini/gemini_v2_5_report.pdf
- Google AI Developer docs expose controllable thinking levels/budgets and thought summaries for Gemini APIs, which supports the general pattern of allocating more inference effort to harder tasks: https://ai.google.dev/gemini-api/docs/thinking and https://ai.google.dev/gemini-api/docs/interactions/thinking

## Research Patterns To Reuse

These papers provide open workflow analogues that can be reproduced with prompting, subagents, and tool checks:

- Tree of Thoughts explores multiple intermediate reasoning paths, self-evaluates choices, and backtracks when useful: https://arxiv.org/abs/2305.10601
- Self-consistency samples diverse reasoning paths and selects the answer that is most consistent across paths: https://arxiv.org/abs/2203.11171
- Reflexion uses verbal feedback and reflection after failures instead of updating model weights: https://arxiv.org/abs/2303.11366
- Multi-agent debate lets multiple model instances propose and critique answers over rounds: https://arxiv.org/abs/2305.14325

## Skill-Level Reproduction

The skill can reproduce the observable problem-solving pattern, not the proprietary training recipe:

1. Increase reasoning budget only when the task warrants it.
2. Generate independent candidate lanes.
3. Critique candidates with a rubric.
4. Verify with tools, tests, source lookup, or proof checks.
5. Reflect on failures and repair once.
6. Synthesize with preserved dissent and confidence.

Avoid overclaiming. If the user asks whether this is equivalent to Gemini Deep Think, answer: "No; it is a workflow-level approximation based on public descriptions and open reasoning patterns."
