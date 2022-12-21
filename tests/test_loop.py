import discord
import pytest

from accountabot.loop import commitment_check_loop


@pytest.mark.asyncio
async def test_commitment_check_loop_sends_failure_and_reminder(
    guild: discord.Guild,
):
    await commitment_check_loop([guild])
    send = guild.text_channels[0].send
    titles = [
        call_args.args[1]["embed"].title for call_args in send.call_args_list
    ]

    assert send.call_count == 2
    assert "Reminder" in titles
    assert "Missed commitment"
