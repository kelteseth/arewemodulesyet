import argparse
import json
import os
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

import yaml
from termcolor import colored


GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GITHUB_REPOSITORY_URL = "https://github.com/{repository}"
GITHUB_REST_REPOSITORY_URL = "https://api.github.com/repos/{repository}"
ECOSYSTEMS_REPOSITORY_URL = (
    "https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/{repository}"
)


def tls_context():
    """Use the system CA bundle with standalone Python distributions."""
    configured_bundle = os.environ.get("SSL_CERT_FILE")
    candidates = [
        configured_bundle,
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return ssl.create_default_context(cafile=candidate)
    return ssl.create_default_context()


TLS_CONTEXT = tls_context()


def normalize_github_repository(value):
    """Return a normalized owner/repository pair, or None for non-GitHub input."""
    if not isinstance(value, str) or not value.strip():
        return None

    value = value.strip()
    if "://" not in value:
        parts = value.strip("/").split("/")
    else:
        parsed = urlparse(value)
        if parsed.hostname not in {"github.com", "www.github.com"}:
            return None
        parts = [part for part in parsed.path.split("/") if part]

    if len(parts) < 2:
        return None

    owner, repository = parts[:2]
    if repository.endswith(".git"):
        repository = repository[:-4]
    if not owner or not repository:
        return None
    return f"{owner}/{repository}".lower()


def repository_for_project(project, override=None):
    """Resolve a project's GitHub repository, honoring a manual override."""
    override = override or {}
    candidates = (
        override.get("github_repository"),
        project.get("github_repository"),
        override.get("homepage"),
        project.get("homepage"),
        override.get("tracking_issue"),
        project.get("tracking_issue"),
    )
    for candidate in candidates:
        repository = normalize_github_repository(candidate)
        if repository:
            return repository
    return None


def discover_repositories(vcpkg_packages, vcpkg_overrides, external_projects):
    """Collect the unique GitHub repositories referenced by all project sources."""
    overrides = {
        item["name"]: item
        for item in vcpkg_overrides.get("ports", [])
        if item.get("name")
    }
    repositories = set()

    for project in vcpkg_packages.get("ports", []):
        repository = repository_for_project(project, overrides.get(project.get("name")))
        if repository:
            repositories.add(repository)

    for project in external_projects.get("projects", []):
        repository = repository_for_project(project)
        if repository:
            repositories.add(repository)

    return sorted(repositories)


def load_yaml(path):
    with path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}


def load_cached_stars(path):
    if not path.exists():
        return {}
    repositories = load_yaml(path).get("repositories", {})
    return {
        repository.lower(): int(stars)
        for repository, stars in repositories.items()
        if isinstance(stars, int) and stars >= 0
    }


def github_http_error_message(error):
    """Extract a safe GitHub API error without exposing request credentials."""
    message = getattr(error, "reason", "request rejected")
    try:
        payload = json.loads(error.read().decode("utf-8", errors="replace"))
        if isinstance(payload, dict) and payload.get("message"):
            message = payload["message"]
    except (OSError, ValueError, AttributeError):
        pass
    return f"HTTP {error.code}: {message}"


def github_graphql_request(repositories, token, timeout):
    fields = []
    for index, repository in enumerate(repositories):
        owner, name = repository.split("/", 1)
        fields.append(
            f"r{index}: repository(owner: {json.dumps(owner)}, "
            f"name: {json.dumps(name)}) {{ stargazerCount }}"
        )
    payload = json.dumps({"query": "query { " + " ".join(fields) + " }"}).encode()
    request = Request(
        GITHUB_GRAPHQL_URL,
        data=payload,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "arewemodulesyet-star-generator",
        },
        method="POST",
    )
    last_error = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=timeout, context=TLS_CONTEXT) as response:
                result = json.load(response)
            break
        except HTTPError as error:
            last_error = github_http_error_message(error)
            if 400 <= error.code < 500 and error.code != 429:
                raise RuntimeError(f"GitHub GraphQL request failed: {last_error}") from error
            if attempt < 2:
                time.sleep(2**attempt)
        except (URLError, OSError, ValueError) as error:
            last_error = error
            if attempt < 2:
                time.sleep(2**attempt)
    else:
        raise RuntimeError(
            f"GitHub GraphQL request failed after three attempts: {last_error}"
        )

    data = result.get("data")
    if not isinstance(data, dict):
        messages = "; ".join(error.get("message", "") for error in result.get("errors", []))
        raise RuntimeError(messages or "GitHub GraphQL response did not contain data")

    stars = {}
    missing = set()
    for index, repository in enumerate(repositories):
        metadata = data.get(f"r{index}")
        if metadata is None:
            missing.add(repository)
        else:
            stars[repository] = int(metadata["stargazerCount"])
    return stars, missing


