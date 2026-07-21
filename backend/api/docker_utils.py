"""Docker helper functions for lab container management."""

import socket
from typing import Any

try:
    import docker
except ImportError:  # pragma: no cover - exercised when docker SDK absent
    docker = None


def get_free_port() -> int:
    """Find the first unused TCP port between 10000 and 20000.

    Returns:
        int: An available host port.
    """
    for port in range(10000, 20001):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("0.0.0.0", port))
            except OSError:
                continue
            return port
    raise RuntimeError("No free port available between 10000 and 20000")


def spawn_container(
    image_tag: str,
    cpu_limit: str,
    ram_limit: str,
    port: int,
) -> str:
    """Create and start a detached lab container on the lab network.

    Args:
        image_tag: Docker image reference to run.
        cpu_limit: CPU quota as a string, for example ``"0.5"``.
        ram_limit: Memory limit string, for example ``"256m"``.
        port: Host port to expose on the local machine.

    Returns:
        str: The full container ID returned by Docker.
    """
    if docker is None:
        raise RuntimeError("docker package is not installed")

    client: Any = docker.from_env()
    nano_cpu_limit: int = int(float(cpu_limit) * 1_000_000_000)
    container = client.containers.run(
        image=image_tag,
        detach=True,
        network="lab-network",
        ports={"80/tcp": port},
        mem_limit=ram_limit,
        nano_cpus=nano_cpu_limit,
    )
    return container.id


def kill_container(container_id: str) -> None:
    """Stop and remove a running container by ID.

    Args:
        container_id: Docker container identifier.
    """
    if docker is None:
        raise RuntimeError("docker package is not installed")

    client: Any = docker.from_env()
    container = client.containers.get(container_id)
    container.stop(timeout=10)
    container.remove(force=True)
