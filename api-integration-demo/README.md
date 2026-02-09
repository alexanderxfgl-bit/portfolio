# API Integration Demo

A comprehensive demonstration of REST API integration with authentication, featuring best practices for API consumption, error handling, and data processing.

## Features

- 🔐 Multiple authentication methods (API Key, OAuth2, JWT)
- 📡 Rate limiting and retry logic
- 📊 Pagination handling for large datasets
- 🔄 Caching with TTL support
- 📈 Response logging and monitoring
- 🧪 Comprehensive test suite

## Setup Instructions

### Prerequisites

- Python 3.8+
- API credentials from your target service

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/api-integration-demo.git
cd api-integration-demo
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure credentials:
```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your API keys
```

## Supported APIs

This demo includes integrations for:
- **GitHub API** - Repository data, user profiles
- **OpenWeather API** - Weather data
- **JSONPlaceholder** - Mock REST API for testing

## Usage

### Basic API Call

```python
from api_client import APIClient

client = APIClient('github')
repos = client.get('/users/octocat/repos')
print(repos)
```

### With Authentication

```python
from auth import OAuth2Handler

auth = OAuth2Handler(
    client_id='your_client_id',
    client_secret='your_secret',
    token_url='https://api.example.com/oauth/token'
)

client = APIClient('example_api', auth=auth)
data = client.get('/protected/resource')
```

### Running the Demo

```bash
# Run all examples
python demo.py

# Run specific integration
python demo.py --service github
python demo.py --service weather
```

## Project Structure

```
api-integration-demo/
├── api_client.py         # Main API client class
├── auth.py              # Authentication handlers
├── cache.py             # Response caching
├── rate_limiter.py      # Rate limiting decorator
├── retry.py             # Retry logic with backoff
├── config.yaml          # API configurations
├── demo.py              # Demo script
├── tests/
│   ├── test_api_client.py
│   ├── test_auth.py
│   └── test_rate_limiter.py
├── requirements.txt
└── README.md
```

## Sample Output

### GitHub API Demo

```
🚀 API Integration Demo - GitHub
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Authentication: Successful (Rate limit: 5000/hour)

📊 User Profile: octocat
   ├─ Name: The Octocat
   ├─ Bio: Hi, I'm the Octocat!
   ├─ Public Repos: 8
   ├─ Followers: 15000
   └─ Following: 9

📁 Recent Repositories:
   1. Hello-World
      ├─ Stars: 2500 ⭐
      ├─ Language: -
      └─ Updated: 2024-01-10

   2. Spoon-Knife
      ├─ Stars: 12000 ⭐
      ├─ Language: HTML
      └─ Updated: 2024-01-08

⏱️  Response Time: 245ms
📊 Rate Limit Remaining: 4998/5000
```

### Weather API Demo

```
🌤️  Weather API Demo - Current Conditions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 Location: San Francisco, CA
🌡️  Temperature: 18.5°C (65.3°F)
💧 Humidity: 72%
💨 Wind Speed: 12.5 km/h
☁️  Conditions: Partly Cloudy

📈 5-Day Forecast:
   Mon: 🌤️  18°C / 12°C - Partly Cloudy
   Tue: 🌧️  16°C / 11°C - Light Rain
   Wed: ☀️  20°C / 13°C - Sunny
   Thu: 🌤️  19°C / 12°C - Partly Cloudy
   Fri: ☁️  17°C / 11°C - Cloudy
```

### Pagination Example

```
📄 Paginated Results (Page 2/15)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Items on this page: 30
Total items: 432

Navigation:
   ⬅️  Previous: Available
   ➡️  Next: Available
   📄 Current: 2/15

Data:
   31. Project Alpha - Updated 2h ago
   32. Project Beta - Updated 5h ago
   ...
   60. Project Omega - Updated 1d ago
```

## Authentication Examples

### API Key Authentication

```yaml
apis:
  weather:
    base_url: https://api.openweathermap.org/data/2.5
    auth_type: api_key
    api_key: ${WEATHER_API_KEY}
    key_param: appid
```

### OAuth2 Authentication

```python
from auth import OAuth2Handler

oauth = OAuth2Handler(
    client_id='your_client_id',
    client_secret='your_client_secret',
    authorization_url='https://github.com/login/oauth/authorize',
    token_url='https://github.com/login/oauth/access_token'
)

token = oauth.get_token()
```

### JWT Authentication

```python
from auth import JWTHandler

jwt = JWTHandler(secret_key='your_secret')
token = jwt.generate_token({'user_id': 123, 'role': 'admin'})

client = APIClient('my_api')
client.set_header('Authorization', f'Bearer {token}')
```

## Error Handling

The client handles various HTTP errors gracefully:

```
⚠️  HTTP 429: Rate limit exceeded
   Retry after: 3600 seconds
   Next attempt: 2024-01-15 11:30:00

❌ HTTP 404: Resource not found
   URL: /api/v1/users/nonexistent

⚠️  Network Error: Connection timeout
   Retrying (attempt 2/3) in 2 seconds...
```

## Rate Limiting

Built-in rate limiting with configurable limits:

```python
from rate_limiter import rate_limit

@rate_limit(calls=100, period=60)  # 100 calls per minute
def fetch_data():
    return api.get('/data')
```

## Caching

Automatic response caching with TTL:

```python
from cache import Cache

cache = Cache(ttl=300)  # 5 minute cache

# First call hits the API
data = cache.get('weather', fetch_weather)

# Subsequent calls use cached data
data = cache.get('weather')  # Returns cached result
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api_client tests/

# Run specific test
pytest tests/test_auth.py -v
```

## Best Practices Demonstrated

1. **Session Management** - Persistent connections for efficiency
2. **Timeout Handling** - Configurable timeouts with retries
3. **Security** - API keys in environment variables, not code
4. **Logging** - Structured logging for debugging
5. **Error Recovery** - Exponential backoff for transient errors

## License

MIT License
