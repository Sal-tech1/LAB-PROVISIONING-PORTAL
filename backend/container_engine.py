import socket
import docker
from typing import Optional, Dict

def get_docker_client():
    """
    Establishes a connection to the host machine's Docker daemon.
    """
    try:
        # from_env() automatically finds the local Docker socket and connects
        client = docker.from_env()
        
        # Ping the daemon to ensure it's actually alive and responding
        if client.ping():
            return client
            
    except docker.errors.DockerException as e:
        print(f"CRITICAL ERROR: Failed to connect to Docker. Is Docker running? Details: {e}")
        return None


def find_free_port(start_port: int = 10000, end_port: int = 10050) -> Optional[int]:
    """Scans the host for an available port within the specified range."""
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Try to bind to the port. If it fails, the port is in use.
            try:
                s.bind(('0.0.0.0', port))
                return port
            except OSError:
                continue
    return None


def provision_lab_container(template_image: str = "lab-alpine:v2") -> Dict[str, str]:
    """
    Finds a free port, spawns the container, attaches it to the network,
    and returns the connection details.
    """
    client = get_docker_client()
    if not client:
        return {"error": "Could not connect to Docker."}

    # 1. Find an open port
    host_port = find_free_port()
    if not host_port:
        return {"error": "No available ports found for provisioning."}

    print(f"Provisioning lab... Selected Host Port: {host_port}")

    try:
        # 2. Spawn the container
        container = client.containers.run(
            image=template_image,
            detach=True,
            ports={'8080/tcp': host_port},
            network="portal-bridge",
            labels={"type": "student-lab"} 
        )
        
        print(f"Success! Container {container.short_id} running on port {host_port}.")
        
        # 3. Return the vital details to the backend
        return {
            "status": "success",
            "container_id": container.id,
            "short_id": container.short_id,
            "host_port": host_port
        }

    except Exception as e:
        return {"error": f"Failed to spawn container: {str(e)}"}


# A quick test block that only runs if you execute this specific file directly
if __name__ == "__main__":
    print("Testing Docker Provisioning Engine...")
    result = provision_lab_container()
    print("\nFinal API Response:", result)
