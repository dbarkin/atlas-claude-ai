import os
import sys
import re  # Regular expression module
import argparse
import logging
import time
import requests
from requests.auth import HTTPDigestAuth
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mongodb_atlas.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mongodb_atlas")

# Load environment variables
load_dotenv()

ATLAS_PUBLIC_KEY = os.getenv("ATLAS_PUBLIC_KEY")
ATLAS_PRIVATE_KEY = os.getenv("ATLAS_PRIVATE_KEY")
ATLAS_BASE_URL = "https://cloud.mongodb.com/api/atlas/v2"

# Default database user credentials - using environment variables with defaults
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")  

# Headers for the API requests
HEADERS = {
    "Accept": "application/vnd.atlas.2025-02-19+json",
    "Content-Type": "application/json"
}

# Helper function to mask sensitive info in connection strings for logging
def mask_connection_string(connection_string):
    """
    Masks passwords in connection strings for safe logging
    
    Args:
        connection_string (str): The connection string that may contain credentials
        
    Returns:
        str: The masked connection string with password replaced by asterisks
    """
    if not connection_string:
        return connection_string
        
    # Use regex to replace password
    return re.sub(r'(mongodb\+srv://[^:]+:)([^@]+)(@.*)', r'\1*****\3', connection_string)

def get_cluster_connection_string(project_id, cluster_name):
    """
    Get the official connection string from MongoDB Atlas API for a given cluster.
    
    Args:
        project_id (str): The ID of the project containing the cluster
        cluster_name (str): The name of the cluster
        
    Returns:
        str or None: The official connection string if available, None otherwise
    """
    try:
        response = requests.get(
            f"{ATLAS_BASE_URL}/groups/{project_id}/clusters/{cluster_name}",
            auth=HTTPDigestAuth(ATLAS_PUBLIC_KEY, ATLAS_PRIVATE_KEY),
            headers=HEADERS
        )
        
        if response.status_code == 200:
            cluster_data = response.json()
            connection_strings = cluster_data.get("connectionStrings", {})
            
            # Get the standard SRV connection string
            srv_string = connection_strings.get("standardSrv")
            
            if srv_string:
                # Replace the default username with admin and add the password
                if "://" in srv_string:
                    parts = srv_string.split("://")
                    srv_string = f"{parts[0]}://{DB_USER}:{DB_PASSWORD}@{parts[1]}"
                
                logger.info(f"Retrieved official connection string from Atlas API")
                # Log the masked version for security
                logger.debug(f"Connection string: {mask_connection_string(srv_string)}")
                return srv_string
        
        logger.warning(f"Failed to retrieve connection string from API. Status code: {response.status_code}")
        return None
    except Exception as e:
        logger.warning(f"Error retrieving connection string: {str(e)}")
        return None

def construct_connection_string(cluster_name, provider_region=None, cluster_type=None):
    """
    Construct a more accurate MongoDB Atlas connection string.
    
    Args:
        cluster_name (str): The name of the cluster
        provider_region (str, optional): The cloud provider region (e.g., "aws-us-east-1")
        cluster_type (str, optional): The cluster type (e.g., "REPLICASET")
        
    Returns:
        str: A formatted MongoDB Atlas connection string
    """
    # Extract region code from provider_region if available
    region_suffix = ""
    if provider_region:
        if provider_region.startswith("aws-"):
            region_code = provider_region.replace("aws-", "")
            region_suffix = f".{region_code}"
        elif provider_region.startswith("azure-"):
            region_code = provider_region.replace("azure-", "")
            region_suffix = f".{region_code}"
        elif provider_region.startswith("gcp-"):
            region_code = provider_region.replace("gcp-", "")
            region_suffix = f".{region_code}"
    
    # Construct hostname using cluster name and region if available
    hostname = f"{cluster_name}{region_suffix}.mongodb.net"
    
    # Include standard connection options
    connection_string = f"mongodb+srv://{DB_USER}:{DB_PASSWORD}@{hostname}/?retryWrites=true&w=majority"
    return connection_string

# Rest of the code remains the same...

def validate_project_name(name):
    """
    Validate that the project name contains only English characters and numbers,
    and is not longer than 20 characters.
    """
    if not name:
        return False, "Project name cannot be empty"
    
    if len(name) > 20:
        return False, "Project name cannot exceed 20 characters"
    
    # Simple pattern to match only alphanumeric characters
    if not re.match(r'^[a-zA-Z0-9]+$', name):
        return False, "Project name must contain only English characters and numbers"
    
    return True, "Project name is valid"

