"""Skill taxonomy behavior: canonicalization, categories, families, boundaries.

Covers the alias/family extensions added for the taxonomy task, including the
precision guarantees (word boundaries reject matches inside other words).
"""

from __future__ import annotations

from app.services.skills import (
    are_related,
    canonicalize,
    category_of,
    extract_skills,
)


def test_cloud_aliases_canonicalize():
    assert canonicalize("EKS") == "kubernetes"
    assert canonicalize("gke") == "kubernetes"
    assert canonicalize("AKS") == "kubernetes"
    assert canonicalize("s3") == "aws"
    assert canonicalize("EC2") == "aws"
    assert canonicalize("Firebase") == "firebase"


def test_language_and_mobile_skills_canonicalize():
    assert canonicalize("Swift") == "swift"
    assert canonicalize("objective-c") == "objective-c"
    assert canonicalize("objc") == "objective-c"
    assert canonicalize("Dart") == "dart"
    assert canonicalize("bash") == "bash"
    assert canonicalize("shell scripting") == "bash"
    assert canonicalize("Scala") == "scala"
    assert canonicalize("Flutter") == "flutter"
    assert canonicalize("Zendesk") == "zendesk"
    assert canonicalize("Freshdesk") == "freshdesk"
    assert canonicalize("Android") == "android"


def test_new_categories():
    assert category_of("swift") == "language"
    assert category_of("bash") == "language"
    assert category_of("flutter") == "framework"
    assert category_of("android") == "framework"
    assert category_of("firebase") == "cloud"
    assert category_of("ansible") == "devops"
    assert category_of("pulumi") == "devops"
    assert category_of("databricks") == "data"
    assert category_of("mlops") == "ai"
    assert category_of("postman") == "tool"


def test_new_families_relatedness():
    # infra-as-code family
    assert are_related("terraform", "ansible")
    assert are_related("ansible", "pulumi")
    assert not are_related("terraform", "kubernetes")
    # mobile family (cross-platform transferability, partial credit only)
    assert are_related("swift", "flutter")
    assert are_related("android", "objective-c")
    assert not are_related("swift", "react")
    # warehouses extended with databricks
    assert are_related("databricks", "snowflake")
    # cloud family extended with firebase
    assert are_related("firebase", "gcp")


def test_extract_finds_new_skills_with_evidence():
    text = "\n".join(
        [
            "Deployed services onto EKS across three regions.",
            "Data lake stored in S3 buckets.",
            "Built the iOS app in Swift and Kotlin multiplatform.",
        ]
    )
    hits = {hit.canonical: hit for hit in extract_skills(text)}
    assert hits["kubernetes"].found_as == "eks"
    assert "EKS" in hits["kubernetes"].evidence
    assert hits["aws"].found_as == "s3"
    assert hits["swift"].found_as == "swift"


def test_short_aliases_never_match_inside_words():
    # "breaks" contains the letters a-k-s; "talks" and "tasks" contain a-k-s too.
    for sentence in (
        "The candidate breaks down complex problems.",
        "She talks to stakeholders weekly.",
        "Owns the sprint tasks end to end.",
    ):
        hits = {hit.canonical for hit in extract_skills(sentence)}
        assert "kubernetes" not in hits
    # "scalable" starts with "scala" — must not canonicalize as the language.
    hits = {hit.canonical for hit in extract_skills("Plans scalable architectures")}
    assert "scala" not in hits
    # "js" must not fire inside "Node.js" (existing guarantee, still enforced).
    hits = {hit.canonical for hit in extract_skills("Built services in Node.js")}
    assert "javascript" not in hits
    assert "node.js" in hits
