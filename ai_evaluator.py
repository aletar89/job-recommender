import argparse
import json
import os
import sys
from pprint import pprint
from textwrap import dedent
import csv
from openai import OpenAI
from pydantic import BaseModel
from tqdm import tqdm

from scrape_linkedin import JobDescription, cached_job_description

EVALUATIONS_DIR = "jobs_evaluated"

MODEL = "gpt-4o"

prompt = '''
    You are a recruiter helping me to find a job given a description of my skills and experience.
    <my CV>
    # Summary
    Versatile and technically proficient engineer with a broad range of expertise, spanning full-stack web development, algorithm design, electronic system design, and product development. Experienced in leading technical teams, managing end-to-end development cycles, and optimizing large-scale SaaS products. Proven track record in both commercial and academic environments, including co-founding and scaling a SaaS platform to 600,000+ monthly active users.
    
    # Technical Skills
    ## Software Development & Engineering
    ### Full-Stack Web Development
    Backend: Python (Flask), PostgreSQL, RESTful API design
    Frontend: TypeScript, Vue.js (Vue3), D3.js, Tailwind CSS
    Testing & QA: Cypress, Jest
    DevOps & Cloud: AWS (EKS, RDS, Aurora, S3, EC2), GCP (Firebase, BigQuery), Azure (ADB2C)
    CI/CD: ArgoCD, GitHub Actions, Docker, Kubernetes
    Monitoring: Prometheus, Grafana
    Security & Infrastructure: Web Application Firewall (WAF) implementation, authentication via OpenAthens SSO
    
    ### Algorithm & Data Processing
    Designed and optimized the core discovery algorithm of Connected Papers
    Optimized performance of the algorithm by two orders of magnitude.
    Developed an AI-powered support bot using OpenAI SDK, reducing support workload by 70%.
    Built a traffic analysis and mitigation system using a Web Application Firewall to reduce unwanted traffic and compute load by 30%.
    Designed a machine learning algorithm for neural spike classification during Ph.D. research.
    
    ## Embedded & Hardware Development
    ### ASIC & FPGA Design:
    Designed and fabricated an ASIC-based 32-channel current source for neural signal processing.
    Programmed and tested FPGA systems in Verilog.
    
    ### Embedded Systems:
    Firmware development in C for system-on-chip (SoC) architectures.
    Developed real-time spike sorting algorithms for neurophysiological applications.
    
    ### System Integration:
    Designed and built a miniaturized neural signal recording and activation system.
    Integrated high-density silicon probes for in-vivo experiments.
    
    ### PCB Design & Testing:
    Designed and tested custom PCBs using Altium Designer.
    Developed electronic hardware for neuroscience and biomedical applications.
    Product & Business Development
    
    ## Product Design & UX:
    Led the design and implementation of key product features for Connected Papers, focusing on intuitive UX and research-driven improvements.
    Conducted A/B testing and user analytics to refine user experience.
    
    ## Business & Growth Strategy:
    Spearheaded business development, marketing, and analytics efforts to scale Connected Papers profitably.
    Integrated payment processing systems with IPNs and webhooks, enabling seamless monetization.
    
    ## Cross-functional Leadership:
    Managed teams across development, research, and operations in both startup and military environments.
    Coordinated with institutional clients to deploy authentication solutions like OpenAthens-based SSO.
    
    # Research & Academic Background
    ## Neuroscience & Biomedical Engineering:
    Developed a state-of-the-art system for recording and activating neuronal signals, achieving high precision results published in IEEE TBioCAS.
    Conducted research on real-time neural data processing and closed-loop systems for brain-computer interfaces.
    Published work in peer-reviewed conferences and journals in both neuroscience and engineering.
    
    ## Defense & Military R&D:
    Led an IR countermeasure research team in the Israeli Air Force, conducting field experiments involving multiple aircraft and countermeasure systems.
    Modeled and reverse-engineered IR electro-mechanical systems for electronic warfare applications.
    
    # Education
    M.Sc. (Cum Laude) in Electrical Engineering, Tel Aviv University (2018 – 2020)
    B.Sc. in Electrical Engineering & B.Sc. in Physics, Technion Institute of Technology (2007 – 2011)
    
    # Soft Skills
    ## Leadership & Team Management:
    Managed and trained research teams in military, academic, and startup environments.
    Experience in guiding cross-functional teams through product and engineering lifecycles.
    
    ##Problem-Solving & Critical Thinking:
    Adept at tackling complex engineering challenges across software, hardware, and data science.
    Strong analytical skills for system modeling, algorithm development, and experimental design.
    
    ## Communication & Collaboration:
    Comfortable presenting technical concepts to diverse audiences, from business stakeholders to research collaborators.
    Experience working with both technical and non-technical stakeholders to drive project success.
    
    ## Languages
    Fluent in English, Russian, and Hebrew
    Currently learning German
    
    # Key Achievements
    Co-founded and scaled Connected Papers to 600,000+ monthly active users with a low-maintenance, high-margin business model.
    Developed and optimized core recommendation algorithms, automated support workflows, and traffic analysis tools.
    Published research in neuroscience and engineering journals.
    Led R&D efforts in electronic warfare and defense applications.
    </my CV>
    
    Skills self-assessment (1=beginner, 5=expert):
    python: 5
    TypeScript: 5
    REST API: 5
    English: 5
    Data visualization: 5
    SQL: 4
    Prometheus and Grafana: 4
    DevOps: 3
    C, MATLAB: 3
    Node.js: 2
    React: 2
    ML: 2
    pandas, numpy: 2
    pytorch: 1
    German: 1
    Java, Go, Kotlin, C++, C#, Ruby, PHP, Swift, Golang, Rust, Scala, Django: 1
    
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
    '''


