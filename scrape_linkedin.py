"""
This script scrapes jobs from LinkedIn.
"""

import re
import time
from datetime import datetime, timedelta
from enum import Enum
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from job_description import JobDescription, cache_job_description

BASE_SEARCH_URL = (
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"
)
SEARCH_URL = (
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/"
    + "search?keywords={search_query}&geoId={}&f_E=4&f_TPR=r604800&start={start}"
)
JOB_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"


class Geoid(Enum):
    """Geoid for the location of the job search"""

    BERLIN = 103035651
    GERMANY = 101282230
    EUROPE = 91000000


class PostingTime(Enum):
    """Posting time for the job search"""

    PAST_MONTH = "&f_TPR=r2592000"
    PAST_WEEK = "&f_TPR=r604800"
    PAST_24H = "&f_TPR=r86400"
    ANY_TIME = ""


class Remote(Enum):
    """Remote for the job search"""

    ON_SITE = "&f_WT=1"
    REMOTE = "&f_WT=2"
    HYBRID = "&f_WT=3"
    ANY = ""


def format_search_url(
    search_query: str,
    geo_id: Geoid = Geoid.BERLIN,
    post_time: PostingTime = PostingTime.PAST_WEEK,
    remote: Remote = Remote.ANY,
    offset: int = 0,
) -> str:
    """Format the search URL"""
    return BASE_SEARCH_URL + "".join(
        [
            f"keywords={quote(search_query)}",
            f"&geoId={geo_id.value}",
            "&f_E=4",  # Mid-Senior level
            "&f_JT=F",  # Full-time
            post_time.value,
            remote.value,
            f"&start={offset}",
        ]
    )


def get_search_page(search_url: str) -> list[str]:
    """Get the search page"""
    l = []
    res = requests.get(search_url, timeout=30)
    all_jobs_on_this_page = BeautifulSoup(res.text, "html.parser").find_all("li")
    for job_item in all_jobs_on_this_page:
        try:
            jobid = (
                job_item.find("div", {"class": "base-card"})
                .get("data-entity-urn")
                .split(":")[3]
            )
            l.append(jobid)
        except (AttributeError, IndexError) as e:
            print(f"Failed to parse this job item:\n{job_item}\nError: {e}")
    return l


def crawl_search(
    search_query: str,
    num_results: int,
    geo_id: Geoid = Geoid.BERLIN,
    post_time: PostingTime = PostingTime.PAST_WEEK,
    remote: Remote = Remote.ANY,
) -> list[str]:
    """Crawl the search"""
    out: set[str] = set()
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


def parse_posted_time(posted: str) -> str:
    """Parse the posted time"""
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


@cache_job_description
def get_linkedin_job_description(job_id: str) -> JobDescription:
    """Get the job description from LinkedIn"""
    job_url = JOB_URL.format(job_id=job_id)
    resp = requests.get(job_url, timeout=30)
    if resp.status_code == 429:
        print("😴 Rate limited, sleeping for 5 seconds")
        time.sleep(5)
        resp = requests.get(job_url, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"Failed to fetch job {job_id}")
    soup = BeautifulSoup(resp.text, "html.parser")
    try:
        company_elem = soup.find("a", class_="topcard__org-name-link")
        title_h2 = soup.find("h2", class_="top-card-layout__title")
        desc_elem = soup.find("div", class_="show-more-less-html__markup")
        date_elem = soup.find(
            "span", class_=lambda c: c and ("posted-time-ago__text" in c)
        )

        if (
            company_elem is None
            or title_h2 is None
            or desc_elem is None
            or date_elem is None
            or title_h2.parent is None
        ):
            raise AttributeError("Failed to find required elements")

        company = company_elem.text.strip()
        title = title_h2.text.strip()
        url = title_h2.parent.get("href")
        if not isinstance(url, str):
            raise AttributeError("Failed to find valid URL")
        description = desc_elem.get_text("\n", strip=True)
        date_posted = parse_posted_time(date_elem.text.strip())
    except (AttributeError, IndexError) as e:
        raise RuntimeError(f"Failed to parse job {job_id}: {e}\n{resp.text}") from e

    return JobDescription(
        job_id=job_id,
        url=url,
        company=company,
        title=title,
        description=description,
        posted_date=date_posted,
    )


def scrape_linkedin(
    search_query: str,
    num_results: int,
    geo_id: Geoid = Geoid.BERLIN,
    post_time: PostingTime = PostingTime.PAST_WEEK,
    remote: Remote = Remote.ANY,
) -> list[JobDescription]:
    """Scrape LinkedIn"""
    job_ids = crawl_search(search_query, num_results, geo_id, post_time, remote)
    return [get_linkedin_job_description(job_id) for job_id in job_ids]
