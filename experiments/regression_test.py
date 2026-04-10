"""Regression test: run against multiple live APIs and track pass/fail.

Run this after any change to the model builder, registry, or spec loader
to ensure nothing broke across the tool's supported API surface.

Requires:
- Qdrant running locally (docker run -d -p 6333:6333 qdrant/qdrant)
- Meilisearch running locally (docker run -d -p 7700:7700 getmeili/meilisearch)
- CLI_TOKEN env var for OpenAI (or skip OpenAI tests)
"""
from __future__ import annotations

import os
import sys
import warnings
warnings.filterwarnings("ignore")

from openapi_cli_gen import build_cli


class TestRunner:
    def __init__(self):
        self.results: list[tuple[str, str, bool, str]] = []
        self.current_suite = ""

    def suite(self, name: str):
        self.current_suite = name

    def run(self, name: str, app, args: list[str]) -> bool:
        try:
            app(args)
            self.results.append((self.current_suite, name, True, ""))
            return True
        except SystemExit as e:
            if e.code == 0:
                self.results.append((self.current_suite, name, True, ""))
                return True
            self.results.append((self.current_suite, name, False, f"exit {e.code}"))
            return False
        except Exception as e:
            err = f"{type(e).__name__}: {str(e)[:150]}"
            self.results.append((self.current_suite, name, False, err))
            return False

    def summary(self):
        by_suite: dict[str, list[tuple[str, bool, str]]] = {}
        for suite, name, ok, err in self.results:
            by_suite.setdefault(suite, []).append((name, ok, err))

        total_pass = 0
        total = 0
        for suite, tests in by_suite.items():
            pass_count = sum(1 for _, ok, _ in tests if ok)
            total_pass += pass_count
            total += len(tests)
            print(f"\n{suite}: {pass_count}/{len(tests)}")
            for name, ok, err in tests:
                marker = "PASS" if ok else "FAIL"
                print(f"  [{marker}] {name}")
                if err:
                    print(f"         {err}")
        print(f"\n{'='*60}")
        print(f"OVERALL: {total_pass}/{total}")
        return total_pass == total


