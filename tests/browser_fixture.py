"""Print a synthetic response from the real engine for browser boundary regression tests."""
import asyncio
import json

from conftest import FakePubMedConnector
from medical_ai.engine import EvidenceEngine


async def main():
    engine = EvidenceEngine(FakePubMedConnector())
    answer = await engine.answer("What evidence exists about treatment X?")
    insufficient = await EvidenceEngine(FakePubMedConnector(sources=[], passages=[])).answer("What evidence exists about treatment X?")
    high = await engine.answer("What dose of treatment X should adults take?")
    regulator = await engine.answer("Is treatment X approved by the TGA in Australia?")
    print(json.dumps({
        "supported": answer.model_dump(mode="json"),
        "insufficient": insufficient.model_dump(mode="json"),
        "high": high.model_dump(mode="json"),
        "regulator": regulator.model_dump(mode="json"),
    }))


if __name__ == "__main__":
    asyncio.run(main())
