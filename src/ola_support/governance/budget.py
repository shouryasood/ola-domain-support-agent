from __future__ import annotations

from math import ceil
import os


class RequestBudgetExceeded(ValueError):
    def __init__(self, estimated_tokens: int, token_cap: int) -> None:
        self.estimated_tokens = estimated_tokens
        self.token_cap = token_cap
        super().__init__(
            f"Estimated request size {estimated_tokens} tokens exceeds "
            f"the per-request cap of {token_cap}."
        )


def enforce_request_budget(text: str) -> dict[str, int]:
    token_cap = int(os.getenv("TOKEN_BUDGET_PER_REQUEST", "2000"))
    estimated_tokens = ceil(len(text) / 4) + 256

    if estimated_tokens > token_cap:
        raise RequestBudgetExceeded(estimated_tokens, token_cap)

    return {
        "estimated_tokens": estimated_tokens,
        "token_cap": token_cap,
    }
