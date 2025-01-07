# GitHub Contribution Analysis

This Python script analyzes your GitHub contributions across repositories using the GitHub GraphQL API. It calculates the total number of unique days you've made commits.

## Features
- Fetches all repositories you've contributed to
- Retrieves commit history for each repository
- Filters commits by your GitHub username
- Counts unique contribution days

## Setup
1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your GitHub token and username to `.env`
```bash
cp .env.example .env
# Edit .env with your GitHub token and username
```

## Usage
Run the script:
```bash
python pp-github-trouble.py
