"""Main entry point"""

from tqdm import tqdm

from ai_evaluator import cached_job_evaluation, format_bot_output
from airtable import AirTable
from applications_table import AppTable
from parse_glassdoor_jobs import parse_glassdoor_jobs
from scrape_linkedin import scrape_linkedin

THRESHOLD = 85
VERBOSE = False


def main(app_table: AppTable) -> int:
    """Main entry point"""
    linkedin_jobs = scrape_linkedin("Software Engineer", 100)
    glassdoor_jobs = parse_glassdoor_jobs()
    for job_description in tqdm(linkedin_jobs + glassdoor_jobs, desc="Evaluating jobs"):
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

    return 0


if __name__ == "__main__":
    my_table = AirTable()
    # Also possible to use:
    # my_table = CsvTable()
    # TODO: Add more Google Sheet support
    main(my_table)
