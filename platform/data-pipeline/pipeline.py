#!/usr/bin/env python3
"""
Main orchestration pipeline for Phase 1: Data Engineering & Football Intelligence.

This pipeline:
1. Audits all datasets
2. Cleans and normalizes data
3. Engineers features for players and countries
4. Aggregates squad metrics
5. Exports processed datasets to CSV and SQLite
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.constants import DATASETS, OUTPUT_DATASETS, DATABASE_PATH, LOGS_DIR, RECENCY_WEIGHTS
from utils.logging_utils import setup_logger, save_report
from ingestion.loader import DataLoader
from audit.auditor import DataAudit
from cleaning.cleaner import DataCleaner
from feature_engineering.player_features import PlayerFeatureEngineering
from feature_engineering.country_features import CountryFeatureEngineering
from exports.database import FootballIntelligenceDB
from exports.exporter import DataExporter

# Setup logging
logger = setup_logger(__name__, "pipeline.log")


class Phase1Pipeline:
    """Main Phase 1 data engineering pipeline."""
    
    def __init__(self):
        self.data_loader = DataLoader(DATASETS)
        self.audit = DataAudit()
        self.db = FootballIntelligenceDB(DATABASE_PATH)
        self.start_time = None
        self.pipeline_log = {
            "timestamp": datetime.now().isoformat(),
            "steps": {},
        }
    
    def run(self) -> bool:
        """Run the complete pipeline."""
        self.start_time = time.time()
        logger.info("="*80)
        logger.info("PHASE 1: DATA ENGINEERING & FOOTBALL INTELLIGENCE PIPELINE")
        logger.info("="*80)
        
        try:
            # Step 1: Load datasets
            if not self._step_load_data():
                return False
            
            # Step 2: Audit datasets
            if not self._step_audit():
                return False
            
            # Step 3: Clean data
            if not self._step_clean():
                return False
            
            # Step 4: Engineer features
            if not self._step_engineer_features():
                return False
            
            # Step 5: Create master datasets
            if not self._step_create_master():
                return False
            
            # Step 6: Export datasets
            if not self._step_export():
                return False
            
            # Step 7: Store in database
            if not self._step_database():
                return False
            
            logger.info("="*80)
            total_time = time.time() - self.start_time
            logger.info(f"✓ PIPELINE COMPLETED SUCCESSFULLY in {total_time:.2f} seconds")
            logger.info("="*80)
            
            self._save_pipeline_log()
            return True
            
        except Exception as e:
            logger.error(f"Pipeline failed with error: {e}", exc_info=True)
            self.db.close()
            return False
    
    def _step_load_data(self) -> bool:
        """Step 1: Load all datasets."""
        step_name = "Load Datasets"
        logger.info(f"\n[STEP 1] {step_name}")
        start = time.time()
        
        try:
            self.data_loader.load_all()
            duration = time.time() - start
            self.pipeline_log["steps"][step_name] = {
                "status": "success",
                "duration": duration,
            }
            logger.info(f"✓ Loaded {len(self.data_loader.data)} datasets in {duration:.2f}s")
            return True
        except Exception as e:
            logger.error(f"Failed to load datasets: {e}")
            self.pipeline_log["steps"][step_name] = {"status": "failed", "error": str(e)}
            return False
    
    def _step_audit(self) -> bool:
        """Step 2: Audit datasets."""
        step_name = "Dataset Audit"
        logger.info(f"\n[STEP 2] {step_name}")
        start = time.time()
        
        try:
            self.audit.audit_all(self.data_loader.data)
            report_path = OUTPUT_DATASETS["audit_report"]
            self.audit.export_report(report_path)
            
            duration = time.time() - start
            self.pipeline_log["steps"][step_name] = {
                "status": "success",
                "duration": duration,
                "datasets_audited": len(self.audit.results),
            }
            logger.info(f"✓ Audited {len(self.audit.results)} datasets in {duration:.2f}s")
            return True
        except Exception as e:
            logger.error(f"Audit failed: {e}")
            self.pipeline_log["steps"][step_name] = {"status": "failed", "error": str(e)}
            return False
    
    def _step_clean(self) -> bool:
        """Step 3: Clean data."""
        step_name = "Data Cleaning"
        logger.info(f"\n[STEP 3] {step_name}")
        start = time.time()
        
        try:
            cleaner = DataCleaner()
            
            # Clean datasets
            self.cleaned_data = {
                "players": cleaner.clean_players(self.data_loader.get("players")),
                "valuations": cleaner.clean_valuations(self.data_loader.get("player_valuations")),
                "appearances": cleaner.clean_appearances(self.data_loader.get("appearances")),
                "games": cleaner.clean_games(self.data_loader.get("games")),
                "results": cleaner.clean_results(self.data_loader.get("results")),
                "clubs": cleaner.clean_clubs(self.data_loader.get("clubs")),
            }
            
            duration = time.time() - start
            self.pipeline_log["steps"][step_name] = {
                "status": "success",
                "duration": duration,
                "datasets_cleaned": len(self.cleaned_data),
            }
            logger.info(f"✓ Cleaned data in {duration:.2f}s")
            return True
        except Exception as e:
            logger.error(f"Cleaning failed: {e}")
            self.pipeline_log["steps"][step_name] = {"status": "failed", "error": str(e)}
            return False
    
    def _step_engineer_features(self) -> bool:
        """Step 4: Engineer features."""
        step_name = "Feature Engineering"
        logger.info(f"\n[STEP 4] {step_name}")
        start = time.time()
        
        try:
            # Player features
            pfe = PlayerFeatureEngineering()
            
            self.per_90_stats = pfe.calculate_per_90_stats(
                self.cleaned_data["appearances"],
                self.cleaned_data["players"]
            )
            
            self.consistency_scores = pfe.calculate_consistency_score(
                self.cleaned_data["appearances"]
            )
            
            self.recent_form = pfe.calculate_recent_form(
                self.cleaned_data["appearances"]
            )
            
            self.form_scores = pfe.calculate_form_score_with_recency(
                self.recent_form,
                self.consistency_scores
            )
            
            # Country features
            cfe = CountryFeatureEngineering()
            
            self.country_stats = cfe.calculate_country_stats(
                self.cleaned_data["results"]
            )
            
            self.country_recent_form = cfe.calculate_recent_form_country(
                self.cleaned_data["results"]
            )
            
            duration = time.time() - start
            self.pipeline_log["steps"][step_name] = {
                "status": "success",
                "duration": duration,
                "features_engineered": 10,
            }
            logger.info(f"✓ Engineered features in {duration:.2f}s")
            return True
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            self.pipeline_log["steps"][step_name] = {"status": "failed", "error": str(e)}
            return False
    
    def _step_create_master(self) -> bool:
        """Step 5: Create master datasets."""
        step_name = "Create Master Datasets"
        logger.info(f"\n[STEP 5] {step_name}")
        start = time.time()
        
        try:
            pfe = PlayerFeatureEngineering()
            cfe = CountryFeatureEngineering()
            
            # Master players
            self.master_players = pfe.create_master_players(
                self.cleaned_data["players"],
                self.cleaned_data["valuations"],
                self.cleaned_data["appearances"],
                self.form_scores,
                self.consistency_scores,
            )
            
            # Master countries
            self.master_countries = cfe.create_master_countries(
                self.country_stats,
                self.country_recent_form,
                self.data_loader.get("national_teams"),
            )
            
            # Squad aggregates
            self.squad_aggregates = cfe.calculate_squad_aggregates(
                self.master_players
            )
            
            duration = time.time() - start
            self.pipeline_log["steps"][step_name] = {
                "status": "success",
                "duration": duration,
                "master_players": len(self.master_players),
                "master_countries": len(self.master_countries),
                "squad_aggregates": len(self.squad_aggregates),
            }
            logger.info(f"✓ Created master datasets in {duration:.2f}s")
            return True
        except Exception as e:
            logger.error(f"Master dataset creation failed: {e}")
            self.pipeline_log["steps"][step_name] = {"status": "failed", "error": str(e)}
            return False
    
    def _step_export(self) -> bool:
        """Step 6: Export datasets."""
        step_name = "Export Datasets"
        logger.info(f"\n[STEP 6] {step_name}")
        start = time.time()
        
        try:
            exporter = DataExporter()
            
            results = exporter.export_all_datasets(
                self.master_players,
                self.master_countries,
                self.per_90_stats,  # player_form
                self.country_stats,  # country_strength
                self.squad_aggregates,
            )
            
            duration = time.time() - start
            self.pipeline_log["steps"][step_name] = {
                "status": "success",
                "duration": duration,
                "datasets_exported": sum(results.values()),
            }
            logger.info(f"✓ Exported datasets in {duration:.2f}s")
            return True
        except Exception as e:
            logger.error(f"Export failed: {e}")
            self.pipeline_log["steps"][step_name] = {"status": "failed", "error": str(e)}
            return False
    
    def _step_database(self) -> bool:
        """Step 7: Store in database."""
        step_name = "Database Integration"
        logger.info(f"\n[STEP 7] {step_name}")
        start = time.time()
        
        try:
            # Create tables
            self.db.create_tables()
            
            # Insert data
            players_count = self.db.insert_players(self.master_players)
            countries_count = self.db.insert_countries(self.master_countries)
            squads_count = self.db.insert_squad_aggregates(self.squad_aggregates)
            
            self.db.connection.commit()
            
            duration = time.time() - start
            self.pipeline_log["steps"][step_name] = {
                "status": "success",
                "duration": duration,
                "players_inserted": players_count,
                "countries_inserted": countries_count,
                "squads_inserted": squads_count,
            }
            logger.info(f"✓ Database integration completed in {duration:.2f}s")
            return True
        except Exception as e:
            logger.error(f"Database integration failed: {e}")
            self.pipeline_log["steps"][step_name] = {"status": "failed", "error": str(e)}
            return False
        finally:
            self.db.close()
    
    def _save_pipeline_log(self) -> None:
        """Save complete pipeline execution log."""
        try:
            log_path = LOGS_DIR / "pipeline_execution.json"
            self.pipeline_log["total_duration"] = time.time() - self.start_time
            save_report(self.pipeline_log, log_path)
            logger.info(f"✓ Saved pipeline log to {log_path}")
        except Exception as e:
            logger.error(f"Failed to save pipeline log: {e}")


def main():
    """Main entry point."""
    pipeline = Phase1Pipeline()
    success = pipeline.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
