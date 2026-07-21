import docker
from datetime import datetime, timezone
import time

def run_garbage_collector(max_uptime_hours=2):
    print(f"Starting garbage collection. Scanning for labs older than {max_uptime_hours} hours...")
    
    try:
        client = docker.from_env()
    except docker.errors.DockerException as e:
        print(f"CRITICAL ERROR: Could not connect to Docker. {e}")
        return

    # 1. Fetch only the containers we care about
    student_labs = client.containers.list(all=True, filters={"label": "type=student-lab"})
    
    if not student_labs:
        print("No active student labs found. Server is clean.")
        return

    current_time = datetime.now(timezone.utc)
    removed_count = 0

    for container in student_labs:
        try:
            # 2. Extract and format the Docker creation timestamp
            # Docker returns time in a format like '2026-07-21T10:30:00.123456789Z'
            time_string = container.attrs['Created'][:19]
            created_time = datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S")
            created_time = created_time.replace(tzinfo=timezone.utc)
            
            # 3. Calculate total uptime
            uptime = current_time - created_time
            uptime_hours = uptime.total_seconds() / 3600

            # 4. Terminate if it exceeds the limit
            if uptime_hours > max_uptime_hours:
                print(f"Terminating container {container.short_id} (Uptime: {uptime_hours:.2f}h)...")
                # Force=True ensures it stops and removes even if it is hanging
                container.remove(force=True) 
                removed_count += 1
            else:
                print(f"Container {container.short_id} is safe (Uptime: {uptime_hours:.2f}h).")

        except Exception as e:
            print(f"Error processing container {container.short_id}: {e}")

    print(f"Garbage collection complete. Purged {removed_count} idle environments.")

# A loop to run the collector continuously every 30 minutes
if __name__ == "__main__":
    print("Garbage Collector Daemon started. Press Ctrl+C to exit.")
    try:
        while True:
            run_garbage_collector(max_uptime_hours=2)
            print("Sleeping for 30 minutes...\n")
            time.sleep(1800) 
    except KeyboardInterrupt:
        print("\nGarbage Collector stopped.")
