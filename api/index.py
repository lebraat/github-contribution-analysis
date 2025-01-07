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
        return "GitHub token not found in environment variables", None
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    # GraphQL query to get user's repositories
    query = '''
    query($username: String!) {
        user(login: $username) {
            contributionsCollection {
                contributionCalendar {
                    totalContributions
                    weeks {
                        contributionDays {
                            contributionCount
                            date
                        }
                    }
                }
            }
        }
    }
    '''
    
    try:
        response = requests.post('https://api.github.com/graphql', 
                               json={'query': query, 'variables': {'username': username}}, 
                               headers=headers,
                               timeout=5)
        
        if response.status_code != 200:
            return f"GitHub API Error: {response.status_code}", None
            
        data = response.json()
        if 'errors' in data:
            return f"GitHub API Error: {data['errors'][0]['message']}", None
            
        if not data.get('data', {}).get('user'):
            return f"User '{username}' not found", None
            
        contributions = data['data']['user']['contributionsCollection']['contributionCalendar']
        total_days = 0
        monthly_commits = defaultdict(int)
        
        for week in contributions['weeks']:
            for day in week['contributionDays']:
                if day['contributionCount'] > 0:
                    total_days += 1
                    date = datetime.strptime(day['date'], '%Y-%m-%d')
                    month = date.strftime('%Y-%m')
                    monthly_commits[month] += day['contributionCount']
        
        # Sort monthly commits by date
        sorted_monthly = dict(sorted(monthly_commits.items()))
        
        return None, (total_days, sorted_monthly)
    except requests.Timeout:
        return "GitHub API request timed out. Please try again.", None
    except Exception as e:
        return f"Error: {str(e)}", None

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
            error, result = get_commit_days(username)
            if result:
                total_days, monthly_data = result
    
    return render_template('index.html', 
                         username=username,
                         total_days=total_days, 
                         monthly_data=monthly_data,
                         error=error)

if __name__ == '__main__':
    app.run(debug=True)
