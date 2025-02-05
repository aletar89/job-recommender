"""Job description definition and utils"""

import functools
import os
from typing import Callable

from pydantic import BaseModel

JOBS_DIR = "jobs_fetched"


class JobDescription(BaseModel):
    """Job description"""

    job_id: str
    url: str
    company: str
    title: str
    description: str
    posted_date: str


def cache_job_description(
    func: Callable[[str], JobDescription]
) -> Callable[[str], JobDescription]:
    """Decorator that caches job descriptions to files"""

    @functools.wraps(func)
    def wrapper(job_id: str) -> JobDescription:
        if not os.path.exists(JOBS_DIR):
            os.makedirs(JOBS_DIR)

        file_name = JOBS_DIR + f"/{job_id}.json"
        if os.path.exists(file_name):
            with open(file_name, encoding="utf-8") as file:
                return JobDescription.model_validate_json(file.read())

        job = func(job_id)
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(job.model_dump_json())
        return job

    return wrapper


@cache_job_description
def cached_job_description(job_id: str) -> JobDescription:
    """Get job description from cache or fail"""
    raise ValueError(f"Job description for {job_id} not found in {JOBS_DIR}")
