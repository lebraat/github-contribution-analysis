from flask import Flask, render_template
from dotenv import load_dotenv
import os
import requests
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
load_dotenv()

def get_commit_days():
    token = os.getenv('GITHUB_TOKEN')
    username = os.getenv('GITHUB_USERNAME', 'lebraat')
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    # GraphQL query to get user's repositories
    query = '''
    query($username: String!) {
        user(login: $username) {
            repositories(first: 100, orderBy: {field: UPDATED_AT, direction: DESC}) {
                nodes {
                    name
                    owner {
                        login
                    }
                }
            }
        }
    }
    '''
    
    response = requests.post('https://api.github.com/graphql', 
                           json={'query': query, 'variables': {'username': username}}, 
                           headers=headers)
    
    if response.status_code != 200:
        return f"Error: {response.status_code}", []
    
    repos = response.json()['data']['user']['repositories']['nodes']
    print(f"Found {len(repos)} repositories.")
    
    commit_dates = set()
    monthly_commits = defaultdict(set)
    commit_details = defaultdict(list)  # For debugging: store all commits per day
    
    for repo in repos:
        owner = repo['owner']['login']
        name = repo['name']
        
        # Query to get commit history
        commit_query = '''
        query($owner: String!, $name: String!, $cursor: String) {
            repository(owner: $owner, name: $name) {
                defaultBranchRef {
                    target {
                        ... on Commit {
                            history(first: 100, after: $cursor, since: "2022-01-07T00:00:00Z") {
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
                                        message
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        '''
        
        print(f"Fetching commits for {owner}/{name}...")
        has_next_page = True
        cursor = None
        
        while has_next_page:
            variables = {
                'owner': owner,
                'name': name,
                'cursor': cursor
            }
            
            commit_response = requests.post('https://api.github.com/graphql',
                                         json={'query': commit_query, 'variables': variables},
                                         headers=headers)
            
            if commit_response.status_code != 200:
                print(f"Error fetching commits for {owner}/{name}")
                break
                
            result = commit_response.json()
            
            try:
                commit_history = result['data']['repository']['defaultBranchRef']['target']['history']
                for edge in commit_history['edges']:
                    commit = edge['node']
                    if commit['author']['user'] and commit['author']['user']['login'] == username:
                        date = commit['committedDate'].split('T')[0]
                        message = commit['message']
                        commit_dates.add(date)
                        month = date[:7]  # YYYY-MM format
                        monthly_commits[month].add(date)
                        commit_details[date].append(f"{message[:50]}... in {owner}/{name}")
                
                page_info = commit_history['pageInfo']
                has_next_page = page_info['hasNextPage']
                cursor = page_info['endCursor']
            except (KeyError, TypeError) as e:
                print(f"Error processing commits for {owner}/{name}: {str(e)}")
                break
    
    # Debug output
    print("\nDetailed commit information:")
    for date, commits in sorted(commit_details.items()):
        print(f"\n{date} ({len(commits)} commits):")
        for commit in commits:
            print(f"  - {commit}")
    
    print("\nMonthly unique commit days:")
    for month, days in sorted(monthly_commits.items()):
        print(f"{month}: {len(days)} days, dates: {sorted(days)}")
    
    # Sort monthly commits by date and convert sets to counts
    sorted_monthly = {month: len(days) for month, days in sorted(monthly_commits.items())}
    
    return len(commit_dates), sorted_monthly

@app.route('/')
def index():
    total_days, monthly_data = get_commit_days()
    return render_template('index.html', total_days=total_days, monthly_data=monthly_data)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
