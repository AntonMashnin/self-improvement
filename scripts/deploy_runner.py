"""
Deploys an ephemeral Hetzner VPS that:
  1. Connects to Tailscale (no public SSH access)
  2. Registers itself as a uniquely-labelled ephemeral GitHub Actions runner
  3. Runs one job, then exits and shuts down

Outputs server_id, runner_name, runner_label to GITHUB_OUTPUT so the
workflow can target the exact runner and clean up the exact server.
"""
import os
import sys
import time

import requests

HETZNER_TOKEN = os.environ["HETZNER_TOKEN"]
TAILSCALE_AUTH_KEY = os.environ["TAILSCALE_AUTH_KEY"]
RUNNER_TOKEN = os.environ["RUNNER_TOKEN"]
REPO = os.environ["REPO"]  # e.g. "AntonMashnin/self-improvement"

HETZNER_API = "https://api.hetzner.cloud/v1"
IMAGE = os.environ.get("HETZNER_IMAGE", "ubuntu-22.04")

PREFERRED_SERVER_TYPES = os.environ.get(
    "HETZNER_SERVER_TYPES", "cpx12,cx22,cpx22,cx32"
).split(",")

PREFERRED_LOCATIONS = ["nbg1", "fsn1", "hel1", "ash", "hil", "sin"]

# VPS self-destructs after this many minutes even if job never arrives
FAILSAFE_SHUTDOWN_MINUTES = 60


def hetzner_get(path: str) -> dict:
    resp = requests.get(
        f"{HETZNER_API}{path}",
        headers={"Authorization": f"Bearer {HETZNER_TOKEN}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def discover(preferred_types: list[str], preferred_locations: list[str]) -> tuple[str, str]:
    """Return (server_type, location) — first combo available via Hetzner API."""
    all_types = hetzner_get("/server_types")["server_types"]
    type_map = {s["name"]: s for s in all_types}

    for server_type in preferred_types:
        if server_type not in type_map:
            print(f"  {server_type}: unknown, skipping.")
            continue

        available_locations = {
            price["location"]
            for price in type_map[server_type].get("prices", [])
            if price.get("location")
        }

        for loc in preferred_locations:
            if loc in available_locations:
                print(f"Selected: {server_type} in {loc} (available: {sorted(available_locations)})")
                return server_type, loc

        print(f"  {server_type}: not in preferred locations (available: {sorted(available_locations)}), skipping.")

    raise RuntimeError(
        f"None of {preferred_types} are available in preferred locations {preferred_locations}."
    )


def build_cloud_init(runner_name: str, runner_label: str, server_type: str, location: str) -> str:
    return f"""#!/bin/bash
set -euo pipefail
exec > /var/log/runner-setup.log 2>&1

echo "=== Starting runner setup at $(date) ==="

# Failsafe: power off after N minutes even if job never arrives
( sleep {FAILSAFE_SHUTDOWN_MINUTES}m && poweroff ) &

apt-get update -q
apt-get install -y -q curl jq git

# Tailscale — no public SSH, access only via tailnet
# Non-fatal: runner communicates with GitHub directly, not through Tailscale
curl -fsSL https://tailscale.com/install.sh | sh || echo "WARNING: Tailscale install failed"
tailscale up --authkey={TAILSCALE_AUTH_KEY} --ephemeral --hostname={runner_name} || echo "WARNING: Tailscale up failed"

# Create non-root user (GitHub Actions runner refuses to run as root)
useradd -m -s /bin/bash github-runner || true

# Install GitHub Actions runner — version resolved at runtime
RUNNER_VERSION=$(curl -fsSL https://api.github.com/repos/actions/runner/releases/latest \
  | jq -r '.tag_name' | sed 's/v//')
echo "Installing runner v${{RUNNER_VERSION}}..."
mkdir -p /home/github-runner/actions-runner
cd /home/github-runner/actions-runner
curl -fsSL -o runner.tar.gz \
  "https://github.com/actions/runner/releases/download/v${{RUNNER_VERSION}}/actions-runner-linux-x64-${{RUNNER_VERSION}}.tar.gz"
tar xzf runner.tar.gz
rm runner.tar.gz
chown -R github-runner:github-runner /home/github-runner

echo "Registering runner '{runner_name}' label='{runner_label}'..."
sudo -u github-runner ./config.sh \
  --url "https://github.com/{REPO}" \
  --token "{RUNNER_TOKEN}" \
  --name "{runner_name}" \
  --labels "hetzner,{runner_label},{server_type},{location}" \
  --ephemeral \
  --unattended

echo "Starting runner..."
sudo -u github-runner ./run.sh

echo "=== Runner done at $(date). Powering off. ==="
poweroff
"""


def create_server(server_type: str, location: str, runner_name: str, runner_label: str) -> int:
    resp = requests.post(
        f"{HETZNER_API}/servers",
        headers={
            "Authorization": f"Bearer {HETZNER_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "name": runner_name,
            "server_type": server_type,
            "image": IMAGE,
            "location": location,
            "user_data": build_cloud_init(runner_name, runner_label, server_type, location),
            "labels": {
                "purpose": "github-runner",
                "runner_label": runner_label,
            },
        },
        timeout=30,
    )

    if not resp.ok:
        print(f"ERROR creating server: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)

    server_id: int = resp.json()["server"]["id"]
    print(f"Created server '{runner_name}' (id={server_id}, type={server_type}, location={location})")
    return server_id


def write_github_output(**kwargs: str | int) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT", "")
    lines = [f"{k}={v}\n" for k, v in kwargs.items()]
    if output_file:
        with open(output_file, "a") as f:
            f.writelines(lines)
    else:
        print("".join(lines), end="")


def main() -> None:
    suffix = str(int(time.time()))
    runner_name = f"hetzner-{suffix}"
    runner_label = f"run-{suffix}"

    print(f"Runner name:  {runner_name}")
    print(f"Runner label: {runner_label}")

    server_type, location = discover(PREFERRED_SERVER_TYPES, PREFERRED_LOCATIONS)
    server_id = create_server(server_type, location, runner_name, runner_label)

    write_github_output(
        server_id=server_id,
        runner_name=runner_name,
        runner_label=runner_label,
    )

    print("VPS created. Polling starts in the next workflow step.")


if __name__ == "__main__":
    main()
