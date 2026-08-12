from dotenv import load_dotenv
import os
import json
import requests
import anthropic
from datetime import datetime

load_dotenv()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GH_HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
MODEL = "claude-sonnet-4-6"
MAX_TOOL_ITERATIONS = 5

# ---------- TOOL IMPLEMENTATIONS ----------
# Each function returns a JSON-serializable dict.
# Errors are returned as data (not raised) so the model can see and react to them.

def tool_get_repo_info(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    r = requests.get(url, headers=GH_HEADERS)
    if r.status_code == 404:
        return {"error": f"Repository {owner}/{repo} not found (404)."}
    if r.status_code != 200:
        return {"error": f"GitHub API returned status {r.status_code}: {r.text[:200]}"}
    data = r.json()
    return {
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "open_issues_count_includes_prs": data.get("open_issues_count"),
        "language": data.get("language"),
        "default_branch": data.get("default_branch"),
    }

def tool_get_contributors(owner, repo, per_page=5):
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
    r = requests.get(url, headers=GH_HEADERS, params={"per_page": per_page})
    if r.status_code == 404:
        return {"error": f"Repository {owner}/{repo} not found (404)."}
    if r.status_code != 200:
        return {"error": f"GitHub API returned status {r.status_code}: {r.text[:200]}"}
    data = r.json()
    if not isinstance(data, list):
        return {"error": "Unexpected response format", "raw": data}
    return {"contributors": [{"login": c.get("login"), "contributions": c.get("contributions")} for c in data]}

def tool_get_latest_release(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    r = requests.get(url, headers=GH_HEADERS)
    if r.status_code == 404:
        return {"error": f"No releases found for {owner}/{repo} (404)."}
    if r.status_code != 200:
        return {"error": f"GitHub API returned status {r.status_code}: {r.text[:200]}"}
    data = r.json()
    return {"tag_name": data.get("tag_name"), "published_at": data.get("published_at")}

def tool_search_issues_only(owner, repo, state="open", per_page=100):
    # Uses the search API with is:issue to exclude PRs -- this is the correct
    # way to get a true issue count, unlike the repo_info field which mixes issues+PRs.
    url = "https://api.github.com/search/issues"
    query = f"repo:{owner}/{repo} is:issue state:{state}"
    r = requests.get(url, headers=GH_HEADERS, params={"q": query, "per_page": per_page})
    if r.status_code != 200:
        return {"error": f"GitHub API returned status {r.status_code}: {r.text[:200]}"}
    data = r.json()
    return {"true_issue_count_excluding_prs": data.get("total_count")}

TOOL_IMPLS = {
    "get_repo_info": tool_get_repo_info,
    "get_contributors": tool_get_contributors,
    "get_latest_release": tool_get_latest_release,
    "search_issues_only": tool_search_issues_only,
}

# ---------- TOOL SCHEMAS (Anthropic tool-use format) ----------

TOOLS = [
    {
        "name": "get_repo_info",
        "description": "Get basic info about a GitHub repo: stars, forks, open_issues_count (NOTE: this field includes pull requests, not just issues), language, default branch.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repo owner, e.g. 'facebook'"},
                "repo": {"type": "string", "description": "Repo name, e.g. 'react'"},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "get_contributors",
        "description": "Get the top contributors to a repo, ranked by number of contributions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "per_page": {"type": "integer", "description": "How many top contributors to return, default 5"},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "get_latest_release",
        "description": "Get the latest release tag and publish date for a repo. Returns an error if the repo has no releases.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "search_issues_only",
        "description": "Get the TRUE count of open issues for a repo, EXCLUDING pull requests. Use this instead of get_repo_info when the user specifically asks about 'issues' and precision matters, since get_repo_info's count includes PRs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"},
                "state": {"type": "string", "description": "'open' or 'closed', default 'open'"},
            },
            "required": ["owner", "repo"],
        },
    },
]

SYSTEM_PROMPT = """You are an assistant that answers questions about GitHub repositories using the provided tools.

Rules:
- Always use tools to look up real data. Never guess or make up numbers.
- If a tool returns an error (repo not found, no releases, etc.), report that clearly to the user instead of inventing an answer.
- For "open issues" questions, use this exact rule, do not use judgment to override it:
  - DEFAULT: use get_repo_info's open_issues_count field. Since this field includes pull requests, always state that in your answer (e.g. "X open issues (this count includes pull requests)").
  - ONLY use search_issues_only instead when the user's question explicitly says something like "excluding pull requests," "issues only," or "not counting PRs."
  - Do not infer that the user wants PRs excluded just because the exact number seems large or the topic seems important. Follow the literal wording of the question.
- If a number seems unusually high or low relative to context, you may note that, but do not refuse to answer.
- Give a direct, concise final answer once you have the data you need.
"""

# ---------- AGENT LOOP ----------

def run_agent(question, log_dir="logs"):
    os.makedirs(log_dir, exist_ok=True)
    trajectory = {
        "question": question,
        "timestamp": datetime.utcnow().isoformat(),
        "steps": [],
        "final_answer": None,
        "iterations_used": 0,
        "hit_max_iterations": False,
    }

    messages = [{"role": "user", "content": question}]

    for iteration in range(MAX_TOOL_ITERATIONS):
        trajectory["iterations_used"] = iteration + 1

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Log the raw model response for this step
        step_log = {
            "iteration": iteration + 1,
            "stop_reason": response.stop_reason,
            "content_blocks": [],
        }

        assistant_content = []
        tool_results = []

        for block in response.content:
            if block.type == "text":
                step_log["content_blocks"].append({"type": "text", "text": block.text})
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                step_log["content_blocks"].append({
                    "type": "tool_use", "name": tool_name, "input": tool_input
                })
                assistant_content.append({
                    "type": "tool_use", "id": block.id, "name": tool_name, "input": tool_input
                })

                # Execute the tool
                impl = TOOL_IMPLS.get(tool_name)
                if impl is None:
                    result = {"error": f"Unknown tool: {tool_name}"}
                else:
                    try:
                        result = impl(**tool_input)
                    except Exception as e:
                        result = {"error": f"Tool execution failed: {str(e)}"}

                step_log["content_blocks"].append({
                    "type": "tool_result", "name": tool_name, "result": result
                })
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

        trajectory["steps"].append(step_log)
        messages.append({"role": "assistant", "content": assistant_content})

        if response.stop_reason == "tool_use":
            messages.append({"role": "user", "content": tool_results})
            continue
        else:
            # Model gave a final text answer, no more tool calls
            final_text = "".join(b.text for b in response.content if b.type == "text")
            trajectory["final_answer"] = final_text
            break
    else:
        trajectory["hit_max_iterations"] = True
        trajectory["final_answer"] = "[AGENT DID NOT FINISH: hit max tool-call iterations without a final answer]"

    # Save trajectory log
    safe_name = "".join(c if c.isalnum() else "_" for c in question)[:50]
    log_path = os.path.join(log_dir, f"{safe_name}.json")
    with open(log_path, "w") as f:
        json.dump(trajectory, f, indent=2)

    return trajectory


if __name__ == "__main__":
    # Quick manual test -- run one question through the harness
    test_question = "How many stars does facebook/react have?"
    result = run_agent(test_question)
    print("QUESTION:", result["question"])
    print("FINAL ANSWER:", result["final_answer"])
    print("ITERATIONS USED:", result["iterations_used"])
    print(f"\nFull trajectory saved to logs/")