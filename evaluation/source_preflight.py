"""Fail-closed, model-free source-to-oracle preflight for *new* study declarations.

The caller provides a separately maintained inventory of material assertions.
This module checks complete coverage and exact source/runner identity; it cannot
prove that a quoted clause entails an assertion or authenticate a human reviewer.
Do not apply it to historical frozen study grades.
"""
import hashlib


KINDS = {"output", "exception", "compatibility", "negative"}


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def qualify(declaration, *, source, oracle_text, inventory):
    """Return QUALIFIED or NOT QUALIFIED, never an inferred candidate grade.

    inventory maps material assertion ID to {"kind": str, "cases": [labels]}.
    It must be authored/reviewed from the *actual* oracle code, not generated
    from the declaration being checked. Clauses are matched as exact bytes.
    """
    source_hash = _sha256(source)
    oracle_hash = _sha256(oracle_text.encode("utf-8"))
    problems = []
    if not isinstance(inventory, dict) or not inventory:
        problems.append("No independent material case inventory")
        inventory = {}
    if not isinstance(declaration, dict):
        declaration = {}
        problems.append("Declaration is not an object")
    if declaration.get("schema_version") != 1:
        problems.append("Unsupported declaration schema")
    if not isinstance(declaration.get("study_id"), str) or not declaration["study_id"].strip():
        problems.append("Missing study identity")
    author = declaration.get("author")
    if not isinstance(author, str) or not author.strip():
        problems.append("Missing declaration author")
    if declaration.get("source_sha256") != source_hash:
        problems.append("Original source identity mismatch")
    if declaration.get("oracle_sha256") != oracle_hash:
        problems.append("Oracle code identity mismatch")

    rows = declaration.get("expectations")
    if not isinstance(rows, list):
        rows = []
        problems.append("Missing material expectation inventory")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            problems.append("Malformed expectation")
            continue
        identifier = row.get("id")
        if not isinstance(identifier, str) or not identifier:
            problems.append("Expectation lacks ID")
            continue
        if identifier in seen:
            problems.append(f"{identifier}: duplicate expectation")
        seen.add(identifier)
        spec = inventory.get(identifier)
        if spec is None:
            problems.append(f"{identifier}: not in independent oracle inventory")
        elif row.get("kind") != spec["kind"] or row.get("cases") != spec["cases"]:
            problems.append(f"{identifier}: kind or case coverage mismatch")
        if row.get("kind") not in KINDS:
            problems.append(f"{identifier}: unknown expectation kind")
        if not isinstance(row.get("claim"), str) or not row["claim"].strip():
            problems.append(f"{identifier}: no precise expected behavior")
        support = row.get("support")
        clause = row.get("source_clause")
        clause_exact = (isinstance(clause, str) and bool(clause.strip()) and
                        source.count(clause.encode("utf-8")) == 1)
        if not clause_exact and support != "adjudicated":
            problems.append(f"{identifier}: source clause missing or not unique")
        elif clause is not None and not clause_exact:
            problems.append(f"{identifier}: inaccurate adjudication source citation")
        ambiguity = row.get("ambiguity")
        alternatives = row.get("acceptable_alternatives")
        if not isinstance(ambiguity, str) or not isinstance(alternatives, list) or any(
            not isinstance(x, str) or not x.strip() for x in alternatives
        ) or len(set(alternatives)) != len(alternatives):
            problems.append(f"{identifier}: ambiguities/alternatives not documented")
            ambiguity, alternatives = None, []
        if support == "source":
            if ambiguity and not (
                row.get("kind") == "exception" and
                row.get("exception_policy") == "unprescribed_validation" and
                set(alternatives) == {"TypeError", "ValueError"} and
                len(alternatives) == 2 and clause_exact and
                "validat" in clause.lower() and
                not any(exc in clause for exc in ("ValueError", "TypeError"))
            ):
                problems.append(f"{identifier}: disputed/ambiguous source requires adjudication")
            if row.get("adjudication"):
                problems.append(f"{identifier}: conflicting source/adjudication status")
        elif support == "adjudicated":
            decision = row.get("adjudication")
            if (not isinstance(decision, dict) or decision.get("decision") != "supported"
                    or not all(isinstance(decision.get(k), str) and decision[k].strip()
                               for k in ("reviewer", "reference", "rationale"))
                    or decision.get("reviewer") == author):
                problems.append(f"{identifier}: independent supporting adjudication unavailable")
            if not ambiguity or not alternatives:
                problems.append(f"{identifier}: interpretation must record ambiguity and alternatives")
        else:
            problems.append(f"{identifier}: unsupported, unknown or disputed evidence ({support})")

        if row.get("kind") == "exception":
            accepted = row.get("allowed_exceptions")
            if (not isinstance(accepted, list) or not accepted
                    or any(not isinstance(x, str) or not x for x in accepted)
                    or len(accepted) != len(set(accepted))):
                problems.append(f"{identifier}: invalid exception policy")
            elif support == "source":
                if row.get("exception_policy") == "unprescribed_validation":
                    if (not ambiguity or accepted != alternatives or
                            set(accepted) != {"ValueError", "TypeError"} or
                            not isinstance(clause, str) or
                            any(exc in clause for exc in accepted)):
                        problems.append(f"{identifier}: invalid unspecified-class exception policy")
                elif not clause_exact or any(exc not in clause for exc in accepted):
                    problems.append(f"{identifier}: exception class not promised by source")
            elif support == "adjudicated" and alternatives != accepted:
                problems.append(f"{identifier}: adjudicated alternatives disagree with exception policy")
        elif "allowed_exceptions" in row or "exception_policy" in row:
            problems.append(f"{identifier}: exception policy on non-exception expectation")

    for missing in sorted(set(inventory) - seen):
        problems.append(f"{missing}: material assertion not declared")
    return {
        "status": "NOT QUALIFIED" if problems else "QUALIFIED",
        "problems": problems,
        "source_sha256": source_hash,
        "oracle_sha256": oracle_hash,
        "expected_assertions": len(inventory),
        "qualified_assertions": len(inventory) if not problems else 0,
        "model_dispatches": 0,
    }
