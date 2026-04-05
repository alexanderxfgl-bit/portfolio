"""
AI Workflow Automation Engine - YAML-driven workflow execution with LLM nodes.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# --- Models ---
class NodeResult(BaseModel):
    node_id: str
    status: str = "success"  # success, error, skipped, pending_review
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0


class WorkflowRun(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_name: str
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    status: str = "running"  # running, completed, failed, pending_review
    results: list[NodeResult] = []
    context: dict[str, Any] = {}


# --- Node Implementations ---
class LLMNode:
    """Execute an LLM call with templated prompt."""

    def __init__(self, config: dict):
        self.model = config.get("model", "openai/gpt-4o-mini")
        self.prompt_template = config.get("prompt", "")
        self.output_key = config.get("output_key", "result")
        self.temperature = config.get("temperature", 0.3)
        self._client = None

    async def execute(self, context: dict[str, Any]) -> NodeResult:
        import time
        start = time.time()
        try:
            prompt = self._render_template(self.prompt_template, context)

            try:
                import litellm
                response = await litellm.acompletion(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                )
                result = response.choices[0].message.content
            except ImportError:
                result = f"[LiteLLM not installed - would call {self.model} with prompt: {prompt[:100]}...]"

            return NodeResult(
                node_id="llm",
                output={self.output_key: result},
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return NodeResult(node_id="llm", status="error", error=str(e))

    @staticmethod
    def _render_template(template: str, context: dict) -> str:
        result = template
        for key, value in context.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    result = result.replace(f"{{{{{key}.{k}}}}}", str(v))
            else:
                result = result.replace(f"{{{{{key}}}}}", str(value))
        return result


class ConditionNode:
    """Evaluate a condition and return which branch to take."""

    def __init__(self, config: dict):
        self.check = config.get("check", "")
        self.then = config.get("then")
        self.else_branch = config.get("else")

    async def execute(self, context: dict[str, Any]) -> NodeResult:
        import time
        start = time.time()
        try:
            # Simple string equality check (production would use a proper expression engine)
            result = self._evaluate(self.check, context)
            branch = self.then if result else self.else_branch
            return NodeResult(
                node_id="condition",
                output={"result": result, "branch": branch},
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return NodeResult(node_id="condition", status="error", error=str(e))

    @staticmethod
    def _evaluate(check: str, context: dict) -> bool:
        # Handle "value == 'string'" patterns
        if " == '" in check:
            lhs, rhs = check.split(" == '", 1)
            rhs = rhs.rstrip("'")
            # Resolve template references
            for key, value in context.items():
                if isinstance(value, dict):
                    for k, v in value.items():
                        lhs = lhs.replace(f"{{{{{key}.{k}}}}}", str(v))
                else:
                    lhs = lhs.replace(f"{{{{{key}}}}}", str(value))
            return lhs.strip() == rhs
        return False


class WebhookNode:
    """Send data to an HTTP webhook."""

    def __init__(self, config: dict):
        self.url = config.get("url", "")
        self.method = config.get("method", "POST").upper()
        self.body_template = config.get("body", {})
        self.headers = config.get("headers", {})

    async def execute(self, context: dict[str, Any]) -> NodeResult:
        import time
        start = time.time()
        try:
            import aiohttp

            body = {}
            for key, value in self.body_template.items():
                body[key] = self._resolve_value(value, context)

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    self.method, self.url, json=body, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    text = await resp.text()

            return NodeResult(
                node_id="webhook",
                output={"status": resp.status, "body": text[:500]},
                duration_ms=(time.time() - start) * 1000,
            )
        except ImportError:
            return NodeResult(
                node_id="webhook",
                output={"status": "skipped", "body": "aiohttp not installed"},
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return NodeResult(node_id="webhook", status="error", error=str(e))

    @staticmethod
    def _resolve_value(value, context: dict):
        if isinstance(value, str):
            for key, v in context.items():
                if isinstance(v, dict):
                    for k, val in v.items():
                        value = value.replace(f"{{{{{key}.{k}}}}}", str(val))
                else:
                    value = value.replace(f"{{{{{key}}}}}", str(v))
            return value
        return value


class TransformNode:
    """Transform data using simple operations."""

    async def execute(self, context: dict[str, Any], config: dict) -> NodeResult:
        import time
        start = time.time()
        operation = config.get("operation", "identity")
        source = config.get("source", "")

        try:
            data = context.get(source, context)
            if operation == "extract_json":
                result = json.loads(data) if isinstance(data, str) else data
            elif operation == "uppercase":
                result = str(data).upper()
            elif operation == "slice":
                result = str(data)[: config.get("length", 500)]
            else:
                result = data

            return NodeResult(
                node_id="transform",
                output={"result": result},
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return NodeResult(node_id="transform", status="error", error=str(e))


# --- Workflow Engine ---
class WorkflowEngine:
    """Parse and execute YAML workflow definitions."""

    NODE_TYPES = {
        "llm": LLMNode,
        "condition": ConditionNode,
        "webhook": WebhookNode,
    }

    def __init__(self):
        self._node_cache: dict[str, Any] = {}

    def load_workflow(self, path: str) -> dict:
        with open(path) as f:
            return yaml.safe_load(f)

    async def run(self, workflow: dict, initial_context: Optional[dict] = None) -> WorkflowRun:
        run = WorkflowRun(
            workflow_name=workflow.get("name", "unnamed"),
            context=initial_context or {},
        )
        logger.info(f"Starting workflow: {run.workflow_name} (run: {run.run_id})")

        nodes = workflow.get("nodes", [])
        for node_config in nodes:
            node_id = node_config.get("id", "unknown")
            node_type = node_config.get("type")

            logger.info(f"  Executing node: {node_id} (type: {node_type})")

            node_cls = self.NODE_TYPES.get(node_type)
            if not node_cls:
                result = NodeResult(node_id=node_id, status="error", error=f"Unknown node type: {node_type}")
                run.results.append(result)
                continue

            if node_type == "transform":
                result = await TransformNode().execute(run.context, node_config)
            else:
                node = node_cls(node_config)
                result = await node.execute(run.context)

            run.results.append(result)
            if result.output:
                if isinstance(result.output, dict):
                    run.context.update(result.output)

            if result.status == "error":
                logger.error(f"    Node {node_id} failed: {result.error}")
                run.status = "failed"
                break
            elif result.status == "pending_review":
                run.status = "pending_review"
                break

        run.completed_at = datetime.now(timezone.utc).isoformat()
        if run.status == "running":
            run.status = "completed"
        logger.info(f"Workflow {run.workflow_name} finished: {run.status}")
        return run


# --- CLI ---
async def main():
    import argparse

    parser = argparse.ArgumentParser(description="AI Workflow Automation Engine")
    parser.add_argument("--workflow", required=True, help="Path to workflow YAML file")
    parser.add_argument("--data", help="JSON file with initial context data")
    parser.add_argument("--dry-run", action="store_true", help="Parse workflow without executing")
    args = parser.parse_args()

    engine = WorkflowEngine()
    workflow = engine.load_workflow(args.workflow)

    if args.dry_run:
        print(f"Workflow: {workflow.get('name')}")
        print(f"Nodes: {len(workflow.get('nodes', []))}")
        for node in workflow.get("nodes", []):
            print(f"  - {node.get('id')} ({node.get('type')})")
        return

    initial_context = {}
    if args.data:
        with open(args.data) as f:
            initial_context = json.load(f)

    run = await engine.run(workflow, initial_context)
    print(f"\nRun {run.run_id}: {run.status}")
    for r in run.results:
        icon = {"success": "✅", "error": "❌", "skipped": "⏭️", "pending_review": "⏸️"}.get(r.status, "❓")
        print(f"  {icon} {r.node_id}: {r.status} ({r.duration_ms:.0f}ms)")


if __name__ == "__main__":
    asyncio.run(main())
