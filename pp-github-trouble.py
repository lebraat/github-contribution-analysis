import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Disable requests library's connection pooling and caching
requests.adapters.DEFAULT_RETRIES = 0
requests.packages.urllib3.util.connection.HAS_IPV6 = False
requests.packages.urllib3.disable_warnings()

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

# Headers for the API request with cache-control directives
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json",
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0"
}

def get_user_creation_date(username):
    """Fetch the user's account creation date."""
    start_time = time.time()
    logger.info(f"Fetching user creation date for {username}")
    
    query = '''
    query($username: String!) {
        user(login: $username) {
            createdAt
            repositories(first: 1, orderBy: {field: CREATED_AT, direction: ASC}) {
                nodes {
                    createdAt
                }
            }
        }
    }
    '''
    
    session = requests.Session()
    session.mount('https://api.github.com', requests.adapters.HTTPAdapter(max_retries=0))
    
    response = session.post(
        GRAPHQL_URL, 
        json={"query": query, "variables": {"username": username}}, 
        headers=HEADERS
    )
    
    if response.status_code != 200:
        raise Exception(f"GitHub API error: {response.status_code}")
    
    data = response.json()
    user_creation = datetime.strptime(data['data']['user']['createdAt'], "%Y-%m-%dT%H:%M:%SZ").date()
    
    # If user has repositories, use the earliest repo creation date
    repos = data['data']['user']['repositories']['nodes']
    if repos and repos[0]['createdAt']:
        earliest_repo = datetime.strptime(repos[0]['createdAt'], "%Y-%m-%dT%H:%M:%SZ").date()
        result = max(user_creation, earliest_repo)
    else:
        result = user_creation
    
    logger.info(f"User creation date fetch took {time.time() - start_time:.2f} seconds")
    return result

