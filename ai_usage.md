# AI Usage Documentation

## Tools and models used
- **Claude (Anthropic, claude-sonnet-4-6)** — used two ways in this project:
  1. As a development collaborator (via Claude.ai chat) to plan the approach, design the harness, write code, and structure the evaluation.
  2. As the actual reasoning/tool-calling model inside the agent harness itself (called via the Anthropic API in `agent_harness.py`).

## What I used it for

**1. Problem scoping and planning**
Given the take-home brief, I asked Claude to help pick a specific direction (Problem 1: Agent Harness) and narrow it to a concrete, buildable task under the time limit, rather than an open-ended framework. Claude recommended building on the suggested "Pi agent harness" concept but scoping to one specific task: an agent that answers natural-language questions about GitHub repositories using the GitHub REST API.

**2. Defining success criteria before writing code**
Before any implementation, I worked with Claude to define:
- 15 fixed test questions split into three tiers (5 single-lookup, 5 multi-step/chained, 5 edge-case/trap questions)
- A scoring approach that tags failures by type (wrong tool, misread response, hallucination, silent error) rather than just pass/fail

**3. Ground truth verification**
I wrote and ran a script (provided by Claude, `fetch_ground_truth.py`) that pulled live data directly from the GitHub API for three fixed repos (`facebook/react`, `microsoft/vscode`, `octocat/Hello-World`). This was deliberate: rather than trusting the AI's memory of repo statistics (which are stale and change constantly), I verified every ground-truth answer against a real, timestamped API call I ran myself.

**4. Harness implementation**
Claude wrote the core harness (`agent_harness.py`): tool schemas, tool implementations (calling the GitHub REST API), the agent loop (send question → model may call a tool → execute tool → feed result back → repeat until final answer), and a trajectory logger that records every step to a JSON file for inspection.

I also had it write `run_eval.py`, a batch runner that executes all 15 questions and records a summary.

**5. Debugging and fix iteration**
After running the full 15-question eval, I reported the raw output back to Claude. It identified one inconsistency: for an ambiguous "how many open issues" question, the model had silently switched to a PR-filtered issue count without being asked. Claude proposed two possible fixes (always filter with a disclosure, vs. only filter on explicit request) and I chose the latter. Claude then edited the system prompt in `agent_harness.py` to make that behavior a literal, non-judgment-based rule instead of something the model inferred contextually.

## Representative prompts
- "lets go ahead with agent that answers questions from a specific API" — initial task scoping
- "Lets move to phase 1. what should i do here?" — requesting the test question design
- "Lets move to phase 2" — requesting the harness build
- After sharing eval output: asked Claude to score results against ground truth and identify failure patterns
- "only filter when the user explicitly says excluding PRs" — my decision on which fix approach to take, which Claude then implemented

## Which parts were substantially AI-generated
- `fetch_ground_truth.py`, `agent_harness.py`, `run_eval.py`, and the test loop used to verify the fix: written by Claude based on my specifications, reviewed and run by me.
- The 15 test questions and their categorization into tiers: drafted by Claude, reviewed by me before locking them in.
- The system prompt governing agent behavior (including the fix in Phase 4): written by Claude, with the underlying policy decision (which of two fix approaches to take) made by me.

## How I reviewed, tested, and modified the output
- I ran every script myself in PyCharm and pasted the actual terminal output and JSON trajectory logs back for review — I did not accept any code or result on Claude's word alone.
- I independently checked at least one full trajectory log by hand (the Q15 contributor lookup) to confirm the agent's claimed search scope (`per_page: 100`) matched what it actually requested, rather than trusting its stated answer.
- I verified ground truth numbers came from a live API call I ran, not from the AI's internal knowledge.
- After the system prompt fix, I re-ran the three affected questions specifically (not the full 15) to confirm the fix worked and didn't break unrelated behavior, before accepting the change as final.

## Important errors or limitations encountered
- **Ground truth drift**: star/fork counts for `microsoft/vscode` shifted by roughly 1 unit between my initial ground-truth fetch and the later evaluation run, purely because these are live, constantly-changing values on GitHub. This is a limitation of using live data for a fixed evaluation set, not an agent error.
- **Ambiguous question wording**: one test question ("which has more open issues") did not specify whether pull requests should be counted, and the agent silently made an inconsistent judgment call on this before the fix. This was a genuine design flaw in the original system prompt, not a hallucination.
- **`open_issues_count` API quirk**: GitHub's API field for open issues includes pull requests by default, which is not obvious from the field name. This was deliberately built into the evaluation as an edge case, and the harness now explicitly discloses this to the user by default rather than silently returning an ambiguous number.
- Deprecation warning for `datetime.datetime.utcnow()` appeared in testing; left unresolved as it does not affect functionality and was not worth the time under the project deadline.