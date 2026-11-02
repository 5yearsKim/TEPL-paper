#!/usr/bin/env python3
"""Compare both backends on unchanged frozen tasks; retain commands and artifacts."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import tempfile
import time

PAPER = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def classify(reason, phase, returncode):
    if returncode == "timeout":
        return "timeout"
    if phase != "check":
        return phase + "_failed"
    if "outside ordered axis/value contracts" in reason or "require contraction/permutation/summation definitions" in reason:
        return "outside_templates"
    if "independent automatic fields" in reason or ("without derive helpers: " in reason and not reason.split("without derive helpers: ", 1)[1].strip()):
        return "rhs_fields_or_derivations"
    if "canonical dtype contracts" in reason:
        return "dtype_contract"
    if "outside certified view/reindexing schemas" in reason:
        return "outside_schemas"
    if "core schema cannot certify supplied fields" in reason:
        return "supplied_fields_or_helpers"
    if "core guard proof unresolved" in reason:
        return "guard_unresolved"
    if "core backend requires admitted" in reason:
        return "structural_admission"
    return "proof_unresolved" if reason else "check_failed"


def summarize(rows, backends=("default", "core")):
    def counts(population):
        return dict(tasks=len(population), **{
            backend: dict(accepted=sum(r[backend]["accepted"] for r in population),
                          outcomes=dict(Counter(r[backend]["outcome"] for r in population)))
            for backend in backends})
    populations = {
        "axis": [r for r in rows if r["requested_axis_fields"]],
        "verification": [r for r in rows if not r["requested_axis_fields"]],
        "all": rows,
    }
    families = {}
    for op in sorted({op for r in rows for op in r["required_operations"]}):
        group = [r for r in rows if op in r["required_operations"]]
        families[op] = dict(all=counts(group), axis=counts([r for r in group if r["requested_axis_fields"]]))
    return dict(populations={k: counts(v) for k, v in populations.items()}, families=families,
                default_changed=[r["case"] for r in rows if r["default"]["accepted"] != r["previous_default_accepted"]])


def archive_programs(out, rows, backends=("default", "core")):
    """Retain exact program bytes compactly; verify before removing loose copies."""
    with tarfile.open(out / "programs.tar.gz", "w:gz") as archive:
        for path in sorted((out / "programs").rglob("*.json")):
            archive.add(path, arcname=str(path.relative_to(out)), recursive=False)
    with tarfile.open(out / "programs.tar.gz", "r:gz") as archive:
        expected = {r[b]["artifact"]: r[b]["artifact_sha256"]
                    for r in rows for b in backends if r[b]["accepted"]}
        assert set(archive.getnames()) == set(expected)
        for name, digest in expected.items():
            assert hashlib.sha256(archive.extractfile(name).read()).hexdigest() == digest
    shutil.rmtree(out / "programs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--code-root", type=Path, required=True)
    parser.add_argument("--dialects", type=Path, required=True,
                        help="Frozen dialects used by the original 123-task experiment")
    parser.add_argument("--output", type=Path, default=PAPER / "evaluation/backend-comparison")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--backends", nargs="+", choices=["default", "core", "certified"], default=["default", "core"])
    args = parser.parse_args()
    backends = tuple(dict.fromkeys(args.backends))
    if "default" not in backends:
        parser.error("include default for the frozen acceptance comparison")
    out = args.output.resolve()
    if (out / "results.json").exists():
        parser.error("output already contains results; use a fresh directory")
    for name in ("inputs", "logs", *["programs/" + b for b in backends]):
        (out / name).mkdir(parents=True, exist_ok=True)
    shutil.copytree(args.dialects, out / "inputs/dialects", dirs_exist_ok=True)
    frozen_path = PAPER / "evaluation/recorded-results.json"
    frozen = json.loads(frozen_path.read_text())
    assert len(frozen["records"]) == 123
    inputs = []
    for old in frozen["records"]:
        source = frozen["source_snapshots"][old["case"]]["task"]
        path = out / "inputs" / (old["case"] + ".tepl")
        path.write_text(source)
        assert path.read_bytes() == source.encode()
        inputs.append(dict(case=old["case"], rule_name=old["rule_name"],
                           required_operations=old["required_operations"],
                           requested_axis_fields=len(old["axis_fields"]),
                           axis_fields=old["axis_fields"],
                           previous_default_accepted=old["outcome"] in {"verified", "inferred"},
                           source=str(path.relative_to(out)), source_sha256=sha(path)))
    save(out / "plan.json", inputs)
    code = args.code_root.resolve()
    patch = subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=code)
    (out / "implementation.patch").write_bytes(patch)
    # Include untracked implementation files that a Git patch cannot preserve.
    with tarfile.open(out / "implementation-source.tar.gz", "w:gz") as archive:
        names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=code, text=True).splitlines()
        for name in sorted(set(names)):
            path = code / name
            if path.is_file() and (name.startswith(("src/", "schema/", "labs/accepted_core/", "tools/build_program_schema.py", "design/core-acceptance.md")) or "/" not in name):
                archive.add(path, arcname=name, recursive=False)
    (out / "runner.py").write_bytes(Path(__file__).read_bytes())
    binary_hash = sha(args.compiler)
    provenance = dict(protocol="frozen_123_paired_backends_v1", run_at_utc=datetime.now(timezone.utc).isoformat(),
                      compiler_sha256=binary_hash,
                      checkout=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=code, text=True).strip(),
                      build_command="bazel build -c opt //:tepl", jobs=args.jobs, timeout_seconds=args.timeout, backends=list(backends),
                      inventory_sha256=sha(frozen_path), patch_sha256=sha(out / "implementation.patch"),
                      runner_sha256=sha(out / "runner.py"),
                      platform=platform.platform(),
                      cpu=next(line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.startswith("model name")),
                      timing_claim=False, source_mutations="none; exact frozen task text and dialects")
    save(out / "provenance.json", provenance)

    with tempfile.TemporaryDirectory(prefix="tepl-backend-comparison-") as temporary:
        binary = Path(temporary) / "tepl"
        shutil.copy2(args.compiler, binary)
        assert sha(binary) == binary_hash

        def attempt(row, backend):
            flags = ["--" + backend] if backend != "default" else []
            artifact = out / "programs" / backend / (row["case"] + ".json")
            source = out / row["source"]
            result = dict(accepted=False, commands=[])
            phases = [
                ("check", [str(binary), "check", str(source), "--semantic-policy=algebraic", "--rule", row["rule_name"], *flags]),
                ("compile", [str(binary), "compile", str(source), "--semantic-policy=algebraic", *flags, "-o", str(artifact)]),
                ("validate", [str(binary), "validate", str(artifact)]),
            ]
            for phase, argv in phases:
                start = time.monotonic()
                try:
                    process = subprocess.run(argv, text=True, capture_output=True, timeout=args.timeout)
                    status, stdout, stderr = process.returncode, process.stdout, process.stderr
                except subprocess.TimeoutExpired as error:
                    status = "timeout"
                    stdout = error.stdout or b""
                    stderr = error.stderr or b""
                    stdout = stdout.decode(errors="replace") if isinstance(stdout, bytes) else stdout
                    stderr = stderr.decode(errors="replace") if isinstance(stderr, bytes) else stderr
                log = out / "logs" / f"{row['case']}.{backend}.{phase}.txt"
                log.write_text(stdout + "\n" + stderr)
                result["commands"].append(dict(phase=phase, argv=argv, returncode=status,
                                               seconds=time.monotonic() - start, log=str(log.relative_to(out))))
                if phase == "check":
                    result["reason"] = "\n".join(line.strip().removeprefix("reason:").strip() for line in stdout.splitlines() if line.strip().startswith("reason:"))
                    proved = stdout.count("status=proved") == 1 and "additional-guard: true" in stdout
                else:
                    proved = True
                if status != 0 or not proved:
                    result.update(outcome=classify(result.get("reason", ""), phase, status), failure_stage=phase)
                    return result
            program = json.loads(artifact.read_text())
            if backend != "default" and "tepl.core-dag.v1" not in program["capabilities"]:
                raise ValueError("core acceptance without core DAG capability: " + row["case"])
            if backend != "default":
                extension_kinds = {"reverse", "broadcast", "multiplication", "negation", "unit_removal"}
                for rule in program["program"]["rules"]:
                    core = rule.get("core")
                    if core and any(n["kind"] in extension_kinds for side in ("source", "replacement") for n in core["program"][side]):
                        assert "tepl.core-schemas.v1" in program["capabilities"], row["case"]
            def unresolved(value):
                if isinstance(value, dict):
                    return value.get("kind") in {"auto", "auto_field", "hole"} or any(unresolved(v) for v in value.values())
                return isinstance(value, list) and any(unresolved(v) for v in value)
            if unresolved(program):
                raise ValueError("unresolved executable field: " + row["case"])
            result.update(accepted=True, outcome="accepted", artifact=str(artifact.relative_to(out)), artifact_sha256=sha(artifact))
            return result

        def work(row):
            row = dict(row)
            for backend in backends:
                row[backend] = attempt(row, backend)
            for backend in backends:
                if backend != "default" and row[backend]["outcome"] == "outside_templates":
                    supported = {"dot_general", "transpose", "reduce_sum", "add"}
                    if backend == "certified":
                        supported |= {"reverse", "broadcast_in_dim", "multiply", "negate", "remove_unit_axes"}
                    row[backend]["outside_template_operations"] = sorted(set(row["required_operations"]) - supported)
            print(row["case"] + ": " + " ".join(b + "=" + row[b]["outcome"] for b in backends), flush=True)
            return row

        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            rows = list(pool.map(work, inputs))
        assert sha(binary) == binary_hash
    assert sha(args.compiler) == binary_hash
    for row in rows:
        assert sha(out / row["source"]) == row["source_sha256"]
    save(out / "results.json", dict(provenance=provenance, records=rows))
    summary = summarize(rows, backends)
    save(out / "summary.json", summary)
    with (out / "cases.csv").open("w", newline="") as stream:
        fields = ["case", "operations", "axis_fields", "source_sha256"] + [f"{b}_{k}" for b in backends for k in ("outcome", "reason", "outside_template_operations")]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            item = dict(case=row["case"], operations=";".join(row["required_operations"]), axis_fields=row["requested_axis_fields"], source_sha256=row["source_sha256"])
            for b in backends:
                item.update({f"{b}_{k}": row[b][k] for k in ("outcome", "reason")})
                item[f"{b}_outside_template_operations"] = ";".join(row[b].get("outside_template_operations", []))
            writer.writerow(item)
    with (out / "families.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["operation", "tasks", "axis_tasks"] + [f"{b}_{scope}_accepted" for scope in ("all", "axis") for b in backends])
        for op, counts in summary["families"].items():
            writer.writerow([op, counts["all"]["tasks"], counts["axis"]["tasks"], *[counts[p][b]["accepted"] for p in ("all", "axis") for b in backends]])
    archive_programs(out, rows, backends)
    save(out / "manifest.json", {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob("*")) if p.is_file() and p.name != "manifest.json"})
    print(json.dumps(summary["populations"], indent=2))


if __name__ == "__main__":
    main()
