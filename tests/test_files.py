import os

import pytest

from agent.store import Store
from agent.tools.files import FileTools, PathEscapeError


@pytest.fixture
def env(tmp_path):
    root = tmp_path / "target"
    (root / "src").mkdir(parents=True)
    (root / "src" / "A.sol").write_text("line one\nwithdraw here\nline three\n")
    (root / "B.sol").write_text("other\n")
    secret = tmp_path / "secret.txt"
    secret.write_text("TOP SECRET")
    store = Store(":memory:")
    store.start_run("r1", str(root))
    return root, secret, FileTools(root, store, "r1"), store


def logged(store):
    return store.db.execute("SELECT tool, ok FROM tool_calls ORDER BY id").fetchall()


def test_read_normal_file(env):
    _, _, tools, _ = env
    assert "withdraw here" in tools.read_file("src/A.sol")


def test_list_files(env):
    _, _, tools, _ = env
    assert tools.list_files() == ["B.sol", "src/A.sol"]


def test_grep_returns_path_and_line(env):
    _, _, tools, _ = env
    assert tools.grep("withdraw") == ["src/A.sol:2: withdraw here"]


@pytest.mark.parametrize("bad", ["../secret.txt", "src/../../secret.txt", "/etc/passwd"])
def test_escape_paths_refused(env, bad):
    _, _, tools, _ = env
    with pytest.raises(PathEscapeError):
        tools.read_file(bad)


def test_symlink_escape_refused(env):
    root, secret, tools, _ = env
    os.symlink(secret, root / "link.txt")
    with pytest.raises(PathEscapeError):
        tools.read_file("link.txt")


def test_absolute_path_inside_root_is_fine(env):
    root, _, tools, _ = env
    assert "other" in tools.read_file(str(root / "B.sol"))


def test_every_call_logged_including_refused(env):
    _, _, tools, store = env
    tools.read_file("B.sol")
    with pytest.raises(PathEscapeError):
        tools.read_file("../secret.txt")
    assert logged(store) == [("read_file", 1), ("read_file", 0)]
