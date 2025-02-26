# MongoDB Atlas API Client

A command-line tool to interact with the MongoDB Atlas API, allowing you to create projects and clusters programmatically.

## Requirements

- Python 3.11 or higher
- MongoDB Atlas account with API keys

## Setup

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory and add your MongoDB Atlas API keys:

```
ATLAS_PUBLIC_KEY=your_public_key
ATLAS_PRIVATE_KEY=your_private_key
```

## Usage

### List your organizations

First, you may want to list the available organizations to find the correct organization ID:

```bash
python mongodb_atlas.py list-orgs
```

This will display all the organizations you have access to, along with their IDs.

### Create a new project

```bash
python mongodb_atlas.py create-project --name YourProjectName [--org-id YourOrgId]
```

- Project name must contain only alphanumeric characters (A-Z, a-z, 0-9)
- Project name must be 20 characters or less
- If `--org-id` is not provided, the tool will use the first organization available in your account

Upon success, the tool will output the Project ID.

### Create a new free tier (M0) cluster

```bash
python mongodb_atlas.py create-free-cluster --project-id your_project_id --name YourClusterName
```

This will create a new free tier MongoDB cluster with the following configuration:
- Tier: Free (M0)
- Provider: AWS
- Region: US_EAST_1
- Database user: admin
- Database password: Password1

### Create a new paid tier cluster

```bash
python mongodb_atlas.py create-paid-cluster --project-id your_project_id --name YourClusterName --instance-size M10 [--storage-size 20]
```

This will create a new paid tier MongoDB cluster with the following configuration:
- Tier: Specified tier (M10, M20, M30, etc.)
- Provider: AWS
- Region: CA_CENTRAL_1 (ca-central-1)
- 3 node replica set
- Continuous backup: Disabled
- Storage: Specified size (max 50GB) or default based on instance size
- Database user: admin
- Database password: Password1

Upon success, the tool will output the MongoDB connection string.

## Logging

All operations are logged to both the console and a log file (`mongodb_atlas.log`).

## Running Tests

To run the tests, execute:

```bash
pytest -v
```

The tests use mocking to simulate API calls, so no actual API requests are made during testing.