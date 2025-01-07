import requests
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# GitHub API Token and Username from environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
USERNAME = os.getenv('GITHUB_USERNAME', 'lebraat')  # Default to 'lebraat' if not set

if not GITHUB_TOKEN:
    raise ValueError("Please set GITHUB_TOKEN environment variable")

# GraphQL API endpoint
GRAPHQL_URL = "https://api.github.com/graphql"

# Headers for the API request
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

# Query to get repositories the user has contributed to
REPO_QUERY = """
query($username: String!, $cursor: String) {
  user(login: $username) {
    repositoriesContributedTo(first: 100, after: $cursor) {
      pageInfo {
        endCursor
        hasNextPage
      }
      nodes {
        name
        owner {
          login
        }
      }
    }
  }
}
"""

# Query to get commit history for a specific repo
COMMIT_QUERY = """
query($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, after: $cursor) {
            pageInfo {
              endCursor
              hasNextPage
            }
            edges {
              node {
                committedDate
                author {
                  user {
                    login
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

def fetch_repositories(username):
    repositories = []
    cursor = None

    while True:
        variables = {"username": username, "cursor": cursor}
        response = requests.post(GRAPHQL_URL, json={"query": REPO_QUERY, "variables": variables}, headers=HEADERS)
        data = response.json()

        repos = data["data"]["user"]["repositoriesContributedTo"]["nodes"]
        repositories.extend(repos)

        if not data["data"]["user"]["repositoriesContributedTo"]["pageInfo"]["hasNextPage"]:
            break
        cursor = data["data"]["user"]["repositoriesContributedTo"]["pageInfo"]["endCursor"]

    return repositories

def fetch_commit_dates(owner, repo, username):
    commit_dates = set()
    cursor = None

    while True:
        variables = {"owner": owner, "repo": repo, "cursor": cursor}
        response = requests.post(GRAPHQL_URL, json={"query": COMMIT_QUERY, "variables": variables}, headers=HEADERS)
        print(f"API Response for {owner}/{repo}:", response.json())

        commits = response.json()["data"]["repository"]["defaultBranchRef"]["target"]["history"]["edges"]
        for commit in commits:
            # Only count commits by the specified user
            author_login = commit["node"]["author"]["user"]["login"] if commit["node"]["author"]["user"] else None
            if author_login == username:
                date_str = commit["node"]["committedDate"]
                date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").date()
                commit_dates.add(date)

        if not response.json()["data"]["repository"]["defaultBranchRef"]["target"]["history"]["pageInfo"]["hasNextPage"]:
            break
        cursor = response.json()["data"]["repository"]["defaultBranchRef"]["target"]["history"]["pageInfo"]["endCursor"]

    return commit_dates

def main():
    # Step 1: Get the list of repositories the user contributed to
    repositories = fetch_repositories(USERNAME)
    print(f"Found {len(repositories)} repositories.")

    # Step 2: Get the unique commit dates for each repository
    unique_dates = set()

    for repo in repositories:
        owner = repo["owner"]["login"]
        name = repo["name"]
        print(f"Fetching commits for {owner}/{name}...")
        commit_dates = fetch_commit_dates(owner, name, USERNAME)
        unique_dates.update(commit_dates)

    # Step 3: Output the total number of unique commit days
    print(f"Total unique commit days: {len(unique_dates)}")

if __name__ == "__main__":
    main()
