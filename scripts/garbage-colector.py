#!/usr/bin/env python3
"""
garbage_collector.py
Member 4 (SRE) — Week 3 Task 3 / Week 4 Task 1

PURPOSE:
    Finds Docker containers that have been running too long and kills them.
    This prevents the server from running out of memory and CPU when
    students forget to stop their labs.

PLAIN ENGLISH:
    Imagine students keep leaving their computers on and walking away.
    This script is the person who goes around every 15 minutes, checks
    how long each computer has been running unattended, and turns off
    any that have been on for more than 2 hours.

HOW TO RUN MANUALLY:
    python3 garbage_collector.py

HOW IT IS SCHEDULED (Week 4 — cron):
    Open crontab:   crontab -e
    Add this line:  */15 * * * * python3 /path/to/garbage_collector.py >> /var/log/gc.log 2>&1

    Breaking down that cron line:
    */15  = every 15 minutes
    *     = every hour
    *     = every day of the month
    *     = every month
    *     = every day of the week
    The rest = the command to run, saving output to a log file

REQUIREMENTS:
    pip install docker python-dateutil prometheus-client

IMPORTANT — LABEL REQUIREMENT:
    This script ONLY kills containers that have the label:
        managed-by=lab-portal
    Member 2 must add this label when spawning lab containers.
    This prevents accidentally killing Prometheus, Grafana, or other
    system containers running on the same host.
"""

import docker
import logging
import sys
import os
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateutil_parser

# ── Try to import Prometheus client for metrics (optional) ────────────────────
# If not installed, the script still works — it just won't export metrics
try:
    from prometheus_client import Counter, Gauge, start_http_server
    PROMETHEUS_ENABLED = True
except ImportError:
    PROMETHEUS_ENABLED = False

# ── Configuration ──────────────────────────────────────────────────────────────
# How long a lab container is allowed to run before being killed
MAX_AGE_HOURS = int(os.getenv("GC_MAX_AGE_HOURS", "2"))

# Only kill containers with this label — safety guard so we don't kill
# system containers like Prometheus, Grafana, the backend API, etc.
MANAGED_LABEL = os.getenv("GC_MANAGED_LABEL", "managed-by=lab-portal")

# Port for the GC's own Prometheus metrics endpoint (so Grafana can track kills)
METRICS_PORT = int(os.getenv("GC_METRICS_PORT", "9101"))

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

# ── Prometheus metrics (exported so Grafana can show GC activity) ─────────────
if PROMETHEUS_ENABLED:
    gc_containers_killed = Counter(
        "gc_containers_killed_total",
        "Total number of lab containers killed by the garbage collector"
    )
    gc_containers_checked = Counter(
        "gc_containers_checked_total",
        "Total number of containers checked by the garbage collector"
    )
    gc_active_containers = Gauge(
        "gc_active_lab_containers",
        "Current number of managed lab containers running"
    )
    gc_last_run_timestamp = Gauge(
        "gc_last_run_timestamp_seconds",
        "Unix timestamp of the last garbage collection run"
    )


def get_container_age(container) -> timedelta:
    """
    Works out how long a container has been running.

    Args:
        container: A docker-py container object

    Returns:
        timedelta: How long the container has been running
                   e.g. timedelta(hours=2, minutes=34)

    PLAIN ENGLISH:
        Docker stores when each container started as a text timestamp.
        We parse that text into a real date/time, then subtract it from
        'right now' to get the age.
    """
    started_at_str = container.attrs["State"]["StartedAt"]
    started_at = dateutil_parser.parse(started_at_str)
    now = datetime.now(timezone.utc)
    return now - started_at


def is_expired(container, max_age_hours: int = None) -> bool:
    """
    Returns True if the container has exceeded its maximum allowed age.

    Args:
        container: docker-py container object
        max_age_hours: override the global MAX_AGE_HOURS (used in tests)

    Returns:
        bool: True = should be killed, False = still within time limit
    """
    if max_age_hours is None:
        max_age_hours = MAX_AGE_HOURS
    age = get_container_age(container)
    return age > timedelta(hours=max_age_hours)


