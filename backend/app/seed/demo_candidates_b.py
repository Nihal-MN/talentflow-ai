"""Synthetic demo candidates — part B (profiles 6-10).

100% fictional people, companies and contact details. No real PII, ever.
"""

from __future__ import annotations

CANDIDATES_B: list[dict] = [
    {
        "full_name": "Omar Al Farsi",
        "email": "omar.alfarsi@example.com",
        "phone": "+971 50 555 0133",
        "location": "Dubai, UAE",
        "headline": "Senior DevOps Engineer",
        "summary": (
            "DevOps engineer with 6 years of experience running AWS infrastructure "
            "for SaaS products. Owns Kubernetes clusters, Terraform modules and the "
            "observability stack."
        ),
        "links": ["linkedin.com/in/omar-alfarsi"],
        "experience": [
            {
                "title": "Senior DevOps Engineer",
                "company": "Cloudline Systems",
                "location": "Dubai, UAE",
                "start": "May 2021",
                "end": "Present",
                "bullets": [
                    "Run multi-region Kubernetes clusters on AWS EKS for a multi-tenant platform",
                    "Manage infrastructure as code in Terraform across 3 environments",
                    "Built Prometheus and Grafana observability with SLO-based alerting",
                    "Automated deployments with GitHub Actions and cutting release toil",
                ],
            },
            {
                "title": "DevOps Engineer",
                "company": "Mosaic Software",
                "location": "Dubai, UAE",
                "start": "Feb 2019",
                "end": "Apr 2021",
                "bullets": [
                    "Managed Docker-based deployments and Linux servers",
                    "Administered RDS, S3 and IAM policies on AWS",
                    "Scripted operational tooling in Python",
                ],
            },
        ],
        "education": ["BSc Information Technology - University of Sharjah (2014 - 2018)"],
        "skills": [
            "AWS",
            "Kubernetes",
            "Terraform",
            "Docker",
            "GitHub Actions",
            "Linux",
            "Prometheus",
            "Grafana",
            "Python",
            "monitoring",
            "CI/CD",
        ],
        "certifications": [
            "Certified Kubernetes Administrator (2022)",
            "AWS Certified DevOps Engineer - Professional (2021)",
        ],
        "format": "pdf",
    },
    {
        "full_name": "Chen Wei",
        "email": "chen.wei@example.com",
        "phone": "+65 8555 0120",
        "location": "Singapore (Remote)",
        "headline": "Backend Engineer (Platform)",
        "summary": (
            "Backend engineer with 4 years of experience in platform tooling and "
            "developer experience. Moving deeper into DevOps: containers, CI/CD and "
            "cloud operations."
        ),
        "links": ["linkedin.com/in/chen-wei"],
        "experience": [
            {
                "title": "Backend Engineer, Platform",
                "company": "Straits Digital",
                "location": "Singapore",
                "start": "Jun 2022",
                "end": "Present",
                "bullets": [
                    "Maintained internal deployment tooling in Python",
                    "Owned CI/CD pipelines and Docker build infrastructure",
                    "Ran Linux services and automated monitoring checks",
                ],
            },
            {
                "title": "Software Engineer",
                "company": "PanAsia Commerce",
                "location": "Singapore",
                "start": "Jul 2020",
                "end": "May 2022",
                "bullets": [
                    "Built e-commerce backend services in Node.js and Python",
                    "Deployed small workloads to AWS with basic IAM setup",
                ],
            },
        ],
        "education": ["BEng Computer Engineering - NUS (2016 - 2020)"],
        "skills": [
            "Python",
            "Docker",
            "GitHub Actions",
            "Linux",
            "AWS",
            "Node.js",
            "CI/CD",
            "monitoring",
        ],
        "certifications": ["AWS Certified Cloud Practitioner (2023)"],
        "format": "docx",
    },
    {
        "full_name": "Fatima Noor",
        "email": "fatima.noor@example.com",
        "phone": "+971 56 555 0166",
        "location": "Abu Dhabi, UAE",
        "headline": "Machine Learning Engineer",
        "summary": (
            "ML engineer with 5 years of experience shipping production models in "
            "regulated environments. Recent focus on document understanding with "
            "LLMs, embeddings and retrieval-augmented generation."
        ),
        "links": ["linkedin.com/in/fatima-noor", "github.com/fatimanoor-ml"],
        "experience": [
            {
                "title": "Machine Learning Engineer",
                "company": "Vitalis Health",
                "location": "Abu Dhabi, UAE",
                "start": "Jan 2023",
                "end": "Present",
                "bullets": [
                    "Shipped LLM-based clinical document summarization using the OpenAI API",
                    "Built a retrieval-augmented generation pipeline with embeddings and pgvector",
                    "Owned evaluation harnesses and testing with pytest for model code",
                    "Deployed inference services with FastAPI on Kubernetes",
                ],
            },
            {
                "title": "Data Scientist",
                "company": "Falcon Insurance",
                "location": "Dubai, UAE",
                "start": "Sep 2020",
                "end": "Dec 2022",
                "bullets": [
                    "Built risk models in Python with scikit-learn and PyTorch",
                    "Productionized batch scoring pipelines and monitoring",
                ],
            },
        ],
        "education": ["MSc Artificial Intelligence - Khalifa University (2018 - 2020)"],
        "skills": [
            "Python",
            "PyTorch",
            "scikit-learn",
            "LLM",
            "OpenAI API",
            "prompt engineering",
            "RAG",
            "embeddings",
            "pgvector",
            "FastAPI",
            "pytest",
            "Kubernetes",
            "pandas",
        ],
        "certifications": ["DeepLearning.AI TensorFlow Developer (2021)"],
        "format": "pdf",
    },
    {
        "full_name": "Marco Rossi",
        "email": "marco.rossi@example.com",
        "phone": "+971 54 555 0188",
        "location": "Dubai, UAE",
        "headline": "Data Scientist",
        "summary": (
            "Data scientist with 6 years of experience in classical machine learning "
            "and forecasting. Strong statistical foundation; currently extending "
            "skills into modern NLP and LLM tooling."
        ),
        "links": ["linkedin.com/in/marco-rossi"],
        "experience": [
            {
                "title": "Data Scientist",
                "company": "Levant Foods",
                "location": "Dubai, UAE",
                "start": "Mar 2021",
                "end": "Present",
                "bullets": [
                    "Forecasting demand with gradient boosting models in Python",
                    "Built feature pipelines with pandas and numpy",
                    "Presented model results to non-technical stakeholders",
                ],
            },
            {
                "title": "Junior Data Analyst",
                "company": "Adriatic Consulting",
                "location": "Milan, Italy",
                "start": "Jan 2019",
                "end": "Feb 2021",
                "bullets": [
                    "Built SQL reporting and Excel models for retail clients",
                    "Supported forecasting projects with TensorFlow prototypes",
                ],
            },
        ],
        "education": ["MSc Statistics - University of Bologna (2016 - 2018)"],
        "skills": [
            "Python",
            "pandas",
            "numpy",
            "scikit-learn",
            "TensorFlow",
            "SQL",
            "Excel",
            "stakeholder management",
        ],
        "certifications": [],
        "format": "txt",
    },
    {
        "full_name": "Elena Vasquez",
        "email": "elena.vasquez@example.com",
        "phone": "+34 655 555 123",
        "location": "Barcelona, Spain (Remote)",
        "headline": "Senior Frontend Engineer",
        "summary": (
            "Frontend engineer with 5 years of experience building design systems "
            "and data-heavy interfaces in React and TypeScript. Careful about "
            "accessibility and performance."
        ),
        "links": ["linkedin.com/in/elena-vasquez"],
        "experience": [
            {
                "title": "Senior Frontend Engineer",
                "company": "Sagrada Software",
                "location": "Barcelona, Spain",
                "start": "Oct 2022",
                "end": "Present",
                "bullets": [
                    "Led the React and TypeScript rewrite of the analytics console",
                    "Built a Tailwind-based design system used by five product teams",
                    "Improved Core Web Vitals across the customer portal",
                ],
            },
            {
                "title": "Frontend Engineer",
                "company": "Iberia Fintech",
                "location": "Madrid, Spain",
                "start": "Sep 2020",
                "end": "Sep 2022",
                "bullets": [
                    "Developed customer onboarding flows in React and Redux",
                    "Integrated REST APIs and wrote Jest component tests",
                ],
            },
        ],
        "education": ["BSc Computer Science - Universitat Politècnica de Catalunya (2016 - 2020)"],
        "skills": ["React", "TypeScript", "Tailwind", "Redux", "CSS", "Jest", "REST APIs", "Figma"],
        "certifications": [],
        "format": "pdf",
    },
]
