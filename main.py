"""Main entry point"""

from tqdm import tqdm

from ai_evaluator import cached_job_evaluation, format_bot_output
from airtable import AirTable
from applications_table import AppTable
from glassdoor_json_parser import parse_glassdoor_jobs
from job_description import JobDescription
from scrape_linkedin import scrape_linkedin

THRESHOLD = 85
VERBOSE = False


def evalupate_jobs(jobs: list[JobDescription], app_table: AppTable) -> None:
    """Evaluate jobs"""
    for job_description in tqdm(jobs, desc="Evaluating jobs"):

        evaluation = cached_job_evaluation(job_description)
        if VERBOSE:
            print("\n" + format_bot_output(evaluation))

        if (
            evaluation.fit_to_requirements_percentage >= THRESHOLD
            and not app_table.job_id_in_table(job_description.job_id)
        ):
            print(
                f"🎯 Adding {job_description.title} at {job_description.company} to the table "
                f"({evaluation.fit_to_requirements_percentage}% fit)"
            )
            app_table.add_to_table(job_description, evaluation)


if __name__ == "__main__":
    my_table = AirTable()
    # Also possible to use:
    # my_table = CsvTable()
    # TODO: Add more Google Sheet support
    linkedin_jobs = scrape_linkedin("Software Engineer", num_results=100)
    evalupate_jobs(linkedin_jobs, my_table)
    glassdoor_jobs = parse_glassdoor_jobs("glassdoor_exported_data.json")
    evalupate_jobs(glassdoor_jobs, my_table)