def get_organizations():
    """
    Get the list of organizations that the authenticated user belongs to.
    
    Returns:
        tuple: (success, result) where success is a boolean indicating if the operation was successful
               and result is either the list of organizations or an error message
    """
    logger.info("Fetching organizations")
    
    # Check if API keys are available
    if not ATLAS_PUBLIC_KEY or not ATLAS_PRIVATE_KEY:
        logger.error("MongoDB Atlas API keys not found in environment variables")
        return False, "API keys not found. Please set ATLAS_PUBLIC_KEY and ATLAS_PRIVATE_KEY in your .env file"
    
    try:
        response = requests.get(
            f"{ATLAS_BASE_URL}/orgs",
            auth=HTTPDigestAuth(ATLAS_PUBLIC_KEY, ATLAS_PRIVATE_KEY),
            headers=HEADERS
        )
        
        if response.status_code == 200:
            orgs_data = response.json()
            orgs = orgs_data.get("results", [])
            logger.info(f"Successfully fetched {len(orgs)} organizations")
            return True, orgs
        else:
            error_message = f"Failed to fetch organizations. Status code: {response.status_code}, Response: {response.text}"
            logger.error(error_message)
            return False, error_message
            
    except Exception as e:
        error_message = f"Exception occurred while fetching organizations: {str(e)}"
        logger.error(error_message)
        return False, error_message

def create_project(project_name, org_id=None):
    """
    Create a new project in MongoDB Atlas.
    
    Args:
        project_name (str): The name of the project to create
        org_id (str, optional): The organization ID to create the project in.
                               If not provided, will use the first organization found.
    
    Returns:
        tuple: (success, result) where success is a boolean indicating if the operation was successful
               and result is either the project ID or an error message
    """
    logger.info(f"Creating project: {project_name}")
    
    # Validate project name
    valid, message = validate_project_name(project_name)
    if not valid:
        logger.error(f"Validation error: {message}")
        return False, message
    
    # Check if API keys are available
    if not ATLAS_PUBLIC_KEY or not ATLAS_PRIVATE_KEY:
        logger.error("MongoDB Atlas API keys not found in environment variables")
        return False, "API keys not found. Please set ATLAS_PUBLIC_KEY and ATLAS_PRIVATE_KEY in your .env file"
    
    # If no org_id is provided, get the first organization
    if not org_id:
        success, orgs = get_organizations()
        if not success:
            return False, orgs  # This will be the error message
        
        if not orgs:
            return False, "No organizations found for this user"
        
        org_id = orgs[0].get("id")
        logger.info(f"Using organization ID: {org_id}")
    
    # Create project payload
    payload = {
        "name": project_name,
        "orgId": org_id
    }
    
    try:
        response = requests.post(
            f"{ATLAS_BASE_URL}/groups",
            auth=HTTPDigestAuth(ATLAS_PUBLIC_KEY, ATLAS_PRIVATE_KEY),
            headers=HEADERS,
            json=payload
        )
        
        if response.status_code == 201:
            project_data = response.json()
            project_id = project_data.get("id")
            logger.info(f"Project created successfully with ID: {project_id}")
            return True, project_id
        else:
            error_message = f"Failed to create project. Status code: {response.status_code}, Response: {response.text}"
            logger.error(error_message)
            return False, error_message
            
    except Exception as e:
        error_message = f"Exception occurred while creating project: {str(e)}"
        logger.error(error_message)
        return False, error_message

