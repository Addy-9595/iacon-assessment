# GitHub Q&A Agent Harness

An agent harness that answers natural-language questions about GitHub repositories using tool calling. The agent decides which GitHub API endpoints to call, executes them, and reasons over the results to produce a final answer. Every step (tool calls, inputs, results, final answer) is logged to a JSON file for inspection.

## Requirements

- Python 3.9+
- An Anthropic API key (https://console.anthropic.com)
- A GitHub personal access token (no special scopes needed — public repo reads only)

## Setup

1. Clone or download this repository.

2. Create a virtual environment and activate it:
   ```
   python -m venv .venv
   ```
   Windows:
   ```
   .venv\Scripts\activate
   ```
   Mac/Linux:
   ```
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install anthropic requests python-dotenv
   ```

4. Create a `.env` file in the project root with:
   ```
   ANTHROPIC_API_KEY=your_anthropic_key_here
   GITHUB_TOKEN=your_github_token_here
   ```

## Files

- `agent_harness.py` — core harness: tool definitions, tool implementations (GitHub API calls), agent loop, trajectory logging
- `run_eval.py` — runs a fixed set of 15 test questions through the harness and saves a summary
- `fetch_ground_truth.py` — pulls live GitHub data used to independently verify correct answers before evaluation
- `ground_truth.md` — the 15 test questions with pre-verified correct answers
- `logs/` — per-question trajectory logs (created automatically when the harness runs)
- `eval_summary.json` — output of the full 15-question run (created automatically)

## Running the harness on a single question

Run directly:
```
python agent_harness.py
```
This executes one hardcoded test question and prints the final answer, saving the full trajectory to `logs/`.

To ask a different question, edit the `test_question` variable at the bottom of `agent_harness.py`, or import and call it from your own script:
```python
from agent_harness import run_agent

result = run_agent("How many stars does torvalds/linux have?")
print(result["final_answer"])
```

## Running the full evaluation

```
python run_eval.py
```
This runs all 15 fixed test questions, prints progress as it goes, saves a trajectory log per question in `logs/`, and writes a combined summary to `eval_summary.json`.

## Notes

- GitHub API rate limits: 60 requests/hour without a token, 5,000/hour with one. The harness will pass rate-limit errors back to the model rather than crashing.
- The agent caps tool-call iterations at 5 per question to prevent infinite loops.