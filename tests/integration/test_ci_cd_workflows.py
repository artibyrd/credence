"""Unit and shift-left contract tests for GitHub CI/CD workflows, WIF secrets, and least-privileged IAM roles."""

from pathlib import Path

import pytest
import yaml

WORKFLOWS_DIR = Path(__file__).resolve().parents[2] / ".github" / "workflows"
DOCS_DIR = Path(__file__).resolve().parents[2].parent / "credence-docs" / "docs"
SKILLS_DIR = Path(__file__).resolve().parents[2].parent / "credence-agent" / ".agents" / "skills"


@pytest.mark.integration
def test_github_workflows_syntax_and_structure() -> None:
    """Verify all GitHub Actions workflow YAML files are structurally valid and contain required safety controls."""
    assert WORKFLOWS_DIR.exists(), f"Workflows directory not found: {WORKFLOWS_DIR}"
    workflow_files = list(WORKFLOWS_DIR.glob("*.yml"))
    assert len(workflow_files) >= 5, f"Expected at least 5 workflow files, found {len(workflow_files)}"

    for wf_path in workflow_files:
        content = wf_path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict), f"Workflow {wf_path.name} must parse into a dictionary"
        assert "name" in parsed, f"Workflow {wf_path.name} missing 'name'"
        assert "jobs" in parsed, f"Workflow {wf_path.name} missing 'jobs'"

        # Verify concurrency safety and id-token permissions on GCP deploy workflows
        if "deploy" in wf_path.name:
            assert "concurrency" in parsed, f"Deploy workflow {wf_path.name} must define concurrency"
            concurrency = parsed["concurrency"]
            assert concurrency.get("cancel-in-progress") is True, f"{wf_path.name} must have cancel-in-progress: true"
            if "backend" in wf_path.name or "dev" in wf_path.name:
                for job_name, job_spec in parsed["jobs"].items():
                    permissions = job_spec.get("permissions", {})
                    assert permissions.get("id-token") == "write", (
                        f"Job '{job_name}' in {wf_path.name} must declare id-token: write for WIF OIDC authentication"
                    )

        # Verify job timeouts
        for job_name, job_spec in parsed["jobs"].items():
            assert "timeout-minutes" in job_spec, f"Job '{job_name}' in {wf_path.name} must declare timeout-minutes"
            assert job_spec["timeout-minutes"] <= 15, f"Job '{job_name}' timeout too high (>15m)"


@pytest.mark.integration
def test_wif_secret_fallback_contracts() -> None:
    """Verify deploy workflows correctly implement dual-environment WIF secret fallbacks and project IDs."""
    dev_wf = WORKFLOWS_DIR / "deploy-dev.yml"
    backend_wf = WORKFLOWS_DIR / "deploy-backend.yml"

    assert dev_wf.exists()
    assert backend_wf.exists()

    dev_content = dev_wf.read_text(encoding="utf-8")
    backend_content = backend_wf.read_text(encoding="utf-8")

    # Dev workflow contract
    assert "credence-dev-495173" in dev_content, "deploy-dev.yml must default to credence-dev-495173"
    assert "secrets.GCP_DEV_WORKLOAD_IDENTITY_PROVIDER || secrets.GCP_WORKLOAD_IDENTITY_PROVIDER" in dev_content
    assert "secrets.GCP_DEV_SERVICE_ACCOUNT || secrets.GCP_SERVICE_ACCOUNT" in dev_content
    assert "secrets.GCP_DEV_PROJECT_ID || inputs.project_id || 'credence-dev-495173'" in dev_content

    # Prod/Backend workflow contract
    assert "credence-prod-505902" in backend_content, "deploy-backend.yml must default to credence-prod-505902"
    assert "secrets.GCP_WORKLOAD_IDENTITY_PROVIDER" in backend_content
    assert "secrets.GCP_SERVICE_ACCOUNT" in backend_content
    assert "secrets.GCP_PROJECT_ID || inputs.project_id || 'credence-prod-505902'" in backend_content


@pytest.mark.integration
def test_least_privileged_iam_role_canon() -> None:
    """Verify documentation and skills prescribe strictly least-privileged IAM roles for CI/CD."""
    deploy_doc = DOCS_DIR / "deployment-cloudrun.md"
    skill_doc = SKILLS_DIR / "cloudrun-ops" / "SKILL.md"

    for doc_path in [deploy_doc, skill_doc]:
        if doc_path.exists():
            content = doc_path.read_text(encoding="utf-8")
            # Must prescribe least-privileged developer/builder roles
            assert "roles/run.developer" in content, f"{doc_path.name} must prescribe roles/run.developer"
            assert "roles/cloudbuild.builds.builder" in content, (
                f"{doc_path.name} must prescribe roles/cloudbuild.builds.builder"
            )
            assert "roles/iam.workloadIdentityUser" in content, (
                f"{doc_path.name} must prescribe roles/iam.workloadIdentityUser"
            )


@pytest.mark.integration
def test_gcp_project_id_matrix() -> None:
    """Verify GCP project IDs are standardized across Terraform and workflow definitions."""
    tf_dir = Path(__file__).resolve().parents[2] / "terraform"
    if tf_dir.exists():
        dev_vars = tf_dir / "terraform.dev.tfvars"
        prod_vars = tf_dir / "terraform.prod.tfvars"
        if dev_vars.exists():
            dev_content = dev_vars.read_text(encoding="utf-8")
            assert "credence-dev-495173" in dev_content
        if prod_vars.exists():
            prod_content = prod_vars.read_text(encoding="utf-8")
            assert "credence-prod-505902" in prod_content