def format_age(age: timedelta) -> str:
    """
    Converts a timedelta into a human-readable string.

    e.g. timedelta(hours=2, minutes=34) → "2h 34m"
    """
    total_minutes = int(age.total_seconds() / 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"


def kill_container(container) -> bool:
    """
    Kills a single container and logs what happened.

    Args:
        container: docker-py container object to kill

    Returns:
        bool: True if killed successfully, False if something went wrong

    PLAIN ENGLISH:
        We ask Docker to forcefully stop the container (like pulling the plug).
        We log the container ID, name, and how long it had been running.
        If something goes wrong (maybe it already stopped on its own), we
        log the error and return False instead of crashing.
    """
    container_id = container.short_id
    container_name = container.name
    age = get_container_age(container)

    try:
        container.kill()

        if PROMETHEUS_ENABLED:
            gc_containers_killed.inc()

        log.warning(
            f"KILLED  {container_id} | {container_name} | "
            f"age: {format_age(age)} | "
            f"exceeded limit of {MAX_AGE_HOURS}h"
        )
        return True

    except docker.errors.APIError as e:
        log.error(
            f"FAILED to kill {container_id} ({container_name}): {e}"
        )
        return False


def run_garbage_collection() -> dict:
    """
    Main function. Connects to Docker, scans for expired containers,
    and kills them.

    Returns:
        dict: Summary of what happened this run
    """
    log.info("=" * 55)
    log.info("Garbage Collector starting run")
    log.info(f"Max container age:  {MAX_AGE_HOURS} hours")
    log.info(f"Targeting label:    {MANAGED_LABEL}")
    log.info("=" * 55)

    results = {
        "checked":  0,
        "alive":    0,
        "expired":  0,
        "killed":   0,
        "failed":   0,
        "errors":   []
    }

    # ── Step 1: Connect to Docker ──────────────────────────────────────────
    # docker.from_env() reads Docker's connection settings from environment
    # variables, which works both locally and inside Docker containers.
    try:
        client = docker.from_env()
        client.ping()   # quick test — throws exception if Docker is down
        log.info("Connected to Docker daemon successfully")
    except docker.errors.DockerException as e:
        log.error(f"Cannot connect to Docker: {e}")
        log.error("→ Is Docker running? Try: sudo systemctl start docker")
        results["errors"].append(str(e))
        return results

    # ── Step 2: List only managed lab containers ───────────────────────────
    # We filter by:
    #   label=managed-by=lab-portal  (only our lab containers, not system ones)
    #   status=running               (only containers that are actually running)
    try:
        containers = client.containers.list(
            filters={
                "label":  MANAGED_LABEL,
                "status": "running"
            }
        )
    except docker.errors.APIError as e:
        log.error(f"Failed to list containers: {e}")
        results["errors"].append(str(e))
        return results

    results["checked"] = len(containers)

    if PROMETHEUS_ENABLED:
        gc_containers_checked.inc(len(containers))
        gc_active_containers.set(len(containers))

    if not containers:
        log.info("No managed lab containers running. Nothing to clean up.")
    else:
        log.info(f"Found {len(containers)} managed lab container(s) to check:")
        log.info("")

    # ── Step 3: Check each container ──────────────────────────────────────
    for container in containers:
        age = get_container_age(container)
        container_id = container.short_id
        name = container.name

        if is_expired(container):
            results["expired"] += 1
            log.warning(
                f"  ⚠  {container_id} | {name} | "
                f"age: {format_age(age)} → EXPIRED, killing..."
            )
            success = kill_container(container)
            if success:
                results["killed"] += 1
            else:
                results["failed"] += 1
        else:
            # Work out how much time the container has left
            remaining = timedelta(hours=MAX_AGE_HOURS) - age
            results["alive"] += 1
            log.info(
                f"  ✓  {container_id} | {name} | "
                f"age: {format_age(age)} | "
                f"{format_age(remaining)} remaining"
            )

    # ── Step 4: Print summary ──────────────────────────────────────────────
    log.info("")
    log.info("=" * 55)
    log.info("Run complete — Summary:")
    log.info(f"  Containers checked:   {results['checked']}")
    log.info(f"  Still within limit:   {results['alive']}")
    log.info(f"  Expired:              {results['expired']}")
    log.info(f"  Successfully killed:  {results['killed']}")
    log.info(f"  Failed to kill:       {results['failed']}")
    log.info("=" * 55)

    if PROMETHEUS_ENABLED:
        gc_last_run_timestamp.set(datetime.now(timezone.utc).timestamp())

    return results


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Optional: start a tiny HTTP server so Prometheus can scrape GC metrics
    # This runs on port 9101 — Grafana can then graph how many containers
    # the GC has killed over time.
    if PROMETHEUS_ENABLED:
        try:
            start_http_server(METRICS_PORT)
            log.info(
                f"Prometheus metrics server started on "
                f"http://localhost:{METRICS_PORT}/metrics"
            )
        except OSError:
            # Port already in use — not critical, skip it
            log.warning(
                f"Could not start metrics server on port {METRICS_PORT} "
                f"(port may already be in use)"
            )

    results = run_garbage_collection()

    # Exit with code 1 if any kills failed — cron monitoring can detect this
    sys.exit(1 if results["failed"] > 0 else 0)