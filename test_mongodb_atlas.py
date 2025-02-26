import pytest
import os
from unittest.mock import patch, MagicMock
from mongodb_atlas import validate_project_name, get_organizations, create_project, create_free_cluster, create_paid_cluster

# Test project name validation
def test_validate_project_name():
    # Test valid project name
    valid, message = validate_project_name("TestProject123")
    assert valid is True
    
    # Test project name too long
    valid, message = validate_project_name("ThisProjectNameIsTooLongForValidation")
    assert valid is False
    assert "exceed 20 characters" in message
    
    # Test empty project name
    valid, message = validate_project_name("")
    assert valid is False
    assert "cannot be empty" in message
    
    # Test project name with invalid characters
    valid, message = validate_project_name("Test-Project_123")
    assert valid is False
    assert "only English characters and numbers" in message

# Mock the requests module for get_organizations
@patch('mongodb_atlas.requests.get')
def test_get_organizations_success(mock_get):
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": [
        {"id": "org1", "name": "Organization 1"},
        {"id": "org2", "name": "Organization 2"}
    ]}
    mock_get.return_value = mock_response
    
    # Set environment variables for the test
    with patch.dict(os.environ, {"ATLAS_PUBLIC_KEY": "test-key", "ATLAS_PRIVATE_KEY": "test-secret"}):
        # Call the function
        success, result = get_organizations()
        
        # Verify the result
        assert success is True
        assert len(result) == 2
        assert result[0]["id"] == "org1"
        
        # Verify the API was called correctly
        mock_get.assert_called_once()

@patch('mongodb_atlas.requests.get')
def test_get_organizations_failure(mock_get):
    # Mock failed response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Invalid request"
    mock_get.return_value = mock_response
    
    # Set environment variables for the test
    with patch.dict(os.environ, {"ATLAS_PUBLIC_KEY": "test-key", "ATLAS_PRIVATE_KEY": "test-secret"}):
        # Call the function
        success, result = get_organizations()
        
        # Verify the result
        assert success is False
        assert "Failed to fetch organizations" in result

# Mock the requests module for create_project tests
@patch('mongodb_atlas.requests.post')
@patch('mongodb_atlas.get_organizations')
def test_create_project_with_org_id(mock_get_orgs, mock_post):
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": "test-project-id"}
    mock_post.return_value = mock_response
    
    # Set environment variables for the test
    with patch.dict(os.environ, {"ATLAS_PUBLIC_KEY": "test-key", "ATLAS_PRIVATE_KEY": "test-secret"}):
        # Call the function with specific org_id
        success, result = create_project("TestProject", "test-org-id")
        
        # Verify the result
        assert success is True
        assert result == "test-project-id"
        
        # Verify the API was called correctly
        mock_post.assert_called_once()
        # Verify get_organizations was not called
        mock_get_orgs.assert_not_called()

@patch('mongodb_atlas.requests.post')
@patch('mongodb_atlas.get_organizations')
def test_create_project_without_org_id(mock_get_orgs, mock_post):
    # Mock successful responses
    mock_post_response = MagicMock()
    mock_post_response.status_code = 201
    mock_post_response.json.return_value = {"id": "test-project-id"}
    mock_post.return_value = mock_post_response
    
    # Mock get_organizations result
    mock_get_orgs.return_value = (True, [{"id": "auto-org-id", "name": "Auto Org"}])
    
    # Set environment variables for the test
    with patch.dict(os.environ, {"ATLAS_PUBLIC_KEY": "test-key", "ATLAS_PRIVATE_KEY": "test-secret"}):
        # Call the function without org_id
        success, result = create_project("TestProject")
        
        # Verify the result
        assert success is True
        assert result == "test-project-id"
        
        # Verify get_organizations was called
        mock_get_orgs.assert_called_once()
        
        # Verify the API was called with the correct org_id
        mock_post.assert_called_once()
        # Inspect the JSON payload
        call_args = mock_post.call_args[1]["json"]
        assert call_args["orgId"] == "auto-org-id"

@patch('mongodb_atlas.requests.post')
def test_create_project_failure(mock_post):
    # Mock failed response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Invalid request"
    mock_post.return_value = mock_response
    
    # Set environment variables for the test
    with patch.dict(os.environ, {"ATLAS_PUBLIC_KEY": "test-key", "ATLAS_PRIVATE_KEY": "test-secret"}):
        # Call the function
        success, result = create_project("TestProject", "test-org-id")
        
        # Verify the result
        assert success is False
        assert "Failed to create project" in result

@patch('mongodb_atlas.requests.post')
def test_create_project_missing_env_vars(mock_post):
    # Set environment variables for the test (missing)
    with patch.dict(os.environ, {}, clear=True):
        # Call the function
        success, result = create_project("TestProject", "test-org-id")
        
        # Verify the result
        assert success is False
        assert "API keys not found" in result
        
        # Verify the API was not called
        mock_post.assert_not_called()

