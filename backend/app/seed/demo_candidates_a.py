"""Synthetic demo candidates — part A (profiles 1-5).

100% fictional people, companies and contact details. No real PII, ever.
Formats are mixed on purpose (PDF / DOCX / TXT) to exercise the whole
ingestion pipeline.
"""

from __future__ import annotations

CANDIDATES_A: list[dict] = [
    {
        "full_name": "Amira Haddad",
        "email": "amira.haddad@example.com",
        "phone": "+971 50 555 0101",
        "location": "Dubai, UAE",
        "headline": "Senior Software Engineer",
        "summary": (
            "Senior full-stack engineer with 8 years of experience building logistics "
            "and fintech products. Comfortable owning features end to end: PostgreSQL "
            "schemas, Python services and React interfaces used by hundreds of "
            "operations staff every day."
        ),
        "links": ["linkedin.com/in/amira-haddad", "github.com/amira-haddad"],
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "Cedar Freight",
                "location": "Dubai, UAE",
                "start": "Mar 2021",
                "end": "Present",
                "bullets": [
                    "Led the migration of the shipment tracking platform to Python and FastAPI",
                    "Built React and TypeScript dashboards used by 300+ operations staff",
                    "Designed PostgreSQL schemas and deployed services on AWS with Docker",
                    "Introduced GitHub Actions pipelines that cut release time from days to hours",
                ],
            },
            {
                "title": "Software Engineer",
                "company": "Dune Analytics Ltd",
                "location": "Remote",
                "start": "Jun 2018",
                "end": "Feb 2021",
                "bullets": [
                    "Developed REST APIs in Django and Flask for fintech dashboards",
                    "Worked with PostgreSQL, Redis and MongoDB in a service-oriented stack",
                ],
            },
        ],
        "education": ["BSc Computer Science - American University of Sharjah (2014 - 2018)"],
        "skills": [
            "Python",
            "FastAPI",
            "React",
            "TypeScript",
            "PostgreSQL",
            "SQLAlchemy",
            "Docker",
            "AWS",
            "GitHub Actions",
            "Redis",
            "REST APIs",
            "Linux",
        ],
        "certifications": ["AWS Certified Solutions Architect Associate (2023)"],
        "format": "pdf",
    },
    {
        "full_name": "Daniel Okafor",
        "email": "daniel.okafor@example.com",
        "phone": "+234 803 555 0142",
        "location": "Lagos, Nigeria (Remote)",
        "headline": "Senior Backend Engineer",
        "summary": (
            "Backend engineer with 6 years of experience designing service-oriented "
            "systems in Python and Node.js. Focused on API design, data modeling and "
            "reliability for high-traffic platforms."
        ),
        "links": ["linkedin.com/in/daniel-okafor"],
        "experience": [
            {
                "title": "Senior Backend Engineer",
                "company": "Paystream Africa",
                "location": "Lagos, Nigeria",
                "start": "Jan 2022",
                "end": "Present",
                "bullets": [
                    "Designed payments APIs in Python and FastAPI processing millions of requests",
                    "Optimized PostgreSQL query performance for the ledger service",
                    "Ran services on AWS with Docker and monitoring via Prometheus dashboards",
                ],
            },
            {
                "title": "Backend Engineer",
                "company": "Kwara Labs",
                "location": "Lagos, Nigeria",
                "start": "Jul 2019",
                "end": "Dec 2021",
                "bullets": [
                    "Built Node.js microservices and internal admin tools with Vue",
                    "Maintained CI/CD pipelines in GitHub Actions",
                ],
            },
        ],
        "education": ["BSc Software Engineering - University of Lagos (2015 - 2019)"],
        "skills": [
            "Python",
            "FastAPI",
            "Node.js",
            "Vue",
            "PostgreSQL",
            "Docker",
            "AWS",
            "GitHub Actions",
            "REST APIs",
            "Monitoring",
        ],
        "certifications": [],
        "format": "docx",
    },
    {
        "full_name": "Priya Nair",
        "email": "priya.nair@example.com",
        "phone": "+91 98450 55127",
        "location": "Bengaluru, India",
        "headline": "Full Stack Developer",
        "summary": (
            "Full-stack developer with 3 years of experience across the React and "
            "Python ecosystems. Ships user-facing features with TypeScript on the "
            "frontend and Flask services on the backend."
        ),
        "links": ["linkedin.com/in/priya-nair"],
        "experience": [
            {
                "title": "Full Stack Developer",
                "company": "Meridian Retail Tech",
                "location": "Bengaluru, India",
                "start": "Aug 2023",
                "end": "Present",
                "bullets": [
                    "Built React and TypeScript store-ops dashboards",
                    "Developed Flask APIs backed by PostgreSQL",
                    "Containerized services with Docker for staging environments",
                ],
            },
            {
                "title": "Software Developer",
                "company": "Nimbus Software",
                "location": "Kochi, India",
                "start": "Jul 2022",
                "end": "Jul 2023",
                "bullets": [
                    "Maintained a Django application and PostgreSQL reports",
                    "Wrote unit tests with pytest",
                ],
            },
        ],
        "education": ["B.Tech Computer Science - NIT Calicut (2018 - 2022)"],
        "skills": [
            "React",
            "TypeScript",
            "Python",
            "Flask",
            "PostgreSQL",
            "Docker",
            "pytest",
            "CSS",
        ],
        "certifications": [],
        "format": "txt",
    },
    {
        "full_name": "Lucas Meyer",
        "email": "lucas.meyer@example.com",
        "phone": "+971 52 555 0199",
        "location": "Dubai, UAE",
        "headline": "Senior Data Analyst",
        "summary": (
            "Data analyst with 5 years of experience turning commercial data into "
            "decisions. Owns the analytics stack end to end: SQL models, dashboards "
            "in Power BI and experiment design."
        ),
        "links": ["linkedin.com/in/lucas-meyer"],
        "experience": [
            {
                "title": "Senior Data Analyst",
                "company": "Oasis Retail Group",
                "location": "Dubai, UAE",
                "start": "Feb 2022",
                "end": "Present",
                "bullets": [
                    "Own weekly business review dashboards in Power BI used by 40+ managers",
                    "Designed and analyzed A/B testing programs for pricing",
                    "Modeled sales data in SQL and automated reports with Excel macros",
                ],
            },
            {
                "title": "Data Analyst",
                "company": "Levant Foods",
                "location": "Amman, Jordan",
                "start": "Sep 2019",
                "end": "Jan 2022",
                "bullets": [
                    "Built Tableau dashboards for supply chain performance",
                    "Partnered with finance on demand forecasting models",
                ],
            },
        ],
        "education": ["BSc Economics - University of Jordan (2015 - 2019)"],
        "skills": [
            "SQL",
            "Excel",
            "Power BI",
            "Tableau",
            "A/B testing",
            "Python",
            "pandas",
            "Stakeholder management",
            "data visualization",
        ],
        "certifications": ["Microsoft Certified: Power BI Data Analyst Associate (2023)"],
        "format": "docx",
    },
    {
        "full_name": "Sofia Petrova",
        "email": "sofia.petrova@example.com",
        "phone": "+971 55 555 0177",
        "location": "Abu Dhabi, UAE",
        "headline": "BI & Reporting Analyst",
        "summary": (
            "Business intelligence analyst with 4 years of experience in retail "
            "reporting. Strong SQL and visualization skills, comfortable owning "
            "self-service BI for non-technical teams."
        ),
        "links": ["linkedin.com/in/sofia-petrova"],
        "experience": [
            {
                "title": "BI & Reporting Analyst",
                "company": "Falcon Stores",
                "location": "Abu Dhabi, UAE",
                "start": "Apr 2022",
                "end": "Present",
                "bullets": [
                    "Built Looker and Power BI dashboards for 90+ retail stores",
                    "Wrote advanced SQL transformations and data quality checks",
                    "Trained store managers on self-service reporting in Excel",
                ],
            },
            {
                "title": "Reporting Analyst",
                "company": "Gulf Logistics Co",
                "location": "Dubai, UAE",
                "start": "Mar 2020",
                "end": "Mar 2022",
                "bullets": [
                    "Automated weekly operations reports with SQL and Excel",
                    "Supported the e-commerce team with order analytics",
                ],
            },
        ],
        "education": ["MSc Business Analytics - Higher School of Economics (2017 - 2019)"],
        "skills": ["SQL", "Power BI", "Looker", "Excel", "data visualization", "communication"],
        "certifications": [],
        "format": "txt",
    },
]
