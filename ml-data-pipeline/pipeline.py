"""
ML Data Pipeline Framework - Modular ETL for ML training data.
"""
import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# --- Models ---
class StageResult(BaseModel):
    stage_name: str
    status: str = "success"
    rows_in: int = 0
    rows_out: int = 0
    duration_ms: float = 0
    errors: list[str] = []
    warnings: list[str] = []
    metadata: dict[str, Any] = {}


class PipelineRun(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    pipeline_name: str
    version: int = 1
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    status: str = "running"
    results: list[StageResult] = []
    data: Optional[Any] = None


# --- Stage Base ---
class Stage(ABC):
    """Base class for pipeline stages."""

    def __init__(self, config: dict):
        self.config = config
        self.name = config.get("name", self.__class__.__name__)

    @abstractmethod
    async def execute(self, data: Any) -> tuple[Any, StageResult]:
        ...


# --- Extract Stages ---
class CSVExtractStage(Stage):
    """Extract data from CSV files."""

    async def execute(self, data: Any) -> tuple[Any, StageResult]:
        start = time.time()
        try:
            import pandas as pd

            path = self.config.get("path", "")
            chunk_size = self.config.get("chunk_size")

            if chunk_size:
                dfs = []
                for chunk in pd.read_csv(path, chunksize=chunk_size):
                    dfs.append(chunk)
                df = pd.concat(dfs, ignore_index=True)
            else:
                df = pd.read_csv(path)

            result = StageResult(
                stage_name=self.name, rows_out=len(df), duration_ms=(time.time() - start) * 1000
            )
            return df, result
        except Exception as e:
            return data, StageResult(stage_name=self.name, status="error", errors=[str(e)])


class SQLExtractStage(Stage):
    """Extract data from SQL databases."""

    async def execute(self, data: Any) -> tuple[Any, StageResult]:
        start = time.time()
        try:
            import pandas as pd
            from sqlalchemy import create_engine

            source = self.config.get("source", "")
            query = self.config.get("query", "")
            engine = create_engine(source)
            df = pd.read_sql(query, engine)
            engine.dispose()

            return df, StageResult(
                stage_name=self.name, rows_out=len(df), duration_ms=(time.time() - start) * 1000
            )
        except ImportError:
            return data, StageResult(
                stage_name=self.name, status="error", errors=["sqlalchemy not installed"]
            )
        except Exception as e:
            return data, StageResult(stage_name=self.name, status="error", errors=[str(e)])


class JSONExtractStage(Stage):
    """Extract data from JSON files or APIs."""

    async def execute(self, data: Any) -> tuple[Any, StageResult]:
        start = time.time()
        try:
            import pandas as pd

            path = self.config.get("path", "")
            url = self.config.get("url", "")

            if url:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        raw = await resp.json()
            else:
                with open(path) as f:
                    raw = json.load(f)

            df = pd.json_normalize(raw) if isinstance(raw, list) else pd.DataFrame([raw])

            return df, StageResult(
                stage_name=self.name, rows_out=len(df), duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return data, StageResult(stage_name=self.name, status="error", errors=[str(e)])


# --- Transform Stage ---
class TransformStage(Stage):
    """Apply transformations and feature engineering."""

    async def execute(self, data: Any) -> tuple[Any, StageResult]:
        start = time.time()
        rows_in = len(data) if hasattr(data, "__len__") else 0
        errors = []

        try:
            import pandas as pd

            if not isinstance(data, pd.DataFrame):
                data = pd.DataFrame(data)

            for op in self.config.get("operations", []):
                op_type = list(op.keys())[0]
                op_config = op[op_type]

                try:
                    if op_type == "filter":
                        data = data.query(op_config["condition"])
                    elif op_type == "drop":
                        data = data.drop(columns=op_config.get("columns", []))
                    elif op_type == "rename":
                        data = data.rename(columns=op_config)
                    elif op_type == "fillna":
                        data = data.fillna(op_config.get("value", 0))
                    elif op_type == "dropna":
                        data = data.dropna(subset=op_config.get("columns", None))
                    elif op_type == "merge":
                        # Would merge with another dataset in production
                        pass
                    elif op_type == "feature":
                        data[op_config["name"]] = data.eval(op_config.get("expr", "0"))
                    elif op_type == "astype":
                        for col, dtype in op_config.items():
                            data[col] = data[col].astype(dtype)
                except Exception as e:
                    errors.append(f"{op_type}: {str(e)}")

            result = StageResult(
                stage_name=self.name,
                rows_in=rows_in,
                rows_out=len(data),
                duration_ms=(time.time() - start) * 1000,
                errors=errors,
            )
            return data, result
        except Exception as e:
            return data, StageResult(stage_name=self.name, status="error", errors=[str(e)])


# --- Validate Stage ---
class ValidateStage(Stage):
    """Validate data quality."""

    async def execute(self, data: Any) -> tuple[Any, StageResult]:
        start = time.time()
        rows_in = len(data) if hasattr(data, "__len__") else 0
        errors = []
        warnings = []

        try:
            import pandas as pd

            if not isinstance(data, pd.DataFrame):
                data = pd.DataFrame(data)

            checks = self.config.get("checks", [])

            for check in checks:
                check_type = list(check.keys())[0]
                check_config = check[check_type]

                if check_type == "no_nulls":
                    for col in check_config if isinstance(check_config, list) else [check_config]:
                        null_count = data[col].isnull().sum()
                        if null_count > 0:
                            warnings.append(f"{col}: {null_count} null values")

                elif check_type == "range":
                    for col, (lo, hi) in check_config.items():
                        out_of_range = ((data[col] < lo) | (data[col] > hi)).sum()
                        if out_of_range > 0:
                            warnings.append(f"{col}: {out_of_range} values outside [{lo}, {hi}]")

                elif check_type == "unique":
                    for col in check_config if isinstance(check_config, list) else [check_config]:
                        dupes = data[col].duplicated().sum()
                        if dupes > 0:
                            warnings.append(f"{col}: {dupes} duplicate values")

                elif check_type == "schema":
                    expected_cols = set(check_config) if isinstance(check_config, dict) else set(check_config)
                    missing = expected_cols - set(data.columns)
                    if missing:
                        errors.append(f"Missing columns: {missing}")

            status = "error" if errors else ("warning" if warnings else "success")
            result = StageResult(
                stage_name=self.name,
                rows_in=rows_in,
                rows_out=len(data),
                duration_ms=(time.time() - start) * 1000,
                errors=errors,
                warnings=warnings,
                status=status,
            )
            return data, result
        except Exception as e:
            return data, StageResult(stage_name=self.name, status="error", errors=[str(e)])


# --- Load Stage ---
class ParquetLoadStage(Stage):
    """Export data to Parquet format."""

    async def execute(self, data: Any) -> tuple[Any, StageResult]:
        start = time.time()
        try:
            import pandas as pd

            if not isinstance(data, pd.DataFrame):
                data = pd.DataFrame(data)

            path = self.config.get("path", "output/data.parquet")
            path = path.replace("{version}", str(1))
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            data.to_parquet(path, index=False)

            return data, StageResult(
                stage_name=self.name,
                rows_out=len(data),
                duration_ms=(time.time() - start) * 1000,
                metadata={"output_path": path},
            )
        except Exception as e:
            return data, StageResult(stage_name=self.name, status="error", errors=[str(e)])


class CSVLoadStage(Stage):
    """Export data to CSV format."""

    async def execute(self, data: Any) -> tuple[Any, StageResult]:
        start = time.time()
        try:
            import pandas as pd

            if not isinstance(data, pd.DataFrame):
                data = pd.DataFrame(data)

            path = self.config.get("path", "output/data.csv")
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            data.to_csv(path, index=False)

            return data, StageResult(
                stage_name=self.name,
                rows_out=len(data),
                duration_ms=(time.time() - start) * 1000,
                metadata={"output_path": path},
            )
        except Exception as e:
            return data, StageResult(stage_name=self.name, status="error", errors=[str(e)])


# --- Pipeline Engine ---
STAGE_REGISTRY = {
    "csv": CSVExtractStage,
    "sql": SQLExtractStage,
    "json": JSONExtractStage,
    "transform": TransformStage,
    "validate": ValidateStage,
    "parquet": ParquetLoadStage,
    "load_csv": CSVLoadStage,
}


class PipelineEngine:
    """Load and execute YAML-defined data pipelines."""

    def load(self, path: str) -> dict:
        with open(path) as f:
            return yaml.safe_load(f)

    async def run(self, config: dict) -> PipelineRun:
        run = PipelineRun(pipeline_name=config.get("name", "unnamed"))
        logger.info(f"Pipeline: {run.pipeline_name} (run: {run.run_id})")

        data = None
        for stage_config in config.get("stages", []):
            stage_type = stage_config.get("type", "")
            stage_cls = STAGE_REGISTRY.get(stage_type)

            if not stage_cls:
                result = StageResult(stage_name=stage_config.get("name", "?"), status="error",
                                     errors=[f"Unknown stage type: {stage_type}"])
                run.results.append(result)
                run.status = "failed"
                break

            logger.info(f"  Stage: {stage_config.get('name', stage_type)}")
            data, result = await stage_cls(stage_config).execute(data)
            run.results.append(result)

            if result.status == "error":
                logger.error(f"    Failed: {result.errors}")
                run.status = "failed"
                break
            elif result.warnings:
                for w in result.warnings:
                    logger.warning(f"    Warning: {w}")

        run.completed_at = datetime.now(timezone.utc).isoformat()
        if run.status == "running":
            run.status = "completed"
        logger.info(f"Pipeline finished: {run.status}")
        return run


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="ML Data Pipeline Framework")
    parser.add_argument("--config", required=True, help="Path to pipeline YAML config")
    parser.add_argument("--dry-run", action="store_true", help="Parse config without executing")
    args = parser.parse_args()

    engine = PipelineEngine()
    config = engine.load(args.config)

    if args.dry_run:
        print(f"Pipeline: {config.get('name')}")
        print(f"Stages: {len(config.get('stages', []))}")
        for s in config.get("stages", []):
            print(f"  - {s.get('name')} ({s.get('type')})")
        return

    run = await engine.run(config)
    print(f"\nRun {run.run_id}: {run.status}")
    for r in run.results:
        icon = {"success": "✅", "error": "❌", "warning": "⚠️"}.get(r.status, "❓")
        print(f"  {icon} {r.stage_name}: {r.rows_in}→{r.rows_out} rows ({r.duration_ms:.0f}ms)")


if __name__ == "__main__":
    asyncio.run(main())
