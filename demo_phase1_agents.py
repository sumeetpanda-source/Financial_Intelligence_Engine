"""
Run the Phase 1 multi-agent financial intelligence demo.
"""

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path

from agents import OrchestratorAgent


def _json_default(value):
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def main():
    query = "Should I invest in AAPL, MSFT, and NVDA for the next 30 days?"
    project_root = Path(__file__).resolve().parent

    orchestrator = OrchestratorAgent(project_root=project_root)
    result = orchestrator.run(query=query, tickers=["AAPL", "MSFT", "NVDA"])

    reports_dir = project_root / "reports"
    data_dir = project_root / "data"
    reports_dir.mkdir(exist_ok=True)
    data_dir.mkdir(exist_ok=True)

    report_path = reports_dir / "phase1_agent_report.md"
    json_path = data_dir / "phase1_agent_result.json"

    report_path.write_text(result["final_report"], encoding="utf-8")
    json_path.write_text(json.dumps(result, default=_json_default, indent=2), encoding="utf-8")

    print("\nPhase 1 multi-agent demo completed.")
    print(f"Report: {report_path}")
    print(f"JSON:   {json_path}")
    print("\n" + result["final_report"][:1200] + "\n")


if __name__ == "__main__":
    main()
