"""Entrypoint: Run dataset audits and export audit report."""

from pathlib import Path
from utils.logging_utils import setup_logger, save_report
from ingestion.loader import DataLoader
from audit.auditor import DataAudit
from utils.constants import DATASETS, OUTPUT_DATASETS, LOGS_DIR

logger = setup_logger("pipeline", "pipeline.log")


def main():
    logger.info("Starting audit run...")
    loader = DataLoader(DATASETS)
    data = loader.load_all()

    auditor = DataAudit()
    auditor.audit_all(data)
    report_path = OUTPUT_DATASETS.get("audit_report", LOGS_DIR / "audit_report.json")
    auditor.export_report(report_path)

    logger.info("Audit run completed")


if __name__ == "__main__":
    main()
