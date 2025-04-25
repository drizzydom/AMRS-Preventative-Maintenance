import os
import sys
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add parent directory to path to import application modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api_client import ApiClient

class TestApiClient(unittest.TestCase):
    """Test cases for the ApiClient class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create a temporary directory for test configuration
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'config.json')
        
        # Create a test config file
        with open(self.config_file, 'w') as f:
            json.dump({"server_url": "http://test-server.com"}, f)
        
        # Initialize ApiClient with test configuration
        self.api_client = ApiClient(base_url="http://test-server.com", config_file=self.config_file)
    
    def tearDown(self):
        """Clean up after each test"""
        # Remove the temporary directory and its contents
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('requests.post')
    def test_login(self, mock_post):
        """Test successful login"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "token": "test-token",
            "refresh_token": "test-refresh-token",
            "expiry": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        mock_post.return_value = mock_response
        
        # Call login method
        result = self.api_client.login("testuser", "testpass", remember=True)
        
        # Verify results
        self.assertTrue(result)
        self.assertEqual(self.api_client.token, "test-token")
        self.assertEqual(self.api_client.refresh_token, "test-refresh-token")
        self.assertEqual(self.api_client.username, "testuser")
    
    @patch('requests.post')
    def test_login_failure(self, mock_post):
        """Test failed login"""
        # Mock failed API response
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid credentials"}
        mock_post.return_value = mock_response
        
        # Call login method
        result = self.api_client.login("testuser", "wrongpass")
        
        # Verify results
        self.assertFalse(result)
        self.assertIsNone(self.api_client.token)
    
    @patch('requests.post')
    def test_refresh_token(self, mock_post):
        """Test token refresh"""
        # Set up initial tokens
        self.api_client.token = "old-token"
        self.api_client.refresh_token = "test-refresh-token"
        self.api_client.token_expiry = datetime.now() - timedelta(minutes=5)  # Expired token
        
        # Mock successful refresh response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "token": "new-token",
            "refresh_token": "new-refresh-token",
            "expiry": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        mock_post.return_value = mock_response
        
        # Call refresh method
        result = self.api_client._refresh_auth_token()
        
        # Verify results
        self.assertTrue(result)
        self.assertEqual(self.api_client.token, "new-token")
        self.assertEqual(self.api_client.refresh_token, "new-refresh-token")
    
    @patch('keyring.set_password')
    def test_save_auth_tokens(self, mock_set_password):
        """Test saving authentication tokens"""
        # Set up tokens
        self.api_client.token = "test-token"
        self.api_client.refresh_token = "test-refresh-token"
        self.api_client.token_expiry = datetime.now() + timedelta(hours=1)
        self.api_client.username = "testuser"
        
        # Call save method
        self.api_client._save_auth_tokens()
        
        # Verify keyring was called with correct arguments
        mock_set_password.assert_called_once()
        service_name, username, token_data = mock_set_password.call_args[0]
        
        # Parse the JSON data that was saved
        saved_data = json.loads(token_data)
        
        self.assertEqual(saved_data["token"], "test-token")
        self.assertEqual(saved_data["refresh_token"], "test-refresh-token")
        self.assertEqual(saved_data["username"], "testuser")
    
    @patch('keyring.get_password')
    def test_load_auth_tokens(self, mock_get_password):
        """Test loading authentication tokens"""
        # Mock stored token data
        expiry_time = datetime.now() + timedelta(hours=1)
        mock_get_password.return_value = json.dumps({
            "token": "stored-token",
            "refresh_token": "stored-refresh-token",
            "expiry": expiry_time.isoformat(),
            "username": "storeduser"
        })
        
        # Call load method
        self.api_client._load_auth_tokens()
        
        # Verify tokens were loaded correctly
        self.assertEqual(self.api_client.token, "stored-token")
        self.assertEqual(self.api_client.refresh_token, "stored-refresh-token")
        self.assertEqual(self.api_client.username, "storeduser")
        self.assertEqual(self.api_client.token_expiry.isoformat(), expiry_time.isoformat())
    
    @patch('keyring.delete_password')
    def test_logout(self, mock_delete_password):
        """Test logout functionality"""
        # Set up initial state
        self.api_client.token = "test-token"
        self.api_client.refresh_token = "test-refresh-token"
        self.api_client.username = "testuser"
        
        # Mock the server logout call
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.ok = True
            mock_post.return_value = mock_response
            
            # Call logout method
            result = self.api_client.logout()
            
            # Verify results
            self.assertTrue(result)
            self.assertIsNone(self.api_client.token)
            self.assertIsNone(self.api_client.refresh_token)
            self.assertIsNone(self.api_client.username)
            
            # Verify keyring deletion was called
            mock_delete_password.assert_called_once()
    
    @patch('requests.get')
    def test_check_server(self, mock_get):
        """Test server availability check"""
        # Mock successful connection
        mock_response = MagicMock()
        mock_response.ok = True
        mock_get.return_value = mock_response
        
        # Check server
        result = self.api_client.check_server()
        
        # Verify result
        self.assertTrue(result)
        mock_get.assert_called_once()
        
        # Test connection failure
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        result = self.api_client.check_server()
        self.assertFalse(result)
    
    @patch('requests.request')
    def test_execute_request(self, mock_request):
        """Test request execution with authentication"""
        # Set up initial state
        self.api_client.token = "test-token"
        self.api_client.token_expiry = datetime.now() + timedelta(hours=1)
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = True
        mock_response.json.return_value = {"result": "success"}
        mock_request.return_value = mock_response
        
        # Execute request
        result = self.api_client.execute_request("GET", "/api/test", {"param": "value"})
        
        # Verify request was made with correct arguments
        mock_request.assert_called_with(
            "GET", 
            "http://test-server.com/api/test", 
            json={"param": "value"},
            headers={'Authorization': 'Bearer test-token'},
            timeout=15
        )
        
        # Verify result
        self.assertEqual(result, {"result": "success"})
    
    @patch('requests.request')
    def test_execute_request_with_expired_token(self, mock_request):
        """Test request execution with token refresh"""
        # Set up initial state with expired token
        self.api_client.token = "expired-token"
        self.api_client.refresh_token = "test-refresh-token"
        self.api_client.token_expiry = datetime.now() - timedelta(minutes=5)
        
        # First request fails with 401, second succeeds after token refresh
        mock_responses = [
            MagicMock(ok=False, status_code=401),
            MagicMock(ok=True, content=True, json=MagicMock(return_value={"result": "success"}))
        ]
        mock_request.side_effect = mock_responses
        
        # Mock token refresh
        with patch.object(self.api_client, '_refresh_auth_token') as mock_refresh:
            mock_refresh.return_value = True
            self.api_client.token = "new-token"  # Simulate token update
            
            # Execute request
            result = self.api_client.execute_request("GET", "/api/test")
            
            # Verify token refresh was called
            mock_refresh.assert_called_once()
            
            # Verify result
            self.assertEqual(result, {"result": "success"})
