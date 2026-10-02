"""Synchronous Qiskit job returned by the RQS-SVG backend."""

from __future__ import annotations

from qiskit.providers import JobStatus, JobV1


class RqsSvgJob(JobV1):
    """A completed, local RQS-SVG simulation job."""

    _async = False

    def __init__(self, backend, job_id: str, result) -> None:
        super().__init__(backend, job_id)
        self._result = result

    def submit(self) -> None:
        """Submit the job.

        Execution is synchronous, so the result is already available when the
        job is constructed.
        """

    def result(self, timeout=None):
        """Return the completed Qiskit result."""
        return self._result

    def status(self) -> JobStatus:
        """Return the terminal status of this synchronous job."""
        return JobStatus.DONE
