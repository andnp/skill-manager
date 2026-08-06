"""Discover and import Agent Skills from public GitHub repositories."""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlparse

import httpx

from .manifest import load_manifest


class GitHubError(ValueError):
    """Raised when a repository cannot be inspected safely."""


@dataclass(frozen=True)
class DiscoveredSkill:
    """A skill package found in a GitHub repository."""

    name: str
    summary: str
    repository: str
    root: str
    files: tuple[str, ...]


def _repository(url: str) -> tuple[str, str]:
    value = url if "://" in url else f"https://github.com/{url}"
    parsed = urlparse(value)
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise GitHubError("expected a GitHub repository URL or owner/repository")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise GitHubError("repository URL must include an owner and repository")
    return parts[0], parts[1].removesuffix(".git")


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "skill-manager"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _summary(text: str) -> str:
    if text.startswith("---"):
        frontmatter, _, body = text[3:].partition("---")
        match = re.search(r"^description:\s*[\"']?(.*?)[\"']?\s*$", frontmatter, re.MULTILINE)
        if match:
            return match.group(1).strip()
        text = body
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    return "No summary provided"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise GitHubError("skill name could not be converted to a safe folder name")
    return slug


def discover(url: str, client: httpx.Client | None = None) -> list[DiscoveredSkill]:
    """Find every folder containing a ``SKILL.md`` in a repository tree."""
    owner, repo = _repository(url)
    close_client = client is None
    client = client or httpx.Client(timeout=20, headers=_headers())
    try:
        metadata = client.get(f"https://api.github.com/repos/{owner}/{repo}")
        metadata.raise_for_status()
        branch = metadata.json()["default_branch"]
        tree_response = client.get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
        tree_response.raise_for_status()
        tree = tree_response.json()
        if tree.get("truncated"):
            raise GitHubError("GitHub truncated this repository tree; use a smaller repository")
        files = sorted(item["path"] for item in tree.get("tree", []) if item.get("type") == "blob")
        skills: list[DiscoveredSkill] = []
        for skill_file in (path for path in files if Path(path).name.lower() == "skill.md"):
            root = str(Path(skill_file).parent)
            prefix = f"{root}/" if root != "." else ""
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{quote(branch)}/{quote(skill_file)}"
            response = client.get(raw_url)
            response.raise_for_status()
            name = _slug(Path(root).name if root != "." else repo)
            skills.append(
                DiscoveredSkill(
                    name,
                    _summary(response.text),
                    f"{owner}/{repo}",
                    root,
                    tuple(path for path in files if path == skill_file or path.startswith(prefix)),
                )
            )
        return skills
    except httpx.HTTPError as error:
        raise GitHubError(f"GitHub request failed: {error}") from error
    finally:
        if close_client:
            client.close()


def install(skill: DiscoveredSkill, root: Path, client: httpx.Client | None = None) -> Path:
    """Download one discovered skill into the source repository."""
    owner, repo = skill.repository.split("/", 1)
    branch_client = client or httpx.Client(timeout=20, headers=_headers())
    destination_root = root / load_manifest(root).source_dir / skill.name
    try:
        metadata = branch_client.get(f"https://api.github.com/repos/{owner}/{repo}")
        metadata.raise_for_status()
        branch = metadata.json()["default_branch"]
        for remote_path in skill.files:
            relative = Path(remote_path).relative_to(skill.root) if skill.root != "." else Path(remote_path).name
            if relative.is_absolute() or ".." in relative.parts:
                raise GitHubError(f"unsafe path in repository: {remote_path}")
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{quote(branch)}/{quote(remote_path)}"
            response = branch_client.get(raw_url)
            response.raise_for_status()
            target = destination_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(response.content)
        return destination_root
    except httpx.HTTPError as error:
        raise GitHubError(f"GitHub request failed: {error}") from error
    finally:
        if client is None:
            branch_client.close()
