#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "services" / "api"
FRONT_ROOTS = [ROOT / "apps" / "web" / "src", ROOT / "apps" / "mobile" / "src"]
SCAN_EXTS = {".ts", ".tsx", ".js", ".jsx"}
API_PREFIX = "/api/v1"


CALL_RE = re.compile(
    r"""(?P<client>this\.client|client|axios)\.(?P<method>get|post|put|patch|delete)\(\s*(?P<q>["'`])(?P<url>[^"'`]+)(?P=q)""",
    re.IGNORECASE,
)
FETCH_RE = re.compile(r"""fetch\(\s*(?P<q>["'`])(?P<url>[^"'`]+)(?P=q)""", re.IGNORECASE)
METHOD_IN_OPTIONS_RE = re.compile(r"""\bmethod\s*:\s*(?P<q>["'])(?P<method>[A-Z]+)(?P=q)""")
TPL_VAR_RE = re.compile(r"""\$\{[^}]+\}""")
PATH_VAR_RE = re.compile(r"""\{[^}]+\}""")


@dataclass(frozen=True)
class FrontCall:
    method: str
    path: str
    file: str
    line: int
    raw: str


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _normalize_path(path: str) -> str:
    p = path.strip()
    if not p:
        return p
    if p.startswith("http://") or p.startswith("https://"):
        # keep only path if someone hardcoded base URL
        idx = p.find("/", p.find("//") + 2)
        p = p[idx:] if idx != -1 else "/"
    if "?" in p:
        p = p.split("?", 1)[0]
    p = TPL_VAR_RE.sub("{param}", p)
    if p.startswith(API_PREFIX):
        p = p[len(API_PREFIX) :]
    if not p.startswith("/"):
        p = "/" + p
    p = re.sub(r"/{2,}", "/", p)
    p = PATH_VAR_RE.sub("{}", p)
    if len(p) > 1 and p.endswith("/"):
        p = p[:-1]
    return p


def _collect_front_calls() -> list[FrontCall]:
    calls: list[FrontCall] = []
    for root in FRONT_ROOTS:
        if not root.exists():
            continue
        for file in root.rglob("*"):
            if file.suffix.lower() not in SCAN_EXTS:
                continue
            text = file.read_text(encoding="utf-8")

            for m in CALL_RE.finditer(text):
                raw_url = m.group("url")
                if not raw_url.startswith("/"):
                    continue
                method = m.group("method").upper()
                path = _normalize_path(raw_url)
                calls.append(
                    FrontCall(
                        method=method,
                        path=path,
                        file=str(file.relative_to(ROOT)).replace("\\", "/"),
                        line=_line_of(text, m.start()),
                        raw=raw_url,
                    )
                )

            for m in FETCH_RE.finditer(text):
                raw_url = m.group("url")
                if not raw_url.startswith("/"):
                    continue
                method = "GET"
                options_slice = text[m.end() : m.end() + 220]
                method_match = METHOD_IN_OPTIONS_RE.search(options_slice)
                if method_match:
                    method = method_match.group("method").upper()
                path = _normalize_path(raw_url)
                calls.append(
                    FrontCall(
                        method=method,
                        path=path,
                        file=str(file.relative_to(ROOT)).replace("\\", "/"),
                        line=_line_of(text, m.start()),
                        raw=raw_url,
                    )
                )
    return calls


def _load_openapi_operations() -> set[tuple[str, str]]:
    sys.path.insert(0, str(API_ROOT))
    from app.main import app  # noqa: WPS433

    schema = app.openapi()
    ops: set[tuple[str, str]] = set()
    for path, methods in schema.get("paths", {}).items():
        normalized = _normalize_path(path)
        for method in methods.keys():
            ops.add((method.upper(), normalized))
    return ops


def main() -> int:
    front_calls = _collect_front_calls()
    openapi_ops = _load_openapi_operations()

    # unique front operations
    unique_front: dict[tuple[str, str], FrontCall] = {}
    for call in front_calls:
        unique_front.setdefault((call.method, call.path), call)

    missing: list[FrontCall] = []
    for key, call in unique_front.items():
        if key not in openapi_ops:
            missing.append(call)

    print(f"front_calls_total={len(front_calls)}")
    print(f"front_calls_unique={len(unique_front)}")
    print(f"openapi_operations={len(openapi_ops)}")
    print(f"missing_in_openapi={len(missing)}")

    if missing:
        print("\nMissing endpoints (front -> absent OpenAPI):")
        for call in sorted(missing, key=lambda c: (c.file, c.line))[:80]:
            print(f"- {call.method} {call.path} [{call.file}:{call.line}] raw={call.raw}")
        print("\nFAIL: API contract mismatch detected.")
        return 1

    print("PASS: all front user-facing endpoints exist in OpenAPI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

