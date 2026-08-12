from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

REPOS = ["facebook/react", "microsoft/vscode", "octocat/Hello-World"]

def get_repo_info(repo):
    url = f"https://api.github.com/repos/{repo}"
    r = requests.get(url, headers=HEADERS)
    return r.json()

def get_contributors(repo, per_page=5):
    url = f"https://api.github.com/repos/{repo}/contributors"
    r = requests.get(url, headers=HEADERS, params={"per_page": per_page})
    return r.json()

def get_latest_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    r = requests.get(url, headers=HEADERS)
    return r.json()

def get_open_issues_count(repo):
    info = get_repo_info(repo)
    return info.get("open_issues_count")

if __name__ == "__main__":
    for repo in REPOS:
        print(f"\n=== {repo} ===")
        info = get_repo_info(repo)
        print("Stars:", info.get("stargazers_count"))
        print("Open issues (includes PRs):", info.get("open_issues_count"))
        print("Forks:", info.get("forks_count"))
        print("Default branch:", info.get("default_branch"))
        print("Language:", info.get("language"))

        contributors = get_contributors(repo)
        print("Top contributors:")
        if isinstance(contributors, list):
            for c in contributors[:5]:
                print(f"  {c.get('login')}: {c.get('contributions')} contributions")
        else:
            print("  Error or rate-limited:", contributors)

        release = get_latest_release(repo)
        if "tag_name" in release:
            print("Latest release:", release.get("tag_name"), "-", release.get("published_at"))
        else:
            print("Latest release: none found or error:", release.get("message"))