"""
Tests for AI Document Organizer
================================
Run with: pytest tests/ -v
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from organizer.database import Database, FileRecord
from organizer.vision import compute_image_hash, images_are_similar
from organizer.utils import human_readable_size


# ─────────────────────────────────────────────
#  Database tests
# ─────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    yield db
    db.close()


def _make_record(**kwargs) -> FileRecord:
    defaults = dict(
        file_path="/tmp/test.pdf",
        file_name="test.pdf",
        extension=".pdf",
        size_bytes=1024,
        label="report",
        confidence=0.91,
        image_hash=None,
        destination="/organized/report/2024-01/test.pdf",
        scanned_at="2024-01-01T00:00:00",
        moved=False,
    )
    defaults.update(kwargs)
    return FileRecord(**defaults)


def test_upsert_and_retrieve(tmp_db):
    record = _make_record()
    tmp_db.upsert_file(record)
    assert not tmp_db.already_processed("/tmp/test.pdf")


def test_mark_moved(tmp_db):
    record = _make_record()
    tmp_db.upsert_file(record)
    tmp_db.mark_moved("/tmp/test.pdf", "/organized/report/2024-01/test.pdf")
    assert tmp_db.already_processed("/tmp/test.pdf")


def test_upsert_updates_existing(tmp_db):
    tmp_db.upsert_file(_make_record(label="invoice"))
    tmp_db.upsert_file(_make_record(label="contract"))
    row = tmp_db._conn.execute(
        "SELECT label FROM files WHERE file_path = '/tmp/test.pdf'"
    ).fetchone()
    assert row["label"] == "contract"


def test_get_stats_empty(tmp_db):
    stats = tmp_db.get_stats()
    assert stats["total_files"] == 0
    assert stats["files_moved"] == 0


def test_run_lifecycle(tmp_db):
    run_id = tmp_db.start_run()
    assert run_id > 0
    tmp_db.finish_run(run_id, files_found=10, files_moved=7)
    stats = tmp_db.get_stats()
    assert stats["scan_runs"] == 1


def test_image_hashes(tmp_db):
    tmp_db.upsert_file(_make_record(image_hash="abc123", extension=".jpg"))
    hashes = tmp_db.get_image_hashes()
    assert "abc123" in hashes


def test_reset(tmp_db):
    tmp_db.upsert_file(_make_record())
    tmp_db.reset()
    stats = tmp_db.get_stats()
    assert stats["total_files"] == 0


# ─────────────────────────────────────────────
#  Vision utility tests  (no OpenCV required)
# ─────────────────────────────────────────────

def test_images_are_similar_identical():
    # Identical hashes → distance 0 → similar
    h = "f" * 256
    assert images_are_similar(h, h, threshold=10)


def test_images_are_similar_very_different():
    assert not images_are_similar("0" * 256, "f" * 256, threshold=10)


def test_images_are_similar_none():
    assert not images_are_similar(None, "abc", threshold=10)
    assert not images_are_similar("abc", None, threshold=10)


# ─────────────────────────────────────────────
#  Utility tests
# ─────────────────────────────────────────────

@pytest.mark.parametrize("size, expected", [
    (500, "500.0 B"),
    (2048, "2.0 KB"),
    (1_048_576, "1.0 MB"),
    (1_073_741_824, "1.0 GB"),
])
def test_human_readable_size(size, expected):
    assert human_readable_size(size) == expected


# ─────────────────────────────────────────────
#  Classifier (mocked — no model download)
# ─────────────────────────────────────────────

@patch("organizer.classifier._get_pipeline")
def test_classify_above_threshold(mock_pipeline):
    mock_clf = MagicMock()
    mock_clf.return_value = {"labels": ["invoice"], "scores": [0.92]}
    mock_pipeline.return_value = mock_clf

    from organizer.classifier import classify
    label, score = classify("Pay this invoice by Friday", ["invoice", "report"], "fake-model", 0.4)
    assert label == "invoice"
    assert score == pytest.approx(0.92)


@patch("organizer.classifier._get_pipeline")
def test_classify_below_threshold(mock_pipeline):
    mock_clf = MagicMock()
    mock_clf.return_value = {"labels": ["invoice"], "scores": [0.20]}
    mock_pipeline.return_value = mock_clf

    from organizer.classifier import classify
    label, score = classify("some text", ["invoice", "report"], "fake-model", 0.4)
    assert label == "unknown"


def test_classify_empty_text():
    from organizer.classifier import classify
    label, score = classify("", ["invoice", "report"], "fake-model", 0.4)
    assert label == "unknown"
    assert score == 0.0
