#!/usr/bin/env python3
"""Check navigation-page snippets against local HTTP fixtures, never the real API."""

import json
import os
import re
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = [page for group in json.loads((ROOT / "docs.json").read_text())["navigation"]["groups"]
         for page in group["pages"]]
BLOCKS = {page: re.findall(r"^```(\w+)([^\n]*)\n(.*?)^```", (ROOT / (page + ".mdx")).read_text(), re.M | re.S)
          for page in PAGES}
REFERENCE = {
    "api/user": ("GET", "/user", {}, None),
    "api/projects": ("GET", "/projects", {}, None),
    "api/locations/list": ("GET", "/projects/PROJECT_ID/locations",
                           {"limit": ["25"], "city[eq]": ["Seattle"], "includeHours": ["1"]}, None),
    "api/locations/get": ("GET", "/projects/PROJECT_ID/locations/LOCATION_ID",
                          {name: ["1"] for name in ("includeHours", "includeFilters", "includeFields", "includeCallsToAction")}, None),
    "api/locations/create": ("POST", "/projects/PROJECT_ID/locations", {},
                             {"name": "Coming Soon Store", "city": "Seattle", "lat": 47.6062,
                              "lng": -122.3321, "visible": False, "hours": {}}),
    "api/locations/update": ("PATCH", "/projects/PROJECT_ID/locations/LOCATION_ID", {}, {"phone": "555-0101"}),
    "api/locations/put": ("PUT", "/projects/PROJECT_ID/locations/LOCATION_ID", {},
                          {"name": "Downtown Store", "city": "Seattle", "phone": "555-0101"}),
    "api/locations/delete": ("DELETE", "/projects/PROJECT_ID/locations/LOCATION_ID", {}, None),
}
state = {}
checks = 0


