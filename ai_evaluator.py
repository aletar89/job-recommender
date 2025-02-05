"""AI evaluator."""

import csv
import os
from textwrap import dedent

from openai import OpenAI
from pydantic import BaseModel

from job_description import JobDescription, cached_job_description

EVALUATIONS_DIR = "jobs_evaluated"

MODEL = "gpt-4o"

PROMPT = """
    You are a recruiter helping me to find a job given a description of my skills and experience.
    <my CV>
    {cv}
    </my CV>
    
    Skills self-assessment (1=beginner, 5=expert):
    {skills}
    
    On a personal note:
    - I've been doing Full Stack work for the last 5 years and this is what I'm most fresh at but I have a versatile background and I'm open to new challenges as a generalist engineer.
        
    I need you to analyze a job description and answer the following questions:
    - What skills are required for the job? specify the skill, the required proficiency level, my proficiency level (1=beginner, 5=expert), and how strongly is it required level (1=nice to have, 5=must have)
    - How well do my skills and experience fit the job requirements as a percentage? 0-100 (Being overqualified is not a problem)
    IMPORTANT! IF PROFICIENCY IN GERMAN IS A STRONG REQUIREMENT - THE FIT IS 0%. NOT SPEAKING GERMAN IS A DEAL BREAKER.
    - Explain how well my skills and experience fit the job requirements in 1-2 sentences.
    - What is the seniority level of the job? 1 is junior, 3 is mid, 5 is senior
    - what does the company do? what is their main product or claim to fame? what value do they provide? the answer should be less than 10 words
    - summarize the job description - what will I be doing? the answer should be less than 10 words
    
    Please evaluate the fit of the following job description to my skills and experience:
    """


class Requirement(BaseModel):
    """Requirement for a job."""

    skill: str
    required_proficiency_level_1_to_5: int
    my_proficiency_level_1_to_5: int
    requirement_strength_1_to_5: int


class BotOutput(BaseModel):
    """Bot output."""

    requirements: list[Requirement]
    fit_to_requirements_percentage: int
    fit_to_requirements_explanation: str
    seniority_level_1_to_5: int
    what_the_company_does: str
    job_description_summary: str


class JobEvaluation(BotOutput):
    """Job evaluation."""

    job_id: str


def prompt() -> str:
    """Format the prompt."""
    with open("cv.txt", "r", encoding="utf-8") as f:
        cv = f.read()
    with open("skills.txt", "r", encoding="utf-8") as f:
        skills = f.read()
    return dedent(PROMPT.format(cv=cv, skills=skills))


def ask_bot_to_evaluate(job: JobDescription) -> JobEvaluation:
    """Get a job evaluation."""
    completion = OpenAI().beta.chat.completions.parse(
        model=MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": prompt()},
            {"role": "user", "content": f"{job.title}: {job.description}"},
        ],
        response_format=BotOutput,
    )
    bot_output = completion.choices[0].message.parsed
    assert bot_output is not None
    return JobEvaluation(job_id=job.job_id, **bot_output.model_dump())


def cached_job_evaluation(job: JobDescription) -> JobEvaluation:
    """Cached job evaluation."""
    if not os.path.exists(EVALUATIONS_DIR):
        os.makedirs(EVALUATIONS_DIR)
    file_name = f"{EVALUATIONS_DIR}/{job.job_id}.json"
    if os.path.exists(file_name):
        with open(file_name, encoding="utf-8") as file:
            return JobEvaluation.model_validate_json(file.read())

    job_evaluation = ask_bot_to_evaluate(job)

    with open(file_name, "w", encoding="utf-8") as file:
        file.write(job_evaluation.model_dump_json())
    return job_evaluation


def evaluation_result(job_id: str) -> tuple[JobDescription, JobEvaluation]:
    """Evaluate a job."""
    job = cached_job_description(job_id)
    job_evaluation = cached_job_evaluation(job)
    return job, job_evaluation


def format_requirements(requirements: list[Requirement], delimiter: str = ", ") -> str:
    """Format requirements."""
    requirements.sort(key=lambda r: r.requirement_strength_1_to_5, reverse=True)
    return delimiter.join(
        f"{r.skill}({r.requirement_strength_1_to_5}): "
        f"{r.my_proficiency_level_1_to_5}/{r.required_proficiency_level_1_to_5}"
        for r in requirements
    )


def format_bot_output(bot_output: BotOutput) -> str:
    """Format bot output."""
    return "\n".join(
        [
            f"{bot_output.job_description_summary} "
            f"at a company that does {bot_output.what_the_company_does}.",
            "Skills:",
            format_requirements(bot_output.requirements, "\n"),
            f"Fit to requirements: {bot_output.fit_to_requirements_percentage}%"
            f" - {bot_output.fit_to_requirements_explanation}",
        ]
    )


def jsons_to_csv():
    """Convert JSONs to a CSV."""
    out = []
    for file_name in os.listdir(EVALUATIONS_DIR):
        with open(f"{EVALUATIONS_DIR}/{file_name}", encoding="utf-8") as f:

            job = JobEvaluation.model_validate_json(f.read())
            row = {
                "id": job.job_id,
                "what_the_company_does": job.what_the_company_does,
                "job_description_summary": job.job_description_summary,
                "fit_to_requirements_percentage": job.fit_to_requirements_percentage,
                "fit_to_requirements_explanation": job.fit_to_requirements_explanation,
                "seniority_level": job.seniority_level_1_to_5,
                "requirements": format_requirements(job.requirements),
            }
        job_description = cached_job_description(job.job_id)
        row.update(job_description.model_dump())
        if "description" in row:
            del row["description"]
        out.append(row)
    with open("jobs_evaluated.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out[0].keys())
        writer.writeheader()
        writer.writerows(out)


if __name__ == "__main__":
    jsons_to_csv()
