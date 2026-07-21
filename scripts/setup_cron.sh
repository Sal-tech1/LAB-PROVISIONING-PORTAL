#!/bin/bash
# =============================================================================
# setup_cron.sh
# Member 4 (SRE) — Week 4 Task 1
#
# PURPOSE:
#   Automatically installs the garbage collector as a cron job so it
#   runs every 15 minutes without you having to do anything.
#
# WHAT IS CRON?
#   Cron is Linux's built-in task scheduler — like Windows Task Scheduler
#   but for the terminal. You write a "cron job" which is just one line
#   that says: "run THIS command at THESE times."
#
#   The format of a cron line:
#   ┌─── minute (0-59)
#   │  ┌── hour (0-23)
#   │  │  ┌─ day of month (1-31)
#   │  │  │  ┌── month (1-12)
#   │  │  │  │  ┌─ day of week (0-7, where 0 and 7 = Sunday)
#   │  │  │  │  │
#   */15 * * * *   python3 /path/to/garbage_collector.py
#   └─────────────── "every 15 minutes, every hour, every day"
#
# USAGE:
#   chmod +x setup_cron.sh
#   ./setup_cron.sh
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC}    $1"; }
info() { echo -e "${BLUE}[INFO]${NC}  $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo "====================================="
echo "  Setting up Garbage Collector Cron"
echo "  Member 4 (SRE) — Week 4"
echo "====================================="
echo ""

# ── Step 1: Find where garbage_collector.py actually is ───────────────────────
# We look in the same directory as this script first, then /scripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GC_PATH="$SCRIPT_DIR/garbage_collector.py"

if [[ ! -f "$GC_PATH" ]]; then
    err "Cannot find garbage_collector.py at $GC_PATH — make sure both scripts are in the same folder"
fi

info "Found garbage_collector.py at: $GC_PATH"

# ── Step 2: Find Python 3 ─────────────────────────────────────────────────────
if command -v python3.11 &>/dev/null; then
    PYTHON_BIN=$(command -v python3.11)
elif command -v python3 &>/dev/null; then
    PYTHON_BIN=$(command -v python3)
else
    err "Python 3 not found — run host-init.sh first"
fi

info "Using Python at: $PYTHON_BIN ($($PYTHON_BIN --version))"

# ── Step 3: Set up log file ───────────────────────────────────────────────────
LOG_FILE="/var/log/lab-gc.log"

# Create the log file if it doesn't exist
if [[ ! -f "$LOG_FILE" ]]; then
    sudo touch "$LOG_FILE"
    sudo chmod 666 "$LOG_FILE"
    ok "Created log file: $LOG_FILE"
else
    info "Log file already exists: $LOG_FILE"
fi

# ── Step 4: Build the cron line ───────────────────────────────────────────────
# This tells cron:
#   */15 * * * *    = run every 15 minutes
#   >> /var/log/lab-gc.log 2>&1   = save all output (including errors) to log file
CRON_LINE="*/15 * * * * $PYTHON_BIN $GC_PATH >> $LOG_FILE 2>&1"
CRON_COMMENT="# Lab Portal — Garbage Collector (added by setup_cron.sh)"

info "Cron line that will be installed:"
echo "    $CRON_LINE"
echo ""

# ── Step 5: Check if the cron job already exists ──────────────────────────────
# crontab -l lists existing cron jobs
# We grep for our script path to see if it's already there
if crontab -l 2>/dev/null | grep -q "$GC_PATH"; then
    warn "Cron job for garbage_collector.py already exists — skipping to avoid duplicates"
    warn "Current crontab:"
    crontab -l 2>/dev/null | grep "$GC_PATH"
else
    # ── Step 6: Add the cron job ──────────────────────────────────────────
    # We do this by:
    # 1. Dumping the current crontab to a temp file
    # 2. Adding our new line to that file
    # 3. Loading the modified file back as the new crontab
    TEMP_CRON=$(mktemp)
    crontab -l 2>/dev/null > "$TEMP_CRON" || true    # existing jobs (ignore error if empty)
    echo ""                          >> "$TEMP_CRON"  # blank line for readability
    echo "$CRON_COMMENT"             >> "$TEMP_CRON"  # descriptive comment
    echo "$CRON_LINE"                >> "$TEMP_CRON"  # the actual job
    crontab "$TEMP_CRON"                              # install it
    rm "$TEMP_CRON"                                   # clean up temp file

    ok "Cron job installed successfully"
fi

# ── Step 7: Verify it was installed ───────────────────────────────────────────
echo ""
info "Current crontab (all jobs):"
crontab -l 2>/dev/null || echo "(empty)"
echo ""

# ── Step 8: Test run the GC right now ─────────────────────────────────────────
echo ""
info "Running garbage_collector.py once right now to verify it works..."
echo ""
if $PYTHON_BIN "$GC_PATH"; then
    ok "Garbage collector ran successfully"
else
    # Exit code 1 means some containers failed to kill — not necessarily
    # a setup problem, so we warn rather than error
    warn "Garbage collector exited with code 1 — check the output above"
    warn "This may be normal if some containers couldn't be killed"
fi

echo ""
echo "====================================="
echo -e "${GREEN}  Cron setup complete!${NC}"
echo "====================================="
echo ""
echo "The garbage collector will now run every 15 minutes."
echo ""
echo "To watch the log live:"
echo "  tail -f $LOG_FILE"
echo ""
echo "To check your cron jobs:"
echo "  crontab -l"
echo ""
echo "To remove the cron job:"
echo "  crontab -e    (then delete the garbage_collector line)"
echo ""