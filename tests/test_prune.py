"""
Tests for the `prune` subcommand — delete cached result files by engine.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from prophecy.__main__ import prune_command


@pytest.fixture
def data_folder():
    """Cache folder with a mix of engines + a malformed file."""
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp) / "data"
        data.mkdir()
        # Settings needs these files to load, even if prune doesn't read them.
        (data / "prompts.tsv").write_text(
            "id\tcategory\ttopic\tprompt\n1\tCat\tTopic\ttext\n", encoding="utf-8"
        )
        (data / "template.txt").write_text("$prompt\n$text", encoding="utf-8")
        (data / "stories.yml").write_text(
            "X:\n  book: Genesis\n  verses: ['1:1']\n", encoding="utf-8"
        )
        (data / "index.json").write_text("{}", encoding="utf-8")

        cache = data / "results"
        cache.mkdir()

        # Three flavors of "unknown":
        # explicit unknown, null, missing-field-entirely
        (cache / "u_explicit.json").write_text(
            json.dumps({"answer": True, "story": "X", "prompt": "1", "engine": "unknown"})
        )
        (cache / "u_null.json").write_text(
            json.dumps({"answer": True, "story": "X", "prompt": "1", "engine": None})
        )
        (cache / "u_missing.json").write_text(
            json.dumps({"answer": True, "story": "X", "prompt": "1"})
        )
        # Real engines
        (cache / "chatgpt.json").write_text(
            json.dumps({"answer": True, "story": "X", "prompt": "1", "engine": "chatgpt:gpt-4"})
        )
        (cache / "claude.json").write_text(
            json.dumps({"answer": True, "story": "X", "prompt": "1", "engine": "claude-cli:haiku"})
        )
        # Malformed JSON
        (cache / "bad.json").write_text("not valid json {")

        yield data


def _cache_files(data_folder: Path) -> set[str]:
    return {p.name for p in (data_folder / "results").iterdir()}


def test_prune_unknown_catches_explicit_null_and_missing(data_folder):
    with patch.dict(os.environ, {"PROPHECY_DATA_FOLDER": str(data_folder)}, clear=False):
        rc = prune_command(["--engine", "unknown", "--verbosity", "WARNING"])
    assert rc == 0

    remaining = _cache_files(data_folder)
    assert "u_explicit.json" not in remaining
    assert "u_null.json" not in remaining
    assert "u_missing.json" not in remaining
    # Real engines untouched
    assert "chatgpt.json" in remaining
    assert "claude.json" in remaining
    # Malformed file is left alone (skipped, not deleted)
    assert "bad.json" in remaining


def test_prune_specific_engine(data_folder):
    with patch.dict(os.environ, {"PROPHECY_DATA_FOLDER": str(data_folder)}, clear=False):
        rc = prune_command(["--engine", "chatgpt:gpt-4", "--verbosity", "WARNING"])
    assert rc == 0
    remaining = _cache_files(data_folder)
    assert "chatgpt.json" not in remaining
    # Unknown-flavored ones untouched (we didn't ask for unknown)
    assert "u_explicit.json" in remaining
    assert "u_null.json" in remaining
    assert "u_missing.json" in remaining


def test_prune_multiple_engines_comma_sep(data_folder):
    with patch.dict(os.environ, {"PROPHECY_DATA_FOLDER": str(data_folder)}, clear=False):
        rc = prune_command(["--engine", "chatgpt:gpt-4,claude-cli:haiku", "--verbosity", "WARNING"])
    assert rc == 0
    remaining = _cache_files(data_folder)
    assert "chatgpt.json" not in remaining
    assert "claude.json" not in remaining


def test_prune_dry_run_keeps_files(data_folder):
    with patch.dict(os.environ, {"PROPHECY_DATA_FOLDER": str(data_folder)}, clear=False):
        rc = prune_command(["--engine", "unknown", "--dry-run", "--verbosity", "WARNING"])
    assert rc == 0
    remaining = _cache_files(data_folder)
    # Everything still there
    assert "u_explicit.json" in remaining
    assert "u_null.json" in remaining
    assert "u_missing.json" in remaining


def test_prune_engine_is_required(data_folder):
    with patch.dict(os.environ, {"PROPHECY_DATA_FOLDER": str(data_folder)}, clear=False):
        with pytest.raises(SystemExit):
            prune_command(["--verbosity", "WARNING"])


def test_prune_missing_cache_folder():
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp) / "data"
        data.mkdir()
        (data / "prompts.tsv").write_text(
            "id\tcategory\ttopic\tprompt\n1\tCat\tTopic\ttext\n", encoding="utf-8"
        )
        (data / "template.txt").write_text("$prompt\n$text", encoding="utf-8")
        (data / "stories.yml").write_text(
            "X:\n  book: Genesis\n  verses: ['1:1']\n", encoding="utf-8"
        )
        (data / "index.json").write_text("{}", encoding="utf-8")
        # No data/results/ folder

        with patch.dict(os.environ, {"PROPHECY_DATA_FOLDER": str(data)}, clear=False):
            rc = prune_command(["--engine", "unknown", "--verbosity", "WARNING"])
        assert rc == 1
