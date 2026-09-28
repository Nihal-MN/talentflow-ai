"""Skill taxonomy: canonical names, aliases, categories and families.

One shared source of truth, used by:

* the deterministic mock extractor (JD/resume parsing),
* the normalization layer (deduplicating a candidate's skills),
* the matching engine (related-skill detection → "partial" credit).

Design stance: a curated, deliberately small taxonomy that favors precision
over recall. It only ever turns a hard miss into "partial" — it can never mark
a missing skill as met. Everything here is plain data: extend it freely.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: canonical skill name → list of aliases (case-insensitive, word-bounded).
SKILLS: dict[str, list[str]] = {
    # languages
    "python": ["python", "python3"],
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "java": ["java"],
    "kotlin": ["kotlin"],
    "golang": ["golang"],
    "ruby": ["ruby", "ruby on rails", "rails"],
    "php": ["php", "laravel"],
    "c#": ["c#", "csharp", ".net", "dotnet"],
    "c++": ["c++", "cpp"],
    "rust": ["rust"],
    "sql": ["sql"],
    "html": ["html", "html5"],
    "css": ["css", "css3", "scss", "sass"],
    # frontend
    "react": ["react", "react.js", "reactjs"],
    "next.js": ["next.js", "nextjs", "next js"],
    "vue": ["vue", "vue.js", "vuejs"],
    "angular": ["angular", "angularjs"],
    "svelte": ["svelte", "sveltekit"],
    "tailwind": ["tailwind", "tailwindcss", "tailwind css"],
    "redux": ["redux", "zustand"],
    # backend / frameworks
    "node.js": ["node", "node.js", "nodejs", "node js"],
    "express.js": ["express.js", "expressjs", "node express"],
    "nestjs": ["nestjs", "nest.js"],
    "django": ["django"],
    "flask": ["flask"],
    "fastapi": ["fastapi"],
    "spring": ["spring", "spring boot"],
    "graphql": ["graphql", "apollo"],
    "rest": ["rest api", "restful", "rest apis"],
    "grpc": ["grpc"],
    "microservices": ["microservices", "micro-services", "service-oriented"],
    "websockets": ["websockets", "websocket", "socket.io"],
    # data / persistence
    "postgresql": ["postgresql", "postgres", "psql"],
    "mysql": ["mysql", "mariadb"],
    "sqlite": ["sqlite"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "elasticsearch": ["elasticsearch", "opensearch"],
    "sqlalchemy": ["sqlalchemy"],
    "prisma": ["prisma"],
    "pgvector": ["pgvector"],
    "vector databases": [
        "vector database",
        "vector databases",
        "pinecone",
        "weaviate",
        "qdrant",
        "chroma",
        "faiss",
    ],
    "etl": ["etl", "elt", "data pipelines", "data pipeline"],
    "dbt": ["dbt"],
    "airflow": ["airflow", "apache airflow"],
    "spark": ["spark", "pyspark", "apache spark"],
    "kafka": ["kafka", "apache kafka"],
    "rabbitmq": ["rabbitmq"],
    "celery": ["celery"],
    "snowflake": ["snowflake"],
    "bigquery": ["bigquery", "google bigquery"],
    "redshift": ["redshift"],
    "warehousing": ["data warehouse", "data warehousing", "warehousing"],
    # cloud / devops
    "aws": ["aws", "amazon web services"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "azure": ["azure", "microsoft azure"],
    "docker": ["docker", "containers", "containerization"],
    "kubernetes": ["kubernetes", "k8s"],
    "terraform": ["terraform", "infrastructure as code", "iac"],
    "ci/cd": [
        "ci/cd",
        "cicd",
        "ci cd",
        "continuous integration",
        "continuous delivery",
        "continuous deployment",
    ],
    "github actions": ["github actions"],
    "gitlab ci": ["gitlab ci", "gitlab-ci"],
    "jenkins": ["jenkins"],
    "linux": ["linux", "unix"],
    "nginx": ["nginx"],
    "monitoring": ["monitoring", "observability"],
    "prometheus": ["prometheus"],
    "grafana": ["grafana"],
    "datadog": ["datadog"],
    "serverless": ["serverless", "lambda", "cloud functions"],
    # quality / testing
    "unit testing": ["unit testing", "unit tests", "test-driven development", "tdd"],
    "pytest": ["pytest"],
    "jest": ["jest"],
    "vitest": ["vitest"],
    "playwright": ["playwright"],
    "cypress": ["cypress"],
    "selenium": ["selenium"],
    "qa automation": ["qa automation", "test automation", "automated testing"],
    # ai / data science
    "machine learning": ["machine learning", "ml models", "supervised learning"],
    "llm": ["llm", "llms", "large language models", "large language model"],
    "openai api": ["openai api", "openai"],
    "langchain": ["langchain", "llamaindex"],
    "embeddings": ["embeddings", "embedding models"],
    "prompt engineering": ["prompt engineering", "prompt design"],
    "rag": ["rag", "retrieval-augmented generation", "retrieval augmented generation"],
    "numpy": ["numpy"],
    "pandas": ["pandas"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "pytorch": ["pytorch", "torch"],
    "tensorflow": ["tensorflow", "keras"],
    # analytics / product / business
    "excel": ["excel", "microsoft excel"],
    "tableau": ["tableau"],
    "power bi": ["power bi", "powerbi"],
    "looker": ["looker", "looker studio", "data studio"],
    "a/b testing": ["a/b testing", "ab testing", "split testing"],
    "product analytics": ["product analytics", "mixpanel", "amplitude"],
    "data visualization": ["data visualization", "data visualisation", "dashboards"],
    "stakeholder management": ["stakeholder management", "stakeholder communication"],
    "agile": ["agile", "scrum", "kanban"],
    "jira": ["jira", "confluence"],
    "figma": ["figma"],
    "salesforce": ["salesforce"],
    "hubspot": ["hubspot"],
    "github": ["github", "gitlab", "bitbucket"],
    "git": ["git", "version control"],
    # soft skills (kept conservative; used only for advisory signals)
    "communication": ["communication skills", "communication"],
    "leadership": ["leadership", "mentoring", "mentorship", "team lead", "technical lead"],
    "problem solving": ["problem solving", "problem-solving"],
    "ownership": ["ownership", "self-starter", "self starter"],
    "collaboration": ["collaboration", "cross-functional", "cross functional"],
}

#: canonical skill → coarse category (used for display + grouping).
CATEGORIES: dict[str, str] = {
    **dict.fromkeys(
        [
            "python",
            "javascript",
            "typescript",
            "java",
            "kotlin",
            "golang",
            "ruby",
            "php",
            "c#",
            "c++",
            "rust",
            "sql",
            "html",
            "css",
        ],
        "language",
    ),
    **dict.fromkeys(
        [
            "react",
            "next.js",
            "vue",
            "angular",
            "svelte",
            "tailwind",
            "redux",
            "node.js",
            "express.js",
            "nestjs",
            "django",
            "flask",
            "fastapi",
            "spring",
        ],
        "framework",
    ),
    **dict.fromkeys(
        [
            "postgresql",
            "mysql",
            "sqlite",
            "mongodb",
            "redis",
            "elasticsearch",
            "sqlalchemy",
            "prisma",
            "pgvector",
            "vector databases",
        ],
        "database",
    ),
    **dict.fromkeys(["aws", "gcp", "azure", "serverless"], "cloud"),
    **dict.fromkeys(
        [
            "docker",
            "kubernetes",
            "terraform",
            "ci/cd",
            "github actions",
            "gitlab ci",
            "jenkins",
            "linux",
            "nginx",
            "monitoring",
            "prometheus",
            "grafana",
            "datadog",
        ],
        "devops",
    ),
    **dict.fromkeys(
        [
            "etl",
            "dbt",
            "airflow",
            "spark",
            "kafka",
            "rabbitmq",
            "celery",
            "snowflake",
            "bigquery",
            "redshift",
            "warehousing",
        ],
        "data",
    ),
    **dict.fromkeys(
        [
            "unit testing",
            "pytest",
            "jest",
            "vitest",
            "playwright",
            "cypress",
            "selenium",
            "qa automation",
        ],
        "testing",
    ),
    **dict.fromkeys(
        [
            "machine learning",
            "llm",
            "openai api",
            "langchain",
            "embeddings",
            "prompt engineering",
            "rag",
            "numpy",
            "pandas",
            "scikit-learn",
            "pytorch",
            "tensorflow",
        ],
        "ai",
    ),
    **dict.fromkeys(
        [
            "excel",
            "tableau",
            "power bi",
            "looker",
            "a/b testing",
            "product analytics",
            "data visualization",
        ],
        "analytics",
    ),
    **dict.fromkeys(
        [
            "stakeholder management",
            "agile",
            "jira",
            "figma",
            "salesforce",
            "hubspot",
            "github",
            "git",
        ],
        "tool",
    ),
    **dict.fromkeys(
        ["communication", "leadership", "problem solving", "ownership", "collaboration"],
        "soft",
    ),
}

#: skill family → members. Membership implies *transferable* (not equivalent)
#: knowledge; the matching engine awards partial credit at most.
FAMILIES: dict[str, set[str]] = {
    "frontend": {
        "react",
        "next.js",
        "vue",
        "angular",
        "svelte",
        "html",
        "css",
        "tailwind",
        "redux",
    },
    "backend_js": {"node.js", "express.js", "nestjs"},
    "backend_python": {"django", "flask", "fastapi"},
    "languages": {
        "python",
        "javascript",
        "typescript",
        "java",
        "kotlin",
        "golang",
        "ruby",
        "php",
        "c#",
        "c++",
        "rust",
    },
    "databases": {
        "postgresql",
        "mysql",
        "sqlite",
        "mongodb",
        "redis",
        "elasticsearch",
        "sqlalchemy",
        "prisma",
    },
    "cloud": {"aws", "gcp", "azure"},
    "containers": {"docker", "kubernetes"},
    "cicd": {"ci/cd", "github actions", "gitlab ci", "jenkins"},
    "testing": {
        "unit testing",
        "pytest",
        "jest",
        "vitest",
        "playwright",
        "cypress",
        "qa automation",
    },
    "data_pipelines": {"etl", "dbt", "airflow", "spark", "kafka", "rabbitmq", "celery"},
    "warehouses": {"snowflake", "bigquery", "redshift", "warehousing"},
    "analytics": {
        "tableau",
        "power bi",
        "looker",
        "product analytics",
        "data visualization",
        "excel",
    },
    "ai": {
        "machine learning",
        "llm",
        "openai api",
        "langchain",
        "embeddings",
        "prompt engineering",
        "rag",
        "vector databases",
        "pgvector",
    },
    "api_styles": {"rest", "graphql", "grpc", "websockets"},
    "observability": {"monitoring", "prometheus", "grafana", "datadog"},
}

_SKILL_TO_FAMILY: dict[str, str] = {
    skill: family for family, members in FAMILIES.items() for skill in members
}


@dataclass(frozen=True, slots=True)
class SkillHit:
    """A skill mentioned somewhere in a text, with its evidence line."""

    canonical: str
    found_as: str
    evidence: str


def _alias_pattern(alias: str) -> re.Pattern[str]:
    """Word-bounded, case-insensitive pattern; ``+``/``#``/``.`` safe.

    The lookbehind also rejects a preceding dot so short aliases like ``js``
    cannot match inside compound names such as "Node.js" or "Vue.js" (whose
    canonical skills are detected via their own, longer aliases).
    """
    escaped = re.escape(alias).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![A-Za-z0-9+#.]){escaped}(?![A-Za-z0-9+#])", re.IGNORECASE)


#: (canonical, alias, pattern) sorted by alias length so longer aliases win.
_COMPILED: list[tuple[str, str, re.Pattern[str]]] = sorted(
    (
        (canonical, alias, _alias_pattern(alias))
        for canonical, aliases in SKILLS.items()
        for alias in aliases
    ),
    key=lambda item: len(item[1]),
    reverse=True,
)

_ALIAS_LOOKUP: dict[str, str] = {
    alias.lower(): canonical for canonical, aliases in SKILLS.items() for alias in aliases
}


def canonicalize(raw: str) -> str | None:
    """Map a raw skill string to its canonical name, if it is known."""
    cleaned = re.sub(r"\s+", " ", raw.strip().lower()).strip(" .,;:")
    if cleaned in SKILLS:
        return cleaned
    return _ALIAS_LOOKUP.get(cleaned)


def category_of(canonical: str) -> str:
    """Coarse category for display/grouping (defaults to ``other``)."""
    return CATEGORIES.get(canonical, "other")


def family_of(canonical: str) -> str | None:
    """Skill family name, or ``None`` when the skill is not in a family."""
    return _SKILL_TO_FAMILY.get(canonical)


def are_related(skill_a: str, skill_b: str) -> bool:
    """True when two *different* skills belong to the same family."""
    if not skill_a or not skill_b or skill_a == skill_b:
        return False
    family = family_of(skill_a)
    return family is not None and family == family_of(skill_b)


def extract_skills(text: str, *, max_evidence_chars: int = 240) -> list[SkillHit]:
    """Find known skills in ``text``, deduplicated, in order of first mention.

    Matching is line-oriented so the evidence snippet is always traceable to
    the exact source line.
    """
    found: dict[str, SkillHit] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or len(line) > 2000:
            continue
        for canonical, alias, pattern in _COMPILED:
            if canonical in found:
                continue
            if pattern.search(line):
                found[canonical] = SkillHit(
                    canonical=canonical,
                    found_as=alias,
                    evidence=line[:max_evidence_chars],
                )
    return list(found.values())
