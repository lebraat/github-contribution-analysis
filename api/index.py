from flask import Flask, render_template, request, send_from_directory
from dotenv import load_dotenv
import os
import requests
from datetime import datetime
from collections import defaultdict

app = Flask(__name__, template_folder='../templates')
load_dotenv()

def get_commit_days(username):
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        return "GitHub token not found in environment variables", {}
    
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
    
    try:
        response = requests.post('https://api.github.com/graphql', 
                               json={'query': query, 'variables': {'username': username}}, 
                               headers=headers)
        
        if response.status_code != 200:
            return f"GitHub API Error: {response.status_code}", {}
            
        data = response.json()
        if 'errors' in data:
            return f"GitHub API Error: {data['errors'][0]['message']}", {}
            
        if not data.get('data', {}).get('user'):
            return f"User '{username}' not found", {}
            
        repos = data['data']['user']['repositories']['nodes']
        
        commit_dates = set()
        monthly_commits = defaultdict(int)
        
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
            '''
            
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
                    continue
                    
                result = commit_response.json()
                
                try:
                    commit_history = result['data']['repository']['defaultBranchRef']['target']['history']
                    for edge in commit_history['edges']:
                        commit = edge['node']
                        if commit['author']['user'] and commit['author']['user']['login'] == username:
                            date = commit['committedDate'].split('T')[0]
                            commit_dates.add(date)
                            month = date[:7]  # YYYY-MM format
                            monthly_commits[month] += 1
                    
                    page_info = commit_history['pageInfo']
                    has_next_page = page_info['hasNextPage']
                    cursor = page_info['endCursor']
                except (KeyError, TypeError):
                    has_next_page = False
        
        # Sort monthly commits by date
        sorted_monthly = dict(sorted(monthly_commits.items()))
        
        return None, (len(commit_dates), sorted_monthly)
    except Exception as e:
        return f"Error: {str(e)}", (0, {})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('../static', 'favicon.ico')

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    total_days = 0
    monthly_data = {}
    username = None
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if username:
            error, (total_days, monthly_data) = get_commit_days(username)
    
    return render_template('index.html', 
                         username=username,
                         total_days=total_days, 
                         monthly_data=monthly_data,
                         error=error)

# For local development
if __name__ == '__main__':
    app.run(debug=True)
