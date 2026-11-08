from collections.abc import Sequence

from autogen_core.models import ModelInfo
from autogen_ext.models.replay import ReplayChatCompletionClient


def make_mock_client(
    responses: Sequence[str],
) -> ReplayChatCompletionClient:
    return ReplayChatCompletionClient(
        chat_completions=list(responses),
        model_info=ModelInfo(
            vision=False,
            function_calling=False,
            json_output=True,
            family="unknown",
            structured_output=True,
        ),
    )
