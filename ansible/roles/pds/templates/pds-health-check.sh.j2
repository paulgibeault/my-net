#!/bin/bash
# pds-health-check.sh — ping /xrpc/_health and restart PDS if unhealthy.
# Deployed to /usr/local/bin/ by Ansible.

set -euo pipefail

PDS_DOMAIN="{{ pds_domain }}"   # templated by Ansible
COMPOSE_DIR="/opt/pds"
LOG_TAG="pds-health"

check_health() {
  curl --silent --max-time 10 --fail "https://${PDS_DOMAIN}/xrpc/_health" > /dev/null 2>&1
}

if check_health; then
  logger -t "$LOG_TAG" "PDS healthy."
  exit 0
fi

logger -t "$LOG_TAG" "WARNING: PDS health check failed. Restarting stack..."
cd "$COMPOSE_DIR"
docker compose restart pds

# Wait 30s and re-check
sleep 30
if check_health; then
  logger -t "$LOG_TAG" "PDS recovered after restart."
else
  logger -t "$LOG_TAG" "ERROR: PDS still unhealthy after restart. Manual intervention needed."
  # TODO: send Telegram alert via Grafana alerting or direct webhook
  exit 1
fi
