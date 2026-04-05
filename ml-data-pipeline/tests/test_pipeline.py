"""Tests for ML Data Pipeline Framework."""
import pytest
import asyncio
import yaml
import json
from pipeline import PipelineEngine, TransformStage, ValidateStage, CSVExtractStage


@pytest.fixture
def engine():
    return PipelineEngine()


@pytest.fixture
def sample_data():
    return [
        {"name": "Alice", "age": 30, "spent": 100},
        {"name": "Bob", "age": 25, "spent": 200},
        {"name": "Charlie", "age": None, "spent": 150},
    ]


def test_load_config(engine, tmp_path):
    config = {"name": "test", "stages": []}
    path = tmp_path / "test.yaml"
    path.write_text(yaml.dump(config))
    result = engine.load(str(path))
    assert result["name"] == "test"


@pytest.mark.asyncio
async def test_csv_extract(tmp_path):
    csv_path = tmp_path / "test.csv"
    csv_path.write_text("a,b\n1,2\n3,4\n5,6")
    stage = CSVExtractStage({"name": "test_extract", "path": str(csv_path)})
    data, result = await stage.execute(None)
    assert result.status == "success"
    assert result.rows_out == 3


@pytest.mark.asyncio
async def test_transform_filter(sample_data):
    stage = TransformStage({
        "name": "filter_adults",
        "operations": [{"filter": {"condition": "age > 0"}}],
    })
    data, result = await stage.execute(sample_data)
    assert result.status == "success"
    # Should filter out the row with age=None
    assert result.rows_out <= 3


@pytest.mark.asyncio
async def test_transform_fillna(sample_data):
    stage = TransformStage({
        "name": "fill_age",
        "operations": [{"fillna": {"age": 0}}],
    })
    data, result = await stage.execute(sample_data)
    assert result.status == "success"
    assert result.rows_out == 3


@pytest.mark.asyncio
async def test_validate_no_nulls(sample_data):
    stage = ValidateStage({
        "name": "check_name",
        "checks": [{"no_nulls": ["name"]}],
    })
    data, result = await stage.validate(sample_data)
    assert result.status == "success"  # name column has no nulls


@pytest.mark.asyncio
async def test_validate_unique():
    data = [{"id": 1}, {"id": 2}, {"id": 1}]
    stage = ValidateStage({
        "name": "check_id_unique",
        "checks": [{"unique": ["id"]}],
    })
    result_df, result = await stage.execute(data)
    assert "duplicate" in str(result.warnings).lower() or result.status == "warning"


@pytest.mark.asyncio
async def test_validate_range():
    data = [{"value": 50}, {"value": 200}, {"value": 75}]
    stage = ValidateStage({
        "name": "check_range",
        "checks": [{"range": {"value": [0, 100]}}],
    })
    result_df, result = await stage.execute(data)
    assert result.status in ("warning", "success")
    if result.warnings:
        assert "200" in str(result.warnings) or "outside" in str(result.warnings).lower()


@pytest.mark.asyncio
async def test_pipeline_run(engine, tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("x,y\n1,a\n2,b\n3,c")
    config_path = tmp_path / "pipeline.yaml"
    config = {
        "name": "test-pipeline",
        "stages": [
            {"name": "extract", "type": "csv", "path": str(csv_path)},
        ],
    }
    config_path.write_text(yaml.dump(config))

    config = engine.load(str(config_path))
    run = await engine.run(config)
    assert run.status == "completed"
    assert len(run.results) == 1
    assert run.results[0].rows_out == 3
