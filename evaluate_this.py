from airtable import AirTable
from scrape_linkedin import JobDescription

from ai_evaluator import cached_job_evaluation, format_bot_output

description = """
About the job
Let’s face it: out-of-pocket expenses suck. And manual expense spreadsheets are old-school. No one wants to wait until payday to be reimbursed for something they bought for work, and finance teams have better things to do than spend hours tapping away on Excel. At Pleo, we’re on a mission to change this. We’re here to make spend management surprisingly effective and empowering – for finance teams and employees.

We’re doing away with an outdated business process to end out-of-pocket spending, encourage autonomy and give finance teams trust in employees. You'll be selling the SaaS tool (company spending solution) that comes with physical pre-paid cards that are then distributed to all employees of the company. But Pleo’s about more than just paying for stuff. You’ll be helping our customers simplify and streamline their invoices, reimbursements, subscriptions – the lot.

As our first ever Technical Solution Engineer, your primary responsibilities will be to support Pleo customers in creating custom integrations, how to use the product, and being the technical interface for customers from scoping to go live.

What will you be doing?
Support Pleo’s customers in creating custom integrations using Pleo’s APIs to fit their process and system needs.
Support customers to understand the Pleo product and how to build an app or integration using Pleo APIs.
Support customers through the process of scoping, designing, building, testing, and going live with their custom integration.
Be the primary technical interface and point of contact between a customer and Pleo for their custom integration needs and projects. Coordinate contact with different teams and people at Pleo.
Find and engage with partners to build custom integrations with Pleo. Support partner to understand the Pleo product and how to build an integration.
Partner with sales, customer success, support, product, engineering, and partners to advocate for custom integration development in-line with customer needs.
Request, feedback on, and validate partner proposals, including commercial, product, UX, and technical aspects. Work with product teams drive product improvements by bringing product and API feedback from partners and customers.
Become a subject matter expert in how Pleo best integrates with other types of software and on all existing and new integrations.
What we need:
Fluency in English is required as our company language.
Experience in driving the process of defining, building, and launching integrations with partners and internal teams, from start to value.
Use API documentation to independently design solutions addressing the customer needs.
Understanding of REST APIs and ability to troubleshoot errors.
Ability to explain complex technical concepts in simple, understandable terms to non-technical stakeholders, that includes written and verbal communication during presentations and demonstrations
Strong project management and organizational skills
Ability to work as an individual contributor with minimal supervision, with great time management skills.
Nice-to-haves:
Fintech background
Experience from integrations in the accounting/ERP and IDP/HRIS space
Experience working with partners to build integrations and apps for SaaS customers
Experience working in SaaS and financial or accounting services
Experience in outlining user flows and creating wireframe designs"""

job = JobDescription(
    job_id="2AZ3ck",
    description=description,
    title="Technical Solution Engineer",
    company="Pleo",
    posted_date="2024-01-01",
    url="https://wellfound.com/l/2AZ3ck",
)

evaluation = cached_job_evaluation(job)

print(format_bot_output(evaluation))
air_table = AirTable()
if evaluation.fit_to_requirements_percentage >= 0.85 and not air_table.job_id_in_table(
    job.job_id
):
    print(f"🎯 Adding {job.company} to the table")
    air_table.add_to_table(job, evaluation)
