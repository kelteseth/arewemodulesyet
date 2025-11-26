from typing import Any
import subprocess
import json
import yaml
import sys
from datetime import datetime
from pathlib import Path
from termcolor import colored

GIT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S %z"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

MASTER_BRANCH = "master"
OUTPUT_FILE = Path("static") / "data" / "cumulative_stats.json"
DATA_DIR = Path("data")
GENERATED_DIR = DATA_DIR / "generated"
GENERATION_SCRIPT = Path("tools") / "merge_vcpkg_package_list_progress.py"
DATA_FILES = [
    DATA_DIR / "vcpkg_overrides.yml",
    DATA_DIR / "external_projects.yml",
    GENERATED_DIR / "vcpkg_packages.yml",
    GENERATION_SCRIPT,
]
PROGRESS_FILE = DATA_DIR / "progress.yml"


def parse_git_datetime(date_str: str) -> datetime:
    "Parse a Git date into a Python datetime"
    return datetime.strptime(date_str, GIT_DATETIME_FORMAT)


def parse_iso_datetime(date_str: str) -> datetime:
    "Parse a ISO date into a Python datetime"
    return datetime.strptime(date_str, ISO_DATETIME_FORMAT)


def git_date_to_iso(git_date_str: str) -> str:
    "Convert a git date into a ISO date (parseable by Luxon)"

    try:
        dt_object = parse_git_datetime(git_date_str)
        iso_str = dt_object.strftime(ISO_DATETIME_FORMAT)

        return iso_str

    except ValueError as e:
        print(f"Parsing error for '{git_date_str}': {e}")
        return git_date_str


