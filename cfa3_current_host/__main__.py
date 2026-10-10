"""CFA3 Current Host and Community SDK non-admitting command-line interface.

Use python3 -m cfa3_current_host --help.
No command starts a plugin, imports third-party code, modifies host drivers,
certifies vendor software or reports physical Current Host PASS.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from enum import Enum
from pathlib import Path

from .core import Component, Graph, Handoff, Ownership
from .developer_sdk import build_bundle, run_static_testkit, scaffold_plugin


def _jsonable(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(v) for v in value]
    return value


def plan_file(path, changed, trigger):
    source = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(source, dict) or set(source) != {"components", "handoffs"}:
        raise ValueError("graph JSON requires components and handoffs")
    graph = Graph()
    for item in source["components"]:
        graph.register_component(Component(
            component_id=item["component_id"],
            layer=item["layer"],
            revision=item["revision"],
            ownership=Ownership(item["ownership"]),
            capability_ids=tuple(item.get("capability_ids", [])),
            gui=item.get("gui", False),
            parent_id=item.get("parent_id"),
        ))
    for item in source["handoffs"]:
        graph.register_handoff(Handoff(**item))
    from .core import FULL_TRIGGERS
    if trigger not in ("CODE", "INTERFACE", "HOST_CONNECTOR", *sorted(FULL_TRIGGERS)):
        raise ValueError("unrecognized change trigger")
    report = graph.plan(changed, trigger=trigger)
    result = _jsonable(asdict(report))
    result.update({
        "physical_current_host_pass": False,
        "evidence_status": "PENDING_EXTERNAL_PHYSICAL_PROOFS",
        "vendor_drivers_qualified": False,
        "commercial_products_qualified": False,
        "community_plugin_products_qualified": False,
    })
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(prog="cfa3_current_host")
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("plan", help="plan exact CFA3-owned delta tests")
    p.add_argument("--graph", required=True)
    p.add_argument("--changed", nargs="+", required=True)
    p.add_argument("--trigger", default="CODE")
    s = commands.add_parser("plugin-scaffold", help="create a new declarative developer SDK starter")
    s.add_argument("--target", required=True)
    s.add_argument("--id", required=True)
    s.add_argument("--app", required=True)
    s.add_argument("--publisher", required=True)
    s.add_argument("--license", required=True)
    b = commands.add_parser("plugin-build", help="create deterministic plugin bundle, no execution")
    b.add_argument("--root", required=True)
    b.add_argument("--output", required=True)
    i = commands.add_parser("plugin-inspect", help="static host contract testkit")
    i.add_argument("--bundle", required=True)
    i.add_argument("--available-app", action="append", default=[])
    t = commands.add_parser("selftest", help="run CFA3-only reference tests, never issue physical PASS")
    t.add_argument("--repo", default=".")
    t.add_argument("--output", default=None)
    cc = commands.add_parser("catalog-check", help="check 200 CFA3 capabilities without physical PASS")
    cc.add_argument("--catalog", required=True)
    args = parser.parse_args(argv)
    if args.command == "plan":
        result = plan_file(args.graph, args.changed, args.trigger)
    elif args.command == "plugin-scaffold":
        paths = scaffold_plugin(Path(args.target), plugin_id=args.id,
                                app=args.app, publisher=args.publisher,
                                license_expression=args.license)
        result = {"created": [str(x) for x in paths],
                  "admission": "NOT_ADMITTED", "physical_current_host_pass": False}
    elif args.command == "plugin-build":
        output = Path(args.output)
        if output.exists():
            raise ValueError("plugin bundle output already exists")
        binary = build_bundle(Path(args.root))
        with output.open("xb") as writer:
            writer.write(binary)
        result = {"bundle": str(output), "bytes": len(binary),
                  "admission": "NOT_ADMITTED", "physical_current_host_pass": False}
    elif args.command == "plugin-inspect":
        result = run_static_testkit(Path(args.bundle).read_bytes(),
                                    available_cfa3_apps=frozenset(args.available_app))
    elif args.command == "catalog-check":
        from .capability_catalog import load_capability_catalog
        result = load_capability_catalog(Path(args.catalog)).reconciliation()
    elif args.command == "selftest":
        from .local_runner import run_cfa3_owned_reference_tests
        result = run_cfa3_owned_reference_tests(Path(args.repo))
        if args.output is not None:
            output = Path(args.output)
            with output.open("x", encoding="utf-8") as writer:
                writer.write(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    else:
        raise AssertionError("unreachable")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
