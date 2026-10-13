import pytest
import asyncio
from workflow_engine import AsyncWorkflowEngine

@pytest.mark.asyncio
async def test_workflow_execution():
    engine = AsyncWorkflowEngine()

    async def sample_task_a(ctx):
        ctx['data_a'] = "Processed A"
        await asyncio.sleep(0.1)

    async def sample_task_b(ctx):
        assert 'data_a' in ctx
        ctx['data_b'] = "Processed B"

    engine.add_task("task_a", sample_task_a)
    engine.add_task("task_b", sample_task_b, dependencies=["task_a"])

    results = await engine.run_workflow({})
    
    assert engine.tasks["task_a"].status == "COMPLETED"
    assert engine.tasks["task_b"].status == "COMPLETED"