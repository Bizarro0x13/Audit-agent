from agent.gates import MAX_ATTEMPTS, citation_errors, same_issue
from agent.nodes.analyze import area_key
from agent.schemas import Finding


def make_gate_node(tools, store):
    def gate(state):
        attempt = state.get("attempts", 0) + 1
        run_id = state["run_id"]
        findings = list(state.get("findings", []))
        feedback = dict(state.get("feedback", {}))  # schema errors set by analyze
        retry = {}  # area key -> (area, [errors])
        pending = {area_key(a): a for a in state["pending"]}

        for key, errs in feedback.items():
            if errs:
                store.add_gate_result(run_id, "schema", False, f"{key}: {errs[0]}", attempt)
                retry[key] = (pending[key], list(errs))

        for area, draft in state.get("candidates", []):
            errs = citation_errors(draft, tools.read_file)
            ok = not errs
            store.add_gate_result(run_id, "citation", ok, "; ".join(errs) or draft.title, attempt)
            if ok:
                if not any(same_issue(draft, f) for f in findings):  # drop near-duplicates
                    findings.append(Finding(id=f"F-{len(findings) + 1:03d}", **draft.model_dump()))
            else:
                retry.setdefault(area_key(area), (area, []))[1].extend(errs)

        out = {"findings": findings, "attempts": attempt, "candidates": []}
        if retry and attempt < MAX_ATTEMPTS:
            out["pending"] = [a for a, _ in retry.values()]
            out["feedback"] = {k: e for k, (_, e) in retry.items()}
        else:
            out["pending"] = []
            out["feedback"] = {}
            dropped = [f"{k}: dropped after {attempt} attempts: {e[0]}" for k, (_, e) in retry.items()]
            out["gate_errors"] = list(state.get("gate_errors", [])) + dropped
        return out

    return gate
