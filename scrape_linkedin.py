import os
import re
import time
from datetime import datetime, timedelta
from enum import Enum
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
from tqdm import tqdm

BASE_SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"
SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={search_query}&geoId={}&f_E=4&f_TPR=r604800&start={start}"
JOB_URL = 'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}'
JOBS_DIR = "jobs_fetched"


class Geoid(Enum):
    BERLIN = 103035651
    GERMANY = 101282230
    EUROPE = 91000000


class PostingTime(Enum):
    PAST_MONTH = "&f_TPR=r2592000"
    PAST_WEEK = "&f_TPR=r604800"
    PAST_24H = "&f_TPR=r86400"
    ANY_TIME = ""


class Remote(Enum):
    ON_SITE = "&f_WT=1"
    REMOTE = "&f_WT=2"
    HYBRID = "&f_WT=3"
    ANY = ""


class JobDescription(BaseModel):
    job_id: str
    url: str
    company: str
    title: str
    description: str
    posted_date: str


def format_search_url(
        search_query: str,
        geo_id: Geoid = Geoid.BERLIN,
        post_time: PostingTime = PostingTime.PAST_WEEK,
        remote: Remote = Remote.ANY,
        offset: int = 0
) -> str:
    return BASE_SEARCH_URL + "".join([
        f"keywords={quote(search_query)}",
        f"&geoId={geo_id.value}",
        "&f_E=4",  # Mid-Senior level
        "&f_JT=F",  # Full-time
        post_time.value,
        remote.value,
        f"&start={offset}"
    ])


def get_search_page(search_url: str) -> list[str]:
    l = []
    res = requests.get(search_url)
    all_jobs_on_this_page = BeautifulSoup(res.text, 'html.parser').find_all("li")
    for x in range(0, len(all_jobs_on_this_page)):
        try:
            jobid = all_jobs_on_this_page[x].find("div", {"class": "base-card"}).get('data-entity-urn').split(":")[3]
            l.append(jobid)
        except:
            print(f"Failed to parse this job item:\n{all_jobs_on_this_page[x]}")
    return l


def crawl_search(search_query: str,
                 num_results: int,
                 geo_id: Geoid = Geoid.BERLIN,
                 post_time: PostingTime = PostingTime.PAST_WEEK,
                 remote: Remote = Remote.ANY,
                 ) -> list[str]:
    out = set()
    start = 0
    while len(out) < num_results:
        search_url = format_search_url(search_query, geo_id, post_time, remote, start)
        page = get_search_page(search_url)
        if len(page) == 0:
            break
        out.update(page)
        print(f"Found {len(out)} jobs")
        start += len(page)
    return list(out)


def parse_posted_time(posted):
    now = datetime.now()

    match = re.match(r"(\d+)\s+(day|hour|minute|second)s?\s+ago", posted)
    if not match:
        return posted  # Handle cases where the format is unexpected

    amount, unit = int(match.group(1)), match.group(2)

    if unit == "day":
        delta = timedelta(days=amount)
    elif unit == "hour":
        delta = timedelta(hours=amount)
    elif unit == "minute":
        delta = timedelta(minutes=amount)
    elif unit == "second":
        delta = timedelta(seconds=amount)
    else:
        return posted  # Unexpected format

    return (now - delta).date().isoformat()


def get_job_description(job_id: str) -> JobDescription:
    job_url = JOB_URL.format(job_id=job_id)
    resp = requests.get(job_url)
    if resp.status_code == 429:
        print("😴 Rate limited, sleeping for 5 seconds")
        time.sleep(5)
        resp = requests.get(job_url)
    if not resp.ok:
        raise RuntimeError(f"Failed to fetch job {job_id}")
    soup = BeautifulSoup(resp.text, 'html.parser')
    try:
        company = soup.find('a', class_="topcard__org-name-link").text.strip()
        title_h2 = soup.find('h2', class_="top-card-layout__title")
        title = title_h2.text.strip()
        url = title_h2.parent.get('href')
        description = soup.find('div', class_='show-more-less-html__markup').get_text("\n", strip=True)
        date_posted = parse_posted_time(
            soup.find('span', class_=lambda c: c and ('posted-time-ago__text' in c)).text.strip())
    except:
        raise RuntimeError(f"Failed to parse job {job_id}:\n{resp.text}")

    return JobDescription(
        job_id=job_id,
        url=url,
        company=company,
        title=title,
        description=description,
        posted_date=date_posted
    )


def cached_job_description(job_id: str) -> JobDescription:
    if not os.path.exists(JOBS_DIR):
        os.makedirs(JOBS_DIR)
    file_name = JOBS_DIR + f"/{job_id}.json"
    if os.path.exists(file_name):
        with open(file_name, encoding="utf-8") as file:
            return JobDescription.model_validate_json(file.read())
    job = get_job_description(job_id)
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(job.model_dump_json())
    return job


def get_job_descriptions_from_search(num_pages: int) -> list[JobDescription]:
    job_ids = crawl_search(num_pages)
    return [cached_job_description(job_id) for job_id in tqdm(job_ids, desc="Fetching job descriptions")]


if __name__ == "__main__":
    get_job_descriptions_from_search(3)