# Mock the requests module for create_free_cluster tests
@patch('mongodb_atlas.requests.post')
@patch('mongodb_atlas.requests.get')
@patch('mongodb_atlas.time.sleep', return_value=None)
def test_create_free_cluster_success(mock_sleep, mock_get, mock_post):
    # Mock successful response for creating cluster
    mock_post_response = MagicMock()
    mock_post_response.status_code = 201
    mock_post.return_value = mock_post_response
    
    # Mock successful response for checking cluster status
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = {"stateName": "IDLE"}
    mock_get.return_value = mock_get_response
    
    # Set environment variables for the test
    with patch.dict(os.environ, {"ATLAS_PUBLIC_KEY": "test-key", "ATLAS_PRIVATE_KEY": "test-secret"}):
        # Call the function
        success, result = create_free_cluster("test-project-id", "TestCluster")
        
        # Verify the result
        assert success is True
        assert "mongodb+srv://admin:Password1@TestCluster.mongodb.net" in result
        
        # Verify the API was called correctly
        assert mock_post.call_count == 2  # Once for cluster, once for user
        mock_get.assert_called_once()

@patch('mongodb_atlas.requests.post')
def test_create_free_cluster_failure(mock_post):
    # Mock failed response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Invalid request"
    mock_post.return_value = mock_response
    
    # Set environment variables for the test
    with patch.dict(os.environ, {"ATLAS_PUBLIC_KEY": "test-key", "ATLAS_PRIVATE_KEY": "test-secret"}):
        # Call the function
        success, result = create_free_cluster("test-project-id", "TestCluster")
        
        # Verify the result
        assert success is False
        assert "Failed to create cluster" in result

# Mock the requests module for create_paid_cluster tests
@patch('mongodb_atlas.requests.post')
@patch('mongodb_atlas.requests.get')
@patch('mongodb_atlas.time.sleep', return_value=None)
def test_create_paid_cluster_success(mock_sleep, mock_get, mock_post):
    # Mock successful response for creating cluster
    mock_post_response = MagicMock()
    mock_post_response.status_code = 201
    mock_post.return_value = mock_post_response
    
    # Mock successful response for checking cluster status
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = {"stateName": "IDLE"}
    mock_get.return_value = mock_get_response
    
    # Set environment variables for the test
    with patch.dict(os.environ, {"ATLAS_PUBLIC_KEY": "test-key", "ATLAS_PRIVATE_KEY": "test-secret"}):
        # Call the function
        success, result = create_paid_cluster("test-project-id", "TestCluster", "M10", 20)
        
        # Verify the result
        assert success is True
        assert "mongodb+srv://admin:Password1@TestCluster.mongodb.net" in result
        
        # Verify the API was called correctly
        assert mock_post.call_count == 2  # Once for cluster, once for user
        mock_get.assert_called_once()
        
        # Check that proper values were used in the payload
        payload = mock_post.call_args_list[0][1]["json"]
        assert payload["replicationSpecs"][0]["regionConfigs"][0]["electableSpecs"]["instanceSize"] == "M10"
        assert payload["replicationSpecs"][0]["regionConfigs"][0]["electableSpecs"]["diskSizeGB"] == 20

@patch('mongodb_atlas.requests.post')
def test_create_paid_cluster_invalid_storage(mock_post):
    # Set environment variables for the test
    with patch.dict(os.environ, {"ATLAS_PUBLIC_KEY": "test-key", "ATLAS_PRIVATE_KEY": "test-secret"}):
        # Call the function with invalid storage
        success, result = create_paid_cluster("test-project-id", "TestCluster", "M10", 60)
        
        # Verify the result
        assert success is False
        assert "Storage size must be between 1 and 50 GB" in result
        
        # Verify the API was not called
        mock_post.assert_not_called()

@patch('mongodb_atlas.requests.post')
@patch('mongodb_atlas.requests.get')
@patch('mongodb_atlas.time.sleep', return_value=None)
def test_create_paid_cluster_default_storage(mock_sleep, mock_get, mock_post):
    # Mock successful responses
    mock_post_response = MagicMock()
    mock_post_response.status_code = 201
    mock_post.return_value = mock_post_response
    
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = {"stateName": "IDLE"}
    mock_get.return_value = mock_get_response
    
    # Set environment variables for the test
    with patch.dict(os.environ, {"ATLAS_PUBLIC_KEY": "test-key", "ATLAS_PRIVATE_KEY": "test-secret"}):
        # Call the function without storage size for M10
        success, _ = create_paid_cluster("test-project-id", "TestCluster", "M10")
        
        # Check that the correct default storage was used
        payload = mock_post.call_args_list[0][1]["json"]
        assert payload["replicationSpecs"][0]["regionConfigs"][0]["electableSpecs"]["diskSizeGB"] == 10
        
        # Call the function without storage size for M30
        success, _ = create_paid_cluster("test-project-id", "TestCluster", "M30")
        
        # Check that the correct default storage was used
        payload = mock_post.call_args_list[1][1]["json"]
        assert payload["replicationSpecs"][0]["regionConfigs"][0]["electableSpecs"]["diskSizeGB"] == 20