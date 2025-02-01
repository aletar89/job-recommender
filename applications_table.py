import argparse
import sys

from abc import ABC, abstractmethod

from ai_evaluator import JobEvaluation
from scrape_linkedin import JobDescription


class AppTable(ABC):

    @abstractmethod
    def job_id_in_table(self, job_id: str) -> bool:
        pass

    def company_in_table(self, company: str) -> bool:
        pass

    @abstractmethod
    def add_to_table(self, description: JobDescription, evaluation: JobEvaluation) -> None:
        pass