def create_free_cluster(project_id, cluster_name):
    """
    Create a new free tier (M0) MongoDB cluster in the specified project.
    
    Args:
        project_id (str): The ID of the project where the cluster will be created
        cluster_name (str): The name of the cluster to create
    
    Returns:
        tuple: (success, result) where success is a boolean indicating if the operation was successful
               and result is either the cluster connection string or an error message
    """
    logger.info(f"Creating free cluster: {cluster_name} in project: {project_id}")
    
    # Check if API keys are available
    if not ATLAS_PUBLIC_KEY or not ATLAS_PRIVATE_KEY:
        logger.error("MongoDB Atlas API keys not found in environment variables")
        return False, "API keys not found. Please set ATLAS_PUBLIC_KEY and ATLAS_PRIVATE_KEY in your .env file"
    
    # Create free cluster payload
    payload = {
        "name": cluster_name,                        
        "clusterType": 'REPLICASET',
        "replicationSpecs": [{            
            "regionConfigs": [
            {
                "electableSpecs": {
                "ebsVolumeType": "STANDARD",
                "instanceSize": "M0",
                "nodeCount": 3,
                },
                "priority": 7,
                "regionName": 'US_EAST_1',
                "providerName": 'TENANT',
                "backingProviderName": 'AWS'
            },
            ],
        }],
    }
    
    try:
        # Create the cluster
        response = requests.post(
            f"{ATLAS_BASE_URL}/groups/{project_id}/clusters",
            auth=HTTPDigestAuth(ATLAS_PUBLIC_KEY, ATLAS_PRIVATE_KEY),
            headers=HEADERS,
            json=payload
        )
        
        if response.status_code == 201:
            logger.info(f"Cluster creation initiated successfully")
            
            # Wait for the cluster to be created (this could take several minutes)
            cluster_ready = False
            max_attempts = 30
            attempts = 0
            
            while not cluster_ready and attempts < max_attempts:
                time.sleep(30)  # Wait 30 seconds between checks
                attempts += 1
                
                # Check cluster status
                status_response = requests.get(
                    f"{ATLAS_BASE_URL}/groups/{project_id}/clusters/{cluster_name}",
                    auth=HTTPDigestAuth(ATLAS_PUBLIC_KEY, ATLAS_PRIVATE_KEY),
                    headers=HEADERS
                )
                
                if status_response.status_code == 200:
                    cluster_data = status_response.json()
                    status = cluster_data.get("stateName")
                    
                    if status == "IDLE":  # Cluster is ready
                        cluster_ready = True
                        
                        # Create database user
                        user_payload = {
                            "databaseName": "admin",
                            "password": DB_PASSWORD,
                            "roles": [
                                {
                                    "databaseName": "admin",
                                    "roleName": "atlasAdmin"
                                }
                            ],
                            "username": DB_USER
                        }
                        
                        user_response = requests.post(
                            f"{ATLAS_BASE_URL}/groups/{project_id}/databaseUsers",
                            auth=HTTPDigestAuth(ATLAS_PUBLIC_KEY, ATLAS_PRIVATE_KEY),
                            headers=HEADERS,
                            json=user_payload
                        )
                        
                        if user_response.status_code == 201:
                            logger.info("Database user created successfully")
                            
                            # Try to get official connection string from the API
                            api_connection_string = get_cluster_connection_string(project_id, cluster_name)
                            
                            if api_connection_string:
                                connection_string = api_connection_string
                            else:
                                # Fall back to the constructed connection string
                                connection_string = construct_connection_string(cluster_name, "aws-us-east-1", "REPLICASET")
                                
                            # Log masked version of connection string
                            logger.info(f"Cluster created successfully")
                            logger.info(f"Connection string: {mask_connection_string(connection_string)}")
                            return True, connection_string
                            
                        elif user_response.status_code == 409 and "USER_ALREADY_EXISTS" in user_response.text:
                            # User already exists - log as warning and continue
                            warning_message = f"Warning: Database user '{DB_USER}' already exists."
                            logger.warning(warning_message)
                            logger.warning(f"Response details: {user_response.text}")
                            
                            # Try to get official connection string from the API
                            api_connection_string = get_cluster_connection_string(project_id, cluster_name)
                            
                            if api_connection_string:
                                connection_string = api_connection_string
                            else:
                                # Fall back to the constructed connection string
                                connection_string = construct_connection_string(cluster_name, "aws-us-east-1", "REPLICASET")
                            
                            # Log masked version of connection string
                            logger.info(f"Cluster created successfully")
                            logger.info(f"Connection string: {mask_connection_string(connection_string)}")
                            return True, connection_string
                            
                        else:
                            error_message = f"Failed to create database user. Status code: {user_response.status_code}, Response: {user_response.text}"
                            logger.error(error_message)
                            return False, error_message
                    
                    logger.info(f"Waiting for cluster to be ready. Current status: {status}, Attempt: {attempts}/{max_attempts}")
                else:
                    error_message = f"Failed to check cluster status. Status code: {status_response.status_code}, Response: {status_response.text}"
                    logger.error(error_message)
                    return False, error_message
                    
            if not cluster_ready:
                error_message = "Timeout waiting for cluster to be ready"
                logger.error(error_message)
                return False, error_message
        else:
            error_message = f"Failed to create cluster. Status code: {response.status_code}, Response: {response.text}"
            logger.error(error_message)
            return False, error_message
            
    except Exception as e:
        error_message = f"Exception occurred while creating cluster: {str(e)}"
        logger.error(error_message)
        return False, error_message

