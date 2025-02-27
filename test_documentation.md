# MongoDB Atlas Test Suite Documentation

## Table of Contents
- [Project Name Validation Tests](#project-name-validation-tests)
- [Organization Management Tests](#organization-management-tests)
- [Project Management Tests](#project-management-tests)
- [Free Cluster Tests](#free-cluster-tests)
- [Paid Cluster Tests](#paid-cluster-tests)

## Project Name Validation Tests

### `test_validate_project_name`

**Purpose**: Verifies that the project name validation function correctly validates names according to MongoDB Atlas requirements.

**Test Cases**:
- Valid alphanumeric project name
- Project name exceeding 20 characters (should fail)
- Empty project name (should fail)
- Project name with special characters (should fail)

**Verification**:
- For valid names: Asserts the validation returns `True`
- For invalid names: Asserts the validation returns `False` with appropriate error message

**Implementation Notes**:
- No mocking required as this is a pure function test
- Validates against requirements in section 3.2 of the requirements document

## Organization Management Tests

### `test_get_organizations_success`

**Purpose**: Verifies that the function to retrieve organizations works correctly when the API responds successfully.

**Setup**:
- Mocks the `requests.get` function to simulate a successful API response
- Sets up mock environment variables for API authentication
- Mock response returns two sample organizations

**Verification**:
- Confirms function returns success status (`True`)
- Validates organization data is correctly parsed and returned
- Verifies the API was called with correct parameters

**Implementation Notes**:
- Uses `patch` decorator from `unittest.mock` to replace the real `requests.get` with a mock

### `test_get_organizations_failure`

**Purpose**: Tests the error handling when the organization retrieval API call fails.

**Setup**:
- Mocks `requests.get` to return a failure status code (400)
- Sets up mock environment variables for API authentication

**Verification**:
- Confirms function returns failure status (`False`)
- Verifies error message contains "Failed to fetch organizations"

**Implementation Notes**:
- Tests error handling and reporting for API failures
- Ensures failures are properly reported to the caller

## Project Management Tests

### `test_create_project_with_org_id`

**Purpose**: Tests project creation when a specific organization ID is provided.

**Setup**:
- Mocks `requests.post` to simulate a successful project creation
- Sets up environment variables for authentication
- Configures the mock to return a sample project ID

**Verification**:
- Confirms function returns success status
- Verifies the returned project ID matches the expected value
- Ensures the API was called exactly once with the correct organization ID
- Verifies `get_organizations` is not called (as org ID was provided)

**Implementation Notes**:
- Tests the direct project creation path without organization lookup

### `test_create_project_without_org_id`

**Purpose**: Tests project creation when no organization ID is provided, requiring auto-selection of the first organization.

**Setup**:
- Mocks both `requests.post` and `get_organizations`
- Configures `get_organizations` to return a success result with sample organizations
- Sets up environment variables for authentication

**Verification**:
- Confirms function returns success status
- Validates the project ID is correctly returned
- Ensures `get_organizations` was called to retrieve the organization list
- Verifies the API was called with the automatically selected organization ID

**Implementation Notes**:
- Tests the fallback mechanism for organization selection
- Verifies the integration between organization retrieval and project creation

### `test_create_project_failure`

**Purpose**: Tests error handling when the project creation API call fails.

**Setup**:
- Mocks `requests.post` to return a failure status code (400)
- Sets up environment variables for authentication

**Verification**:
- Confirms function returns failure status
- Ensures error message contains "Failed to create project"

**Implementation Notes**:
- Tests error handling and reporting for project creation failures

### `test_create_project_missing_env_vars`

**Purpose**: Tests the behavior when required API credentials are missing.

**Setup**:
- Directly patches the module-level variables `ATLAS_PUBLIC_KEY` and `ATLAS_PRIVATE_KEY` to `None`

**Verification**:
- Confirms function returns failure status
- Verifies error message contains "API keys not found"

**Implementation Notes**:
- Tests the authentication prerequisite check
- Ensures appropriate error messaging when credentials are missing

## Free Cluster Tests

### `test_create_free_cluster_success`

**Purpose**: Tests the successful creation of a free (M0) tier MongoDB cluster.

**Setup**:
- Patches `get_cluster_connection_string` to avoid extra API calls
- Mocks `requests.post` for cluster and user creation
- Mocks `requests.get` for cluster status check
- Mocks `time.sleep` to avoid delays during testing
- Configures mock responses for success scenarios
- Sets up environment variables for authentication

**Verification**:
- Confirms function returns success status
- Verifies connection string format is correct
- Checks that the API was called correctly for both cluster creation and user creation
- Ensures only one status check was performed

**Implementation Notes**:
- Tests the complete free cluster creation workflow
- Patches multiple components to isolate the test functionality
- Verifies the connection string construction for free clusters

### `test_create_free_cluster_failure`

**Purpose**: Tests error handling when free cluster creation fails.

**Setup**:
- Mocks `requests.post` to return a failure status code (400)
- Sets up environment variables for authentication

**Verification**:
- Confirms function returns failure status
- Ensures error message contains "Failed to create cluster"

**Implementation Notes**:
- Tests error handling and reporting for cluster creation failures
- Focuses on early failure detection during the initial API call

## Paid Cluster Tests

### `test_create_paid_cluster_success`

**Purpose**: Tests the successful creation of a paid tier MongoDB cluster with specific instance and storage sizes.

**Setup**:
- Patches `get_cluster_connection_string` to avoid extra API calls
- Mocks `requests.post` for cluster and user creation
- Mocks `requests.get` for cluster status check
- Mocks `time.sleep` to avoid delays during testing
- Configures mock responses for success scenarios
- Sets up environment variables for authentication

**Verification**:
- Confirms function returns success status
- Verifies connection string format is correct
- Checks that the API was called correctly for both cluster creation and user creation
- Ensures only one status check was performed
- Verifies that the correct instance size (M10) and storage size (20GB) were used in the API payload

**Implementation Notes**:
- Tests the complete paid cluster creation workflow with explicit configuration
- Verifies payload construction for the MongoDB Atlas API
- Checks that the connection string reflects the paid cluster format

### `test_create_paid_cluster_invalid_storage`

**Purpose**: Tests validation of storage size for paid clusters.

**Setup**:
- Mocks `requests.post` (though it should not be called)
- Sets up environment variables for authentication
- Attempts to create a cluster with an invalid storage size (60GB, exceeding the 50GB limit)

**Verification**:
- Confirms function returns failure status
- Ensures error message contains "Storage size must be between 1 and 50 GB"
- Verifies the API was not called (validation failed before API call)

**Implementation Notes**:
- Tests input validation for storage size
- Ensures invalid configurations are rejected early

### `test_create_paid_cluster_default_storage`

**Purpose**: Tests the default storage size selection based on instance type.

**Setup**:
- Patches `get_cluster_connection_string` to avoid extra API calls
- Uses complex mocking with side effects to handle multiple API calls
- Mocks `requests.post` with different responses for M10 and M30 clusters
- Mocks `requests.get` for cluster status check
- Mocks `time.sleep` to avoid delays during testing
- Sets up environment variables for authentication

**Verification**:
- Makes two calls to `create_paid_cluster`: one with M10 instance type, another with M30
- For M10: Verifies a default storage size of 10GB is used
- For M30: Verifies a default storage size of 20GB is used
- Ensures the payload structure is correct for both calls

**Implementation Notes**:
- Tests the logic for default storage size selection
- Uses sophisticated mocking to handle multiple sequential API calls
- Verifies that different default values are applied based on instance size
