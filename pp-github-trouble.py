import requests
from datetime import datetime, timedelta
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

def get_user_creation_date(username):
    """Fetch the user's account creation date."""
    query = '''
    query($username: String!) {
        user(login: $username) {
            createdAt
        }
    }
    '''
    
    response = requests.post(
        GRAPHQL_URL, 
        json={"query": query, "variables": {"username": username}}, 
        headers=HEADERS
    )
    
    if response.status_code != 200:
        raise Exception(f"GitHub API error: {response.status_code}")
    
    data = response.json()
    return datetime.strptime(data['data']['user']['createdAt'], "%Y-%m-%dT%H:%M:%SZ").date()

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
            json={"query": '''
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
                                createdAt
                            }
                        }
                    }
                }
            ''', "variables": variables}, 
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

def fetch_commit_dates(owner, repo, username, user_creation_date):
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
            json={"query": '''
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
            ''', "variables": variables}, 
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
                commit_date = datetime.strptime(commit['committedDate'], "%Y-%m-%dT%H:%M:%SZ").date()
                # Only count commits after user creation
                if commit_date >= user_creation_date:
                    commit_dates.add(commit_date)

        has_next_page = commit_history['pageInfo']['hasNextPage']
        cursor = commit_history['pageInfo']['endCursor']

    return commit_dates

def verify_github_contributions(username, threshold=1, years_back=3):
    """
    Verify GitHub contributions with configurable threshold.
    
    :param username: GitHub username to verify
    :param threshold: Minimum number of contribution days required
    :param years_back: Number of years to look back
    :return: Verification result dictionary
    """
    try:
        # Get user creation date
        user_creation_date = get_user_creation_date(username)
        
        # Fetch repositories
        repositories = fetch_repositories(username)
        
        # Collect unique commit dates
        unique_commit_dates = set()
        for repo in repositories:
            repo_commit_dates = fetch_commit_dates(
                repo['owner']['login'], 
                repo['name'], 
                username, 
                user_creation_date
            )
            unique_commit_dates.update(repo_commit_dates)
        
        # Filter dates within the specified years
        cutoff_date = datetime.now().date() - timedelta(days=years_back * 365)
        filtered_dates = {date for date in unique_commit_dates if date >= cutoff_date}
        
        # Prepare verification result
        result = {
            'valid': len(filtered_dates) >= threshold,
            'contribution_days': len(filtered_dates),
            'threshold': threshold,
            'years_back': years_back,
            'user_creation_date': user_creation_date
        }
        
        return result

    except Exception as e:
        return {
            'valid': False,
            'error': str(e)
        }

def main():
    """Main function to analyze GitHub contributions."""
    try:
        # You can adjust the threshold and years as needed
        result = verify_github_contributions(USERNAME, threshold=1, years_back=3)
        
        if result.get('valid'):
            print(f"Verification Passed!")
            print(f"Total unique contribution days: {result['contribution_days']}")
        else:
            print(f"Verification Failed.")
            print(f"Error: {result.get('error', 'Did not meet contribution threshold')}")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
