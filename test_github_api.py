#!/usr/bin/env python3
import requests
import os
import sys

github_pat = os.getenv("GITHUB_PAT")
if not github_pat:
    print("ERROR: GITHUB_PAT environment variable not set")
    sys.exit(1)

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {github_pat}",
    "X-GitHub-Api-Version": "2022-11-28",
}

try:
    print("Testing GitHub API connection...")
    r = requests.get("https://api.github.com/orgs/ms-mfg-community", headers=headers, timeout=10)
    print(f"Status Code: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"Organization: {data.get('login')}")
        print(f"Public Repos: {data.get('public_repos')}")
        print("✓ GitHub API authentication successful")
    else:
        print(f"Error: {r.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")
    sys.exit(1)
