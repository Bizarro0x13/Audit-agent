from pathlib import Path

from agent.nodes.analyze import reference_block
from agent.rag import Index, chunk_file, from_env, tokens
from agent.schemas import FocusArea

KNOWLEDGE = Path(__file__).parent.parent / "knowledge"


def test_tokens_drop_stopwords_and_lowercase():
    assert tokens("The Reentrancy of a CALL") == ["reentrancy", "call"]


def test_chunks_keep_title_and_respect_size():
    text = "# Title\n" + "\n\n".join(["para " * 60] * 6)
    chunks = chunk_file("x.md", text, max_chars=700)
    assert len(chunks) > 1
    assert all(c.text.startswith("# Title") for c in chunks)


def test_relevant_note_ranks_first():
    idx = Index.build(KNOWLEDGE)
    top = idx.search("external call before state update re-enter balance", k=3)
    assert top and top[0].source == "reentrancy.md"
    top = idx.search("tx.origin authorization msg.sender", k=1)
    assert top[0].source == "tx-origin-auth.md"


def test_search_respects_k_and_ignores_unknown_words():
    idx = Index.build(KNOWLEDGE)
    assert len(idx.search("reentrancy", k=2)) <= 2
    assert idx.search("zzzz qqqq", k=3) == []


def test_empty_folder_gives_empty_index(tmp_path):
    assert Index.build(tmp_path).search("anything") == []


def test_from_env_is_off_by_default(monkeypatch):
    monkeypatch.delenv("AGENT_RAG", raising=False)
    assert from_env() is None
    monkeypatch.setenv("AGENT_RAG", "1")
    monkeypatch.setenv("AGENT_RAG_DIR", str(KNOWLEDGE))
    assert from_env() is not None


def test_prompt_has_notes_only_when_rag_is_on():
    area = FocusArea(file="a.sol", bug_class="reentrancy")
    assert reference_block(None, area, "code") == ""
    block = reference_block(Index.build(KNOWLEDGE), area, "call value balance")
    assert "<notes>" in block and "do not report something only because" in block
