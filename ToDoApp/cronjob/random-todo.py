#!/usr/bin/env python3
"""
CronJob script that creates a todo with a random Wikipedia article URL
"""
import os
import sys
import requests
from urllib.parse import urlparse, urljoin

def get_random_wikipedia_url():
    """Get a random Wikipedia article URL by following redirect"""
    try:
        # Wikipedia's Special:Random uses a meta refresh redirect
        # We need to follow redirects and get the final URL
        session = requests.Session()
        
        # First request - get the redirect
        response = session.get(
            "https://en.wikipedia.org/wiki/Special:Random",
            allow_redirects=True,
            timeout=10
        )
        
        final_url = response.url
        
        # If we still got Special:Random, the redirect might be in the page content
        # or we need to check the history
        if "Special:Random" in final_url or final_url.endswith("/Special:Random"):
            # Check response history for redirects
            if hasattr(response, 'history') and response.history:
                # Get the last redirect URL
                final_url = response.history[-1].headers.get('Location', final_url)
                if final_url.startswith('/'):
                    final_url = "https://en.wikipedia.org" + final_url
            else:
                # Try making another request - sometimes it takes a moment
                response = session.get(
                    "https://en.wikipedia.org/wiki/Special:Random",
                    allow_redirects=True,
                    timeout=10
                )
                final_url = response.url
        
        # Final check - if still Special:Random, try one more time with fresh session
        if "Special:Random" in final_url:
            session = requests.Session()
            response = session.get(
                "https://en.wikipedia.org/wiki/Special:Random",
                allow_redirects=True,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            final_url = response.url
        
        return final_url
    except Exception as e:
        print(f"Error fetching random Wikipedia URL: {e}", file=sys.stderr, flush=True)
        return None

def create_todo(content, backend_url):
    """Create a todo via the backend API"""
    try:
        response = requests.post(
            f"{backend_url}/todos",
            json={"content": content},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        print(f"Successfully created todo: {result.get('todo', content)}", flush=True)
        return True
    except Exception as e:
        print(f"Error creating todo: {e}", file=sys.stderr, flush=True)
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr, flush=True)
        return False

def main():
    # Get backend URL from environment variable
    backend_url = os.getenv("BACKEND_URL", "http://todo-backend-service.project:80")
    
    print("Fetching random Wikipedia article...", flush=True)
    wiki_url = get_random_wikipedia_url()
    
    if not wiki_url:
        print("Failed to get random Wikipedia URL", file=sys.stderr, flush=True)
        sys.exit(1)
    
    print(f"Random Wikipedia article: {wiki_url}", flush=True)
    
    # Create todo content
    todo_content = f"Read {wiki_url}"
    
    print(f"Creating todo: {todo_content}", flush=True)
    success = create_todo(todo_content, backend_url)
    
    if success:
        print("CronJob completed successfully", flush=True)
        sys.exit(0)
    else:
        print("CronJob failed to create todo", file=sys.stderr, flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
