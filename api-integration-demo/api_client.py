#!/usr/bin/env python3
"""
API Integration Demo
Demonstrates REST API consumption with authentication, rate limiting, and error handling.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """Configuration for an API endpoint."""
    name: str
    base_url: str
    auth_type: str  # 'none', 'api_key', 'oauth2', 'bearer'
    api_key: Optional[str] = None
    api_key_header: Optional[str] = None
    bearer_token: Optional[str] = None
    timeout: int = 30
    rate_limit_per_minute: int = 60


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""
    
    def __init__(self, max_calls: int, period: int = 60):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        # Remove calls outside the period
        self.calls = [c for c in self.calls if now - c < self.period]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, waiting {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self.calls.append(time.time())


class APIClient:
    """
    A robust API client with authentication, rate limiting, and retry logic.
    """
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.session = requests.Session()
        self.rate_limiter = RateLimiter(config.rate_limit_per_minute)
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Setup authentication
        self._setup_auth()
    
    def _setup_auth(self):
        """Configure authentication headers."""
        if self.config.auth_type == 'api_key':
            if self.config.api_key_header:
                self.session.headers[self.config.api_key_header] = self.config.api_key
            else:
                self.session.params = {'api_key': self.config.api_key}
        
        elif self.config.auth_type == 'bearer':
            self.session.headers['Authorization'] = f'Bearer {self.config.bearer_token}'
        
        # Default headers
        self.session.headers.update({
            'User-Agent': 'API-Integration-Demo/1.0',
            'Accept': 'application/json',
        })
    
    def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request with rate limiting and error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to base_url)
            **kwargs: Additional arguments for requests
            
        Returns:
            Response data as dictionary
        """
        self.rate_limiter.wait_if_needed()
        
        url = urljoin(self.config.base_url, endpoint)
        
        try:
            start_time = time.time()
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.config.timeout,
                **kwargs
            )
            response_time = (time.time() - start_time) * 1000
            
            response.raise_for_status()
            
            logger.info(f"{method} {url} - {response.status_code} ({response_time:.0f}ms)")
            
            # Parse response
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Retry after {retry_after}s")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a GET request."""
        return self.request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a POST request."""
        kwargs = {}
        if json_data:
            kwargs['json'] = json_data
        elif data:
            kwargs['data'] = data
        return self.request('POST', endpoint, **kwargs)
    
    def get_paginated(self, endpoint: str, params: Optional[Dict] = None, 
                      page_param: str = 'page', limit_param: str = 'per_page',
                      limit: int = 100) -> list:
        """
        Fetch all paginated results.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            page_param: Name of page parameter
            limit_param: Name of items per page parameter
            limit: Maximum items per page
            
        Returns:
            List of all results
        """
        all_results = []
        page = 1
        params = params or {}
        params[limit_param] = limit
        
        while True:
            params[page_param] = page
            response = self.get(endpoint, params=params)
            
            # Handle different response structures
            if isinstance(response, list):
                results = response
            elif 'data' in response:
                results = response['data']
            elif 'results' in response:
                results = response['results']
            else:
                results = [response]
            
            if not results:
                break
            
            all_results.extend(results)
            
            # Check if there are more pages
            if len(results) < limit:
                break
            
            page += 1
            logger.debug(f"Fetching page {page}...")
        
        logger.info(f"Fetched {len(all_results)} total items from {page} page(s)")
        return all_results


class GitHubAPI:
    """GitHub API integration example."""
    
    def __init__(self, token: Optional[str] = None):
        token = token or os.getenv('GITHUB_TOKEN')
        config = APIConfig(
            name='github',
            base_url='https://api.github.com',
            auth_type='bearer' if token else 'none',
            bearer_token=token,
            rate_limit_per_minute=60 if token else 10
        )
        self.client = APIClient(config)
    
    def get_user(self, username: str) -> Dict[str, Any]:
        """Get user profile information."""
        return self.client.get(f'/users/{username}')
    
    def get_repos(self, username: str) -> list:
        """Get all public repositories for a user."""
        return self.client.get_paginated(
            f'/users/{username}/repos',
            params={'sort': 'updated', 'direction': 'desc'}
        )
    
    def get_rate_limit(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        return self.client.get('/rate_limit')


class WeatherAPI:
    """OpenWeatherMap API integration example."""
    
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            raise ValueError("OpenWeather API key required")
        
        config = APIConfig(
            name='openweather',
            base_url='https://api.openweathermap.org/data/2.5',
            auth_type='api_key',
            api_key=api_key,
            api_key_header=None,  # Uses query param
            rate_limit_per_minute=60
        )
        self.client = APIClient(config)
    
    def get_current_weather(self, city: str, units: str = 'metric') -> Dict[str, Any]:
        """Get current weather for a city."""
        params = {
            'q': city,
            'units': units,
            'appid': self.client.config.api_key
        }
        return self.client.get('/weather', params=params)
    
    def get_forecast(self, city: str, units: str = 'metric') -> Dict[str, Any]:
        """Get 5-day forecast for a city."""
        params = {
            'q': city,
            'units': units,
            'appid': self.client.config.api_key
        }
        return self.client.get('/forecast', params=params)


class JSONPlaceholderAPI:
    """JSONPlaceholder API for testing (no auth required)."""
    
    def __init__(self):
        config = APIConfig(
            name='jsonplaceholder',
            base_url='https://jsonplaceholder.typicode.com',
            auth_type='none',
            rate_limit_per_minute=100
        )
        self.client = APIClient(config)
    
    def get_posts(self) -> list:
        """Get all posts."""
        return self.client.get('/posts')
    
    def get_post(self, post_id: int) -> Dict[str, Any]:
        """Get a specific post."""
        return self.client.get(f'/posts/{post_id}')
    
    def create_post(self, title: str, body: str, user_id: int) -> Dict[str, Any]:
        """Create a new post."""
        return self.client.post('/posts', json_data={
            'title': title,
            'body': body,
            'userId': user_id
        })


def print_github_demo():
    """Demonstrate GitHub API integration."""
    print("\n" + "="*60)
    print("🚀 API Integration Demo - GitHub")
    print("="*60)
    
    try:
        github = GitHubAPI()
        
        # Check rate limit
        rate_limit = github.get_rate_limit()
        remaining = rate_limit['rate']['remaining']
        limit = rate_limit['rate']['limit']
        print(f"\n✅ Authentication: Successful (Rate limit: {remaining}/{limit}/hour)")
        
        # Get user profile
        user = github.get_user('octocat')
        print(f"\n📊 User Profile: {user['login']}")
        print(f"   ├─ Name: {user.get('name', 'N/A')}")
        print(f"   ├─ Bio: {user.get('bio', 'N/A')}")
        print(f"   ├─ Public Repos: {user['public_repos']}")
        print(f"   ├─ Followers: {user['followers']}")
        print(f"   └─ Following: {user['following']}")
        
        # Get repositories
        repos = github.get_repos('octocat')[:5]
        print(f"\n📁 Recent Repositories:")
        for i, repo in enumerate(repos, 1):
            lang = repo.get('language') or '-'
            updated = repo['updated_at'][:10]
            print(f"   {i}. {repo['name']}")
            print(f"      ├─ Stars: {repo['stargazers_count']} ⭐")
            print(f"      ├─ Language: {lang}")
            print(f"      └─ Updated: {updated}")
        
        print(f"\n⏱️  Rate Limit Remaining: {remaining}/{limit}")
        
    except Exception as e:
        print(f"\n⚠️  GitHub API Error: {e}")
        print("   (Set GITHUB_TOKEN environment variable for higher rate limits)")


def print_weather_demo():
    """Demonstrate Weather API integration."""
    print("\n" + "="*60)
    print("🌤️  Weather API Demo")
    print("="*60)
    
    try:
        weather = WeatherAPI()
        
        # Get weather for San Francisco
        data = weather.get_current_weather('San Francisco,US')
        
        print(f"\n📍 Location: {data['name']}, {data['sys']['country']}")
        print(f"🌡️  Temperature: {data['main']['temp']:.1f}°C")
        print(f"💧 Humidity: {data['main']['humidity']}%")
        print(f"💨 Wind Speed: {data['wind']['speed']} m/s")
        print(f"☁️  Conditions: {data['weather'][0]['description'].title()}")
        
        # Get forecast
        forecast = weather.get_forecast('San Francisco,US')
        print(f"\n📈 5-Day Forecast:")
        
        # Group by day
        from collections import defaultdict
        daily = defaultdict(list)
        for item in forecast['list'][:15]:  # First 15 entries (3 days)
            date = item['dt_txt'][:10]
            daily[date].append(item)
        
        icons = {'Clear': '☀️', 'Clouds': '☁️', 'Rain': '🌧️', 'Snow': '❄️'}
        for date, items in list(daily.items())[:5]:
            temps = [i['main']['temp'] for i in items]
            condition = items[0]['weather'][0]['main']
            icon = icons.get(condition, '🌤️')
            print(f"   {date}: {icon} {min(temps):.0f}°C / {max(temps):.0f}°C - {condition}")
        
    except ValueError as e:
        print(f"\n⚠️  {e}")
        print("   (Set OPENWEATHER_API_KEY environment variable to use this demo)")
    except Exception as e:
        print(f"\n⚠️  Weather API Error: {e}")


def print_jsonplaceholder_demo():
    """Demonstrate JSONPlaceholder API."""
    print("\n" + "="*60)
    print("🧪 JSONPlaceholder API Demo (Mock Data)")
    print("="*60)
    
    api = JSONPlaceholderAPI()
    
    # Get posts
    posts = api.get_posts()[:3]
    print(f"\n📝 Sample Posts:")
    for post in posts:
        print(f"   • {post['title'][:50]}...")
    
    # Create a post
    print(f"\n✏️  Creating new post...")
    new_post = api.create_post(
        title='API Integration Demo',
        body='This post was created via API!',
        user_id=1
    )
    print(f"   ✓ Created post ID: {new_post['id']}")
    print(f"   ✓ Title: {new_post['title']}")


def main():
    """Run all API demos."""
    print_github_demo()
    print_weather_demo()
    print_jsonplaceholder_demo()
    
    print("\n" + "="*60)
    print("✅ All demos completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
