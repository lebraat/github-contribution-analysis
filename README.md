# GitHub Contribution Analyzer

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

## Future Improvements
- Add more detailed contribution statistics
- Implement caching
- Enhance error handling
