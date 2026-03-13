import re

from data_pipeline.pipeline import PipelineContext, Step

COOKIE_ARTIFACT = "Sorry, we are not allowed to show you this content due to your cookie settings."


class CleanerStep(Step):
    """Remove scraping artifacts and normalize whitespace."""

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        for doc in ctx.raw_documents:
            text: str = doc["content"]
            text = text.replace(COOKIE_ARTIFACT, "")
            text = re.sub(r"^ +", "", text, flags=re.MULTILINE)
            text = re.sub(r"\n{3,}", "\n\n", text)
            doc["content"] = text.strip()
        return ctx