def create_paid_cluster(project_id, cluster_name, instance_size, storage_size=None):
    """
    Create a new paid tier MongoDB cluster in the specified project.
    
    Args:
        project_id (str): The ID of the project where the cluster will be created
        cluster_name (str): The name of the cluster to create
        instance_size (str): The instance size (e.g., M10, M20, M30)
        storage_size (int, optional): Storage size in GB (max 50). Default is None which will use default storage for the instance.
    
    Returns:
        tuple: (success, result) where success is a boolean indicating if the operation was successful
               and result is either the cluster connection string or an error message
    """
    logger.info(f"Creating paid cluster: {cluster_name} in project: {project_id} with instance size: {instance_size}")
    
    # Check if API keys are available
    if not ATLAS_PUBLIC_KEY or not ATLAS_PRIVATE_KEY:
        logger.error("MongoDB Atlas API keys not found in environment variables")
        return False, "API keys not found. Please set ATLAS_PUBLIC_KEY and ATLAS_PRIVATE_KEY in your .env file"
    
    # Validate storage size
    if storage_size is not None:
        try:
            storage_size = int(storage_size)
            if storage_size <= 0 or storage_size > 50:
                return False, "Storage size must be between 1 and 50 GB"
        except ValueError:
            return False, "Storage size must be a valid integer"
    else:
        # Default storage size based on instance size
        if instance_size in ["M10", "M20"]:
            storage_size = 10
        else:
            storage_size = 20
    
    # Define the region to be used
    region_name = "CA_CENTRAL_1"
    provider_region = "aws-ca-central-1"
    
    # Create paid cluster payload
    payload = {
        "name": cluster_name,
        "clusterType": "REPLICASET",
        "backupEnabled": False,  # Disable continuous cloud backup
        "replicationSpecs": [{            
            "regionConfigs": [{
                "electableSpecs": {
                    "instanceSize": instance_size,
                    "diskSizeGB": storage_size,
                    "nodeCount": 3
                },
                "priority": 7,
                "regionName": region_name,
                "providerName": "AWS"
            }]
        }]
    }
    
    try:
        # Create the cluster
        response = requests.post(
            f"{ATLAS_BASE_URL}/groups/{project_id}/clusters",
            auth=HTTPDigestAuth(ATLAS_PUBLIC_KEY, ATLAS_PRIVATE_KEY),
            headers=HEADERS,
            json=payload
        )
        
        if response.status_code == 201:
            logger.info(f"Paid cluster creation initiated successfully")
            
            # Wait for the cluster to be created (this could take several minutes)
            cluster_ready = False
            max_attempts = 60  # Paid clusters might take longer to provision
            attempts = 0
            
            while not cluster_ready and attempts < max_attempts:
                time.sleep(30)  # Wait 30 seconds between checks
                attempts += 1
                
                # Check cluster status
                status_response = requests.get(
                    f"{ATLAS_BASE_URL}/groups/{project_id}/clusters/{cluster_name}",
                    auth=HTTPDigestAuth(ATLAS_PUBLIC_KEY, ATLAS_PRIVATE_KEY),
                    headers=HEADERS
                )
                
                if status_response.status_code == 200:
                    cluster_data = status_response.json()
                    status = cluster_data.get("stateName")
                    
                    if status == "IDLE":  # Cluster is ready
                        cluster_ready = True
                        
                        # Create database user
                        user_payload = {
                            "databaseName": "admin",
                            "password": DB_PASSWORD,
                            "roles": [
                                {
                                    "databaseName": "admin",
                                    "roleName": "atlasAdmin"
                                }
                            ],
                            "username": DB_USER
                        }
                        
                        user_response = requests.post(
                            f"{ATLAS_BASE_URL}/groups/{project_id}/databaseUsers",
                            auth=HTTPDigestAuth(ATLAS_PUBLIC_KEY, ATLAS_PRIVATE_KEY),
                            headers=HEADERS,
                            json=user_payload
                        )
                        
                        if user_response.status_code == 201:
                            logger.info("Database user created successfully")
                            
                            # Try to get official connection string from the API
                            api_connection_string = get_cluster_connection_string(project_id, cluster_name)
                            
                            if api_connection_string:
                                connection_string = api_connection_string
                            else:
                                # Fall back to the constructed connection string with region
                                connection_string = construct_connection_string(cluster_name, provider_region, "REPLICASET")
                            
                            # Log masked version of connection string
                            logger.info(f"Paid cluster created successfully")
                            logger.info(f"Connection string: {mask_connection_string(connection_string)}")
                            return True, connection_string
                        
                        elif user_response.status_code == 409 and "USER_ALREADY_EXISTS" in user_response.text:
                            # User already exists - log as warning and continue
                            warning_message = f"Warning: Database user '{DB_USER}' already exists."
                            logger.warning(warning_message)
                            logger.warning(f"Response details: {user_response.text}")
                            
                            # Try to get official connection string from the API
                            api_connection_string = get_cluster_connection_string(project_id, cluster_name)
                            
                            if api_connection_string:
                                connection_string = api_connection_string
                            else:
                                # Fall back to the constructed connection string with region
                                connection_string = construct_connection_string(cluster_name, provider_region, "REPLICASET")
                            
                            # Log masked version of connection string
                            logger.info(f"Paid cluster created successfully")
                            logger.info(f"Connection string: {mask_connection_string(connection_string)}")
                            return True, connection_string
                            
                        else:
                            error_message = f"Failed to create database user. Status code: {user_response.status_code}, Response: {user_response.text}"
                            logger.error(error_message)
                            return False, error_message
                    
                    logger.info(f"Waiting for paid cluster to be ready. Current status: {status}, Attempt: {attempts}/{max_attempts}")
                else:
                    error_message = f"Failed to check cluster status. Status code: {status_response.status_code}, Response: {status_response.text}"
                    logger.error(error_message)
                    return False, error_message
                    
            if not cluster_ready:
                error_message = "Timeout waiting for paid cluster to be ready"
                logger.error(error_message)
                return False, error_message
        else:
            error_message = f"Failed to create paid cluster. Status code: {response.status_code}, Response: {response.text}"
            logger.error(error_message)
            return False, error_message
            
    except Exception as e:
        error_message = f"Exception occurred while creating paid cluster: {str(e)}"
        logger.error(error_message)
        return False, error_message

