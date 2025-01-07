# GitHub Contribution Analyzer

## 🚀 Quick Start for Everyone

### What is this?
This is a simple web tool that helps you understand your GitHub contribution activity over the last 3 years. Whether you're a student, professional, or just curious about your coding journey, this app provides insights into your GitHub contributions.

### How to Use the App
1. Visit: [https://github-contribution-analysis.vercel.app/](https://github-contribution-analysis.vercel.app/)
2. Enter your GitHub username in the input box
3. Click "Analyze"

### Understanding Your Results

#### Total Days with Commits
- This number shows how many unique days you've made contributions in the last 3 years
- Each day you made at least one commit counts, regardless of the number of commits

#### Monthly Commit Chart
- The bar graph shows your commit activity by month
- Taller bars mean more commits in that month
- Helps you visualize your coding consistency and productivity patterns

### 🤔 What Counts as a Contribution?
- Commits to repositories you own or contribute to
- Pull requests
- Issues you've opened or commented on
- Repository reviews

### Tips for Interpreting Your Data
- A high number of commit days shows consistent coding activity
- Gaps in the chart might indicate:
  - Vacation periods
  - Busy times in your personal or professional life
  - Shifts in project focus

### Privacy and Security
- We only read public information from your GitHub profile
- No personal data is stored or shared

## Overview
A web application that provides insights into a GitHub user's contributions over the last 3 years, visualizing commit activity and total contribution days.

## Features
- Input any GitHub username
- Analyze contributions from the last 3 years
- Visualize monthly commit distribution
- Responsive and user-friendly interface

## Technologies
- Python
- Flask
- GitHub GraphQL API
- Chart.js
- Vercel Deployment

## Prerequisites
- Python 3.9+
- GitHub Personal Access Token

## Setup and Installation

### Local Development
1. Clone the repository
```bash
git clone https://github.com/lebraat/github-contribution-analysis.git
cd github-contribution-analysis
```

2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
Create a `.env` file in the project root:
```
GITHUB_TOKEN=your_github_personal_access_token
```

5. Run the application
```bash
python api/index.py
```

### Vercel Deployment
1. Fork the repository
2. Connect to Vercel
3. Add environment variable `GITHUB_TOKEN`

## Environment Variables
- `GITHUB_TOKEN`: GitHub Personal Access Token with `read:user` scope

## API Limitations
- Queries contributions for the last 3 years
- Uses GitHub GraphQL API with rate limiting considerations

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
MIT License

## Troubleshooting
- Ensure GitHub token has correct permissions
- Check network connectivity
- Verify GitHub username exists

## 🛠️ Local Development Setup

### Prerequisites
- Python 3.7+
- GitHub Personal Access Token with repo scope

### Setup Steps
1. Clone the repository
2. Create a `.env` file in the root directory with:
   ```
   GITHUB_TOKEN=your_github_token
   GITHUB_USERNAME=your_github_username
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python app.py
   ```
5. Visit `http://localhost:5000` in your browser

## Recent Updates
- Fixed JavaScript/Jinja2 template integration for proper JSON parsing
- Improved chart rendering with proper data handling
- Enhanced error handling for GitHub API responses
- Added monthly contribution visualization with Chart.js

## Future Improvements
- Add more detailed contribution statistics
- Implement caching
- Enhance error handling
