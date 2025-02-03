import sys
from tqdm import tqdm
from ai_evaluator import evaluate_job, format_bot_output
from airtable import AirTable
from scrape_linkedin import crawl_search

THRESHOLD = 85
VERBOSE = False


def main() -> int:
    """Main entry point"""
    job_ids = crawl_search("Software Engineer", 100)
    air_table = AirTable()
    for job_id in tqdm(job_ids, desc="Evaluating jobs"):
        description, evaluation = evaluate_job(job_id)
        if VERBOSE:
            print("\n"+format_bot_output(evaluation))
        if evaluation.fit_to_requirements_percentage >= THRESHOLD and not air_table.job_id_in_table(job_id):
            print(f"🎯 Adding {description.company} to the table")
            air_table.add_to_table(description, evaluation)

    return 0


if __name__ == "__main__":
    sys.exit(main())
