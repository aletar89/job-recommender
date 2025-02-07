"""Script to parse jobs scraped from Glassdoor."""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from job_description import JOBS_DIR, JobDescription


def extract_job_id(url: str) -> str:
    """Extract jobListingId from Glassdoor URL."""
    parsed_url = urlparse(url)
    params = parse_qs(parsed_url.query)
    job_id = params.get("jobListingId", [""])[0]
    return job_id


def parse_posted_time(posted: str) -> str:
    """Parse the posted time from Glassdoor format (e.g. '5d', '15h') to ISO format."""
    now = datetime.now()

    match = re.match(r"(\d+)([dh])", posted)
    if not match:
        return ""  # Return empty string for unexpected formats

    amount, unit = int(match.group(1)), match.group(2)

    if unit == "d":
        delta = timedelta(days=amount)
    elif unit == "h":
        delta = timedelta(hours=amount)
    else:
        return ""  # Unexpected unit

    return (now - delta).date().isoformat()


def parse_glassdoor_jobs(file_name: str) -> list[JobDescription]:
    """Parse jobs scraped from Glassdoor."""
    output_dir = Path(JOBS_DIR)
    output_dir.mkdir(exist_ok=True)

    if not Path(file_name).exists():
        print(f"File with scraped Glassdoor jobs {file_name} does not exist")
        return []

    with open(file_name, "r", encoding="utf-8") as f:
        jobs_data = json.load(f)

    jobs: list[JobDescription] = []
    print(f"Found {len(jobs_data)} jobs")
    for job in jobs_data:

        job_id = extract_job_id(job["link"])
        if not job_id:
            print(f"Skipping job {job['title']} because it has no jobListingId")
            continue
        filepath = output_dir / f"{job_id}.json"
        job_desc = JobDescription(
            job_id=job_id,
            url=job["link"],
            company=job["company"],
            title=job["title"],
            description=job["description"],
            posted_date=parse_posted_time(job["age"]),
        )
        jobs.append(job_desc)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(job_desc.__dict__, f, indent=2)
    return jobs
