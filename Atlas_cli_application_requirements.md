# MongoDB Atlas CLI Application Requirements

## Overview

This document outlines the functional requirements for the MongoDB Atlas CLI application, a command-line tool designed to automate the provisioning and management of MongoDB Atlas resources. The application enables users to create projects and clusters programmatically through a simple command-line interface.

## 1. Authentication and Authorization

| ID | Requirement |
|----|-------------|
| 1.1 | The system must authenticate with MongoDB Atlas using public and private API keys |
| 1.2 | The system must securely load credentials from environment variables or a .env file |
| 1.3 | The system must handle authentication failures gracefully with appropriate error messages |

## 2. Organization Management

| ID | Requirement |
|----|-------------|
| 2.1 | The system must be able to retrieve a list of organizations associated with the authenticated user |
| 2.2 | The system must display organization IDs and names when listing organizations |
| 2.3 | The system must automatically use the first available organization if none is specified |

## 3. Project Management

| ID | Requirement |
|----|-------------|
| 3.1 | The system must create new projects within specified organizations |
| 3.2 | The system must validate project names according to MongoDB Atlas requirements: |
|     | - Must contain only alphanumeric characters (A-Z, a-z, 0-9) |
|     | - Must not exceed 20 characters |
|     | - Cannot be empty |
| 3.3 | The system must return the project ID upon successful creation |

## 4. Cluster Management - Free Tier

| ID | Requirement |
|----|-------------|
| 4.1 | The system must create free tier (M0) MongoDB clusters |
| 4.2 | Free clusters must be configured with: |
|     | - AWS as the provider |
|     | - US_EAST_1 as the region |
|     | - REPLICASET as the cluster type |
|     | - 3 nodes in the replica set |
| 4.3 | The system must wait for free clusters to be fully provisioned before completing |
| 4.4 | The system must implement a timeout mechanism (30 attempts with 30-second intervals) |

## 5. Cluster Management - Paid Tier

| ID | Requirement |
|----|-------------|
| 5.1 | The system must create paid tier MongoDB clusters with specified instance sizes (M10-M200) |
| 5.2 | The system must allow configurable storage sizes for paid clusters up to 50GB |
| 5.3 | The system must implement appropriate defaults for storage size based on instance type: |
|     | - 10GB for M10 and M20 instances |
|     | - 20GB for all other instance types |
| 5.4 | Paid clusters must be configured with: |
|     | - AWS as the provider |
|     | - CA_CENTRAL_1 as the region |
|     | - REPLICASET as the cluster type |
|     | - 3 nodes in the replica set |
|     | - Continuous backup disabled |
| 5.5 | The system must wait for paid clusters to be fully provisioned with longer timeout (60 attempts) |
| 5.6 | The system must validate storage size input (between 1-50GB) |

## 6. User Management

| ID | Requirement |
|----|-------------|
| 6.1 | The system must create a default database user (admin/Password1) with atlasAdmin role |
| 6.2 | The system must handle the case where a user already exists and continue execution |
| 6.3 | The system must log user creation conflicts as warnings, not errors |

## 7. Error Handling and Logging

| ID | Requirement |
|----|-------------|
| 7.1 | The system must implement comprehensive error handling for all API operations |
| 7.2 | The system must log all operations, successes, warnings, and errors to both console and file |
| 7.3 | The system must provide detailed error messages for failed operations |
| 7.4 | The system must detect and report timeout conditions for long-running operations |
| 7.5 | The system must handle API-specific error responses with appropriate messages |

## 8. Command Line Interface

| ID | Requirement |
|----|-------------|
| 8.1 | The system must provide a command-line interface with the following commands: |
|     | - `list-orgs`: List available organizations |
|     | - `create-project`: Create a new project |
|     | - `create-free-cluster`: Create a new free tier cluster |
|     | - `create-paid-cluster`: Create a new paid tier cluster |
| 8.2 | Each command must accept appropriate arguments with validation |
| 8.3 | The system must display help text when invalid commands are used |
| 8.4 | The system must return appropriate exit codes (0 for success, 1 for failure) |

## 9. Connection Management

| ID | Requirement |
|----|-------------|
| 9.1 | The system must generate and return MongoDB connection strings for created clusters |
| 9.2 | Connection strings must follow the format: `mongodb+srv://admin:Password1@{cluster_name}.mongodb.net` |

## 10. Testing and Quality Assurance

| ID | Requirement |
|----|-------------|
| 10.1 | The system must have unit tests for core functionality |
| 10.2 | Tests must use mocking to simulate API calls without making actual requests |

## 11. Documentation

| ID | Requirement |
|----|-------------|
| 11.1 | The system must provide documentation for installation and usage |
| 11.2 | Documentation must include examples for each supported command |
| 11.3 | Documentation must explain configuration requirements (API keys, environment variables) |

## Usage Example

```bash
# List organizations
python mongodb_atlas.py list-orgs

# Create a project
python mongodb_atlas.py create-project --name TestProject

# Create a free cluster
python mongodb_atlas.py create-free-cluster --project-id PROJECT_ID --name mycluster

# Create a paid cluster
python mongodb_atlas.py create-paid-cluster --project-id PROJECT_ID --name mycluster --instance-size M10 --storage-size 20
```

## Environment Setup

The application requires the following environment variables to be set in a `.env` file:

```
ATLAS_PUBLIC_KEY=your_public_key
ATLAS_PRIVATE_KEY=your_private_key
```
