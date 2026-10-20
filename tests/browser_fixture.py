"""Print a synthetic response from the real engine for browser boundary regression tests."""
import asyncio

from conftest import FakePubMedConnector
from medical_ai.engine import EvidenceEngine


async def main():
    answer = await EvidenceEngine(FakePubMedConnector()).answer("What evidence exists about treatment X?")
    print(answer.model_dump_json())


if __name__ == "__main__":
    asyncio.run(main())
