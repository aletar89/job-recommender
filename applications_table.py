"""Abstract base class for application tables."""

from abc import ABC, abstractmethod

from ai_evaluator import JobEvaluation
from scrape_linkedin import JobDescription


class AppTable(ABC):
    """Abstract base class for application tables."""

    @abstractmethod
    def job_id_in_table(self, job_id: str) -> bool:
        """Check if a job ID is in the table."""

    @abstractmethod
    def add_to_table(
        self, description: JobDescription, evaluation: JobEvaluation
    ) -> None:
        """Add a job to the table."""
