import os
import sys
from pathlib import Path

import environ

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"

sys.path.insert(0, str(SRC_DIR))

from llm.openai import OpenAIProvider
from llm.types import LLMMessage


environ.Env.read_env(ROOT_DIR / ".env")


def main() -> None:
    provider = OpenAIProvider(
        api_key=os.environ["OPENAI_API_KEY"],
        model=os.environ["LLM_MODEL"],
    )

    response = provider.generate(
        [
            LLMMessage(
                role="system",
                content="Answer concisely.",
            ),
            LLMMessage(
                role="user",
                content="Reply with exactly: connection-ok",
            ),
        ]
    )

    print(f"Model: {response.model}")
    print(f"Response: {response.content}")


if __name__ == "__main__":
    main()
