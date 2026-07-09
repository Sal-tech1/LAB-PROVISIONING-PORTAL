import docker

def get_docker_client():
    """
    Establishes a connection to the host machine's Docker daemon.
    """
    try:
        # from_env() automatically finds the local Docker socket and connects
        client = docker.from_env()
        
        # Ping the daemon to ensure it's actually alive and responding
        if client.ping():
            print("Success: Connected to the Docker daemon.")
            return client
            
    except docker.errors.DockerException as e:
        print(f"CRITICAL ERROR: Failed to connect to Docker. Is Docker running? Details: {e}")
        return None

# A quick test block that only runs if you execute this specific file
if __name__ == "__main__":
    get_docker_client()
