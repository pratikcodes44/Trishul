import subprocess
import sys


def test_main_help_runs_and_mode_flag_absent():
    result = subprocess.run(
        [sys.executable, "main.py", "--help"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0
    assert "Project Trishul" in result.stdout
    assert "--mode" not in result.stdout
