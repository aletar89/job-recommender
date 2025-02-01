import os

from pyairtable import Api
from pyairtable.formulas import LOWER, EQ, match

from ai_evaluator import JobEvaluation, format_bot_output
from applications_table import AppTable
from scrape_linkedin import JobDescription

APP_ID = "appSHT3ZGlckOHaVy"
TABLE_ID = "tblmDsJrr7cwBGsv5"


class AirTable(AppTable):
    def __init__(self):
        self.table = Api(os.environ['AIRTABLE_API_KEY']).table(APP_ID, TABLE_ID)

    def job_id_in_table(self, job_id: str) -> bool:
        res = self.table.first(formula=match({"id": job_id}))
        return res is not None

    def company_in_table(self, company: str) -> bool:
        res = self.table.first(formula=match({"Company": company}))
        return res is not None

    def same_company_applications(self, company: str) -> list[dict]:
        res = self.table.all(formula=match({"Company": company}))
        return res


    def add_to_table(self, description: JobDescription, evaluation: JobEvaluation) -> None:
        self.table.create(
            {
                'Job description': description.description,
                'Company': description.company,
                'Job': description.title,
                'id': description.job_id,
                'Stage': 'Bot suggestion',
                'url': description.url,
                'bot opinion': format_bot_output(evaluation),
            }
        )


if __name__ == '__main__':
    at = AirTable()
    at.company_in_table("momox")
