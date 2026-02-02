"""Tests for crossref_local.jobs module."""

import tempfile
from pathlib import Path

from crossref_local import jobs


class TestJobsModule:
    """Test the jobs module public API."""

    def test_jobs_exports(self):
        """Test that jobs module exports expected functions."""
        assert hasattr(jobs, "create")
        assert hasattr(jobs, "get")
        assert hasattr(jobs, "list_jobs")
        assert hasattr(jobs, "run")
        assert callable(jobs.create)
        assert callable(jobs.get)
        assert callable(jobs.list_jobs)
        assert callable(jobs.run)


class TestJobQueue:
    """Test JobQueue class directly with temp directory."""

    def test_create_returns_job(self):
        """Test that create returns a Job object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs.JobQueue(jobs_dir=Path(tmpdir))
            job = queue.create(items=["item1", "item2"], name="test_job")
            assert job is not None
            assert hasattr(job, "id")
            assert job.items == ["item1", "item2"]
            assert job.metadata.get("name") == "test_job"

    def test_create_persists_job(self):
        """Test that created job is persisted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs.JobQueue(jobs_dir=Path(tmpdir))
            job = queue.create(items=["item1", "item2", "item3"], name="test_job")
            # Job should be retrievable
            loaded = queue.load(job.id)
            assert loaded is not None
            assert loaded.metadata.get("name") == "test_job"
            assert len(loaded.items) == 3

    def test_load_nonexistent_job_returns_none(self):
        """Test that loading non-existent job returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs.JobQueue(jobs_dir=Path(tmpdir))
            result = queue.load("nonexistent_job_id")
            assert result is None

    def test_list_returns_list(self):
        """Test that list returns a list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs.JobQueue(jobs_dir=Path(tmpdir))
            result = queue.list()
            assert isinstance(result, list)

    def test_list_includes_created_jobs(self):
        """Test that list includes created jobs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs.JobQueue(jobs_dir=Path(tmpdir))
            job1 = queue.create(items=["a"], name="job1")
            job2 = queue.create(items=["b"], name="job2")

            job_list = queue.list()
            job_ids = [j.id for j in job_list]

            assert job1.id in job_ids
            assert job2.id in job_ids

    def test_delete_removes_job(self):
        """Test that delete removes a job."""
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = jobs.JobQueue(jobs_dir=Path(tmpdir))
            job = queue.create(items=["a"])

            assert queue.load(job.id) is not None
            result = queue.delete(job.id)
            assert result is True
            assert queue.load(job.id) is None


class TestJob:
    """Test Job dataclass."""

    def test_job_pending_property(self):
        """Test pending property returns items not processed."""
        job = jobs.Job(id="test", items=["a", "b", "c"])
        job.completed = ["a"]
        job.failed = {"b": "error"}

        assert job.pending == ["c"]

    def test_job_progress_property(self):
        """Test progress property returns correct percentage."""
        job = jobs.Job(id="test", items=["a", "b", "c", "d"])
        job.completed = ["a", "b"]

        assert job.progress == 50.0

    def test_job_to_dict(self):
        """Test to_dict serialization."""
        job = jobs.Job(id="test123", items=["x", "y"])
        d = job.to_dict()

        assert d["id"] == "test123"
        assert d["items"] == ["x", "y"]
        assert "status" in d
        assert "created_at" in d

    def test_job_from_dict(self):
        """Test from_dict deserialization."""
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
        job = jobs.Job.from_dict(data)

        assert job.id == "test456"
        assert job.items == ["p", "q"]
        assert job.completed == ["p"]
        assert job.status == "running"
