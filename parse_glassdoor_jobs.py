import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from scrape_linkedin import JobDescription


def extract_job_id(url: str) -> str:
    """Extract jobListingId from Glassdoor URL."""
    try:
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        job_id = params.get("jobListingId", [""])[0]
        return job_id
    except:
        return ""


def parse_glassdoor_jobs():
    output_dir = Path("jobs_fetched")
    output_dir.mkdir(exist_ok=True)

    with open("exported_data.json", "r", encoding="utf-8") as f:
        jobs_data = json.load(f)

    job_ids = []
    print(f"Found {len(jobs_data)} jobs")
    existing_counter = 0
    for i, job in enumerate(jobs_data):
        job_id = extract_job_id(job["link"])
        if not job_id:
            print(f"Skipping job {job['title']} because it has no jobListingId")
            continue
        job_ids.append(job_id)
        filepath = output_dir / f"{job_id}.json"
        if filepath.exists():
            existing_counter += 1
            continue
        job_desc = JobDescription(
            job_id=job_id,
            url=job["link"],
            company=job["company"],
            title=job["title"],
            description=job["description"],
            posted_date="",
        )

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(job_desc.__dict__, f, indent=2)

    print(f"Skipped {existing_counter} jobs because they already exist")
    return job_ids


if __name__ == "__main__":
    parse_glassdoor_jobs()
