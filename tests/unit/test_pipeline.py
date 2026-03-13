import pytest

from data_pipeline.pipeline import Pipeline, PipelineContext, Step


class AddStep(Step):
    async def run(self, ctx: PipelineContext) -> PipelineContext:
        ctx.extras["count"] = ctx.extras.get("count", 0) + 1
        return ctx


class DoubleStep(Step):
    async def run(self, ctx: PipelineContext) -> PipelineContext:
        ctx.extras["count"] = ctx.extras.get("count", 0) * 2
        return ctx


@pytest.mark.asyncio
async def test_pipeline_runs_steps_in_order():
    pipeline = Pipeline(steps=[AddStep(), DoubleStep(), AddStep()])
    ctx = await pipeline.run()
    assert ctx.extras["count"] == 3  # (0+1)*2 + 1


@pytest.mark.asyncio
async def test_pipeline_empty():
    pipeline = Pipeline(steps=[])
    ctx = await pipeline.run()
    assert ctx.extras == {}
