#!/usr/bin/env python3

from typing import Any
import subprocess
import json
import os
import yaml
import datetime
from pathlib import Path

MASTER_BRANCH = "master"
OUTPUT_FILE = Path("static") / "data" / "cumulative_stats.json"
DATA_DIR = Path("data")
GENERATION_SCRIPT = Path("generate_vcpkg_usage_stats.py")
DATA_FILES = [
    DATA_DIR / "progress_overwrite.yml",
    DATA_DIR / "raw_progress.yml",
    GENERATION_SCRIPT,
]
PROGRESS_FILE = DATA_DIR / "progress.yml"


def git_date_to_iso(git_date_str: str) -> str:
    "Convert a git date into a ISO date (parseable by Luxon)"

    input_format = "%Y-%m-%d %H:%M:%S %z"
    output_format = "%Y-%m-%dT%H:%M:%S%z"

    try:
        # 1. Analizza la stringa di input nella struttura datetime
        dt_object = datetime.datetime.strptime(git_date_str, input_format)

        # 2. Riformatta l'oggetto datetime nel formato ISO 8601 corretto
        iso_str = dt_object.strftime(output_format)

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


def parse_datetime(date_str: str) -> datetime.datetime:
    "Parse a Git ISO date into a Python datetime"
    return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %z")


def get_latest_date(filepath: Path) -> tuple[str | None, list[dict[str, int | str]]]:
    """
    Reads the existing JSON file and returns the date of the last processed
    commit (if it exist) in the ISO format required by 'git log --since' and
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
        latest_date = None
        latest_date_string = None

        # 1. Iterate through all entries to find the maximum date
        for entry in existing_data:
            date_str = str(entry.get("commit_date", ""))
            if date_str:
                # Use datetime.datetime.strptime with the specific format
                # The format string %Y-%m-%d %H:%M:%S %z matches the
                # "2025-11-05 21:38:28 -0700" style.
                try:
                    current_date = parse_datetime(date_str)

                    if latest_date is None or current_date > latest_date:
                        latest_date = current_date
                        latest_date_string = date_str  # Keep the original format
                except ValueError:
                    # Handle any entries with incorrectly formatted dates
                    print(f"Skipping entry with malformed date: {date_str}")

        # Git log --since expects a date format like "YYYY-MM-DD HH:MM:SS TZ"
        # We return the exact string, and the existing data list.
        print(f"Latest commit date found: {latest_date_string}")
        return latest_date_string, existing_data

    return None, []


def get_commit_history(since_date_str: str | None = None) -> list[dict[str, int | str]]:
    """Gets commit SHA and author date for all commits on the main branch."""

    git_command = [
        "git",
        "log",
        "--date=iso",
        "--pretty=format:%H|%ad",
        MASTER_BRANCH,
    ]

    since_date: datetime.datetime | None = None
    if since_date_str:
        # Add the filtering argument to the git log command
        git_command.append(f'--since="{since_date_str}"')
        since_date = parse_datetime(since_date_str)

    # --pretty=format:'%H|%ad' gets SHA and date, separated by a pipe
    log_output = run_git_command(git_command)

    # Process the output into a list of (sha, date) tuples
    history: list[dict[str, int | str]] = []
    for line in log_output.splitlines():
        sha, date = line.split("|", 1)

        cur_datetime = parse_datetime(date)
        if (not since_date) or (cur_datetime > since_date):
            history.append({"sha": sha, "date": date})

    return history


def process_history() -> None:
    """Iterate through history and collect data."""

    # 1. Get the last recorded date and existing data (Optimized step)
    since_date, historical_data = get_latest_date(OUTPUT_FILE)

    # 2. Get history, only including commits newer than the last recorded one
    new_commits = get_commit_history(since_date_str=since_date)

    # Create the output directory if it doesn't exist
    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    # Use git reset --hard to ensure a clean state before starting
    _ = run_git_command(["git", "reset", "--hard", MASTER_BRANCH])

    for idx, commit in enumerate(new_commits):
        print(
            "{idx}/{tot} Processing commit {sha} ({date})…".format(
                idx=idx + 1,
                tot=len(new_commits),
                sha=commit["sha"],
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
                    ["python3", str(GENERATION_SCRIPT), "--merge"],
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

    # Final cleanup to ensure repo is on main branch state
    _ = run_git_command(["git", "reset", "--hard", MASTER_BRANCH])

    # Reverse the history to plot chronologically (oldest commit first)
    historical_data.reverse()

    # 5. Write the final JSON array
    with OUTPUT_FILE.open("wt") as f:
        json.dump(historical_data, f, indent=4)

    print(f"\n{len(historical_data)} data points in {OUTPUT_FILE}")


if __name__ == "__main__":
    process_history()
