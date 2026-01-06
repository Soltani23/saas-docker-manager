import docker
from docker.errors import DockerException, NotFound, APIError
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DockerManager:
    """Wrapper class for Docker API operations with error handling"""
    
    def __init__(self, base_url='unix:///var/run/docker.sock'):
        """Initialize Docker client
        
        Args:
            base_url: Docker daemon socket URL
        """
        try:
            self.client = docker.DockerClient(base_url=base_url)
            self.client.ping()
            logger.info("Successfully connected to Docker daemon")
        except DockerException as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise
    
    def create_nginx_container(self, container_name, port, html_content, user_id):
        """Create and start an Nginx container with custom HTML
        
        Args:
            container_name: Unique name for the container
            port: Host port to bind
            html_content: Custom HTML content for index page
            user_id: Owner user ID
            
        Returns:
            dict: Container information (id, name, status, port)
        """
        try:
            # Create temporary HTML file content
            html_dir = f"/tmp/nginx_{container_name}"
            os.makedirs(html_dir, exist_ok=True)
            
            html_path = os.path.join(html_dir, "index.html")
            with open(html_path, 'w') as f:
                f.write(html_content)
            
            # Create container with volume mount
            container = self.client.containers.run(
                'nginx:alpine',
                name=container_name,
                ports={'80/tcp': port},
                volumes={html_dir: {'bind': '/usr/share/nginx/html', 'mode': 'ro'}},
                labels={'user_id': str(user_id), 'managed_by': 'docker-saas'},
                detach=True,
                restart_policy={'Name': 'unless-stopped'}
            )
            
            logger.info(f"Created container {container_name} for user {user_id}")
            
            return {
                'id': container.id,
                'name': container.name,
                'status': container.status,
                'port': port
            }
            
        except APIError as e:
            logger.error(f"Docker API error creating container: {e}")
            raise Exception(f"Failed to create container: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating container: {e}")
            raise
    
    def get_container_status(self, container_id):
        """Get current status of a container
        
        Args:
            container_id: Docker container ID
            
        Returns:
            str: Container status (running, stopped, etc.)
        """
        try:
            container = self.client.containers.get(container_id)
            container.reload()
            return container.status
        except NotFound:
            logger.warning(f"Container {container_id} not found")
            return 'removed'
        except Exception as e:
            logger.error(f"Error getting container status: {e}")
            return 'unknown'
    
    def start_container(self, container_id):
        """Start a stopped container
        
        Args:
            container_id: Docker container ID
            
        Returns:
            bool: Success status
        """
        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info(f"Started container {container_id}")
            return True
        except NotFound:
            logger.error(f"Container {container_id} not found")
            return False
        except APIError as e:
            logger.error(f"Failed to start container: {e}")
            return False
    
    def stop_container(self, container_id):
        """Stop a running container
        
        Args:
            container_id: Docker container ID
            
        Returns:
            bool: Success status
        """
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10)
            logger.info(f"Stopped container {container_id}")
            return True
        except NotFound:
            logger.error(f"Container {container_id} not found")
            return False
        except APIError as e:
            logger.error(f"Failed to stop container: {e}")
            return False
    
    def delete_container(self, container_id):
        """Remove a container (must be stopped first)
        
        Args:
            container_id: Docker container ID
            
        Returns:
            bool: Success status
        """
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=True)
            logger.info(f"Deleted container {container_id}")
            return True
        except NotFound:
            logger.error(f"Container {container_id} not found")
            return False
        except APIError as e:
            logger.error(f"Failed to delete container: {e}")
            return False
    
    def get_container_logs(self, container_id, tail=100):
        """Get container logs
        
        Args:
            container_id: Docker container ID
            tail: Number of lines to retrieve
            
        Returns:
            str: Container logs
        """
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail).decode('utf-8')
            return logs
        except NotFound:
            return "Container not found"
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return f"Error: {str(e)}"
    
    def list_user_containers(self, user_id):
        """List all containers for a specific user
        
        Args:
            user_id: User ID
            
        Returns:
            list: List of container dictionaries
        """
        try:
            filters = {'label': f'user_id={user_id}'}
            containers = self.client.containers.list(all=True, filters=filters)
            
            result = []
            for c in containers:
                result.append({
                    'id': c.id,
                    'name': c.name,
                    'status': c.status,
                    'image': c.image.tags[0] if c.image.tags else 'unknown'
                })
            
            return result
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return []
