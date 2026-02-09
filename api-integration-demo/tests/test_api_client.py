import pytest
import responses
from unittest.mock import Mock, patch

from api_client import APIClient, APIConfig, GitHubAPI, JSONPlaceholderAPI


class TestAPIClient:
    """Tests for the APIClient class."""
    
    @responses.activate
    def test_get_request_success(self):
        """Test successful GET request."""
        responses.add(
            responses.GET,
            'https://api.example.com/test',
            json={'status': 'ok'},
            status=200
        )
        
        config = APIConfig(
            name='test',
            base_url='https://api.example.com',
            auth_type='none'
        )
        client = APIClient(config)
        
        result = client.get('/test')
        assert result == {'status': 'ok'}
    
    @responses.activate
    def test_post_request(self):
        """Test POST request with JSON data."""
        responses.add(
            responses.POST,
            'https://api.example.com/posts',
            json={'id': 1, 'title': 'Test'},
            status=201
        )
        
        config = APIConfig(
            name='test',
            base_url='https://api.example.com',
            auth_type='none'
        )
        client = APIClient(config)
        
        result = client.post('/posts', json_data={'title': 'Test'})
        assert result['id'] == 1
    
    @responses.activate
    def test_rate_limit_handling(self):
        """Test handling of rate limit response."""
        responses.add(
            responses.GET,
            'https://api.example.com/test',
            status=429,
            headers={'Retry-After': '60'}
        )
        
        config = APIConfig(
            name='test',
            base_url='https://api.example.com',
            auth_type='none'
        )
        client = APIClient(config)
        
        with pytest.raises(Exception):
            client.get('/test')


class TestGitHubAPI:
    """Tests for GitHub API integration."""
    
    @responses.activate
    def test_get_user(self):
        """Test fetching user profile."""
        responses.add(
            responses.GET,
            'https://api.github.com/users/testuser',
            json={
                'login': 'testuser',
                'name': 'Test User',
                'public_repos': 10,
                'followers': 100
            },
            status=200
        )
        
        github = GitHubAPI(token='fake_token')
        user = github.get_user('testuser')
        
        assert user['login'] == 'testuser'
        assert user['public_repos'] == 10


class TestJSONPlaceholderAPI:
    """Tests for JSONPlaceholder API."""
    
    @responses.activate
    def test_get_posts(self):
        """Test fetching posts."""
        responses.add(
            responses.GET,
            'https://jsonplaceholder.typicode.com/posts',
            json=[
                {'id': 1, 'title': 'Post 1'},
                {'id': 2, 'title': 'Post 2'}
            ],
            status=200
        )
        
        api = JSONPlaceholderAPI()
        posts = api.get_posts()
        
        assert len(posts) == 2
        assert posts[0]['title'] == 'Post 1'
    
    @responses.activate  
    def test_create_post(self):
        """Test creating a post."""
        responses.add(
            responses.POST,
            'https://jsonplaceholder.typicode.com/posts',
            json={'id': 101, 'title': 'New Post'},
            status=201
        )
        
        api = JSONPlaceholderAPI()
        result = api.create_post('New Post', 'Body text', 1)
        
        assert result['id'] == 101
