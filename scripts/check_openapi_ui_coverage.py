#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "services" / "api"
FRONT_ROOTS = [ROOT / "apps" / "web" / "src", ROOT / "apps" / "mobile" / "src"]
SCAN_EXTS = {".ts", ".tsx", ".js", ".jsx"}
API_PREFIX = "/api/v1"
EXCLUSIONS_FILE = ROOT / "scripts" / "openapi_ui_exclusions.json"

# Endpoints considered "user-facing" for coverage
USER_PREFIXES = [
    "/auth",
    "/rbac",
    "/actors",
    "/lots",
    "/trades",
    "/transactions",
    "/payments",
    "/payment-providers",
    "/invoices",
    "/documents",
    "/ledger",
    "/exports",
    "/transports",
    "/transformations",
    "/notifications",
    "/catalog",
    "/territories",
    "/geo-points",
    "/dashboards",
    "/reports",
    "/inspections",
    "/violations",
    "/penalties",
    "/taxes",
    "/approvals",
    "/admin",
    "/verify",
    "/or",
    "/or-compliance",
    "/emergency-alerts",
    "/fees",
    "/health",
    "/ready",
]


CALL_RE = re.compile(
    r"""(?P<client>this\.client|client|axios)\.(?P<method>get|post|put|patch|delete)\(\s*(?P<q>["'`])(?P<url>[^"'`]+)(?P=q)""",
    re.IGNORECASE,
)
FETCH_RE = re.compile(r"""fetch\(\s*(?P<q>["'`])(?P<url>[^"'`]+)(?P=q)""", re.IGNORECASE)
METHOD_IN_OPTIONS_RE = re.compile(r"""\bmethod\s*:\s*(?P<q>["'])(?P<method>[A-Z]+)(?P=q)""")
TPL_VAR_RE = re.compile(r"""\$\{[^}]+\}""")
PATH_VAR_RE = re.compile(r"""\{[^}]+\}""")


@dataclass(frozen=True)
class FrontOp:
    method: str
    path: str


def _normalize_path(path: str) -> str:
    p = path.strip()
    if not p:
        return p
    if p.startswith("http://") or p.startswith("https://"):
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


def _collect_front_ops() -> set[FrontOp]:
    out: set[FrontOp] = set()
    for root in FRONT_ROOTS:
        if not root.exists():
            continue
        for file in root.rglob("*"):
            if file.suffix.lower() not in SCAN_EXTS:
                continue
            text = file.read_text(encoding="utf-8")

            for m in CALL_RE.finditer(text):
                url = m.group("url")
                if not url.startswith("/"):
                    continue
                out.add(FrontOp(method=m.group("method").upper(), path=_normalize_path(url)))

            for m in FETCH_RE.finditer(text):
                url = m.group("url")
                if not url.startswith("/"):
                    continue
                method = "GET"
                options_slice = text[m.end() : m.end() + 220]
                mm = METHOD_IN_OPTIONS_RE.search(options_slice)
                if mm:
                    method = mm.group("method").upper()
                out.add(FrontOp(method=method, path=_normalize_path(url)))
    return out


def _load_openapi_ops() -> set[FrontOp]:
    sys.path.insert(0, str(API_ROOT))
    from app.main import app  # noqa: WPS433

    schema = app.openapi()
    out: set[FrontOp] = set()
    for path, methods in schema.get("paths", {}).items():
        npath = _normalize_path(path)
        for m in methods.keys():
            out.add(FrontOp(method=m.upper(), path=npath))
    return out


def _is_user_facing(op: FrontOp) -> bool:
    return any(op.path.startswith(prefix) for prefix in USER_PREFIXES)


def _load_exclusions() -> tuple[set[FrontOp], list[str]]:
    exact: set[FrontOp] = set()
    prefixes: list[str] = []
    if not EXCLUSIONS_FILE.exists():
        return exact, prefixes
    data = json.loads(EXCLUSIONS_FILE.read_text(encoding="utf-8"))
    for item in data.get("exclude_exact", []):
        exact.add(FrontOp(method=item["method"].upper(), path=_normalize_path(item["path"])))
    for item in data.get("exclude_prefix", []):
        prefixes.append(item["prefix"])
    return exact, prefixes


def _excluded(op: FrontOp, exact: set[FrontOp], prefixes: list[str]) -> bool:
    if op in exact:
        return True
    return any(op.path.startswith(p) for p in prefixes)


def main() -> int:
    front_ops = _collect_front_ops()
    api_ops = _load_openapi_ops()
    exact_excl, prefix_excl = _load_exclusions()

    user_ops = {op for op in api_ops if _is_user_facing(op)}
    uncovered = sorted(
        [
            op
            for op in user_ops
            if op not in front_ops and not _excluded(op, exact_excl, prefix_excl)
        ],
        key=lambda x: (x.path, x.method),
    )

    print(f"front_unique_ops={len(front_ops)}")
    print(f"openapi_ops={len(api_ops)}")
    print(f"user_facing_openapi_ops={len(user_ops)}")
    print(f"uncovered_user_ops={len(uncovered)}")

    if uncovered:
        print("\nOpenAPI user-facing endpoints not exposed/called by front:")
        for op in uncovered[:120]:
            print(f"- {op.method} {op.path}")
        print("\nFAIL: reverse UI coverage mismatch detected.")
        return 1

    print("PASS: all user-facing OpenAPI endpoints are exposed/called by front.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

