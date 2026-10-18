"""Experiment Service for DCN Error Detection System.

Thread-safe manager for benchmark experiments and analytical visualizations.
Uses safe staging to prevent concurrent collisions and allow user confirmation
before overwriting project baseline files.
"""

import os
import sys
import time
import shutil
import tempfile
import threading
from typing import Dict, Any, List, Optional
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.experiment_runner import run_all_experiments
from experiments.metrics import compute_and_save_metrics
from visualization.plot_results import generate_all_plots

EXPECTED_CHARTS = [
    "detection_rate_by_error_type.png",
    "detection_rate_vs_error_magnitude.png",
    "processing_time_vs_data_size.png",
    "overhead_vs_data_size.png"
]


class ExperimentService:
    """Manages benchmark experiment execution, staging, and baseline persistence."""

    def __init__(self, root_dir: str = PROJECT_ROOT):
        self.root_dir = root_dir
        self.lock = threading.Lock()
        self.is_running = False
        self.current_run_info: Optional[Dict[str, Any]] = None
        self.last_staged_run: Optional[Dict[str, Any]] = None

    def get_baseline_status(self) -> Dict[str, Any]:
        """Check status of project baseline CSV and graph files."""
        baseline_exp_csv = os.path.join(self.root_dir, "experiment_results.csv")
        baseline_metrics_csv = os.path.join(self.root_dir, "metrics_results.csv")
        baseline_viz_dir = os.path.join(self.root_dir, "visualization")

        has_exp_csv = os.path.exists(baseline_exp_csv) and os.path.getsize(baseline_exp_csv) > 0
        has_metrics_csv = os.path.exists(baseline_metrics_csv) and os.path.getsize(baseline_metrics_csv) > 0

        charts_status: Dict[str, bool] = {}
        for c in EXPECTED_CHARTS:
            c_path = os.path.join(baseline_viz_dir, c)
            charts_status[c] = os.path.exists(c_path) and os.path.getsize(c_path) > 0

        all_charts_exist = all(charts_status.values())
        baseline_ready = has_exp_csv and has_metrics_csv and all_charts_exist

        mtime = None
        if has_metrics_csv:
            mtime = time.ctime(os.path.getmtime(baseline_metrics_csv))

        return {
            "baseline_ready": baseline_ready,
            "has_experiment_csv": has_exp_csv,
            "has_metrics_csv": has_metrics_csv,
            "charts_status": charts_status,
            "all_charts_exist": all_charts_exist,
            "last_modified": mtime,
            "is_running": self.is_running
        }

    def run_benchmark(
        self,
        data_sizes: Optional[List[int]] = None,
        multi_error_amounts: Optional[List[int]] = None,
        burst_lengths: Optional[List[int]] = None,
        trials: int = 50
    ) -> Dict[str, Any]:
        """Execute benchmark experiments safely inside an isolated staging directory."""
        if not self.lock.acquire(blocking=False):
            return {
                "success": False,
                "error": "Another experiment run is currently in progress. Please wait for it to finish."
            }

        self.is_running = True
        run_id = f"run_{int(time.time())}"
        staging_dir = tempfile.mkdtemp(prefix=f"dcn_web_{run_id}_")

        staging_exp_csv = os.path.join(staging_dir, "experiment_results.csv")
        staging_metrics_csv = os.path.join(staging_dir, "metrics_results.csv")
        staging_viz_dir = os.path.join(staging_dir, "visualization")
        os.makedirs(staging_viz_dir, exist_ok=True)

        sizes = data_sizes if data_sizes else [32, 64, 128, 256, 512]
        mags = multi_error_amounts if multi_error_amounts else [1, 2, 3, 4, 5, 8]
        bursts = burst_lengths if burst_lengths else [2, 4, 8, 16]
        trials_count = max(1, trials)

        self.current_run_info = {
            "run_id": run_id,
            "start_time": time.time(),
            "status": "running",
            "staging_dir": staging_dir,
            "trials_count": trials_count,
            "data_sizes": sizes
        }

        try:
            t0 = time.time()
            # 1. Run experiments
            raw_results = run_all_experiments(
                data_sizes=sizes,
                multi_error_amounts=mags,
                burst_lengths=bursts,
                trials=trials_count,
                output_file=staging_exp_csv,
                verbose=False
            )

            # 2. Compute metrics
            compute_and_save_metrics(
                input_file=staging_exp_csv,
                output_file=staging_metrics_csv,
                verbose=False
            )

            # 3. Generate 4 analytical plots
            generated_plots = generate_all_plots(
                csv_path=staging_metrics_csv,
                output_dir=staging_viz_dir,
                verbose=False
            )

            elapsed = time.time() - t0

            # Validate outputs
            valid_exp = os.path.exists(staging_exp_csv) and os.path.getsize(staging_exp_csv) > 0
            valid_metrics = os.path.exists(staging_metrics_csv) and os.path.getsize(staging_metrics_csv) > 0
            valid_charts = all(
                os.path.exists(os.path.join(staging_viz_dir, c)) and os.path.getsize(os.path.join(staging_viz_dir, c)) > 0
                for c in EXPECTED_CHARTS
            )

            if not (valid_exp and valid_metrics and valid_charts):
                raise RuntimeError("One or more benchmark output files failed to generate.")

            # Automatically copy outputs to baseline so they are immediately available
            target_exp_csv = os.path.join(self.root_dir, "experiment_results.csv")
            target_metrics_csv = os.path.join(self.root_dir, "metrics_results.csv")
            target_viz_dir = os.path.join(self.root_dir, "visualization")
            os.makedirs(target_viz_dir, exist_ok=True)

            try:
                shutil.copy2(staging_exp_csv, target_exp_csv)
                shutil.copy2(staging_metrics_csv, target_metrics_csv)
                for c in EXPECTED_CHARTS:
                    src_chart = os.path.join(staging_viz_dir, c)
                    if os.path.exists(src_chart):
                        shutil.copy2(src_chart, os.path.join(target_viz_dir, c))
            except Exception as copy_err:
                print(f"[Warning] Failed to copy staged files to baseline: {copy_err}")

            run_result = {
                "success": True,
                "run_id": run_id,
                "staging_dir": staging_dir,
                "elapsed_seconds": round(elapsed, 2),
                "total_trials": len(raw_results),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "charts": EXPECTED_CHARTS,
                "is_staged": True
            }

            self.last_staged_run = run_result
            self.current_run_info = {
                **run_result,
                "status": "completed"
            }
            return run_result

        except Exception as e:
            shutil.rmtree(staging_dir, ignore_errors=True)
            err_res = {
                "success": False,
                "error": f"Experiment execution failed: {str(e)}",
                "status": "error"
            }
            self.current_run_info = err_res
            return err_res

        finally:
            self.is_running = False
            self.lock.release()

    def apply_staged_results(self) -> Dict[str, Any]:
        """Apply the last staged experiment run to project baseline."""
        if not self.last_staged_run or "staging_dir" not in self.last_staged_run:
            return {"success": False, "error": "No staged experiment results available to apply."}

        staging_dir = self.last_staged_run["staging_dir"]
        if not os.path.exists(staging_dir):
            return {"success": False, "error": "Staged results directory no longer exists."}

        try:
            staging_exp_csv = os.path.join(staging_dir, "experiment_results.csv")
            staging_metrics_csv = os.path.join(staging_dir, "metrics_results.csv")
            staging_viz_dir = os.path.join(staging_dir, "visualization")

            target_exp_csv = os.path.join(self.root_dir, "experiment_results.csv")
            target_metrics_csv = os.path.join(self.root_dir, "metrics_results.csv")
            target_viz_dir = os.path.join(self.root_dir, "visualization")
            os.makedirs(target_viz_dir, exist_ok=True)

            shutil.copy2(staging_exp_csv, target_exp_csv)
            shutil.copy2(staging_metrics_csv, target_metrics_csv)
            for c in EXPECTED_CHARTS:
                src_chart = os.path.join(staging_viz_dir, c)
                if os.path.exists(src_chart):
                    shutil.copy2(src_chart, os.path.join(target_viz_dir, c))

            # Clean up staging directory
            shutil.rmtree(staging_dir, ignore_errors=True)
            applied_run_id = self.last_staged_run.get("run_id")
            self.last_staged_run = None

            return {
                "success": True,
                "message": "Experiment results and analytical graphs applied to project baseline.",
                "run_id": applied_run_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to apply results to baseline: {str(e)}"
            }

    def discard_staged_results(self) -> Dict[str, Any]:
        """Discard the staged experiment run without modifying project baseline."""
        if not self.last_staged_run or "staging_dir" not in self.last_staged_run:
            return {"success": True, "message": "No staged results to discard."}

        staging_dir = self.last_staged_run.get("staging_dir")
        if staging_dir and os.path.exists(staging_dir):
            shutil.rmtree(staging_dir, ignore_errors=True)

        discarded_id = self.last_staged_run.get("run_id")
        self.last_staged_run = None
        return {
            "success": True,
            "message": "Staged results discarded. Previous baseline preserved.",
            "run_id": discarded_id
        }

    def get_metrics_table(self, source: str = "baseline") -> Dict[str, Any]:
        """Read metrics CSV and return summarized table data."""
        csv_path = None
        if source == "staged" and self.last_staged_run:
            staging_dir = self.last_staged_run.get("staging_dir")
            if staging_dir:
                candidate = os.path.join(staging_dir, "metrics_results.csv")
                if os.path.exists(candidate):
                    csv_path = candidate

        if not csv_path:
            candidate = os.path.join(self.root_dir, "metrics_results.csv")
            if os.path.exists(candidate):
                csv_path = candidate

        if not csv_path or not os.path.exists(csv_path):
            return {
                "success": False,
                "error": "Metrics dataset not found. Please run experiments first."
            }

        try:
            df = pd.read_csv(csv_path)
            # Pick key columns for UI display
            cols = [
                "technique", "error_type", "data_size", "error_amount",
                "trials", "detection_rate", "average_processing_time", "average_overhead_percentage"
            ]
            available_cols = [c for c in cols if c in df.columns]
            sample_df = df[available_cols].copy()

            # Format values cleanly
            records = sample_df.to_dict(orient="records")
            for r in records:
                if "average_processing_time" in r and r["average_processing_time"] is not None:
                    # Convert to microseconds
                    r["latency_us"] = round(r["average_processing_time"] * 1e6, 2)
                if "detection_rate" in r and r["detection_rate"] is not None:
                    r["detection_rate"] = round(r["detection_rate"], 1)
                if "average_overhead_percentage" in r and r["average_overhead_percentage"] is not None:
                    r["overhead_pct"] = round(r["average_overhead_percentage"], 1)

            return {
                "success": True,
                "records": records,
                "total_rows": len(records),
                "source": "staged" if (csv_path and "staging" in csv_path) else "baseline"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse metrics: {str(e)}"
            }

    def get_graph_file_path(self, filename: str, source: str = "auto") -> Optional[str]:
        """Locate full absolute path for a requested graph image."""
        if filename not in EXPECTED_CHARTS:
            return None

        # Check staged run first if requested or auto
        if source in ("staged", "auto") and self.last_staged_run:
            staging_dir = self.last_staged_run.get("staging_dir")
            if staging_dir:
                staged_path = os.path.join(staging_dir, "visualization", filename)
                if os.path.exists(staged_path) and os.path.getsize(staged_path) > 0:
                    return staged_path

        # Check baseline visualization dir
        baseline_path = os.path.join(self.root_dir, "visualization", filename)
        if os.path.exists(baseline_path) and os.path.getsize(baseline_path) > 0:
            return baseline_path

        return None


# Global service instance
experiment_service = ExperimentService()
