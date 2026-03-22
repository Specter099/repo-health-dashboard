from collect_metrics import compute_health_score


def _base_repo(**overrides):
    defaults = {
        "stale_branch_count": 0,
        "open_pr_count": 0,
        "branch_protection": True,
        "has_license": True,
        "has_description": True,
        "dependabot_alerts": 0,
        "staleness": "fresh",
    }
    defaults.update(overrides)
    return defaults


def test_perfect_score():
    assert compute_health_score(_base_repo()) == 100


def test_no_branch_protection():
    assert compute_health_score(_base_repo(branch_protection=False)) == 90


def test_stale_branches_capped():
    # 10 stale branches * 5 = 50, but capped at 20
    assert compute_health_score(_base_repo(stale_branch_count=10)) == 80


def test_multiple_deductions():
    repo = _base_repo(
        branch_protection=False,
        has_license=False,
        has_description=False,
        open_pr_count=3,
    )
    # -10 (protection) -5 (license) -3 (description) -9 (3 PRs * 3)
    assert compute_health_score(repo) == 73
