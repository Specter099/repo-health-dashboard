# CLAUDE.md

## Project Overview

**repo-health-dashboard** monitors GitHub repository health by collecting metrics via the GitHub API, computing health scores, and generating a static HTML dashboard. The dashboard is deployed to GitHub Pages and/or AWS S3 with CloudFront.

**Data flow:** GitHub API → `collect_metrics.py` → `dist/metrics.json` → `build_dashboard.py` → `dist/index.html` → deploy

## Tech Stack

- **Language:** Python 3.12
- **Dependencies:** requests, python-dateutil, jinja2
- **Infrastructure:** AWS CDK (`aws-cdk-lib ~2.208.0`, `cdk-nag`, `specter-static-site`)
- **Testing:** pytest
- **Linting:** ruff
- **CI/CD:** GitHub Actions
- **Frontend:** Single-file vanilla HTML/CSS/JS (no build tools)

## Project Structure

```
├── collect_metrics.py    # GitHub API metrics collector (main logic)
├── build_dashboard.py    # HTML dashboard generator
├── app.py                # AWS CDK infrastructure definition
├── requirements.txt      # Runtime dependencies
├── requirements-dev.txt  # Dev dependencies (includes ruff, pytest)
├── requirements-cdk.txt  # CDK/infrastructure dependencies
├── cdk.json              # CDK configuration
├── tests/
│   ├── conftest.py       # Path setup for imports
│   └── test_health_score.py  # Tests for health score calculation
├── examples/
│   └── index.html        # Example dashboard output
├── dist/                 # Build output (gitignored)
└── .github/
    └── workflows/
        ├── ci.yml        # CI pipeline (lint + test)
        └── dashboard.yml # Scheduled dashboard build & deploy
```

## Key Commands

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Lint / format
ruff check .
ruff format .

# Collect metrics (requires GITHUB_TOKEN env var)
python3 collect_metrics.py

# Build dashboard from collected metrics
python3 build_dashboard.py

# CDK deploy (requires AWS credentials + requirements-cdk.txt)
python3 app.py
```

## Health Score Algorithm

Located in `collect_metrics.py:compute_health_score()`. Base score of 100 with weighted deductions:

| Factor             | Points Each | Cap |
|--------------------|-------------|-----|
| Stale branches     | 5           | 20  |
| Open PRs           | 3           | 15  |
| No branch protection | 10       | 10  |
| No license         | 5           | 5   |
| No description     | 3           | 3   |
| Dependabot alerts  | 5           | 20  |
| Staleness level    | 0–10        | 10  |

## Code Conventions

- **Commits:** Follow [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `chore:`, `docs:`
- **Python style:** Use type hints (e.g., `dict | None`, `list[str]`). Follow ruff defaults.
- **PRs:** Small and focused. Fill out the PR template. Link related issues.
- **Tests:** Write tests for non-trivial changes. Use the `_base_repo()` factory pattern in test files.
- **No new files** unless necessary — prefer editing existing files.

## CI/CD

- **CI (`ci.yml`):** Runs on PRs and pushes to `main`. Uses shared workflow from `Specter099/.github` (Python linting + tests).
- **Dashboard (`dashboard.yml`):** Scheduled daily at 6am UTC + manual dispatch. Builds metrics, generates HTML, deploys to GitHub Pages and/or S3.

## Environment Variables

- `GITHUB_TOKEN` — Required for `collect_metrics.py` to access GitHub API
- `GITHUB_USERNAME` — GitHub user whose repos are monitored
- AWS credentials — Required for CDK deployment and S3 operations

## Important Notes

- `dist/` is gitignored — build outputs are not committed
- The frontend is a single self-contained HTML file with embedded CSS/JS
- The GitHub API collector handles pagination (100 items/page) and graceful error handling for 403/404 responses
- CODEOWNERS: `@Specter099` owns all files
