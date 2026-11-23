import os

from agent.schemas import FocusArea

SYSTEM = """You plan a code review. You are given a list of files with sizes.
Pick 3-8 focus areas: each is one file plus one well-known bug class to check
(for example: reentrancy, missing access control, integer overflow, unchecked return values,
unsafe external calls, logic errors). Only choose files from the list."""


def make_plan_node(model, tools):
    def plan(state):
        files = tools.list_files()
        listing = "\n".join(f"{f} ({len(tools.read_file(f))} chars)" for f in files)
        focus = model.call(
            "plan", SYSTEM, listing, schema=list[FocusArea],
            model=os.environ.get("AGENT_PLAN_MODEL", "claude-haiku-5-5"),
        )
        known = set(files)
        return {"plan": [f for f in focus if f.file in known][:8]}

    return plan
