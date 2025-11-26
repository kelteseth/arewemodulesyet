"""
Compute completion status for the historical chart.

This script:
1. Loads frozen historical data from data/historical_stats.json (old file structure)
2. Traverses git history on master branch for new commits
3. For each commit, reads data files directly with git show (no checkout)
4. Merges the YAML data in memory and counts completed projects
5. Outputs to static/data/cumulative_stats.json

No working tree modifications - safe to run with uncommitted changes.
"""

import json
import subprocess
from datetime import datetime
from io import StringIO
from pathlib import Path

import yaml
from termcolor import colored

# Git/date formats
GIT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S %z"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

# File paths
DATA_DIR = Path("data")
GENERATED_DIR = DATA_DIR / "generated"
HISTORICAL_FILE = DATA_DIR / "historical_stats.json"
OUTPUT_FILE = Path("static") / "data" / "cumulative_stats.json"

# Data files to read from git (new structure only)
VCPKG_PACKAGES = GENERATED_DIR / "vcpkg_packages.yml"
VCPKG_OVERRIDES = DATA_DIR / "vcpkg_overrides.yml"
EXTERNAL_PROJECTS = DATA_DIR / "external_projects.yml"

MASTER_BRANCH = "master"


def run_git(args: list[str], silent: bool = False) -> str:
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if not silent:
            print(colored(f"Git error: {e.stderr.strip()}", "red"))
        raise


def git_show(sha: str, filepath: Path) -> str | None:
    """Read file contents from a specific commit without checkout."""
    try:
        return run_git(["show", f"{sha}:{filepath.as_posix()}"], silent=True)
    except subprocess.CalledProcessError:
        return None


def parse_git_date(date_str: str) -> datetime:
    """Parse git date format."""
    return datetime.strptime(date_str, GIT_DATETIME_FORMAT)


def to_iso_date(date_str: str) -> str:
    """Convert git date to ISO format."""
    dt = parse_git_date(date_str)
    return dt.strftime(ISO_DATETIME_FORMAT)


def parse_iso_date(date_str: str) -> datetime:
    """Parse ISO date format."""
    return datetime.strptime(date_str, ISO_DATETIME_FORMAT)


def load_historical_data() -> list[dict]:
    """Load frozen historical data from old file structure."""
    if not HISTORICAL_FILE.exists():
        print(colored(f"⚠️  No historical data at {HISTORICAL_FILE}", "yellow"))
        return []
    
    with HISTORICAL_FILE.open("r") as f:
        data = json.load(f)
    print(colored(f"📜 Loaded {len(data)} historical data points", "blue"))
    return data


def get_latest_date(data: list[dict]) -> datetime | None:
    """Find the most recent date in the data."""
    if not data:
        return None
    
    latest = None
    for entry in data:
        try:
            dt = parse_iso_date(entry["commit_date"])
            if latest is None or dt > latest:
                latest = dt
        except (ValueError, KeyError):
            pass
    return latest


def get_commits_since(since_date: datetime | None) -> list[dict]:
    """Get commits on master since a date."""
    args = ["log", "--date=iso", "--pretty=format:%H|%ad", MASTER_BRANCH]
    if since_date:
        args.append(f'--since="{since_date.strftime(GIT_DATETIME_FORMAT)}"')
    
    output = run_git(args)
    if not output:
        return []
    
    commits = []
    for line in output.splitlines():
        sha, date = line.split("|", 1)
        commit_dt = parse_git_date(date)
        # Only include if strictly after since_date
        if since_date is None or commit_dt > since_date:
            commits.append({"sha": sha, "date": date})
    
    return commits


