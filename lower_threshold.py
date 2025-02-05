"""
This script evaluates jobs from Glassdoor with a lower threshold and adds them to the Airtable.
"""

from pathlib import Path

from tqdm import tqdm

from ai_evaluator import JobEvaluation
from airtable import AirTable
from scrape_linkedin import JobDescription

LOWER_THRESHOLD = 80


def main() -> int:
    """Main entry point"""
    # Get all evaluated jobs
    eval_path = Path("jobs_evaluated")
    job_evals = []
    for file in eval_path.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            job_eval = JobEvaluation.model_validate_json(f.read())
            job_evals.append((file.stem, job_eval))

    air_table = AirTable()

    # Process jobs that meet lower threshold
    for job_id, evaluation in tqdm(job_evals, desc="Processing jobs"):
        if evaluation.fit_to_requirements_percentage >= LOWER_THRESHOLD:
            # Only process if not already in table
            if not air_table.job_id_in_table(job_id):
                # Load original job description
                job_path = Path("jobs_fetched") / f"{job_id}.json"
                with open(job_path, "r", encoding="utf-8") as f:
                    description = JobDescription.model_validate_json(f.read())

                print(f"🎯 Adding {description.company} to the table")
                air_table.add_to_table(description, evaluation)

    return 0


if __name__ == "__main__":
    main()