def fetch_repositories(username):
    """Fetch repositories the user has contributed to."""
    start_time = time.time()
    logger.info(f"Fetching repositories for {username}")
    
    repositories = []
    has_next_page = True
    cursor = None

    session = requests.Session()
    session.mount('https://api.github.com', requests.adapters.HTTPAdapter(max_retries=0))

    while has_next_page:
        variables = {
            "username": username,
            "cursor": cursor
        }

        response = session.post(
            GRAPHQL_URL, 
            json={"query": '''
                query($username: String!, $cursor: String) {
                    user(login: $username) {
                        repositoriesContributedTo(first: 100, after: $cursor, contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) {
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

    logger.info(f"Repository fetch for {username} took {time.time() - start_time:.2f} seconds")
    return repositories

def fetch_commit_dates(owner, repo, username, user_creation_date):
    """Fetch commit dates for a specific repository."""
    start_time = time.time()
    logger.info(f"Fetching commit dates for {owner}/{repo}")
    
    commit_dates = set()
    has_next_page = True
    cursor = None

    session = requests.Session()
    session.mount('https://api.github.com', requests.adapters.HTTPAdapter(max_retries=0))

    while has_next_page:
        variables = {
            "owner": owner,
            "repo": repo,
            "username": username,
            "cursor": cursor
        }

        response = session.post(
            GRAPHQL_URL, 
            json={"query": '''
                query($username: String!, $cursor: String) {
                    user(login: $username) {
                        contributionsCollection {
                            commitContributionsByRepository {
                                repository {
                                    createdAt
                                }
                                contributions(first: 100, after: $cursor) {
                                    pageInfo {
                                        endCursor
                                        hasNextPage
                                    }
                                    nodes {
                                        occurredAt
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

        contributions = data['data']['user']['contributionsCollection']['commitContributionsByRepository']
        
        for repo_contributions in contributions:
            repo_created_at = datetime.strptime(repo_contributions['repository']['createdAt'], "%Y-%m-%dT%H:%M:%SZ")
            
            for node in repo_contributions['contributions']['nodes']:
                commit_date = datetime.strptime(node['occurredAt'], "%Y-%m-%dT%H:%M:%SZ")
                
                # Only count commits after both user creation and repo creation
                if (commit_date.date() >= user_creation_date and 
                    commit_date >= repo_created_at):
                    commit_dates.add(commit_date.strftime("%Y-%m-%d"))

            page_info = repo_contributions['contributions']['pageInfo']
            has_next_page = page_info['hasNextPage']
            cursor = page_info['endCursor']

    logger.info(f"Commit dates fetch for {owner}/{repo} took {time.time() - start_time:.2f} seconds")
    return commit_dates

def verify_github_contributions(username, threshold=120, years_back=3):
    """
    Verify GitHub contributions with Gitcoin Passport-like criteria.
    
    :param username: GitHub username to verify
    :param threshold: Minimum number of contribution days required
    :param years_back: Number of years to look back
    :return: Verification result dictionary
    """
    start_time = time.time()
    logger.info(f"Starting contribution verification for {username}")
    
    try:
        # Get user creation date
        user_creation_date = get_user_creation_date(username)
        
        # Use a single GraphQL query to get all contributions
        session = requests.Session()
        session.mount('https://api.github.com', requests.adapters.HTTPAdapter(max_retries=0))
        
        cutoff_date = datetime.now() - timedelta(days=years_back * 365)
        
        response = session.post(
            GRAPHQL_URL,
            json={"query": '''
                query($username: String!, $from: DateTime!) {
                    user(login: $username) {
                        contributionsCollection(from: $from) {
                            commitContributionsByRepository {
                                repository {
                                    createdAt
                                }
                                contributions(first: 100) {
                                    nodes {
                                        occurredAt
                                    }
                                }
                            }
                        }
                    }
                }
            ''', "variables": {
                "username": username,
                "from": cutoff_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            }},
            headers=HEADERS
        )
        
        if response.status_code != 200:
            raise Exception(f"GitHub API error: {response.status_code}")
            
        data = response.json()
        if 'errors' in data:
            raise Exception(f"GitHub API error: {data['errors']}")
            
        unique_commit_dates = set()
        contributions = data['data']['user']['contributionsCollection']['commitContributionsByRepository']
        
        for repo_contributions in contributions:
            repo_created_at = datetime.strptime(repo_contributions['repository']['createdAt'], "%Y-%m-%dT%H:%M:%SZ")
            
            for node in repo_contributions['contributions']['nodes']:
                commit_date = datetime.strptime(node['occurredAt'], "%Y-%m-%dT%H:%M:%SZ")
                
                # Only count commits after both user creation and repo creation
                if (commit_date.date() >= user_creation_date and 
                    commit_date >= repo_created_at):
                    unique_commit_dates.add(commit_date.strftime("%Y-%m-%d"))
        
        # Prepare verification result
        result = {
            'valid': len(unique_commit_dates) >= threshold,
            'contribution_days': len(unique_commit_dates),
            'threshold': threshold,
            'years_back': years_back,
            'user_creation_date': user_creation_date,
            'dates': sorted(list(unique_commit_dates))
        }
        
        logger.info(f"Contribution verification for {username} completed in {time.time() - start_time:.2f} seconds")
        return result

    except Exception as e:
        logger.error(f"Error in contribution verification: {e}")
        return {
            'valid': False,
            'error': str(e)
        }

def main():
    """Main function to analyze GitHub contributions."""
    try:
        # Verify contributions with Gitcoin Passport-like criteria
        result = verify_github_contributions(USERNAME, threshold=120, years_back=3)
        
        if result.get('valid'):
            print(f"Verification Passed!")
            print(f"Total unique contribution days: {result['contribution_days']}")
            print(f"First contribution date: {result['dates'][0]}")
            print(f"Last contribution date: {result['dates'][-1]}")
        else:
            print(f"Verification Failed.")
            print(f"Total unique contribution days: {result.get('contribution_days', 0)}")
            print(f"Error: {result.get('error', 'Did not meet contribution threshold')}")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
