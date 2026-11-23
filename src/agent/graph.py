from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from agent.nodes.analyze import make_analyze_node
from agent.nodes.approve import make_approve_node
from agent.nodes.gate import make_gate_node
from agent.nodes.plan import make_plan_node
from agent.nodes.report import make_report_node
from agent.nodes.verify import make_verify_node
from agent.schemas import Finding, FocusArea


class State(TypedDict, total=False):
    run_id: str
    target_root: str
    plan: list[FocusArea]
    pending: list[FocusArea]
    candidates: list
    feedback: dict
    findings: list[Finding]
    gate_errors: list[str]
    attempts: int
    cost_usd: float
    approved_ids: list[str]
    auto_approved: bool


def build_graph(model, tools, store, ask, report_path="report.md", checkpointer=None,
                interrupt_after=None, verify=True, rag=None):
    g = StateGraph(State)
    after_gate = "verify" if verify else "approve"
    g.add_node("plan", make_plan_node(model, tools))
    g.add_node("analyze", make_analyze_node(model, tools, rag))
    g.add_node("gate", make_gate_node(tools, store))
    if verify:
        g.add_node("verify", make_verify_node(model, tools, store))
    g.add_node("approve", make_approve_node(ask, store))
    g.add_node("report", make_report_node(report_path))
    g.add_edge(START, "plan")
    g.add_edge("plan", "analyze")
    g.add_edge("analyze", "gate")
    g.add_conditional_edges("gate", lambda s: "analyze" if s["pending"] else after_gate)
    if verify:
        g.add_edge("verify", "approve")
    g.add_edge("approve", "report")
    g.add_edge("report", END)
    return g.compile(checkpointer=checkpointer, interrupt_after=interrupt_after)
