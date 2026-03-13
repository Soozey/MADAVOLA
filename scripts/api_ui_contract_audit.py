#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "services" / "api"
FRONT_ROOTS = [ROOT / "apps" / "web" / "src", ROOT / "apps" / "mobile" / "src"]
SCAN_EXTS = {".ts", ".tsx", ".js", ".jsx"}
API_PREFIX = "/api/v1"
EXCLUSIONS_FILE = ROOT / "scripts" / "openapi_ui_exclusions.json"
REPORT_FILE = ROOT / "docs" / "api-ui-contract-report.md"

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
class FrontCall:
    method: str
    path: str
    file: str
    line: int
    raw: str


@dataclass(frozen=True)
class Op:
    method: str
    path: str


def normalize_path(path: str) -> str:
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


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def collect_front_calls() -> list[FrontCall]:
    calls: list[FrontCall] = []
    for root in FRONT_ROOTS:
        if not root.exists():
            continue
        for file in root.rglob("*"):
            if file.suffix.lower() not in SCAN_EXTS:
                continue
            text = file.read_text(encoding="utf-8")

            for m in CALL_RE.finditer(text):
                raw = m.group("url")
                if not raw.startswith("/"):
                    continue
                calls.append(
                    FrontCall(
                        method=m.group("method").upper(),
                        path=normalize_path(raw),
                        file=str(file.relative_to(ROOT)).replace("\\", "/"),
                        line=line_of(text, m.start()),
                        raw=raw,
                    )
                )

            for m in FETCH_RE.finditer(text):
                raw = m.group("url")
                if not raw.startswith("/"):
                    continue
                method = "GET"
                options_slice = text[m.end() : m.end() + 220]
                mm = METHOD_IN_OPTIONS_RE.search(options_slice)
                if mm:
                    method = mm.group("method").upper()
                calls.append(
                    FrontCall(
                        method=method,
                        path=normalize_path(raw),
                        file=str(file.relative_to(ROOT)).replace("\\", "/"),
                        line=line_of(text, m.start()),
                        raw=raw,
                    )
                )
    return calls


def load_openapi_ops() -> set[Op]:
    sys.path.insert(0, str(API_ROOT))
    from app.main import app  # noqa: WPS433

    schema = app.openapi()
    ops: set[Op] = set()
    for path, methods in schema.get("paths", {}).items():
        npath = normalize_path(path)
        for method in methods.keys():
            ops.add(Op(method=method.upper(), path=npath))
    return ops


def load_exclusions() -> tuple[set[Op], list[str]]:
    exact: set[Op] = set()
    prefixes: list[str] = []
    if not EXCLUSIONS_FILE.exists():
        return exact, prefixes
    data = json.loads(EXCLUSIONS_FILE.read_text(encoding="utf-8"))
    for item in data.get("exclude_exact", []):
        exact.add(Op(method=item["method"].upper(), path=normalize_path(item["path"])))
    for item in data.get("exclude_prefix", []):
        prefixes.append(item["prefix"])
    return exact, prefixes


def is_user_facing(op: Op) -> bool:
    return any(op.path.startswith(prefix) for prefix in USER_PREFIXES)


def is_excluded(op: Op, exact: set[Op], prefixes: list[str]) -> bool:
    if op in exact:
        return True
    return any(op.path.startswith(p) for p in prefixes)


def write_report(
    *,
    mode: str,
    front_calls_total: int,
    front_unique: int,
    openapi_ops_count: int,
    user_ops_count: int,
    missing_in_openapi: list[FrontCall],
    uncovered_user_ops: list[Op],
) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# API-UI Contract Audit Report")
    lines.append("")
    lines.append(f"- Generated at (UTC): `{ts}`")
    lines.append(f"- Mode: `{mode}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Front calls (total): **{front_calls_total}**")
    lines.append(f"- Front calls (unique method+path): **{front_unique}**")
    lines.append(f"- OpenAPI operations: **{openapi_ops_count}**")
    lines.append(f"- User-facing OpenAPI operations: **{user_ops_count}**")
    lines.append(f"- Front -> OpenAPI missing: **{len(missing_in_openapi)}**")
    lines.append(f"- OpenAPI(user-facing) -> UI uncovered: **{len(uncovered_user_ops)}**")
    lines.append("")

    lines.append("## Front -> OpenAPI Missing")
    lines.append("")
    if not missing_in_openapi:
        lines.append("- None")
    else:
        for item in sorted(missing_in_openapi, key=lambda x: (x.file, x.line, x.method, x.path)):
            lines.append(
                f"- `{item.method} {item.path}` in `{item.file}:{item.line}` (raw: `{item.raw}`)"
            )
    lines.append("")

    lines.append("## OpenAPI User-Facing -> UI Uncovered")
    lines.append("")
    if not uncovered_user_ops:
        lines.append("- None")
    else:
        for op in sorted(uncovered_user_ops, key=lambda x: (x.path, x.method)):
            lines.append(f"- `{op.method} {op.path}`")
    lines.append("")

    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["forward", "reverse", "both"], default="both")
    args = parser.parse_args()

    front_calls = collect_front_calls()
    openapi_ops = load_openapi_ops()
    exact_excl, prefix_excl = load_exclusions()

    unique_front_map: dict[tuple[str, str], FrontCall] = {}
    for c in front_calls:
        unique_front_map.setdefault((c.method, c.path), c)

    openapi_set = {(o.method, o.path) for o in openapi_ops}
    missing_in_openapi = [
        c for k, c in unique_front_map.items() if k not in openapi_set
    ]

    front_ops = {Op(method=k[0], path=k[1]) for k in unique_front_map.keys()}
    user_ops = {o for o in openapi_ops if is_user_facing(o)}
    uncovered_user_ops = [
        o for o in user_ops if o not in front_ops and not is_excluded(o, exact_excl, prefix_excl)
    ]

    write_report(
        mode=args.mode,
        front_calls_total=len(front_calls),
        front_unique=len(unique_front_map),
        openapi_ops_count=len(openapi_ops),
        user_ops_count=len(user_ops),
        missing_in_openapi=missing_in_openapi,
        uncovered_user_ops=uncovered_user_ops,
    )

    print(f"front_calls_total={len(front_calls)}")
    print(f"front_calls_unique={len(unique_front_map)}")
    print(f"openapi_operations={len(openapi_ops)}")
    print(f"user_facing_openapi_operations={len(user_ops)}")
    print(f"missing_in_openapi={len(missing_in_openapi)}")
    print(f"uncovered_user_ops={len(uncovered_user_ops)}")
    print(f"report={REPORT_FILE.relative_to(ROOT).as_posix()}")

    fail_forward = len(missing_in_openapi) > 0
    fail_reverse = len(uncovered_user_ops) > 0

    if args.mode == "forward":
        if fail_forward:
            print("FAIL: front endpoints missing in OpenAPI.")
            return 1
        print("PASS: front endpoints are covered by OpenAPI.")
        return 0
    if args.mode == "reverse":
        if fail_reverse:
            print("FAIL: OpenAPI user-facing endpoints are not covered by UI.")
            return 1
        print("PASS: OpenAPI user-facing endpoints are covered by UI.")
        return 0

    if fail_forward or fail_reverse:
        print("FAIL: API-UI contract mismatch detected.")
        return 1
    print("PASS: bidirectional API-UI contract checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

