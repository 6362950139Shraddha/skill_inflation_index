"""
generate_sample_data.py

Generates a realistic SYNTHETIC dataset of job postings for a chosen role,
spanning multiple quarters, with an intentional upward "credential inflation"
trend baked in. This lets you build and test the full pipeline before
plugging in real scraped/archived data.

Swap this out for real data from:
  - scraper/wayback_scraper.py (archived postings from a job board)
  - Licensed datasets (Kaggle job posting archives, Lightcast, etc.)
  - Official APIs (Indeed Publisher API, LinkedIn Talent API, etc.)

Usage:
    python generate_sample_data.py --role "Data Analyst" --n_per_quarter 150 \
        --start 2022Q1 --end 2024Q4 --out ../output/sample_postings.csv
"""

import argparse
import random
import pandas as pd
from datetime import datetime

SKILL_POOL = [
    "SQL", "Python", "Excel", "Tableau", "Power BI", "R", "AWS", "Azure",
    "GCP", "Looker", "Snowflake", "dbt", "Airflow", "Spark", "Git",
    "Statistics", "A/B Testing", "Machine Learning", "Salesforce", "SAP",
]

DEGREE_LEVELS = ["None mentioned", "Bachelor's preferred", "Bachelor's required",
                  "Master's preferred", "Master's required"]

BUZZWORDS = [
    "fast-paced environment", "wear many hats", "self-starter",
    "stakeholder management", "cross-functional collaboration",
    "ownership mindset", "ambiguity", "scrappy", "high-growth",
]

COMPANY_SIZES = ["startup", "mid-size", "enterprise"]

TEMPLATES = [
    "We are looking for a {role} with {years}+ years of experience. "
    "Required skills: {skills}. {degree}. {buzz}",
    "{role} - join our team! Ideal candidate has {years} years of relevant "
    "experience and is proficient in {skills}. {degree}. We're looking for "
    "someone who can {buzz}.",
    "As a {role}, you will work with {skills}. Minimum {years} years "
    "experience required. {degree}. Must thrive in a {buzz}.",
]


def quarter_range(start, end):
    """Yield (year, quarter) tuples from start to end inclusive, e.g. '2022Q1'."""
    sy, sq = int(start[:4]), int(start[5])
    ey, eq = int(end[:4]), int(end[5])
    y, q = sy, sq
    while (y, q) <= (ey, eq):
        yield y, q
        q += 1
        if q > 4:
            q = 1
            y += 1


def quarter_index(year, quarter, start_year, start_quarter):
    """Number of quarters elapsed since the start, used to drive the inflation trend."""
    return (year - start_year) * 4 + (quarter - start_quarter)


def generate_posting(role, year, quarter, q_idx, total_quarters):
    """Generate one synthetic posting with inflation trending upward over time."""
    # Base drift: experience requirement creeps up ~0.06 yrs/quarter with noise
    progress = q_idx / max(total_quarters - 1, 1)  # 0 -> 1 across the whole range
    base_years = 2 + progress * 3.5  # drifts from ~2 yrs to ~5.5 yrs
    years = max(0, round(random.gauss(base_years, 1.1)))

    # Skill count also drifts up: from ~3 avg skills to ~7 avg skills
    base_skill_count = 3 + progress * 4
    n_skills = max(1, min(len(SKILL_POOL), round(random.gauss(base_skill_count, 1.5))))
    skills = random.sample(SKILL_POOL, n_skills)

    # Degree requirement stringency drifts up too
    degree_weights = [
        max(0.05, 0.5 - progress * 0.45),   # "None mentioned" shrinks
        0.25,
        0.10 + progress * 0.15,             # "Bachelor's required" grows
        0.10,
        0.05 + progress * 0.15,             # "Master's required" grows
    ]
    degree = random.choices(DEGREE_LEVELS, weights=degree_weights, k=1)[0]

    # Buzzword / scope-creep language becomes more common over time
    n_buzz = 1 if random.random() > progress * 0.6 else random.randint(2, 3)
    buzz = ", ".join(random.sample(BUZZWORDS, min(n_buzz, len(BUZZWORDS))))

    template = random.choice(TEMPLATES)
    description = template.format(
        role=role, years=years, skills=", ".join(skills), degree=degree, buzz=buzz
    )

    month = {1: 2, 2: 5, 3: 8, 4: 11}[quarter]
    posted_date = datetime(year, month, 15)

    return {
        "job_title": role,
        "company_size": random.choice(COMPANY_SIZES),
        "posted_date": posted_date.strftime("%Y-%m-%d"),
        "year": year,
        "quarter": f"{year}Q{quarter}",
        "description": description,
        "years_experience_true": years,   # ground truth, for validating extraction later
        "skill_count_true": n_skills,
        "degree_level_true": degree,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", default="Data Analyst")
    parser.add_argument("--n_per_quarter", type=int, default=150)
    parser.add_argument("--start", default="2022Q1")
    parser.add_argument("--end", default="2024Q4")
    parser.add_argument("--out", default="../output/sample_postings.csv")
    args = parser.parse_args()

    quarters = list(quarter_range(args.start, args.end))
    start_year, start_quarter = quarters[0]
    total_quarters = len(quarters)

    rows = []
    for i, (year, quarter) in enumerate(quarters):
        for _ in range(args.n_per_quarter):
            rows.append(generate_posting(args.role, year, quarter, i, total_quarters))

    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)
    print(f"Generated {len(df)} synthetic postings for '{args.role}' "
          f"across {total_quarters} quarters -> {args.out}")


if __name__ == "__main__":
    main()
