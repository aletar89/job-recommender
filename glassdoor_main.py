"""
This script evaluates jobs from Glassdoor and adds them to the Airtable.
"""

import sys

from tqdm import tqdm

from ai_evaluator import JobEvaluation, cached_job_evaluation, format_bot_output
from airtable import AirTable
from parse_glassdoor_jobs import parse_glassdoor_jobs
from scrape_linkedin import JobDescription

THRESHOLD = 85
VERBOSE = False


def evaluate_job(job_id: str) -> tuple[JobDescription, JobEvaluation]:
    """Evaluate a job from Glassdoor and return the job description and evaluation."""
    with open(f"glassdoor_jobs/{job_id}.json", "r", encoding="utf-8") as f:
        job_desc = JobDescription.model_validate_json(f.read())
    job_eval = cached_job_evaluation(job_desc)
    return job_desc, job_eval


def main() -> int:
    """Main entry point"""
    job_ids = parse_glassdoor_jobs()
    air_table = AirTable()
    for job_id in tqdm(job_ids, desc="Evaluating jobs"):
        description, evaluation = evaluate_job(job_id)
        if VERBOSE:
            print("\n" + format_bot_output(evaluation))
        if (
            evaluation.fit_to_requirements_percentage >= THRESHOLD
            and not air_table.job_id_in_table(job_id)
        ):
            print(f"🎯 Adding {description.company} to the table")
            air_table.add_to_table(description, evaluation)

    return 0


if __name__ == "__main__":
    sys.exit(main())