def main():
    parser = argparse.ArgumentParser(description="MongoDB Atlas API Client")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create project command
    project_parser = subparsers.add_parser("create-project", help="Create a new project")
    project_parser.add_argument("--name", required=True, help="Project name (max 20 alphanumeric characters)")
    project_parser.add_argument("--org-id", help="Organization ID (if not provided, the first available organization will be used)")
    
    # List organizations command
    org_parser = subparsers.add_parser("list-orgs", help="List available organizations")
    
    # Create free cluster command
    free_cluster_parser = subparsers.add_parser("create-free-cluster", help="Create a new free tier (M0) cluster")
    free_cluster_parser.add_argument("--project-id", required=True, help="Project ID")
    free_cluster_parser.add_argument("--name", required=True, help="Cluster name")
    
    # Create paid cluster command
    paid_cluster_parser = subparsers.add_parser("create-paid-cluster", help="Create a new paid tier cluster")
    paid_cluster_parser.add_argument("--project-id", required=True, help="Project ID")
    paid_cluster_parser.add_argument("--name", required=True, help="Cluster name")
    paid_cluster_parser.add_argument("--instance-size", required=True, 
                                   choices=["M10", "M20", "M30", "M40", "M50", "M60", "M80", "M140", "M200"],
                                   help="Instance size (e.g., M10, M20, M30)")
    paid_cluster_parser.add_argument("--storage-size", type=int, 
                                   help="Storage size in GB (max 50, default based on instance size)")
    
    args = parser.parse_args()
    
    if args.command == "list-orgs":
        success, result = get_organizations()
        if success:
            print("Available organizations:")
            for org in result:
                print(f"ID: {org.get('id')}, Name: {org.get('name')}")
            sys.exit(0)
        else:
            print(f"Failed to list organizations: {result}")
            sys.exit(1)
    
    elif args.command == "create-project":
        success, result = create_project(args.name, args.org_id)
        if success:
            print(f"Project created successfully. Project ID: {result}")
            sys.exit(0)
        else:
            print(f"Failed to create project: {result}")
            sys.exit(1)
    
    elif args.command == "create-free-cluster":
        success, result = create_free_cluster(args.project_id, args.name)
        if success:
            print(f"Free cluster created successfully.")
            # Print masked connection string to console
            print(f"Connection string: {mask_connection_string(result)}")
            print("NOTE: Use the actual password when connecting to your database.")
            sys.exit(0)
        else:
            print(f"Failed to create free cluster: {result}")
            sys.exit(1)
    
    elif args.command == "create-paid-cluster":
        success, result = create_paid_cluster(args.project_id, args.name, args.instance_size, args.storage_size)
        if success:
            print(f"Paid cluster created successfully.")
            # Print masked connection string to console
            print(f"Connection string: {mask_connection_string(result)}")
            print("NOTE: Use the actual password when connecting to your database.")
            sys.exit(0)
        else:
            print(f"Failed to create paid cluster: {result}")
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()