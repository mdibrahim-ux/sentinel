from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import PurePosixPath
from typing import Any

SKIP_PARTS = {
    ".git", "node_modules", "dist", "build", "coverage", ".venv", "venv", "vendor",
    "__pycache__", ".next", "target", "site-packages", "bower_components",
}
SOURCE_EXTENSIONS = {
    ".py": "Python", ".pyi": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".mjs": "JavaScript", ".cjs": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".java": "Java", ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
    ".cs": "C#", ".cpp": "C++", ".cc": "C++", ".c": "C", ".h": "C/C++", ".hpp": "C++",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".sql": "SQL", ".sh": "Shell",
    ".yaml": "YAML", ".yml": "YAML", ".json": "JSON", ".toml": "TOML",
}
TEXT_EXTENSIONS = set(SOURCE_EXTENSIONS) | {
    ".md", ".txt", ".ini", ".cfg", ".env.example", ".dockerfile", ".xml", ".lock",
    ".properties", ".gradle", ".tf", ".graphql", ".gql", ".make", ".mk", ".rst",
}

SECRET_PATTERNS = [
    ("SEC-001", "Potential hard-coded credential", re.compile(
        r"(?i)(?:api[_-]?key|secret[_-]?key|client[_-]?secret|access[_-]?token|password)\s*[:=]\s*['\"](?!\s*(?:\*{3,}|<[^>]+>|your_|changeme|example|dummy|placeholder|redacted))[^'\"\s]{8,}['\"]"
    )),
    ("SEC-002", "Private key material", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("SEC-003", "Possible cloud access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
]

RULES = {
    "PY-SEC-001": ("HIGH", "Dynamic code execution via eval/exec", "User-controlled text passed to eval/exec can execute arbitrary Python code.", "Replace dynamic execution with explicit parsing or a constrained mapping of allowed operations.", "security"),
    "PY-SEC-002": ("HIGH", "Subprocess uses shell=True", "Shell interpolation can turn untrusted input into operating-system commands.", "Pass an argument list with shell=False and validate each argument.", "security"),
    "PY-SEC-003": ("MEDIUM", "Potential unsafe pickle deserialization", "Untrusted pickle payloads can execute code during deserialization.", "Use a data-only format such as JSON for untrusted input; only load trusted, integrity-checked pickle data.", "security"),
    "PY-SEC-004": ("MEDIUM", "Potential unsafe YAML load", "yaml.load without a safe loader may construct arbitrary Python objects.", "Use yaml.safe_load or explicitly configure SafeLoader for untrusted YAML.", "security"),
    "JS-SEC-001": ("HIGH", "Dynamic JavaScript evaluation", "eval or Function constructors can execute attacker-controlled code.", "Replace dynamic evaluation with structured data handling and explicit dispatch.", "security"),
    "JS-SEC-002": ("MEDIUM", "Unsafe HTML injection sink", "Assigning untrusted strings to innerHTML can enable cross-site scripting.", "Prefer textContent or sanitize HTML with a well-maintained allow-list sanitizer.", "security"),
    "JS-SEC-003": ("HIGH", "Shell command execution API", "Executing a shell command with interpolated data can permit command injection.", "Use a fixed executable and argument arrays; validate input and avoid shell execution.", "security"),
    "JS-SEC-004": ("MEDIUM", "React raw HTML rendering", "dangerouslySetInnerHTML bypasses React's normal text escaping.", "Avoid raw HTML or sanitize the input before rendering it.", "security"),
    "GEN-SEC-001": ("HIGH", "Possible hard-coded credential", "A credential-like value appears to be embedded in source code.", "Rotate exposed credentials, remove them from history where appropriate, and load secrets from a managed secret store or environment.", "security"),
    "GEN-SEC-002": ("HIGH", "Private key material in repository", "Private key material should not be committed to source control.", "Revoke or rotate the key, remove it from repository history, and load it from a secret manager.", "security"),
    "GEN-SEC-003": ("HIGH", "Possible cloud access key", "The value resembles an AWS access key identifier.", "Revoke or rotate the credential and use short-lived role credentials rather than embedded keys.", "security"),
    "QUAL-001": ("LOW", "Large source file", "Large files can hide unrelated responsibilities and increase review cost.", "Consider extracting cohesive modules and adding tests around the boundaries.", "quality"),
    "QUAL-002": ("LOW", "Debug mode or verbose exception output", "Debug settings can expose internals if enabled in a deployed environment.", "Confirm this setting is disabled in production and route errors through structured logging.", "quality"),
    "QUAL-003": ("LOW", "Placeholder implementation marker", "A TODO/FIXME marker may indicate unfinished behavior.", "Create a tracked issue or resolve the marker before release if it affects a critical path.", "quality"),
    "DEP-001": ("LOW", "Unpinned dependency version", "A dependency range without a lock or exact pin weakens reproducibility.", "Commit a lockfile or pin the version according to your team's update policy.", "dependency"),
    "DOC-001": ("INFO", "README not detected", "A repository overview was not found at the root or in common readme locations.", "Add setup, architecture, testing, configuration, and deployment instructions.", "documentation"),
    "TEST-001": ("INFO", "Test files not detected", "No likely test files or test directories were detected.", "Add automated tests for core business rules and security-sensitive behavior.", "quality"),
}


def _normalize_path(path: str) -> str:
    path = path.replace("\\", "/").lstrip("/")
    parts = PurePosixPath(path).parts
    if not path or ".." in parts or any(part in SKIP_PARTS for part in parts):
        return ""
    return path[:350]


def _safe_evidence(line: str) -> str:
    redacted = line.strip()[:260]
    for _, _, pat in SECRET_PATTERNS:
        redacted = pat.sub("[REDACTED CREDENTIAL-LIKE VALUE]", redacted)
    redacted = re.sub(r"(?i)(authorization\s*[:=]\s*)(bearer\s+)?[^\s,;]+", r"\1[REDACTED]", redacted)
    return redacted


def _finding(rule_id: str, title: str, severity: str, category: str, path: str, line: int,
             evidence: str, description: str, remediation: str, confidence: float = 0.8,
             verified: str = "pattern-detected") -> dict[str, Any]:
    fid = hashlib.sha1(f"{rule_id}:{path}:{line}:{title}".encode()).hexdigest()[:12].upper()
    return {
        "id": fid, "rule_id": rule_id, "title": title, "severity": severity,
        "category": category, "path": path, "line_start": line, "line_end": line,
        "evidence": _safe_evidence(evidence), "description": description,
        "impact": f"Potential {severity.lower()}-priority issue; confirm whether the evidence is reachable and exploitable in the deployed context.",
        "remediation": remediation, "confidence": round(confidence, 2), "verification": verified,
        "status": "open", "note": "", "references": _reference_for(rule_id),
    }


def _reference_for(rule_id: str) -> list[str]:
    if rule_id.startswith("PY-"):
        return ["https://docs.python.org/3/library/ast.html", "https://owasp.org/www-project-top-ten/"]
    if rule_id.startswith("JS-"):
        return ["https://owasp.org/www-project-top-ten/", "https://developer.mozilla.org/en-US/docs/Web/Security"]
    if rule_id.startswith("DEP-"):
        return ["https://pip.pypa.io/en/stable/topics/repeatable-installs/", "https://docs.npmjs.com/cli/v10/configuring-npm/package-lock-json"]
    return ["https://owasp.org/www-project-top-ten/"]


class PythonSecurityVisitor(ast.NodeVisitor):
    def __init__(self, path: str, source: str):
        self.path, self.source = path, source
        self.findings: list[dict[str, Any]] = []
        self.lines = source.splitlines()

    def add(self, rule: str, lineno: int, confidence: float = .86) -> None:
        severity, title, description, remediation, category = RULES[rule]
        line = self.lines[lineno - 1] if 0 < lineno <= len(self.lines) else ""
        self.findings.append(_finding(rule, title, severity, category, self.path, lineno, line,
                                      description, remediation, confidence))

    def visit_Call(self, node: ast.Call) -> None:
        name = node.func.id if isinstance(node.func, ast.Name) else ""
        dotted = ""
        if isinstance(node.func, ast.Attribute):
            dotted = node.func.attr
            if isinstance(node.func.value, ast.Name):
                dotted = f"{node.func.value.id}.{dotted}"
        if name in {"eval", "exec"}:
            self.add("PY-SEC-001", node.lineno, .9)
        if dotted in {"subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_output", "subprocess.check_call"}:
            if any(k.arg == "shell" and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords):
                self.add("PY-SEC-002", node.lineno, .94)
        if dotted in {"pickle.loads", "pickle.load", "_pickle.loads", "_pickle.load"}:
            self.add("PY-SEC-003", node.lineno, .82)
        if dotted in {"yaml.load", "yaml.unsafe_load"}:
            safe = any(k.arg == "Loader" and getattr(k.value, "id", "") in {"SafeLoader", "CSafeLoader"} for k in node.keywords)
            if not safe:
                self.add("PY-SEC-004", node.lineno, .8)
        self.generic_visit(node)


def analyze_files(files: dict[str, bytes], options: dict[str, bool] | None = None,
                  source_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    options = options or {"include_security": True, "include_quality": True, "include_architecture": True}
    source_metadata = source_metadata or {}
    normalized: dict[str, str] = {}
    binary_skipped = 0
    for raw_path, raw_bytes in files.items():
        path = _normalize_path(raw_path)
        if not path or len(raw_bytes) > 1024 * 1024:
            continue
        ext = PurePosixPath(path).suffix.lower()
        if ext not in TEXT_EXTENSIONS and not PurePosixPath(path).name.lower().startswith(("dockerfile", "makefile")):
            binary_skipped += 1
            continue
        if b"\x00" in raw_bytes[:4096]:
            binary_skipped += 1
            continue
        try:
            normalized[path] = raw_bytes.decode("utf-8", errors="replace")
        except Exception:
            binary_skipped += 1

    findings: list[dict[str, Any]] = []
    file_rows: list[dict[str, Any]] = []
    lang_counts: Counter[str] = Counter()
    lang_lines: Counter[str] = Counter()
    total_lines = 0
    total_bytes = 0
    imports: dict[str, set[str]] = defaultdict(set)
    total_functions = 0
    total_classes = 0
    py_parse_errors = 0
    test_files: list[str] = []
    dependency_files: list[str] = []
    has_readme = any(PurePosixPath(p).name.lower().startswith("readme") for p in normalized)
    root_files = sorted(p for p in normalized if len(PurePosixPath(p).parts) == 1)

    for path, source in sorted(normalized.items()):
        ext = PurePosixPath(path).suffix.lower()
        lang = SOURCE_EXTENSIONS.get(ext, "Config/Docs")
        lines = source.splitlines()
        loc = sum(1 for line in lines if line.strip() and not line.strip().startswith(("#", "//", "/*", "* ")))
        total_lines += len(lines)
        total_bytes += len(source.encode("utf-8"))
        if lang != "Config/Docs":
            lang_counts[lang] += 1
            lang_lines[lang] += loc
        file_rows.append({"path": path, "language": lang, "lines": len(lines), "loc": loc, "bytes": len(source.encode("utf-8"))})
        lower = path.lower()
        if any(x in lower for x in ("test_", "_test.", "/tests/", "/test/", ".spec.", ".test.")):
            test_files.append(path)
        if PurePosixPath(path).name.lower() in {"requirements.txt", "pyproject.toml", "poetry.lock", "pipfile", "pipfile.lock", "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "pom.xml", "go.mod", "cargo.toml"}:
            dependency_files.append(path)

        if options.get("include_security", True):
            for number, line in enumerate(lines, 1):
                for rule_id, title, pattern in SECRET_PATTERNS:
                    if pattern.search(line):
                        sev, _, desc, fix, category = RULES["GEN-SEC-001" if rule_id == "SEC-001" else "GEN-SEC-002" if rule_id == "SEC-002" else "GEN-SEC-003"]
                        # Never preserve the matched value in any finding field.
                        rid = "GEN-SEC-001" if rule_id == "SEC-001" else "GEN-SEC-002" if rule_id == "SEC-002" else "GEN-SEC-003"
                        findings.append(_finding(rid, title, sev, category, path, number, line, desc, fix, .76, "pattern-detected"))
                if ext in {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}:
                    patterns = [
                        ("JS-SEC-001", re.compile(r"\beval\s*\(|\bnew\s+Function\s*\(")),
                        ("JS-SEC-002", re.compile(r"\.innerHTML\s*=")),
                        ("JS-SEC-003", re.compile(r"\bexec(?:Sync)?\s*\([^\n]*(?:\$\{|\+\s*[A-Za-z_$]|\`)") ),
                        ("JS-SEC-004", re.compile(r"dangerouslySetInnerHTML")),
                    ]
                    for rid, pat in patterns:
                        if pat.search(line):
                            sev, title, desc, fix, category = RULES[rid]
                            findings.append(_finding(rid, title, sev, category, path, number, line, desc, fix, .8))
                if re.search(r"(?i)\bdebug\s*=\s*(?:true|1)\b|DEBUG\s*=\s*['\"](?:true|1|yes)['\"]", line):
                    if options.get("include_quality", True):
                        sev, title, desc, fix, category = RULES["QUAL-002"]
                        findings.append(_finding("QUAL-002", title, sev, category, path, number, line, desc, fix, .78))
                if options.get("include_quality", True) and re.search(r"\b(TODO|FIXME|XXX)\b", line):
                    sev, title, desc, fix, category = RULES["QUAL-003"]
                    findings.append(_finding("QUAL-003", title, sev, category, path, number, line, desc, fix, .64))
            if len(lines) > 500 and options.get("include_quality", True):
                sev, title, desc, fix, category = RULES["QUAL-001"]
                findings.append(_finding("QUAL-001", title, sev, category, path, 1,
                                         f"File contains {len(lines)} lines.", desc, fix, .9))
        if ext == ".py":
            try:
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        total_functions += 1
                    elif isinstance(node, ast.ClassDef):
                        total_classes += 1
                if options.get("include_security", True):
                    visitor = PythonSecurityVisitor(path, source)
                    visitor.visit(tree)
                    findings.extend(visitor.findings)
                if options.get("include_architecture", True):
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports[path].add(alias.name)
                        elif isinstance(node, ast.ImportFrom) and node.module:
                            imports[path].add(node.module)
            except SyntaxError:
                py_parse_errors += 1
        elif ext in {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"} and options.get("include_architecture", True):
            for match in re.finditer(r"(?:import\s+(?:[^'\"]+\s+from\s+)?|require\s*\()\s*['\"]([^'\"]+)['\"]", source):
                imports[path].add(match.group(1))

    if options.get("include_quality", True):
        if not has_readme:
            sev, title, desc, fix, category = RULES["DOC-001"]
            findings.append(_finding("DOC-001", title, sev, category, "", 0, "No README file found.", desc, fix, .95))
        if not test_files:
            sev, title, desc, fix, category = RULES["TEST-001"]
            findings.append(_finding("TEST-001", title, sev, category, "", 0, "No likely test files found.", desc, fix, .85))
        for path in dependency_files:
            if PurePosixPath(path).name.lower() == "requirements.txt":
                for number, line in enumerate(normalized[path].splitlines(), 1):
                    stripped = line.strip()
                    if stripped and not stripped.startswith(("#", "-", "git+", "http:")) and not re.search(r"(?:==|===|~=)\s*\d", stripped):
                        findings.append(_finding("DEP-001", RULES["DEP-001"][1], "LOW", "dependency", path, number,
                                                 line, RULES["DEP-001"][2], RULES["DEP-001"][3], .7))

    unique: dict[str, dict[str, Any]] = {}
    for f in findings:
        unique.setdefault(f["id"], f)
    findings = list(unique.values())
    severity_counts = Counter(f["severity"] for f in findings)
    category_counts = Counter(f["category"] for f in findings)
    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    findings.sort(key=lambda f: (severity_order.index(f["severity"]) if f["severity"] in severity_order else 5, -f["confidence"], f["path"], f["line_start"]))

    graph_edges: list[dict[str, str]] = []
    modules = set(normalized)
    for source_path, targets in imports.items():
        for target in targets:
            match = None
            stem = target.replace(".", "/").replace("@/", "")
            for candidate in modules:
                base = str(PurePosixPath(candidate).with_suffix(""))
                if target.startswith("."):
                    parent = str(PurePosixPath(source_path).parent)
                    base = str(PurePosixPath(parent, target).as_posix())
                    base = str(PurePosixPath(base))
                if base == stem or base.endswith("/" + stem) or base.startswith(stem + "/"):
                    match = candidate
                    break
            if match and match != source_path and len(graph_edges) < 200:
                graph_edges.append({"source": source_path, "target": match, "kind": "import"})

    total_files = len(normalized)
    # Transparent heuristic health score, not a claim that the repository is secure.
    penalties = sum({"CRITICAL": 18, "HIGH": 10, "MEDIUM": 5, "LOW": 2, "INFO": .5}.get(f["severity"], 1) * f["confidence"] for f in findings)
    health_score = max(0, min(100, round(100 - penalties / max(1, total_files) * 4)))
    source_commit = source_metadata.get("commit_sha")
    return {
        "schema_version": "1.0",
        "project": source_metadata.get("project_label") or source_metadata.get("repo_name") or "Uploaded codebase",
        "source": {"type": source_metadata.get("type", "upload"), "repository_url": source_metadata.get("repository_url", ""),
                   "branch": source_metadata.get("branch", ""), "commit_sha": source_commit or "unknown", "snapshot_at": source_metadata.get("snapshot_at", "")},
        "summary": {"health_score": health_score, "health_method": "100 minus confidence-weighted finding penalties, normalized by analyzed file count. A heuristic triage aid, not a security certification.",
                    "files_analyzed": total_files, "source_lines": sum(r["loc"] for r in file_rows), "physical_lines": total_lines,
                    "bytes_analyzed": total_bytes, "findings_total": len(findings), "functions": total_functions,
                    "classes": total_classes, "parse_errors": py_parse_errors, "binary_or_unsupported_skipped": binary_skipped,
                    "tests_detected": len(test_files), "dependency_files": len(dependency_files)},
        "languages": [{"name": name, "files": lang_counts[name], "loc": lang_lines[name]} for name in sorted(lang_counts, key=lambda n: (-lang_lines[n], n))],
        "severity_counts": {s: severity_counts.get(s, 0) for s in severity_order},
        "category_counts": dict(category_counts),
        "findings": findings,
        "files": sorted(file_rows, key=lambda r: (-r["loc"], r["path"])),
        "architecture": {"nodes": [{"id": p, "language": SOURCE_EXTENSIONS.get(PurePosixPath(p).suffix.lower(), "Config/Docs")} for p in sorted(normalized) if PurePosixPath(p).suffix.lower() in SOURCE_EXTENSIONS],
                          "edges": graph_edges, "scope_note": "Edges are inferred from static import statements; dynamic loading and runtime-only relationships may be missing."},
        "coverage": {"python_ast": "enabled", "javascript_typescript": "pattern and import analysis; full AST parsing not enabled", "dependency_advisory_database": "not queried; network advisory results are not included", "runtime_execution": "not run; untrusted project code is never executed by default", "private_repository_support": "requires an explicit authorization integration"},
        "tool_versions": {"sentinal_analyzer": "0.1.0", "python_runtime": "runtime-reported"},
    }


def parse_manifest_dependencies(files: dict[str, bytes]) -> list[dict[str, Any]]:
    deps: list[dict[str, Any]] = []
    for path, raw in files.items():
        name = PurePosixPath(path).name.lower()
        if name == "requirements.txt":
            for line in raw.decode("utf-8", "replace").splitlines():
                val = line.strip()
                if val and not val.startswith(("#", "-")):
                    m = re.match(r"([A-Za-z0-9_.-]+)\s*(.*)", val)
                    if m:
                        deps.append({"manifest": path, "name": m.group(1), "declared": m.group(2).strip() or "unversioned", "ecosystem": "pypi"})
        elif name == "package.json":
            try:
                data = json.loads(raw.decode("utf-8", "replace"))
                for section in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
                    for pkg, ver in data.get(section, {}).items():
                        deps.append({"manifest": path, "name": pkg, "declared": str(ver), "ecosystem": "npm"})
            except (ValueError, AttributeError):
                continue
    return sorted(deps, key=lambda d: (d["ecosystem"], d["name"].lower()))
