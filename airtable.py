"""Airtable API wrapper."""

import os

from pyairtable import Api
from pyairtable.formulas import match

from ai_evaluator import JobEvaluation, format_bot_output
from applications_table import AppTable

from scrape_linkedin import JobDescription


class AirTable(AppTable):
    """Airtable API wrapper."""

    def __init__(self):
        self.table = Api(os.environ["AIRTABLE_API_KEY"]).table(
            os.environ["APP_ID"], os.environ["TABLE_ID"]
        )

    def job_id_in_table(self, job_id: str) -> bool:
        res = self.table.first(formula=match({"id": job_id}))
        return res is not None

    def add_to_table(
        self, description: JobDescription, evaluation: JobEvaluation
    ) -> None:
        self.table.create(
            {
                "Job description": description.description,
                "Company": description.company,
                "Job": description.title,
                "id": description.job_id,
                "Stage": "Bot suggestion",
                "url": description.url,
                "bot opinion": format_bot_output(evaluation),
            }
        )