class Requirement(BaseModel):
    skill: str
    required_proficiency_level_1_to_5: int
    my_proficiency_level_1_to_5: int
    requirement_strength_1_to_5: int


class BotOutput(BaseModel):
    requirements: list[Requirement]
    fit_to_requirements_percentage: int
    fit_to_requirements_explanation: str
    seniority_level_1_to_5: int
    what_the_company_does: str
    job_description_summary: str


class JobEvaluation(BotOutput):
    job_id: str


def get_job_evaluation(job: JobDescription) -> JobEvaluation:
    completion = OpenAI().beta.chat.completions.parse(
        model=MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": dedent(prompt)},
            {"role": "user", "content": f"{job.title}: {job.description}"}
        ],
        response_format=BotOutput,
    )
    bot_output = completion.choices[0].message.parsed
    assert bot_output is not None
    return JobEvaluation(job_id=job.job_id, **bot_output.model_dump())


def cached_job_evaluation(job: JobDescription) -> JobEvaluation:
    if not os.path.exists(EVALUATIONS_DIR):
        os.makedirs(EVALUATIONS_DIR)
    file_name = f"{EVALUATIONS_DIR}/{job.job_id}.json"
    if os.path.exists(file_name):
        with open(file_name, encoding="utf-8") as file:
            return JobEvaluation.model_validate_json(file.read())

    job_evaluation = get_job_evaluation(job)

    with open(file_name, "w", encoding="utf-8") as file:
        file.write(job_evaluation.model_dump_json())
    return job_evaluation


def evaluate_job(job_id: str) -> tuple[JobDescription, JobEvaluation]:
    job = cached_job_description(job_id)
    return job, cached_job_evaluation(job)


def csv_to_jsons():
    with open("jobs_evaluated.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            job = JobEvaluation(
                job_id=row["id"],
                what_the_company_does=row["what_the_company_does"],
                job_description_summary=row["job_description_summary"],
                fit_to_requirements_percentage=int(row["fit_to_requirements_percentage"]),
                fit_to_requirements_explanation=row["fit_to_requirements_explanation"],
                seniority_level_1_to_5=int(row["seniority_level"]),
            )
            with open(f"{EVALUATIONS_DIR}/{job.job_id}.json", "w", encoding="utf-8") as f:
                f.write(job.model_dump_json())


def format_requirements(requirements: list[Requirement], delimiter: str = ", ") -> str:
    requirements.sort(key=lambda r: r.requirement_strength_1_to_5, reverse=True)
    return delimiter.join(
        f"{r.skill}({r.requirement_strength_1_to_5}): {r.my_proficiency_level_1_to_5}/{r.required_proficiency_level_1_to_5}"
        for r in requirements)


def format_bot_output(bot_output: BotOutput) -> str:
    return "\n".join([
        f"{bot_output.job_description_summary} at a company that does {bot_output.what_the_company_does}.",
        "Skills:",
        format_requirements(bot_output.requirements, "\n"),
        f"Fit to requirements: {bot_output.fit_to_requirements_percentage}% - {bot_output.fit_to_requirements_explanation}",
    ])


def jsons_to_csv():
    out = []
    for file_name in os.listdir(EVALUATIONS_DIR):
        with open(f"{EVALUATIONS_DIR}/{file_name}", encoding="utf-8") as f:
            job = BotOutput.model_validate_json(f.read())
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
        row | job_description.model_dump()
        if "description" in row:
            del row["description"]
        out.append(row)
    with open("jobs_evaluated.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out[0].keys())
        writer.writeheader()
        writer.writerows(out)


if __name__ == "__main__":
    jsons_to_csv()