class Fixture(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def handle_request(self):
        parsed = urlsplit(self.path)
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        body = json.loads(raw) if raw else None
        request = {"method": self.command, "path": parsed.path.removeprefix("/api/v2"),
                   "query": parse_qs(parsed.query), "body": body,
                   "auth": self.headers.get("Authorization"), "accept": self.headers.get("Accept"),
                   "contentType": self.headers.get("Content-Type")}
        state["requests"].append(request)
        mode = state["mode"]
        status = 200
        response = {"data": {"id": "LOCATION_ID"}}
        if mode == "disconnect" and self.command == "PATCH":
            self.close_connection = True
            return
        if mode.startswith("status-"):
            status = int(mode.split("-")[1])
        elif mode in ("rate-limit", "rate-limit-one-second") and len(state["requests"]) == 1:
            status = 429
        elif mode == "rate-limit-write" and self.command == "PATCH" and not state.get("limited"):
            status = 429
            state["limited"] = True
        elif mode == "reject-second" and self.command == "PATCH" and parsed.path.endswith("SECOND_LOCATION_ID"):
            status = 422
        if status != 200:
            response = {"message": "Fixture request failed.", "errors": {"hours": ["Correct the hours field."]}}
        elif self.command == "GET" and parsed.path.endswith("/locations"):
            page = int(request["query"].get("page", ["1"])[0])
            data = [{"id": "LOCATION_ID"}] if page == 1 else [{"id": "SECOND_LOCATION_ID"}]
            if mode == "empty":
                data = []
            response = {"data": data, "links": {"next": None if page == 2 or mode == "empty" else "page2"},
                        "meta": {"current_page": page, "last_page": 1 if mode == "empty" else 2}}
        elif self.command == "GET" and parsed.path.endswith("/projects"):
            response = {"data": [{"id": "PROJECT_ID", "name": "Fixture project"}]}
        elif self.command == "DELETE":
            response = {"success": True}
        elif self.command == "PATCH":
            state["saved"].append(request)
        payload = b"not json" if mode == "non-json" else json.dumps(response).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Retry-After", "1" if mode == "rate-limit-one-second" else "0")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = handle_request


def reset(mode="ok"):
    state.clear()
    state.update(mode=mode, requests=[], saved=[])


def check(condition, message):
    global checks
    if not condition:
        raise AssertionError(message)
    checks += 1


def run(code, language, mode="ok", changes=None, apply=False, token="fixture-only"):
    reset(mode)
    # Only replace the fixed documented API base; no production token or request is used.
    code = code.replace("https://storerocket.io/api/v2", base)
    assert "https://storerocket.io" not in code, "Unexpected production URL in executable example"
    filename = directory / ("example.mjs" if language == "javascript" else "example.php")
    filename.write_text(code)
    if changes is not None:
        (directory / "changes.json").write_text(json.dumps(changes))
    env = {**os.environ, "STOREROCKET_TOKEN": token, "STOREROCKET_PROJECT_ID": "PROJECT_ID"}
    command = ["node" if language == "javascript" else "php", str(filename)]
    if apply:
        command.append("--apply")
    result = subprocess.run(command, cwd=directory, env=env, capture_output=True, text=True, timeout=15)
    return result, list(state["requests"]), list(state["saved"])


with tempfile.TemporaryDirectory(prefix="sr-docs-examples-") as temporary:
    directory = Path(temporary)
    server = HTTPServer(("127.0.0.1", 0), Fixture)
    base = f"http://127.0.0.1:{server.server_port}/api/v2"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        syntax = {"javascript": 0, "php": 0, "json": 0, "bash": 0}
        for page, blocks in BLOCKS.items():
            for language, title, code in blocks:
                if language == "json":
                    json.loads(code)
                elif language == "bash":
                    subprocess.run(["bash", "-n"], input=code, text=True, check=True, capture_output=True)
                elif language in ("javascript", "php"):
                    path = directory / ("syntax.mjs" if language == "javascript" else "syntax.php")
                    path.write_text(code)
                    command = ["node", "--check", str(path)] if language == "javascript" else ["php", "-l", str(path)]
                    subprocess.run(command, check=True, capture_output=True)
                if language in syntax:
                    syntax[language] += 1

        # Execute the exact authored reference code: encoded query, payload, headers and error exit.
        for page, expected in REFERENCE.items():
            for language in ("javascript", "php"):
                check(sum(lang == language for lang, _title, _code in BLOCKS[page]) == 1,
                      f"{page}: expected exactly one {language} example")
            for language, title, code in BLOCKS[page]:
                if language not in ("javascript", "php"):
                    continue
                result, requests, _saved = run(code, language)
                check(result.returncode == 0, f"{page}/{language}: {result.stderr}")
                check(len(requests) == 1, f"{page}/{language}: expected one request")
                actual = requests[0]
                check((actual["method"], actual["path"], actual["query"], actual["body"]) == expected,
                      f"{page}/{language}: wrong request: {actual}")
                check(actual["auth"] == "Bearer fixture-only" and actual["accept"] == "application/json",
                      f"{page}/{language}: auth/Accept headers")
                if expected[3] is not None:
                    check(actual["contentType"] == "application/json", f"{page}/{language}: JSON header")
                for status in (401, 422, 429, 500):
                    result, requests, _saved = run(code, language, f"status-{status}")
                    check(result.returncode != 0 and f"HTTP {status}" in result.stdout + result.stderr and len(requests) == 1,
                          f"{page}/{language}: error {status} was hidden or retried")

        # First-request paths are runnable without a hidden write.
        for page in ("api/authentication", "api/quickstart"):
            for language in ("javascript", "php"):
                check(sum(lang == language for lang, _title, _code in BLOCKS[page]) ==
                      (2 if page == "api/quickstart" else 1), f"{page}: missing {language} example")
            for language, title, code in BLOCKS[page]:
                if language not in ("javascript", "php"):
                    continue
                result, requests, _saved = run(code, language)
                check(result.returncode == 0 and requests and all(r["method"] == "GET" for r in requests),
                      f"{page}/{language}: first request failed or wrote data")

        for language in ("javascript", "php"):
            check(sum(lang == language for lang, _title, _code in BLOCKS["api/sync-locations"]) == 1,
                  f"Sync guide: expected exactly one {language} script")
        guide = {language: code for language, _title, code in BLOCKS["api/sync-locations"]
                 if language in ("javascript", "php")}
        changes = [{"id": "SECOND_LOCATION_ID", "phone": "555-0101", "hours": {"mon": "09:00-17:00"}}]
        for language, code in guide.items():
            result, requests, saved = run(code, language, changes=changes)
            check(result.returncode == 0 and "Would PATCH SECOND_LOCATION_ID" in result.stdout and not saved,
                  f"{language}: preview must not write")
            check([r["query"] for r in requests] == [
                {"limit": ["100"], "includeHours": ["1"], "page": [str(p)]} for p in (1, 2)],
                f"{language}: skipped a page or changed flags")
            result, requests, saved = run(code, language, changes=changes, apply=True)
            check(result.returncode == 0 and "Sync complete." in result.stdout and len(saved) == 1,
                  f"{language}: apply failed")
            check(saved[0]["path"].endswith("/SECOND_LOCATION_ID") and saved[0]["body"] ==
                  {"phone": "555-0101", "hours": {"mon": "09:00-17:00"}}, f"{language}: wrong PATCH body")
            for hours in ({}, None, {"mon": None}):
                result, _requests, saved = run(code, language, changes=[{"id": "LOCATION_ID", "hours": hours}], apply=True)
                check(result.returncode == 0 and saved[0]["body"] == {"hours": hours},
                      f"{language}: lost object/null/weekday-clear semantics")
            for bad in ([{"id": "LOCATION_ID", "phone": "x"}, {"id": "OUTSIDE_PROJECT", "phone": "y"}],
                        [{"id": "LOCATION_ID"}, {"id": "LOCATION_ID"}], [{"id": 123}], {}):
                result, requests, saved = run(code, language, changes=bad, apply=True)
                check(result.returncode != 0 and not saved and all(r["method"] == "GET" for r in requests),
                      f"{language}: bad input/preflight sent a write")
            result, requests, saved = run(code, language, mode="empty", changes=[], apply=True)
            check(result.returncode == 0 and len(requests) == 1 and not saved, f"{language}: empty project")
            result, requests, saved = run(code, language, mode="reject-second", changes=[
                {"id": "LOCATION_ID", "phone": "x"}, {"id": "SECOND_LOCATION_ID", "phone": "y"}], apply=True)
            check(result.returncode != 0 and "HTTP 422" in result.stdout + result.stderr and len(saved) == 1 and
                  "Updated LOCATION_ID." in result.stdout and "Sync complete." not in result.stdout,
                  f"{language}: failed batch falsely reported atomic/successful")
            for mode in ("rate-limit", "rate-limit-write"):
                result, requests, saved = run(code, language, mode=mode, changes=changes, apply=True)
                check(result.returncode == 0 and "waiting 0 seconds" in result.stdout and len(saved) == 1,
                      f"{language}: Retry-After was not respected")
            started = time.monotonic()
            result, requests, saved = run(code, language, mode="rate-limit-one-second", changes=changes, apply=True)
            check(result.returncode == 0 and time.monotonic() - started >= 0.95 and
                  "waiting 1 seconds" in result.stdout and len(saved) == 1,
                  f"{language}: did not wait for positive Retry-After")
            result, requests, saved = run(code, language, mode="status-429", changes=changes, apply=True)
            check(result.returncode != 0 and len(requests) == 4 and not saved, f"{language}: unbounded retries")
            for mode in ("disconnect", "non-json", "status-401", "status-403", "status-404", "status-500"):
                result, requests, saved = run(code, language, mode=mode, changes=changes, apply=True)
                check(result.returncode != 0 and not saved and
                      sum(r["method"] == "PATCH" for r in requests) <= 1,
                      f"{language}: failure falsely succeeded or retried an ambiguous write")
            result, requests, saved = run(code, language, changes=changes, apply=True, token="")
            check(result.returncode != 0 and not requests, f"{language}: missing token sent a request")

        # A negative control proves the PHP object-shape check can catch a real regression.
        bad_php = next(code for lang, _title, code in BLOCKS["api/locations/create"] if lang == "php")
        bad_php = bad_php.replace("new stdClass()", "[]")
        result, requests, _saved = run(bad_php, "php")
        try:
            check(requests[0]["body"] == REFERENCE["api/locations/create"][3],
                  "PHP mutation changed hours from {} to []")
        except AssertionError:
            check(result.returncode == 0 and requests[0]["body"]["hours"] == [],
                  "Negative control failed for an unrelated reason")
        else:
            raise AssertionError("The contract assertion failed to catch the {} -> [] mutation")
        print(json.dumps({"navigationPages": len(PAGES), "syntax": syntax, "runtimeChecks": checks,
                          "negativeControl": "Detected PHP empty-object-to-array mutation",
                          "network": "localhost fixtures only; no production API writes"}, indent=2))
    finally:
        server.shutdown()
        server.server_close()
