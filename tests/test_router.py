import pytest
from core.router import CommandContext, CommandRouter

@pytest.mark.asyncio
async def test_router_registration_and_dispatch():
    test_router = CommandRouter()

    @test_router.register("ping", "Responds with pong", "/ping", "test", aliases=["p"])
    async def cmd_ping(ctx: CommandContext) -> str:
        return "pong"

    ctx = CommandContext(
        sender="6281234567890",
        jid="6281234567890@s.whatsapp.net",
        is_group=False,
        raw_message={},
        args=[],
        text="/ping"
    )

    # Test main command
    res1 = await test_router.dispatch("/ping", ctx)
    assert res1 == "pong"

    # Test alias
    res2 = await test_router.dispatch("/p", ctx)
    assert res2 == "pong"

    # Test unknown command
    res3 = await test_router.dispatch("/unknown", ctx)
    assert "tidak dikenali" in res3

    # Test non-command returns None
    res4 = await test_router.dispatch("just a regular text", ctx)
    assert res4 is None