def fetch_from_github(repositories, token, timeout, batch_size=75):
    stars = {}
    missing = set()
    failed = set()
    errors = {}
    for offset in range(0, len(repositories), batch_size):
        batch = repositories[offset : offset + batch_size]
        try:
            batch_stars, batch_missing = github_graphql_request(batch, token, timeout)
            stars.update(batch_stars)
            missing.update(batch_missing)
        except RuntimeError as error:
            failed.update(batch)
            errors[str(error)] = errors.get(str(error), 0) + 1
        print(
            f"\rFetched {min(offset + len(batch), len(repositories))}/{len(repositories)} repositories...",
            end="",
            flush=True,
        )
    print()
    for error, count in errors.items():
        print(colored(f"GitHub API error in {count} batch(es): {error}", "red"))
    return stars, missing, failed


def ecosystems_metadata_request(repository, timeout):
    url = ECOSYSTEMS_REPOSITORY_URL.format(repository=quote(repository, safe=""))
    request = Request(url, headers={"User-Agent": "arewemodulesyet-star-generator"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=timeout, context=TLS_CONTEXT) as response:
                result = json.load(response)
            return int(result["stargazers_count"]), "found"
        except HTTPError as error:
            if error.code == 404:
                return None, "missing"
        except (OSError, URLError, ValueError, KeyError, TypeError):
            pass
        if attempt < 2:
            time.sleep(2**attempt)
    return None, "failed"


def resolve_github_repository(repository, timeout):
    """Follow GitHub web redirects and return the current repository name."""
    url = GITHUB_REPOSITORY_URL.format(repository=repository)
    request = Request(
        url,
        headers={"User-Agent": "arewemodulesyet-star-generator"},
        method="HEAD",
    )
    for attempt in range(3):
        try:
            with urlopen(request, timeout=timeout, context=TLS_CONTEXT) as response:
                canonical = normalize_github_repository(response.geturl())
            return canonical, "found" if canonical else "missing"
        except HTTPError as error:
            if error.code == 404:
                return None, "missing"
        except (OSError, URLError, ValueError):
            pass
        if attempt < 2:
            time.sleep(2**attempt)
    return None, "failed"


def github_rest_stars(repository, timeout):
    """Fetch one public repository from GitHub when the mirror has no entry."""
    url = GITHUB_REST_REPOSITORY_URL.format(repository=repository)
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "arewemodulesyet-star-generator",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    for attempt in range(3):
        try:
            with urlopen(request, timeout=timeout, context=TLS_CONTEXT) as response:
                result = json.load(response)
            return int(result["stargazers_count"]), "found"
        except HTTPError as error:
            if error.code == 404:
                return None, "missing"
        except (OSError, URLError, ValueError, KeyError, TypeError):
            pass
        if attempt < 2:
            time.sleep(2**attempt)
    return None, "failed"


def ecosystems_request(repository, timeout):
    star_count, status = ecosystems_metadata_request(repository, timeout)
    if status == "found":
        return repository, star_count, False
    if status == "failed":
        return repository, None, True

    canonical, status = resolve_github_repository(repository, timeout)
    if status == "failed":
        return repository, None, True
    if status == "missing":
        return repository, None, False

    # ecosyste.ms indexes repositories by their current GitHub name and does
    # not follow old GitHub aliases, so retry it after resolving redirects.
    if canonical != repository:
        star_count, status = ecosystems_metadata_request(canonical, timeout)
        if status == "found":
            return repository, star_count, False
        if status == "failed":
            return repository, None, True

    # A live GitHub repository may not have reached the mirror yet. This REST
    # fallback is only used for that small remainder, preserving API quota.
    star_count, status = github_rest_stars(canonical, timeout)
    if status == "found":
        return repository, star_count, False
    return repository, None, status == "failed"


def fetch_from_ecosystems(repositories, timeout, workers):
    stars = {}
    missing = set()
    failed = set()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(ecosystems_request, repository, timeout) for repository in repositories]
        for count, future in enumerate(as_completed(futures), start=1):
            repository, star_count, request_failed = future.result()
            if request_failed:
                failed.add(repository)
            elif star_count is None:
                missing.add(repository)
            else:
                stars[repository] = star_count
            if count % 25 == 0 or count == len(repositories):
                print(
                    f"\rFetched {count}/{len(repositories)} repositories...",
                    end="",
                    flush=True,
                )
    print()
    return stars, missing, failed