def main():
    runner = TestRunner()

    # === QDRANT (requires Docker) ===
    runner.suite("Qdrant")
    try:
        spec = "https://raw.githubusercontent.com/qdrant/qdrant/master/docs/redoc/master/openapi.json"
        app = build_cli(spec=spec, name="qdrant", base_url="http://localhost:6333")
        runner.run("Service root", app, ["service", "root"])
        runner.run("Healthz", app, ["service", "healthz"])
        runner.run("List collections", app, ["collections", "get-collections"])
        runner.run("Create collection", app, [
            "collections", "create",
            "--collection-name", "regression_test",
            "--vectors", '{"size": 4, "distance": "Cosine"}',
        ])
        runner.run("Get collection", app, [
            "collections", "get-collection", "--collection-name", "regression_test",
        ])
        runner.run("Exists", app, [
            "collections", "exists", "--collection-name", "regression_test",
        ])
        runner.run("Delete collection", app, [
            "collections", "delete", "--collection-name", "regression_test",
        ])
    except Exception as e:
        print(f"Qdrant setup failed: {e}")

    # === MEILISEARCH (requires Docker) ===
    runner.suite("Meilisearch")
    try:
        spec = "https://raw.githubusercontent.com/meilisearch/open-api/main/open-api.json"
        app = build_cli(spec=spec, name="meili", base_url="http://localhost:7700")
        runner.run("Health", app, ["health", "get"])
        runner.run("Version", app, ["version", "get"])
        runner.run("List indexes", app, ["indexes", "list"])
        runner.run("Create index", app, [
            "indexes", "create-index", "--uid", "regression_test", "--primary-key", "id",
        ])
        runner.run("Stats", app, ["stats", "get"])
        runner.run("List tasks", app, ["tasks", "get-tasks"])
        runner.run("Delete index", app, [
            "indexes", "delete-index", "--index-uid", "regression_test",
        ])
    except Exception as e:
        print(f"Meilisearch setup failed: {e}")

    # === OPENAI (requires CLI_TOKEN) ===
    if os.environ.get("CLI_TOKEN"):
        runner.suite("OpenAI")
        try:
            spec = "https://raw.githubusercontent.com/openai/openai-openapi/2025-03-21/openapi.yaml"
            app = build_cli(spec=spec, name="cli")
            runner.run("Models list", app, ["models", "list"])
            runner.run("Models retrieve", app, ["models", "retrieve", "--model", "gpt-4o-mini"])
            runner.run("Embeddings", app, [
                "embeddings", "create",
                "--input", "Hello",
                "--model", "text-embedding-3-small",
                "--dimensions", "4",
            ])
            runner.run("Moderations", app, [
                "moderations", "create", "--input", "I love cats",
            ])
            runner.run("Legacy completions", app, [
                "completions", "create",
                "--model", "gpt-3.5-turbo-instruct",
                "--prompt", "Python is",
                "--max-tokens", "5",
            ])
            runner.run("Chat completion", app, [
                "chat", "create-completion",
                "--model", "gpt-4o-mini",
                "--messages", '[{"role":"user","content":"Reply with exactly 3 words"}]',
            ])
            runner.run("Files list", app, ["files", "list"])
            runner.run("Vector stores list", app, ["vector-stores", "list-vector-stores"])
        except Exception as e:
            print(f"OpenAI setup failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Skipping OpenAI tests (CLI_TOKEN not set)")

    # === QDRANT POINTS CRUD ===
    runner.suite("Qdrant Points")
    try:
        spec = "https://raw.githubusercontent.com/qdrant/qdrant/master/docs/redoc/master/openapi.json"
        app = build_cli(spec=spec, name="qdrant", base_url="http://localhost:6333")
        runner.run("Create collection", app, [
            "collections", "create",
            "--collection-name", "pts_regression",
            "--vectors", '{"size": 4, "distance": "Cosine"}',
        ])
        runner.run("Upsert points", app, [
            "points", "upsert",
            "--collection-name", "pts_regression",
            "--root", '{"points": [{"id": 1, "vector": [0.1, 0.2, 0.3, 0.4], "payload": {"city": "NYC"}}, {"id": 2, "vector": [0.5, 0.6, 0.7, 0.8]}]}',
        ])
        runner.run("Count points", app, ["points", "count", "--collection-name", "pts_regression"])
        runner.run("Get point", app, ["points", "get-point", "--collection-name", "pts_regression", "--id", "1"])
        runner.run("Scroll points", app, ["points", "scroll", "--collection-name", "pts_regression", "--limit", "10"])
        runner.run("Query points", app, [
            "search", "query-points",
            "--collection-name", "pts_regression",
            "--query", "[0.1, 0.2, 0.3, 0.4]",
            "--limit", "2",
        ])
        runner.run("Cleanup", app, ["collections", "delete", "--collection-name", "pts_regression"])
    except Exception as e:
        print(f"Qdrant Points setup failed: {e}")

    # === TYPESENSE (requires Docker) ===
    runner.suite("Typesense")
    try:
        spec = "https://raw.githubusercontent.com/typesense/typesense-api-spec/master/openapi.yml"
        app = build_cli(spec=spec, name="ts", base_url="http://localhost:8108")
        runner.run("Health", app, ["health", "health"])
    except Exception as e:
        print(f"Typesense setup failed: {e}")

    # === GITHUB PUBLIC API (no auth needed) ===
    runner.suite("GitHub (public)")
    try:
        spec = "https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json"
        app = build_cli(spec=spec, name="gh", base_url="https://api.github.com")
        runner.run("Meta root", app, ["meta", "meta/root"])
        runner.run("Zen", app, ["meta", "meta/get-zen"])
        runner.run("Octocat", app, ["meta", "meta/get-octocat"])
        runner.run("Rate limit", app, ["rate-limit", "rate-limit/get"])
        runner.run("Get license", app, ["licenses", "licenses/get", "--license", "mit"])
        runner.run("Get user", app, ["users", "users/get-by-username", "--username", "shivaam"])
    except Exception as e:
        print(f"GitHub setup failed: {e}")

    success = runner.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