def merge_yaml_data(vcpkg_packages: str, vcpkg_overrides: str | None, external_projects: str | None) -> tuple[int, int]:
    """
    Merge YAML data in memory (mimics merge_vcpkg_package_list_progress.py logic).
    Returns (completed, total).
    """
    # Parse vcpkg packages
    packages = yaml.safe_load(StringIO(vcpkg_packages))
    ports = {p["name"]: p for p in packages.get("ports", [])}
    
    # Apply overrides
    if vcpkg_overrides:
        overrides = yaml.safe_load(StringIO(vcpkg_overrides))
        for override in overrides.get("ports", []):
            name = override["name"]
            if name in ports:
                ports[name].update(override)
    
    # Add external projects
    if external_projects:
        external = yaml.safe_load(StringIO(external_projects))
        for project in external.get("ports", []):
            ports[project["name"]] = project
    
    # Count
    total = len(ports)
    completed = len([p for p in ports.values() if p.get("status") == "✅"])
    
    return completed, total


def process_commit(sha: str, date: str) -> dict | None:
    """Process a single commit and return stats using git show (no checkout)."""
    # Read vcpkg_packages (required)
    vcpkg_packages = git_show(sha, VCPKG_PACKAGES)
    if not vcpkg_packages:
        return None
    
    # Read optional files
    vcpkg_overrides = git_show(sha, VCPKG_OVERRIDES)
    external_projects = git_show(sha, EXTERNAL_PROJECTS)
    
    try:
        completed, total = merge_yaml_data(vcpkg_packages, vcpkg_overrides, external_projects)
        return {
            "commit_date": to_iso_date(date),
            "completed": completed,
            "total": total,
        }
    except Exception:
        return None


def get_current_stats() -> dict | None:
    """Read current stats from local progress.yml file."""
    progress_file = DATA_DIR / "progress.yml"
    if not progress_file.exists():
        return None
    
    with progress_file.open("r") as f:
        progress = yaml.safe_load(f)
    
    ports = progress.get("ports", [])
    completed = len([p for p in ports if p.get("status") == "✅"])
    total = len(ports)
    
    # Use current time
    from datetime import timezone
    now = datetime.now(timezone.utc).astimezone()
    
    return {
        "commit_date": now.strftime(ISO_DATETIME_FORMAT),
        "completed": completed,
        "total": total,
    }


def main() -> None:
    print()
    print(colored("📊 Computing historical completion status...", "cyan", attrs=["bold"]))
    print()
    
    # Load historical data
    historical = load_historical_data()
    latest_date = get_latest_date(historical)
    
    if latest_date:
        print(colored(f"📅 Latest data point: {latest_date.date()}", "blue"))
    
    # Get new commits from master
    commits = get_commits_since(latest_date)
    new_data = []
    
    if not commits:
        print(colored("ℹ️  No new commits on master.", "blue"))
    else:
        print(colored(f"🔍 Processing {len(commits)} commits from master...", "cyan"))
        print()
        
        for idx, commit in enumerate(commits):
            print(
                colored(f"{idx + 1}/{len(commits)}", "cyan") +
                f" {commit['sha'][:8]} ({commit['date'][:10]})...",
                end=" "
            )
            
            stats = process_commit(commit["sha"], commit["date"])
            if stats:
                new_data.append(stats)
                print(colored(f"✓ {stats['completed']}/{stats['total']}", "green"))
            else:
                print(colored("skipped", "yellow"))
    
    # Also add current local state (from progress.yml)
    current = get_current_stats()
    if current:
        # Check if we should add it (different from last entry)
        merged_so_far = historical + new_data
        last_entry = merged_so_far[-1] if merged_so_far else None
        
        if (not last_entry or 
            last_entry.get("completed") != current["completed"] or
            last_entry.get("total") != current["total"]):
            new_data.append(current)
            print(colored(f"📍 Added current state: {current['completed']}/{current['total']}", "green"))
        else:
            print(colored("ℹ️  Current state unchanged from last entry.", "blue"))
    
    # Merge and sort by date
    merged = historical + new_data
    merged.sort(key=lambda x: x.get("commit_date", ""))
    
    # Write output
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with OUTPUT_FILE.open("w") as f:
        json.dump(merged, f, indent=4)
    
    print()
    print(colored("✅ Done!", "green"))
    print(colored(f"📊 {len(merged)} data points written to {OUTPUT_FILE}", "green", attrs=["bold"]))
    if new_data:
        print(colored(f"   (+{len(new_data)} new)", "cyan"))


if __name__ == "__main__":
    main()
