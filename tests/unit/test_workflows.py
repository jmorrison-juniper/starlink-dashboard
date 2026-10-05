"""Keep the CodeQL workflow and the misthelper-devtools pins of each workflow correct.

A future edit can remove a workflow value with no failed run, for example the
cancel guard for main or the config-file input. These tests read the workflow
files as text, because the test environment has no YAML package.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # The repository root, two levels above this file.
WORKFLOWS = ROOT / ".github" / "workflows"  # The folder of the GitHub Actions workflows.
CODEQL_WORKFLOW = WORKFLOWS / "codeql.yml"  # Code scanning keys the alerts on this path.
CODEQL_CONFIG = ROOT / ".github" / "codeql" / "codeql-config.yml"  # The config that the scan reads.
DEVTOOLS_COMMIT = "da02d4c6a2163d1882f2ad25fce80b8ba38304d1"  # The commit of misthelper-devtools v0.6.2.
DEVTOOLS_USES = re.compile(  # Matches each call to a shared misthelper-devtools workflow.
    r"uses: jmorrison-juniper/misthelper-devtools/\.github/workflows/(?P<name>[\w-]+\.yml)"
    r"@(?P<commit>[0-9a-f]+)(?P<comment>.*)$",
    re.MULTILINE,
)


def _devtools_pins() -> list[tuple[str, str, str, str]]:
    """Return the file, the shared workflow, the commit, and the comment of each devtools pin."""
    pins = []  # Collects one tuple for each pin in each workflow file.
    for workflow in sorted(WORKFLOWS.glob("*.yml")):  # Sorted so a failure message is stable.
        for match in DEVTOOLS_USES.finditer(workflow.read_text()):  # Each shared workflow call.
            pins.append((workflow.name, match["name"], match["commit"], match["comment"].strip()))  # Keep the values.
    return pins  # The caller checks each pin.


def test_each_devtools_pin_names_release_0_6_2() -> None:
    """Each workflow pins the same misthelper-devtools commit, so the shared jobs match one release."""
    pins = _devtools_pins()  # Read the pins from the workflow files.
    assert len(pins) == 4, pins  # ci, codeql, ste-lint, and the stranded branch report.
    for workflow, shared, commit, comment in pins:  # Check each pin on its own for a clear message.
        assert commit == DEVTOOLS_COMMIT, f"{workflow} pins {shared} at {commit}"  # The full SHA of v0.6.2.
        assert comment == "# v0.6.2", f"{workflow} names {comment!r}"  # Dependabot moves the comment with the pin.


def test_codeql_workflow_calls_the_shared_analysis_for_python() -> None:
    """The CodeQL caller uses the shared workflow with the Python language and the config file."""
    text = CODEQL_WORKFLOW.read_text()  # The caller workflow under test.
    assert "/reusable-codeql.yml@" in text  # The shared CodeQL workflow does the analysis.
    assert "\n  codeql:\n" in text  # The job ID gives the check name "codeql / Analyze (python)".
    assert "languages: '[\"python\"]'" in text  # The repository holds Python code only.
    assert "config-file: ./.github/codeql/codeql-config.yml" in text  # The scan reads the config of this repository.
    assert CODEQL_CONFIG.is_file()  # A missing config file fails the CodeQL init step.
    assert "  - starlink-api-reference\n" in CODEQL_CONFIG.read_text()  # The scan skips the SpaceX submodule.


def test_codeql_workflow_triggers_and_permissions() -> None:
    """The CodeQL caller runs on each event that the issue names and has the least permissions."""
    text = CODEQL_WORKFLOW.read_text()  # The caller workflow under test.
    triggers = text.split("\nconcurrency:", 1)[0]  # The on block comes before the concurrency block.
    assert re.search(r"^  pull_request:\s*$", triggers, re.MULTILINE)  # No branch filter, so each pull request scans.
    assert re.search(r"^  push:\n    branches: \[main\]$", triggers, re.MULTILINE)  # One event starts one run.
    assert re.search(r"^  schedule:\n(?:    #.*\n)*    - cron: ", triggers, re.MULTILINE)  # A weekly scan.
    assert re.search(r"^  workflow_dispatch:\s*$", triggers, re.MULTILINE)  # A manual scan.
    assert re.search(r"^permissions: \{\}$", text, re.MULTILINE)  # The top level removes each permission.
    for scope in ("actions: read", "contents: read", "security-events: write"):  # The scopes of the job.
        assert f"      {scope}\n" in text, scope  # The job grants each scope that the upload needs.


def test_codeql_workflow_never_cancels_a_main_run() -> None:
    """A new commit cancels a pull request run, but a run on main always finishes."""
    text = CODEQL_WORKFLOW.read_text()  # The caller workflow under test.
    assert "group: ${{ github.workflow }}-${{ github.head_ref || github.ref }}" in text  # One group per branch.
    assert "cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}" in text  # The guard for main.
