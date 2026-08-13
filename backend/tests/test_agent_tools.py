import asyncio

import pytest

from app.agents.tools.python_tool import (
    run_python_utility,
)


def test_python_calculator_utility():
    result = asyncio.run(
        run_python_utility(
            operation="calculator",
            expression="(25 * 12) / 4",
        )
    )

    assert result["result"] == 75


def test_python_utility_blocks_arbitrary_code():
    with pytest.raises(
        ValueError
    ):
        asyncio.run(
            run_python_utility(
                operation="calculator",
                expression="__import__('os').system('echo bad')",
            )
        )
