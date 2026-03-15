import re

from data_pipeline.interfaces import IDocumentCleaner
from data_pipeline.models import RawDocument

COOKIE_ARTIFACT = "Sorry, we are not allowed to show you this content due to your cookie settings."


class RegexDocumentCleaner(IDocumentCleaner):
    async def clean(self, documents: list[RawDocument]) -> list[RawDocument]:
        cleaned: list[RawDocument] = []
        for doc in documents:
            text = doc.content
            text = text.replace(COOKIE_ARTIFACT, "")
            text = re.sub(r"^ +", "", text, flags=re.MULTILINE)
            text = re.sub(r"\n{3,}", "\n\n", text)
            cleaned.append(RawDocument(source_file=doc.source_file, content=text.strip()))
        return cleaned
