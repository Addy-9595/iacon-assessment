Tier A — single lookup

How many stars does facebook/react have? → 247,201
What language is microsoft/vscode primarily written in? → TypeScript
What is the default branch of octocat/Hello-World? → master
How many forks does facebook/react have? → 51,226
What is the latest release version tag of microsoft/vscode? → 1.133.0

Tier B — multi-step / chained
6. Which of the three repos has the most forks, and how many? → react, 51,226
7. Who is the top contributor to facebook/react, and how many contributions do they have? → sebmarkbage, 1,939
8. Between microsoft/vscode and octocat/Hello-World, which has more open issues, and by how much? → vscode, by 12,903 (19,804 vs 6,901)
9. Rank all three repos by star count, highest to lowest. → react (247,201) > vscode (188,633) > Hello-World (3,765)
10. Which of the three repos has no listed primary language? → octocat/Hello-World

Tier C — traps / edge cases
11. How many stars does facebook/this-repo-does-not-exist-12345 have? → Correct behavior: report a 404 / "repo not found," not a hallucinated number. This is the single most important test in your set — flag it clearly in your analysis.
12. What is the latest release of octocat/Hello-World? → None exists (404 on releases/latest). Correct behavior: say so, don't invent a version number.
13. How many open issues (excluding pull requests) does octocat/Hello-World have? → Trap: the API field conflates issues and PRs. There's no single correct number without a follow-up call filtering by pull_request field. Correct behavior: either flag the ambiguity or attempt the filtered call — either is defensible, but silently reporting 6,901 as "issues" is a documented failure mode.
14. Is octocat/Hello-World's open issue count (6,901) unusually high for a repo with only 3,765 stars? → Tests judgment, not lookup — there's no numeric ground truth, this checks whether the agent notices the anomaly or reports the number with false confidence.
15. How many contributions does torvalds have to microsoft/vscode? → Correct behavior: report that this person isn't in the contributor list (0 or "not found"), not guess a number.