"""CSV table."""

import os
import csv
from applications_table import AppTable

from scrape_linkedin import JobDescription
from ai_evaluator import JobEvaluation


class CsvTable(AppTable):
    """CSV table."""

    def __init__(self, table_name: str = "jobs_evaluated.csv"):
        self.table_name = table_name

    def job_id_in_table(self, job_id: str) -> bool:
        """Check if a job ID is in the table."""
        if not os.path.exists(self.table_name):
            return False
        with open(self.table_name, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["id"] == job_id:
                    return True
        return False

    def add_to_table(
        self, description: JobDescription, evaluation: JobEvaluation
    ) -> None:
        """Add a job to the table."""
        row = {
            "job_id": description.job_id,
            "title": description.title,
            "company": description.company,
            "url": description.url,
            "fit": evaluation.fit_to_requirements_percentage,
            "explanation": evaluation.fit_to_requirements_explanation,
            "seniority": evaluation.seniority_level_1_to_5,
            "what_the_company_does": evaluation.what_the_company_does,
            "job_description_summary": evaluation.job_description_summary,
        }
        if not os.path.exists(self.table_name):
            with open(self.table_name, "w", encoding="utf-8") as f:
                fieldnames = row.keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

        with open(self.table_name, "a", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            writer.writerow(row)