def run_git_command(command: list[str]) -> str:
    """Executes a git command and returns the output string."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e.cmd}\n{e.stderr}")
        raise


def get_latest_date(filepath: Path) -> tuple[str | None, list[dict[str, int | str]]]:
    """
    Reads the existing JSON file and returns the date of the last processed
    commit (if it exist) in the format required by 'git log --since' and
    the data file itself.
    """
    if not filepath.exists():
        print("No existing data file found. Will process full history.")
        return None, []

    with open(filepath, "r") as f:
        try:
            existing_data: list[dict[str, int | str]] = json.load(f)
        except json.JSONDecodeError:
            print(f"Error decoding {filepath}. Starting fresh.")
            return None, []

    if existing_data:
        # Initialize the latest date tracker
        latest_date: datetime | None = None

        # 1. Iterate through all entries to find the maximum date
        for entry in existing_data:
            date_str = str(entry.get("commit_date", ""))
            if date_str:
                try:
                    current_date = parse_iso_datetime(date_str)

                    if latest_date is None or current_date > latest_date:
                        latest_date = current_date
                except ValueError:
                    # Handle any entries with incorrectly formatted dates
                    print(f"Skipping entry with malformed date: {date_str}")

        print(f"Latest commit date found: {latest_date}")
        return latest_date, existing_data

    return None, []


def get_commit_history(
    since_date: datetime | None = None,
) -> list[dict[str, int | str]]:
    """Gets commit SHA and author date for all commits on the main branch."""

    git_command = [
        "git",
        "log",
        "--date=iso",
        "--pretty=format:%H|%ad",
        MASTER_BRANCH,
    ]

    if since_date:
        # Add the filtering argument to the git log command
        git_command.append(
            (
                '--since="{since_date_str}"'.format(
                    since_date_str=datetime.strftime(
                        since_date,
                        GIT_DATETIME_FORMAT,
                    ),
                )
            ),
        )

    # --pretty=format:'%H|%ad' gets SHA and date, separated by a pipe
    log_output = run_git_command(git_command)

    # Process the output into a list of (sha, date) tuples
    history: list[dict[str, int | str]] = []
    for line in log_output.splitlines():
        sha, date = line.split("|", 1)

        cur_datetime = parse_git_datetime(date)
        if (not since_date) or (cur_datetime > since_date):
            history.append({"sha": sha, "date": date})

    return history


def check_git_safety() -> bool:
    """
    Check if it's safe to run git operations that modify the working tree.
    Returns True if safe, False otherwise.
    """
    # Check for uncommitted changes
    status = run_git_command(["git", "status", "--porcelain"])
    if status:
        print(colored("⚠️  WARNING: You have uncommitted changes!", "red", attrs=["bold"]))
        print(colored("This script will modify your git working tree.", "yellow"))
        print(colored("Uncommitted changes:", "yellow"))
        for line in status.splitlines()[:10]:
            print(f"  {line}")
        if len(status.splitlines()) > 10:
            print(f"  ... and {len(status.splitlines()) - 10} more")
        print()
        return False
    
    # Check current branch
    current_branch = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    print(colored(f"📍 Current branch: {current_branch}", "blue"))
    
    return True


def process_history() -> None:
    """Iterate through history and collect data."""
    
    print()
    print(colored("🔍 Computing historical completion status...", "cyan", attrs=["bold"]))
    print()
    
    # Safety check before doing anything destructive
    if not check_git_safety():
        print(colored("❌ Aborting: Please commit or stash your changes first.", "red"))
        print(colored("   Run: git stash", "yellow"))
        print(colored("   Then run this script again.", "yellow"))
        sys.exit(1)
    
    # Store current branch/commit to restore later
    original_ref = run_git_command(["git", "rev-parse", "HEAD"])
    original_branch = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    print(colored(f"📌 Will restore to: {original_branch} ({original_ref[:8]})", "blue"))
    print()

    since_date, historical_data = get_latest_date(OUTPUT_FILE)
    new_commits = get_commit_history(since_date=since_date)

    if not new_commits:
        print(colored("✅ No new commits to process.", "green"))
        return

    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    for idx, commit in enumerate(new_commits):
        print(
            colored(
                "{idx}/{tot}".format(idx=idx + 1, tot=len(new_commits)),
                "cyan",
            )
            + " Processing commit {sha} ({date})…".format(
                sha=commit["sha"][:8],
                date=commit["date"],
            ),
        )

        try:
            # 1. Temporarily checkout the necessary files for this commit
            checkout_command = [
                "git",
                "checkout",
                str(commit["sha"]),
                "--",
            ] + [str(x) for x in DATA_FILES]
            _ = run_git_command(checkout_command)

            # 2. Run the original generation script
            # Note: This assumes the script generates data/progress.yml
            if GENERATION_SCRIPT.exists():
                # Suppress output of the sub-script
                _ = subprocess.run(
                    ["python3", str(GENERATION_SCRIPT)],
                    check=True,
                    capture_output=True,
                )

                # 3. Extract the required values from the generated file
                if PROGRESS_FILE.exists():
                    with PROGRESS_FILE.open("rt") as f:
                        progress_data: dict[str, Any] = yaml.safe_load(f)

                    items = progress_data["ports"]

                    # Extract values
                    completed = len([x for x in items if x["status"] == "✅"])
                    total = len(items)

                    # Store the data point
                    historical_data.append(
                        {
                            "commit_date": git_date_to_iso(commit["date"]),
                            "completed": completed,
                            "total": total,
                        }
                    )

        except Exception as e:
            # Continue to the next commit even if one fails
            print(f"Skipping commit {commit['sha']} due to error: {e}")

        finally:
            # 4. Clean up (remove generated file and reset checked-out files)
            if PROGRESS_FILE.exists():
                PROGRESS_FILE.unlink()

            # Restore the original state of the checked-out files
            restore_command = ["git", "checkout", "HEAD", "--"] + [
                str(x) for x in DATA_FILES
            ]
            _ = run_git_command(restore_command)

    # Restore to original branch/commit
    print()
    print(colored(f"🔄 Restoring to original state: {original_branch}...", "blue"))
    _ = run_git_command(["git", "checkout", original_branch])
    _ = run_git_command(["git", "reset", "--hard", original_ref])
    print(colored("✅ Repository restored successfully.", "green"))

    # Reverse the history to plot chronologically (oldest commit first)
    historical_data.reverse()

    # 5. Write the final JSON array
    with OUTPUT_FILE.open("wt") as f:
        json.dump(historical_data, f, indent=4)

    print()
    print(colored(f"📊 {len(historical_data)} data points written to {OUTPUT_FILE}", "green", attrs=["bold"]))


if __name__ == "__main__":
    process_history()
