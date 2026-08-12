from agent_harness import run_agent

for q in [
    "Which of these three repos has the most forks: facebook/react, microsoft/vscode, octocat/Hello-World? How many forks does it have?",
    "Between microsoft/vscode and octocat/Hello-World, which has more open issues, and by how much?",
    "How many open issues, excluding pull requests, does octocat/Hello-World have?",
]:
    result = run_agent(q)
    print("\nQ:", q)
    print("A:", result["final_answer"])