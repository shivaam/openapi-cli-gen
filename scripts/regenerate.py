#!/usr/bin/env python3
"""Regenerate all CLI wrapper packages from wrappers/manifest.yaml.

Usage:
    # Regenerate all wrappers into build/wrappers/
    python scripts/regenerate.py

    # Regenerate + publish to PyPI
    python scripts/regenerate.py --publish

    # Regenerate a single wrapper
    python scripts/regenerate.py --only openai-rest-cli

    # Regenerate + push to each wrapper's GitHub repo
    python scripts/regenerate.py --push
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "wrappers" / "manifest.yaml"
BUILD_DIR = ROOT / "build" / "wrappers"


def load_manifest(only: str | None = None) -> list[dict]:
    with open(MANIFEST) as f:
        data = yaml.safe_load(f)
    wrappers = data["wrappers"]
    if only:
        wrappers = [w for w in wrappers if w["name"] == only]
        if not wrappers:
            print(f"Error: wrapper '{only}' not found in manifest", file=sys.stderr)
            sys.exit(1)
    return wrappers


def regenerate(wrapper: dict) -> Path:
    """Run openapi-cli-gen generate for a single wrapper."""
    name = wrapper["name"]
    output = BUILD_DIR / name
    cmd = [
        sys.executable, "-m", "openapi_cli_gen", "generate",
        "--spec", wrapper["spec_url"],
        "--name", name,
        "--output", str(output),
    ]
    if wrapper.get("base_url"):
        cmd += ["--base-url", wrapper["base_url"]]
    if wrapper.get("description"):
        cmd += ["--description", wrapper["description"]]
    if wrapper.get("version"):
        cmd += ["--wrapper-version", wrapper["version"]]

    print(f"\n{'='*60}")
    print(f"Generating: {name}")
    print(f"  spec: {wrapper['spec_url']}")
    print(f"  output: {output}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FAILED: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"  {result.stdout.strip()}")
    return output


def publish(output_dir: Path, name: str) -> None:
    """Build and upload a wrapper package to PyPI."""
    print(f"  Publishing {name} to PyPI...")
    # Build
    subprocess.run(
        [sys.executable, "-m", "build", str(output_dir)],
        check=True, capture_output=True, text=True,
    )
    # Upload
    dist_dir = output_dir / "dist"
    result = subprocess.run(
        [sys.executable, "-m", "twine", "upload", str(dist_dir / "*")],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  Publish failed: {result.stderr}", file=sys.stderr)
    else:
        print(f"  Published {name}")


def push_to_repo(output_dir: Path, wrapper: dict) -> None:
    """Clone the wrapper's repo, copy generated files, commit, and push."""
    repo = wrapper.get("repo")
    if not repo:
        print(f"  No repo configured for {wrapper['name']}, skipping push")
        return

    name = wrapper["name"]
    clone_dir = BUILD_DIR / f"{name}-repo"

    print(f"  Pushing to {repo}...")

    # Clone (shallow)
    if clone_dir.exists():
        subprocess.run(["rm", "-rf", str(clone_dir)], check=True)
    subprocess.run(
        ["git", "clone", "--depth=1", f"https://github.com/{repo}.git", str(clone_dir)],
        check=True, capture_output=True, text=True,
    )

    # Copy generated files over (preserve .git)
    for item in output_dir.iterdir():
        dest = clone_dir / item.name
        if item.is_dir():
            subprocess.run(["rm", "-rf", str(dest)], check=True)
            subprocess.run(["cp", "-r", str(item), str(dest)], check=True)
        else:
            subprocess.run(["cp", str(item), str(dest)], check=True)

    # Commit and push if there are changes
    result = subprocess.run(
        ["git", "-C", str(clone_dir), "status", "--porcelain"],
        capture_output=True, text=True,
    )
    if not result.stdout.strip():
        print(f"  No changes for {name}")
        return

    version = _get_openapi_cli_gen_version()
    subprocess.run(
        ["git", "-C", str(clone_dir), "add", "-A"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(clone_dir), "commit", "-m",
         f"regenerate with openapi-cli-gen v{version}"],
        check=True, capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "-C", str(clone_dir), "push"],
        check=True, capture_output=True, text=True,
    )
    print(f"  Pushed {name} to {repo}")


def _get_openapi_cli_gen_version() -> str:
    import openapi_cli_gen
    return openapi_cli_gen.__version__


def main():
    parser = argparse.ArgumentParser(description="Regenerate CLI wrapper packages")
    parser.add_argument("--only", help="Regenerate only this wrapper (by name)")
    parser.add_argument("--publish", action="store_true", help="Build and publish to PyPI")
    parser.add_argument("--push", action="store_true", help="Push to each wrapper's GitHub repo")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()

    wrappers = load_manifest(only=args.only)
    version = _get_openapi_cli_gen_version()
    print(f"openapi-cli-gen version: {version}")
    print(f"Wrappers to regenerate: {len(wrappers)}")

    if args.dry_run:
        for w in wrappers:
            print(f"  - {w['name']} (spec: {w['spec_url']})")
        return

    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    for wrapper in wrappers:
        output = regenerate(wrapper)
        if args.push:
            push_to_repo(output, wrapper)
        if args.publish:
            publish(output, wrapper["name"])

    print(f"\nDone. {len(wrappers)} wrapper(s) regenerated.")
    if not args.publish:
        print(f"Packages in: {BUILD_DIR}")
        print("Run with --publish to upload to PyPI")


if __name__ == "__main__":
    main()
