"""
extract_features.py

Extracts structured features from raw job posting text:
  - years of experience required
  - skill mentions (against a configurable taxonomy)
  - degree requirement level
  - buzzword / scope-creep language count

Usage:
    python extract_features.py --in ../output/sample_postings.csv \
        --out ../output/features.csv
"""

import argparse
import re
import pandas as pd

# --- Configurable taxonomy: extend this for other roles ---------------------
SKILL_TAXONOMY = [
    "SQL", "Python", "Excel", "Tableau", "Power BI", "R", "AWS", "Azure",
    "GCP", "Looker", "Snowflake", "dbt", "Airflow", "Spark", "Git",
    "Statistics", "A/B Testing", "Machine Learning", "Salesforce", "SAP",
]

BUZZWORDS = [
    "fast-paced", "wear many hats", "self-starter", "stakeholder management",
    "cross-functional", "ownership mindset", "ambiguity", "scrappy",
    "high-growth",
]

# Matches patterns like: "3+ years", "minimum 5 years", "at least 2-4 years"
YEARS_PATTERN = re.compile(
    r"(\d+)\s*\+?\s*(?:-\s*\d+\s*)?years?", re.IGNORECASE
)

DEGREE_PATTERNS = [
    (re.compile(r"master'?s.{0,15}required", re.IGNORECASE), "Master's required"),
    (re.compile(r"master'?s.{0,15}preferred", re.IGNORECASE), "Master's preferred"),
    (re.compile(r"bachelor'?s.{0,15}required", re.IGNORECASE), "Bachelor's required"),
    (re.compile(r"bachelor'?s.{0,15}preferred", re.IGNORECASE), "Bachelor's preferred"),
]


def extract_years_experience(text):
    """Return the first (typically primary) years-of-experience mention, or None."""
    matches = YEARS_PATTERN.findall(text)
    if not matches:
        return None
    return int(matches[0])


def extract_skills(text):
    """Return the list of taxonomy skills mentioned in the text."""
    found = []
    for skill in SKILL_TAXONOMY:
        # word-boundary match, case-insensitive
        pattern = re.compile(r"\b" + re.escape(skill) + r"\b", re.IGNORECASE)
        if pattern.search(text):
            found.append(skill)
    return found


def extract_degree_level(text):
    """Return the strictest degree requirement phrase found, or 'None mentioned'."""
    for pattern, label in DEGREE_PATTERNS:
        if pattern.search(text):
            return label
    return "None mentioned"


def extract_buzzword_count(text):
    """Count scope-creep / soft-requirement buzzwords present."""
    text_lower = text.lower()
    return sum(1 for b in BUZZWORDS if b in text_lower)


def process_dataframe(df, text_col="description"):
    df = df.copy()
    df["years_experience_extracted"] = df[text_col].apply(extract_years_experience)
    df["skills_extracted"] = df[text_col].apply(extract_skills)
    df["skill_count_extracted"] = df["skills_extracted"].apply(len)
    df["degree_level_extracted"] = df[text_col].apply(extract_degree_level)
    df["buzzword_count"] = df[text_col].apply(extract_buzzword_count)
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", default="../output/sample_postings.csv")
    parser.add_argument("--out", dest="out_path", default="../output/features.csv")
    parser.add_argument("--text_col", default="description")
    args = parser.parse_args()

    df = pd.read_csv(args.in_path)
    df = process_dataframe(df, text_col=args.text_col)

    # skills_extracted is a list -> store as pipe-separated string for CSV
    df["skills_extracted"] = df["skills_extracted"].apply(lambda x: "|".join(x))

    df.to_csv(args.out_path, index=False)
    print(f"Extracted features for {len(df)} postings -> {args.out_path}")
    print(df[["years_experience_extracted", "skill_count_extracted",
              "degree_level_extracted", "buzzword_count"]].describe(include="all"))


if __name__ == "__main__":
    main()
