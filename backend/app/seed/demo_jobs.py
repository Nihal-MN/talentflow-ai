"""Synthetic demo job descriptions — 100% fictional, no real company data.

Used by the seed command (``python -m app.seed``) and written as reference
files into ``examples/jobs/``. Keys are the slugs for those files.
"""

from __future__ import annotations

DEMO_JOBS: dict[str, dict] = {
    "senior-full-stack-engineer": {
        "filename": "senior-full-stack-engineer.md",
        "company": "Cedar Freight",
        "text": """\
Senior Full Stack Engineer

Company: Cedar Freight
Location: Dubai, UAE - Hybrid
Employment type: Full-time

About the role
Cedar Freight builds logistics software that moves shipments across the GCC.
You will own features end to end, from PostgreSQL schema design to polished
React interfaces used daily by operations teams.

Requirements
- 5+ years of software engineering experience
- Expert-level Python and FastAPI
- Strong React and TypeScript skills
- PostgreSQL and SQLAlchemy experience
- Docker and CI/CD experience
- Experience deploying and operating services on AWS
- Bachelor's degree in Computer Science or a related field

Nice to have
- Kubernetes
- Experience in logistics or supply chain

We review every application within one week. Cedar Freight is an equal
opportunity employer.
""",
    },
    "data-analyst": {
        "filename": "data-analyst.md",
        "company": "Oasis Retail Group",
        "text": """\
Data Analyst

Company: Oasis Retail Group
Location: Dubai, UAE
Employment type: Full-time

About the role
Oasis Retail Group runs 120 stores across the region. As our Data Analyst you
will turn store and e-commerce data into decisions: dashboards, experiments
and weekly business reviews.

Requirements
- 3+ years of experience as a data analyst or similar role
- Advanced SQL skills
- Strong Excel skills
- Experience building dashboards in Power BI or Tableau
- Experience designing and reading A/B testing results
- Excellent communication skills with non-technical stakeholders
- Bachelor's degree in Statistics, Economics or a related field

Nice to have
- Python for data analysis (pandas, numpy)
- Experience in retail or e-commerce
""",
    },
    "devops-engineer": {
        "filename": "devops-engineer.md",
        "company": "Cloudline Systems",
        "text": """\
DevOps Engineer

Company: Cloudline Systems
Location: Remote (UTC+4 timezone preferred)
Employment type: Full-time

About the role
Cloudline Systems runs a multi-tenant SaaS platform for 400+ customers. You
will own our infrastructure: deployments, observability, cost and reliability.

Requirements
- 4+ years of DevOps or SRE experience
- Deep AWS knowledge (ECS, RDS, S3, IAM)
- Kubernetes in production
- Terraform and infrastructure-as-code practices
- Docker containers
- CI/CD pipelines (GitHub Actions or GitLab CI)
- Strong Linux administration skills
- Prometheus and Grafana monitoring experience

Nice to have
- Python automation scripting
- Experience in SaaS environments
""",
    },
    "machine-learning-engineer": {
        "filename": "machine-learning-engineer.md",
        "company": "Vitalis Health",
        "text": """\
Machine Learning Engineer

Company: Vitalis Health
Location: Abu Dhabi, UAE
Employment type: Full-time

About the role
Vitalis Health builds clinical decision-support software. You will ship ML
systems that help clinicians focus on patients: retrieval, document
understanding and careful evaluation.

Requirements
- 4+ years of production machine learning experience
- Strong Python and machine learning fundamentals
- PyTorch or TensorFlow experience
- Experience deploying LLM-based features (OpenAI API, prompt engineering)
- Experience with embeddings and retrieval (RAG, vector databases)
- Experience with pytest and testing ML code
- Bachelor's or Master's degree in Computer Science or a related field

Nice to have
- Experience in healthcare or regulated industries
- Kubernetes deployment experience
""",
    },
}
