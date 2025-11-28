#!/bin/bash
#
# Baby Monitor Deployment Script
# Deploys the baby monitor to Raspberry Pi Zero 2 W
#

set -e

# Configuration
PI_HOST="${PI_HOST:-raspberrypi-zero}"
PI_USER="${PI_USER:-pi}"
REMOTE_DIR="/home/${PI_USER}/baby-monitor"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check SSH connection
check_connection() {
    log_info "Checking connection to ${PI_HOST}..."
    if ! ssh -o ConnectTimeout=5 "${PI_HOST}" "echo 'Connected'" > /dev/null 2>&1; then
        log_error "Cannot connect to ${PI_HOST}"
        log_info "Make sure the Pi is powered on and SSH is enabled"
        exit 1
    fi
    log_success "Connected to ${PI_HOST}"
}

# Install MediaMTX if not present
install_mediamtx() {
    log_info "Checking MediaMTX installation..."

    if ssh "${PI_HOST}" "test -f /usr/local/bin/mediamtx"; then
        log_success "MediaMTX already installed"
        return
    fi

    log_info "Installing MediaMTX..."

    # Determine architecture
    ARCH=$(ssh "${PI_HOST}" "uname -m")
    log_info "Detected architecture: ${ARCH}"

    # Pi Zero 2 W is ARM64 capable but may run 32-bit OS
    if [[ "$ARCH" == "aarch64" ]]; then
        MEDIAMTX_ARCH="linux_arm64v8"
    else
        MEDIAMTX_ARCH="linux_armv7"
    fi

    MEDIAMTX_VERSION="v1.9.3"
    MEDIAMTX_URL="https://github.com/bluenviron/mediamtx/releases/download/${MEDIAMTX_VERSION}/mediamtx_${MEDIAMTX_VERSION}_${MEDIAMTX_ARCH}.tar.gz"

    ssh "${PI_HOST}" "
        cd /tmp
        wget -q '${MEDIAMTX_URL}' -O mediamtx.tar.gz
        tar -xzf mediamtx.tar.gz mediamtx
        sudo mv mediamtx /usr/local/bin/
        sudo chmod +x /usr/local/bin/mediamtx
        rm mediamtx.tar.gz
    "

    log_success "MediaMTX installed"
}

# Create directory structure on Pi
create_directories() {
    log_info "Creating directory structure on Pi..."

    ssh "${PI_HOST}" "
        mkdir -p ${REMOTE_DIR}/{config,services,scripts,web}
    "

    log_success "Directories created"
}

# Deploy files
deploy_files() {
    log_info "Deploying files to Pi..."

    # Copy all files from pi/ directory
    rsync -avz --progress \
        "${PROJECT_DIR}/pi/" \
        "${PI_HOST}:${REMOTE_DIR}/"

    # Make scripts executable
    ssh "${PI_HOST}" "chmod +x ${REMOTE_DIR}/scripts/*.py 2>/dev/null || true"

    log_success "Files deployed"
}

# Clean up old services that are no longer needed
cleanup_old_services() {
    log_info "Cleaning up old services..."

    ssh "${PI_HOST}" "
        # Stop and disable old camera service if exists
        sudo systemctl stop baby-monitor-camera.service 2>/dev/null || true
        sudo systemctl disable baby-monitor-camera.service 2>/dev/null || true
        sudo rm -f /etc/systemd/system/baby-monitor-camera.service
        sudo systemctl daemon-reload
    " 2>/dev/null || true

    log_success "Cleanup complete"
}

# Install systemd services
install_services() {
    log_info "Installing systemd services..."

    ssh "${PI_HOST}" "
        # Copy only the services we need
        sudo cp ${REMOTE_DIR}/services/baby-monitor.service /etc/systemd/system/
        sudo cp ${REMOTE_DIR}/services/baby-monitor-api.service /etc/systemd/system/

        # Reload systemd
        sudo systemctl daemon-reload

        # Enable services
        sudo systemctl enable baby-monitor.service
        sudo systemctl enable baby-monitor-api.service
    "

    log_success "Services installed and enabled"
}

# Start or restart services
start_services() {
    log_info "Starting services..."

    ssh "${PI_HOST}" "
        # Stop existing services first
        sudo systemctl stop baby-monitor-api.service 2>/dev/null || true
        sudo systemctl stop baby-monitor.service 2>/dev/null || true

        # Start services
        sudo systemctl start baby-monitor.service
        sleep 3
        sudo systemctl start baby-monitor-api.service
    "

    log_success "Services started"
}

# Check service status
check_status() {
    log_info "Checking service status..."

    echo ""
    echo "=== Service Status ==="

    for service in baby-monitor baby-monitor-api; do
        status=$(ssh "${PI_HOST}" "systemctl is-active ${service}.service 2>/dev/null || echo 'inactive'")
        if [[ "$status" == "active" ]]; then
            echo -e "  ${GREEN}✓${NC} ${service}: ${status}"
        else
            echo -e "  ${RED}✗${NC} ${service}: ${status}"
        fi
    done

    echo ""
}

# Get Pi IP address
get_pi_ip() {
    PI_IP=$(ssh "${PI_HOST}" "hostname -I | awk '{print \$1}'")
    echo "$PI_IP"
}

# Main deployment
main() {
    echo ""
    echo "=========================================="
    echo "  Baby Monitor Deployment"
    echo "=========================================="
    echo ""

    check_connection
    install_mediamtx
    create_directories
    deploy_files
    cleanup_old_services
    install_services
    start_services

    echo ""
    sleep 3
    check_status

    PI_IP=$(get_pi_ip)

    echo ""
    echo "=========================================="
    echo "  Deployment Complete!"
    echo "=========================================="
    echo ""
    echo "Access your baby monitor at:"
    echo ""
    echo -e "  ${GREEN}Web Interface:${NC} http://${PI_IP}:8889/baby-monitor/"
    echo -e "  ${GREEN}Control API:${NC}   http://${PI_IP}:5000/api/status"
    echo ""
    echo "Troubleshooting:"
    echo "  View logs:  ssh ${PI_HOST} 'journalctl -u baby-monitor -f'"
    echo "  Restart:    ssh ${PI_HOST} 'sudo systemctl restart baby-monitor'"
    echo ""
}

# Run main function
main "$@"
