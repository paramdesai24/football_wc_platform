"""
Data audit system for quality inspection.
"""

import pandas as pd
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class DataAudit:
    """Comprehensive data auditing system."""
    
    def __init__(self):
        self.results = {}
    
    def audit_dataset(self, df: pd.DataFrame, name: str) -> Dict[str, Any]:
        """Audit a single dataset."""
        if df is None or len(df) == 0:
            logger.warning(f"Empty or None dataset: {name}")
            return {}
        
        audit = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "rows": len(df),
            "columns": len(df.columns),
            "memory_mb": df.memory_usage(deep=True).sum() / 1024**2,
            "schema": {},
            "missing_values": {},
            "duplicates": {},
            "statistics": {},
            "issues": [],
        }
        
        # Schema analysis
        for col in df.columns:
            audit["schema"][col] = {
                "dtype": str(df[col].dtype),
                "non_null_count": int(df[col].notna().sum()),
                "null_count": int(df[col].isna().sum()),
                "null_percent": float(df[col].isna().sum() / len(df) * 100),
                "unique_values": int(df[col].nunique()),
            }
        
        # Missing values analysis
        missing = df.isnull().sum()
        audit["missing_values"] = {
            col: {
                "count": int(missing[col]),
                "percent": float(missing[col] / len(df) * 100) if len(df) > 0 else 0,
            }
            for col in missing[missing > 0].index
        }
        
        # Duplicates analysis
        dup_rows = df.duplicated().sum()
        audit["duplicates"] = {
            "total_duplicate_rows": int(dup_rows),
            "percent": float(dup_rows / len(df) * 100) if len(df) > 0 else 0,
        }
        
        # Column-level statistics
        for col in df.select_dtypes(include=["number"]).columns:
            audit["statistics"][col] = {
                "min": float(df[col].min()) if not df[col].isna().all() else None,
                "max": float(df[col].max()) if not df[col].isna().all() else None,
                "mean": float(df[col].mean()) if not df[col].isna().all() else None,
                "median": float(df[col].median()) if not df[col].isna().all() else None,
                "std": float(df[col].std()) if not df[col].isna().all() else None,
            }
        
        # Issue detection
        if audit["missing_values"]:
            audit["issues"].append("Contains missing values")
        if audit["duplicates"]["total_duplicate_rows"] > 0:
            audit["issues"].append(f"Contains {dup_rows} duplicate rows")
        
        self.results[name] = audit
        logger.info(f"✓ Audited {name}: {len(df)} rows, {len(df.columns)} columns")
        
        return audit
    
    def audit_all(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Audit multiple datasets."""
        for name, df in datasets.items():
            if df is not None:
                self.audit_dataset(df, name)
        return self.results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate summary audit report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_datasets": len(self.results),
            "datasets": self.results,
            "summary": {
                "total_rows": sum(d.get("rows", 0) for d in self.results.values()),
                "total_memory_mb": sum(d.get("memory_mb", 0) for d in self.results.values()),
                "datasets_with_issues": sum(
                    1 for d in self.results.values() if d.get("issues")
                ),
                "critical_issues": [],
            },
        }
        
        # Find critical issues
        for name, audit in self.results.items():
            if audit.get("missing_values"):
                high_missing = {
                    col: info["percent"]
                    for col, info in audit["missing_values"].items()
                    if info["percent"] > 50
                }
                if high_missing:
                    report["summary"]["critical_issues"].append(
                        f"{name}: High missing values ({high_missing})"
                    )
        
        logger.info(f"✓ Generated audit report for {len(self.results)} datasets")
        return report
    
    def export_report(self, output_path: Path) -> bool:
        """Export audit report to JSON."""
        import json
        try:
            report = self.generate_report()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"✓ Exported audit report to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export audit report: {e}")
            return False
