import requests
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# GitHub API Token and Username from environment variables
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
USERNAME = os.getenv('GITHUB_USERNAME')

if not GITHUB_TOKEN:
    raise ValueError("Please set GITHUB_TOKEN environment variable")

if not USERNAME:
    raise ValueError("Please set GITHUB_USERNAME environment variable")

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
    """Fetch repositories the user has contributed to."""
    repositories = []
    has_next_page = True
    cursor = None

    while has_next_page:
        variables = {
            "username": username,
            "cursor": cursor
        }

        response = requests.post(
            GRAPHQL_URL, 
            json={"query": REPO_QUERY, "variables": variables}, 
            headers=HEADERS
        )

        if response.status_code != 200:
            raise Exception(f"GitHub API error: {response.status_code}")

        data = response.json()
        if 'errors' in data:
            raise Exception(f"GitHub API error: {data['errors']}")

        repo_data = data['data']['user']['repositoriesContributedTo']
        repositories.extend(repo_data['nodes'])

        has_next_page = repo_data['pageInfo']['hasNextPage']
        cursor = repo_data['pageInfo']['endCursor']

    return repositories

def fetch_commit_dates(owner, repo, username):
    """Fetch commit dates for a specific repository."""
    commit_dates = set()
    has_next_page = True
    cursor = None

    while has_next_page:
        variables = {
            "owner": owner,
            "repo": repo,
            "cursor": cursor
        }

        response = requests.post(
            GRAPHQL_URL, 
            json={"query": COMMIT_QUERY, "variables": variables}, 
            headers=HEADERS
        )

        if response.status_code != 200:
            raise Exception(f"GitHub API error: {response.status_code}")

        data = response.json()
        if 'errors' in data:
            raise Exception(f"GitHub API error: {data['errors']}")

        commit_history = data['data']['repository']['defaultBranchRef']['target']['history']
        
        for edge in commit_history['edges']:
            commit = edge['node']
            if commit['author']['user'] and commit['author']['user']['login'] == username:
                commit_dates.add(commit['committedDate'].split('T')[0])

        has_next_page = commit_history['pageInfo']['hasNextPage']
        cursor = commit_history['pageInfo']['endCursor']

    return commit_dates

def main():
    """Main function to analyze GitHub contributions."""
    try:
        # Fetch repositories
        repositories = fetch_repositories(USERNAME)
        
        # Collect unique commit dates
        unique_commit_dates = set()
        for repo in repositories:
            repo_commit_dates = fetch_commit_dates(repo['owner']['login'], repo['name'], USERNAME)
            unique_commit_dates.update(repo_commit_dates)
        
        # Print results
        print(f"Total unique days with commits: {len(unique_commit_dates)}")
        print("Commit dates:")
        for date in sorted(unique_commit_dates):
            print(date)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
