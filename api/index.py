from flask import Flask, render_template, request, send_from_directory
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__, template_folder='../templates')
load_dotenv()

def get_contributions_for_year(username, start_date, end_date, headers):
    if not username:
        raise ValueError("Username must be provided")

    query = '''
    query($username: String!, $from: DateTime!, $to: DateTime!) {
        user(login: $username) {
            contributionsCollection(from: $from, to: $to) {
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
    
    response = requests.post('https://api.github.com/graphql', 
                           json={
                               'query': query,
                               'variables': {
                                   'username': username,
                                   'from': start_date.strftime('%Y-%m-%dT00:00:00Z'),
                                   'to': end_date.strftime('%Y-%m-%dT23:59:59Z')
                               }
                           }, 
                           headers=headers,
                           timeout=5)
    
    if response.status_code != 200:
        raise Exception(f"GitHub API Error: {response.status_code}")
        
    data = response.json()
    if 'errors' in data:
        raise Exception(f"GitHub API Error: {data['errors'][0]['message']}")
        
    if not data.get('data', {}).get('user'):
        raise Exception(f"User '{username}' not found")
        
    return data['data']['user']['contributionsCollection']['contributionCalendar']

def get_commit_days(username):
    if not username:
        return "Username must be provided", None

    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        return "GitHub token not found in environment variables", None
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    try:
        # Calculate date ranges for the last 3 years
        end_date = datetime.now()
        total_days = 0
        monthly_commits = defaultdict(int)
        
        # Query each year separately
        for year in range(3):
            year_end = end_date - timedelta(days=365 * year)
            year_start = year_end - timedelta(days=365)
            
            contributions = get_contributions_for_year(username, year_start, year_end, headers)
            
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
        return str(e), None

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
        else:
            error = "Username must be provided"
    
    return render_template('index.html', 
                         username=username,
                         total_days=total_days, 
                         monthly_data=monthly_data,
                         error=error)

if __name__ == '__main__':
    app.run(debug=True)
