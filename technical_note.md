# Technical Note

## Why I chose this problem

I chose Problem 1 (Agent Harness) because it offered the clearest path to a small, complete, end-to-end system within the time limit, rather than an open framework I'd risk leaving half-built. Within that, I scoped to one narrow task: an agent that answers natural-language questions about GitHub repositories using the GitHub REST API. I picked GitHub specifically because it's free to access, well documented, and I could independently verify every answer by hand against the live API — which mattered more to me than picking a "more interesting" domain I couldn't easily check.

## Decisions and tradeoffs

Before writing any code, I locked a fixed set of 15 test questions across three tiers — 5 single-lookup, 5 multi-step/chained, 5 deliberate edge cases — with correct answers pulled from a live API call I ran myself, not from memory or assumption. This was a deliberate choice to avoid the trap of building first and figuring out "what counts as correct" after the fact.

I built four tools: repo info, contributors, latest release, and a filtered issue search. The fourth tool exists because of a real quirk I found while pulling ground truth: GitHub's `open_issues_count` field silently includes pull requests. Rather than hide this, I built it into the evaluation as a trap question, since it's exactly the kind of subtle misreading a careless agent would get wrong without anyone noticing.

I capped tool-call iterations at 5 per question to prevent runaway loops, and logged every tool call, input, and result to a JSON trajectory file per question. This was a direct response to the assignment's requirement that agent behavior be inspectable — I wanted anyone reviewing this to be able to see exactly why the agent gave a given answer, not just the final text.

## What worked

14 of 15 questions passed on the first full run, including all five Tier A lookups and, more importantly, every Tier C trap: the agent correctly reported a 404 instead of hallucinating a star count for a nonexistent repo, correctly reported "no releases" instead of inventing a version number, and correctly scoped its own contributor search rather than falsely claiming coverage it hadn't actually requested. I verified that last one specifically by reading the raw trajectory log, not just trusting the agent's stated claim — the logged tool input matched what it said it had checked.

## What didn't work, and what I did about it

One question ("between these two repos, which has more open issues") exposed an inconsistency: the original system prompt told the model to prefer the PR-filtered issue count "when precision matters," which let the model infer on its own, question by question, whether a user's ambiguous phrasing meant they wanted PRs excluded. In practice this made behavior unpredictable — the same underlying ambiguity could be resolved two different ways depending on the model's read of the situation.

I fixed this by replacing judgment-based inference with a literal, mechanical rule: only exclude PRs when the question explicitly says so ("excluding pull requests," "issues only"); otherwise use the raw count and disclose that it includes PRs. I verified the fix worked by re-running the three affected questions and confirming the raw-vs-filtered behavior now depended only on the wording of the question, not on the model's interpretation of importance.

## How I evaluated the result

Rather than a single accuracy percentage, I scored by tier and by failure type, because an aggregate number would have hidden the two real findings that mattered: live ground-truth drift (star counts shift over hours simply because GitHub data is live, not because the agent is wrong) and the issue-count ambiguity above. I consider clean handling of Tier C — the trap questions — more informative than raw accuracy, since Tier A questions are close to trivial for any competent tool-calling setup, while error handling on missing data is what actually distinguishes a careful harness from a fragile one.

## What I would build or test next

I'd add a tool that lets the agent compare a repo's issue-to-star ratio against a baseline of similar repos, so "is this unusual?" questions get a quantified answer instead of the qualitative judgment the current harness gives. I'd also want to stress-test with adversarial phrasing — deliberately ambiguous or misleading questions — to find more cases like the issue-count one before they show up as silent inconsistencies rather than obvious failures.

## If I joined Iacon Autonomics

I'd want to work on evaluation methodology for agent harnesses themselves — specifically, how to detect when an agent's behavior is internally inconsistent (as with the issue-count case here) rather than simply wrong. A single accuracy number on a fixed test set is cheap to produce and easy to game by overfitting to the test questions; I think the harder and more valuable problem is building evaluation that surfaces inconsistency and unjustified confidence, which matters more once agents are given tools with real-world consequences rather than read-only API calls like this project used.