def write_cache(path, repositories, stars, provider):
    path.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "header": {
            "generated_date": int(time.time()),
            "provider": provider,
            "repository_count": len(repositories),
            "resolved_count": len(stars),
        },
        "repositories": {repository: stars[repository] for repository in sorted(stars)},
    }
    header = """###############################################################################
# DO NOT EDIT THIS FILE - IT IS AUTO-GENERATED
#
# This file is generated by tools/generate_github_stars.py.
###############################################################################

"""
    with path.open("w", encoding="utf-8") as stream:
        stream.write(header)
        yaml.safe_dump(output, stream, allow_unicode=True, sort_keys=False)


def main():
    parser = argparse.ArgumentParser(description="Generate cached GitHub star counts for tracked projects")
    parser.add_argument(
        "--provider",
        choices=("auto", "github", "ecosystems"),
        default="auto",
        help="Use GitHub GraphQL with a token, or the public ecosyste.ms mirror",
    )
    parser.add_argument("--workers", type=int, default=32, help="Concurrent ecosyste.ms requests")
    parser.add_argument("--timeout", type=int, default=45, help="Per-request timeout in seconds")
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Fetch only repositories that do not already have a cached star count",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    cache_path = data_dir / "generated" / "github_stars.yml"
    repositories = discover_repositories(
        load_yaml(data_dir / "generated" / "vcpkg_packages.yml"),
        load_yaml(data_dir / "vcpkg_overrides.yml"),
        load_yaml(data_dir / "external_projects.yml"),
    )
    cached_stars = load_cached_stars(cache_path)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    provider = args.provider
    if provider == "auto":
        provider = "github" if token else "ecosystems"
    if provider == "github" and not token:
        parser.error("the github provider requires GITHUB_TOKEN or GH_TOKEN")

    repositories_to_fetch = repositories
    if args.only_missing:
        repositories_to_fetch = [
            repository for repository in repositories if repository not in cached_stars
        ]
        if not repositories_to_fetch:
            print(colored("The star cache already covers every discovered repository.", "green"))
            return

    print()
    print(
        colored(
            f"Fetching stars for {len(repositories_to_fetch)} GitHub repositories via {provider}...",
            "cyan",
        )
    )
    if provider == "github":
        fetched_stars, missing, failed = fetch_from_github(
            repositories_to_fetch, token, args.timeout
        )
    else:
        fetched_stars, missing, failed = fetch_from_ecosystems(
            repositories_to_fetch, args.timeout, args.workers
        )

    # Preserve a previous value only when a request failed. A confirmed missing
    # repository must stay absent so the UI can fall back to the vcpkg metric.
    stars = {
        repository: cached_stars[repository]
        for repository in repositories
        if args.only_missing and repository in cached_stars
    }
    stars.update(fetched_stars)
    for repository in failed:
        if repository in cached_stars:
            stars[repository] = cached_stars[repository]

    if len(failed) == len(repositories_to_fetch):
        raise SystemExit("Unable to fetch any GitHub star counts; existing cache was not changed")
    cached_current_repositories = {
        repository: cached_stars[repository]
        for repository in repositories
        if repository in cached_stars
    }
    if cached_current_repositories and len(stars) < len(cached_current_repositories) * 0.8:
        raise SystemExit("Star refresh lost more than 20% of cached values; existing cache was not changed")

    write_cache(cache_path, repositories, stars, provider)
    print(colored(f"Saved {len(stars)} star counts to {cache_path}", "green"))
    if missing:
        print(
            colored(
                f"{len(missing)} repositories were not found; fallback data will be used.",
                "yellow",
            )
        )
    if failed:
        preserved = sum(repository in cached_stars for repository in failed)
        print(
            colored(
                f"{len(failed)} requests failed ({preserved} cached values preserved).",
                "yellow",
            )
        )


if __name__ == "__main__":
    main()
