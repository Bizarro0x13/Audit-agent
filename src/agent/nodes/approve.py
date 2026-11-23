from agent.schemas import Status


def make_approve_node(ask, store):
    """Nothing is 'approved' unless a person (the ask function) says yes.

    y = approved, n = rejected by the human, s = left undecided (not reported).
    Findings the verifier already rejected are not shown.
    """

    def approve(state):
        findings = list(state.get("findings", []))
        approved = []
        for f in findings:
            if f.status == Status.rejected:
                continue
            answer = ask(f)
            if answer == "y":
                f.status = Status.approved
                approved.append(f.id)
            elif answer == "n":
                f.status = Status.rejected
                f.verifier_note = (f.verifier_note + " [rejected by human]").strip()
        for f in findings:
            store.save_finding(state["run_id"], f.id, f.model_dump_json())
        return {"findings": findings, "approved_ids": approved}

    return approve
