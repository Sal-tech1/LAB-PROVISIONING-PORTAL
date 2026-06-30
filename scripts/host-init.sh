#!/bin/bash
# host-init.sh
# USAGE:
#   chmod +x host-init.sh    # make the script executable (run once)
#   sudo ./host-init.sh      # run it as admin
#
# WHAT IT INSTALLS:
#   - Docker (runs containers)
#   - Python 3.11 (backend API)
#   - Node.js 20 (frontend)
#   - PostgreSQL client tools (database)
#   - curl and git (utilities)
#


set -euo pipefail   # Stop immediately if any command fails

# ── Colours for readable output ──────────────────────────────────────────────
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Colour

log_info()    { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_success() { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Check we are running as root ─────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    log_error "Please run this script as root: sudo ./host-init.sh"
fi

echo "  Lab Provisioning Portal — Host Setup"
echo "  Member 4 (SRE) — Week 1"

# ── Step 1: Update package list ──────────────────────────────────────────────
log_info "Updating package list..."
apt-get update -qq
log_success "Package list updated"

# ── Step 2: Install basic utilities ──────────────────────────────────────────
log_info "Installing curl and git..."
apt-get install -y -qq curl git ca-certificates gnupg lsb-release
log_success "curl and git installed"

# ── Step 3: Install Docker ────────────────────────────────────────────────────
# We check if Docker is already installed before doing anything
if command -v docker &>/dev/null; then
    log_warn "Docker already installed ($(docker --version)). Skipping."
else
    log_info "Installing Docker..."

    # Add Docker's official GPG key (proves the download is genuine)
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Add Docker's repository to apt sources
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" \
        | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Start Docker and enable it to auto-start on reboot
    systemctl start docker
    systemctl enable docker

    log_success "Docker installed ($(docker --version))"
fi

# ── Step 4: Add current user to the docker group ─────────────────────────────
# This lets you run docker commands without typing sudo every time
if [[ -n "${SUDO_USER:-}" ]]; then
    if groups "$SUDO_USER" | grep -q '\bdocker\b'; then
        log_warn "User $SUDO_USER already in docker group. Skipping."
    else
        usermod -aG docker "$SUDO_USER"
        log_success "Added $SUDO_USER to docker group"
        log_warn "You will need to log out and back in for docker group to take effect"
    fi
fi

# ── Step 5: Install Python 3.11 ──────────────────────────────────────────────
if command -v python3.11 &>/dev/null; then
    log_warn "Python 3.11 already installed ($(python3.11 --version)). Skipping."
else
    log_info "Installing Python 3.11..."
    add-apt-repository -y ppa:deadsnakes/ppa > /dev/null 2>&1
    apt-get update -qq
    apt-get install -y -qq python3.11 python3.11-venv python3.11-dev python3-pip
    log_success "Python 3.11 installed ($(python3.11 --version))"
fi

# ── Step 6: Install Node.js 20 ───────────────────────────────────────────────
if command -v node &>/dev/null; then
    log_warn "Node.js already installed ($(node --version)). Skipping."
else
    log_info "Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null 2>&1
    apt-get install -y -qq nodejs
    log_success "Node.js installed ($(node --version))"
fi

# ── Step 7: Install PostgreSQL client tools ───────────────────────────────────
# We install the CLIENT tools only — the actual database runs in Docker
if command -v psql &>/dev/null; then
    log_warn "PostgreSQL client already installed. Skipping."
else
    log_info "Installing PostgreSQL client tools..."
    apt-get install -y -qq postgresql-client
    log_success "PostgreSQL client installed ($(psql --version))"
fi

# ── Step 8: Verify Docker is working ─────────────────────────────────────────
log_info "Verifying Docker works..."
if docker run --rm hello-world > /dev/null 2>&1; then
    log_success "Docker is working correctly"
else
    log_error "Docker test failed. Check the Docker installation."
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo -e "${GREEN}  Setup complete!${NC}"
echo ""
echo "Installed:"
echo "  Docker:     $(docker --version)"
echo "  Python:     $(python3.11 --version)"
echo "  Node.js:    $(node --version)"
echo "  npm:        $(npm --version)"
echo "  psql:       $(psql --version)"
echo ""
echo "Next step: run 'docker compose up' from the project root"
echo ""