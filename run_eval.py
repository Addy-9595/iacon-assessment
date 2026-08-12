from agent_harness import run_agent
import json

QUESTIONS = [
    # Tier A -- single lookup
    "How many stars does facebook/react have?",
    "What language is microsoft/vscode primarily written in?",
    "What is the default branch of octocat/Hello-World?",
    "How many forks does facebook/react have?",
    "What is the latest release version tag of microsoft/vscode?",

    # Tier B -- multi-step / chained
    "Which of these three repos has the most forks: facebook/react, microsoft/vscode, octocat/Hello-World? How many forks does it have?",
    "Who is the top contributor to facebook/react, and how many contributions do they have?",
    "Between microsoft/vscode and octocat/Hello-World, which has more open issues, and by how much?",
    "Rank facebook/react, microsoft/vscode, and octocat/Hello-World by star count, highest to lowest.",
    "Which of these three repos has no listed primary language: facebook/react, microsoft/vscode, octocat/Hello-World?",

    # Tier C -- traps / edge cases
    "How many stars does facebook/this-repo-does-not-exist-12345 have?",
    "What is the latest release of octocat/Hello-World?",
    "How many open issues, excluding pull requests, does octocat/Hello-World have?",
    "Is octocat/Hello-World's open issue count unusually high for a repo with only 3,765 stars? Explain briefly.",
    "How many contributions does the user 'torvalds' have to microsoft/vscode?",
]

TIER_LABELS = ["A"] * 5 + ["B"] * 5 + ["C"] * 5

if __name__ == "__main__":
    summary = []

    for i, (question, tier) in enumerate(zip(QUESTIONS, TIER_LABELS), start=1):
        print(f"\n[{i}/15] (Tier {tier}) Running: {question}")
        result = run_agent(question, log_dir="logs")
        print(f"  -> {result['final_answer'][:150]}")

        summary.append({
            "number": i,
            "tier": tier,
            "question": question,
            "final_answer": result["final_answer"],
            "iterations_used": result["iterations_used"],
            "hit_max_iterations": result["hit_max_iterations"],
        })

    with open("eval_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\n\nAll 15 questions run. Summary saved to eval_summary.json")
    print("Individual trajectory logs saved in logs/")