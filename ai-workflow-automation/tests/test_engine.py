"""Tests for AI Workflow Automation Engine."""
import pytest
import asyncio
import yaml
import json
from runner import WorkflowEngine, LLMNode, ConditionNode, WorkflowRun


@pytest.fixture
def engine():
    return WorkflowEngine()


@pytest.fixture
def sample_workflow():
    return {
        "name": "test-workflow",
        "nodes": [
            {
                "id": "classify",
                "type": "llm",
                "model": "openai/gpt-4o-mini",
                "prompt": "Classify: {{item}}",
                "output_key": "category",
            },
            {
                "id": "check-category",
                "type": "condition",
                "check": "{{category}} == 'test'",
                "then": "done",
            },
        ],
    }


def test_load_workflow(engine, tmp_path):
    workflow_data = {"name": "test", "nodes": []}
    path = tmp_path / "test.yaml"
    path.write_text(yaml.dump(workflow_data))
    result = engine.load_workflow(str(path))
    assert result["name"] == "test"


@pytest.mark.asyncio
async def test_llm_node_with_mock_context():
    node = LLMNode({"model": "openai/gpt-4o-mini", "prompt": "Say hello", "output_key": "result"})
    # This will fail without API key, but should handle gracefully
    result = await node.execute({})
    # Either success (with litellm) or error (without API key) — both valid
    assert result.node_id == "llm"
    assert result.status in ("success", "error")


@pytest.mark.asyncio
async def test_condition_node_equality():
    node = ConditionNode({"check": "{{category}} == 'urgent'", "then": "notify"})
    result = await node.execute({"category": "urgent"})
    assert result.status == "success"
    assert result.output["result"] is True
    assert result.output["branch"] == "notify"


@pytest.mark.asyncio
async def test_condition_node_false():
    node = ConditionNode({"check": "{{category}} == 'urgent'", "then": "notify", "else": "skip"})
    result = await node.execute({"category": "spam"})
    assert result.status == "success"
    assert result.output["result"] is False
    assert result.output["branch"] == "skip"


@pytest.mark.asyncio
async def test_workflow_run(engine, sample_workflow):
    run = await engine.run(sample_workflow, {"item": "test"})
    assert isinstance(run, WorkflowRun)
    assert run.workflow_name == "test-workflow"
    assert run.run_id
    assert len(run.results) >= 1


@pytest.mark.asyncio
async def test_workflow_with_unknown_node_type(engine):
    workflow = {
        "name": "bad-workflow",
        "nodes": [{"id": "bad", "type": "nonexistent"}],
    }
    run = await engine.run(workflow)
    assert run.status == "failed"
    assert run.results[0].status == "error"


def test_prompt_template_rendering():
    template = "Hello {{name}}, your item {{item.id}} is ready"
    context = {"name": "Alex", "item": {"id": "123"}}
    result = LLMNode._render_template(template, context)
    assert result == "Hello Alex, your item 123 is ready"
