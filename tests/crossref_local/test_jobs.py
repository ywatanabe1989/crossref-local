"""Tests for crossref_local.jobs module."""

from pathlib import Path

import pytest

from crossref_local import jobs


# ---------- module-level API surface ----------


@pytest.mark.parametrize("attr", ["create", "get", "list_jobs", "run"])
def test_jobs_module_exposes_expected_callable(attr):
    # Arrange
    target = jobs
    # Act
    obj = getattr(target, attr, None)
    # Assert
    assert callable(obj)


# ---------- JobQueue ----------


@pytest.fixture
def queue(tmp_path):
    """Construct a fresh JobQueue pointing at tmp_path."""
    return jobs.JobQueue(jobs_dir=tmp_path)


def test_jobqueue_create_returns_non_none_job_object(queue):
    # Arrange
    items = ["item1", "item2"]
    # Act
    job = queue.create(items=items, name="test_job")
    # Assert
    assert job is not None


def test_jobqueue_create_assigns_id_attribute_to_new_job(queue):
    # Arrange
    items = ["item1", "item2"]
    # Act
    job = queue.create(items=items, name="test_job")
    # Assert
    assert hasattr(job, "id")


def test_jobqueue_create_preserves_items_on_new_job(queue):
    # Arrange
    items = ["item1", "item2"]
    # Act
    job = queue.create(items=items, name="test_job")
    # Assert
    assert job.items == items


def test_jobqueue_create_stores_name_in_metadata(queue):
    # Arrange
    # Act
    job = queue.create(items=["a", "b"], name="test_job")
    # Assert
    assert job.metadata.get("name") == "test_job"


def test_jobqueue_load_returns_persisted_job_after_create(queue):
    # Arrange
    job = queue.create(items=["item1", "item2", "item3"], name="test_job")
    # Act
    loaded = queue.load(job.id)
    # Assert
    assert loaded is not None


def test_jobqueue_load_preserves_item_count_after_round_trip(queue):
    # Arrange
    job = queue.create(items=["item1", "item2", "item3"], name="test_job")
    # Act
    loaded = queue.load(job.id)
    # Assert
    assert len(loaded.items) == 3


def test_jobqueue_load_returns_none_for_unknown_job_id(queue):
    # Arrange
    # Act
    result = queue.load("nonexistent_job_id")
    # Assert
    assert result is None


def test_jobqueue_list_returns_list_instance_when_empty(queue):
    # Arrange
    # Act
    result = queue.list()
    # Assert
    assert isinstance(result, list)


def test_jobqueue_list_includes_every_created_job_id(queue):
    # Arrange
    job1 = queue.create(items=["a"], name="job1")
    job2 = queue.create(items=["b"], name="job2")
    # Act
    listed_ids = [j.id for j in queue.list()]
    # Assert
    assert {job1.id, job2.id}.issubset(set(listed_ids))


def test_jobqueue_delete_returns_true_for_existing_job(queue):
    # Arrange
    job = queue.create(items=["a"])
    # Act
    result = queue.delete(job.id)
    # Assert
    assert result is True


def test_jobqueue_delete_makes_job_subsequently_unloadable(queue):
    # Arrange
    job = queue.create(items=["a"])
    queue.delete(job.id)
    # Act
    loaded = queue.load(job.id)
    # Assert
    assert loaded is None


# ---------- Job dataclass ----------


def test_job_pending_property_excludes_completed_and_failed_items():
    # Arrange
    job = jobs.Job(id="test", items=["a", "b", "c"])
    job.completed = ["a"]
    job.failed = {"b": "error"}
    # Act
    pending = job.pending
    # Assert
    assert pending == ["c"]


def test_job_progress_property_reports_percentage_of_completed_items():
    # Arrange
    job = jobs.Job(id="test", items=["a", "b", "c", "d"])
    job.completed = ["a", "b"]
    # Act
    pct = job.progress
    # Assert
    assert pct == 50.0


@pytest.fixture
def _simple_job_dict():
    job = jobs.Job(id="test123", items=["x", "y"])
    return job.to_dict()


def test_job_to_dict_preserves_id(_simple_job_dict):
    # Arrange
    d = _simple_job_dict
    # Act
    # Assert
    assert d["id"] == "test123"


def test_job_to_dict_preserves_items(_simple_job_dict):
    # Arrange
    d = _simple_job_dict
    # Act
    # Assert
    assert d["items"] == ["x", "y"]


def test_job_to_dict_includes_status_key(_simple_job_dict):
    # Arrange
    d = _simple_job_dict
    # Act
    # Assert
    assert "status" in d


def test_job_to_dict_includes_created_at_key(_simple_job_dict):
    # Arrange
    d = _simple_job_dict
    # Act
    # Assert
    assert "created_at" in d


@pytest.fixture
def _round_tripped_job():
    data = {
        "id": "test456",
        "items": ["p", "q"],
        "completed": ["p"],
        "failed": {},
        "status": "running",
        "created_at": 1234567890.0,
        "updated_at": 1234567890.0,
        "metadata": {"name": "test"},
    }
    return jobs.Job.from_dict(data)


def test_job_from_dict_restores_id(_round_tripped_job):
    # Arrange
    job = _round_tripped_job
    # Act
    # Assert
    assert job.id == "test456"


def test_job_from_dict_restores_items_list(_round_tripped_job):
    # Arrange
    job = _round_tripped_job
    # Act
    # Assert
    assert job.items == ["p", "q"]


def test_job_from_dict_restores_completed_list(_round_tripped_job):
    # Arrange
    job = _round_tripped_job
    # Act
    # Assert
    assert job.completed == ["p"]


def test_job_from_dict_restores_status(_round_tripped_job):
    # Arrange
    job = _round_tripped_job
    # Act
    # Assert
    assert job.status == "running"
