#!/usr/bin/env python3
from pathlib import Path

import aws_cdk as cdk
import boto3
from specter_static_site import StaticSiteStack

ssm = boto3.client("ssm", region_name="us-east-1")


def _ssm_param(name: str, decrypt: bool = False) -> str:
    return ssm.get_parameter(Name=name, WithDecryption=decrypt)["Parameter"]["Value"]


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
    cognito_user_pool_id="us-east-1_RW1qVorak",
    cognito_client_id=_ssm_param("/github-health-dashboard/cognito-client-id"),
    cognito_client_secret=_ssm_param(
        "/github-health-dashboard/cognito-client-secret", decrypt=True
    ),
    cognito_domain="thelauerfam.auth.us-east-1.amazoncognito.com",
    skip_deployment=True,
    env=cdk.Environment(
        account="451645558365",
        region="us-east-1",
    ),
)

app.synth()
