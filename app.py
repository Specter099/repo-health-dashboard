#!/usr/bin/env python3
from pathlib import Path

import aws_cdk as cdk
from specter_static_site import StaticSiteStack

app = cdk.App()

dist_path = str(Path(__file__).parent / "dist")

StaticSiteStack(
    app,
    "RepoHealthDashboard",
    domain_name="github-health.thelauerfam.com",
    dist_path=dist_path,
    hosted_zone_id="Z03182223J9MCRROVG2FB",
    dashboard_name="repo-health",
    deploy_role_arns=["arn:aws:iam::451645558365:role/github-actions-role"],
    env=cdk.Environment(
        account="451645558365",
        region="us-east-1",
    ),
)

app.synth()
