import asyncio


async def _3smsg(client, umsg, error: str, rmsg=None):
    if rmsg is None:
        rmsg = await client.send_message(umsg.chat.id, error.format("🕒"))
    else:
        await rmsg.edit(error.format("🕒"))
    await asyncio.sleep(1.0)
    await rmsg.edit(error.format("🕑"))
    await asyncio.sleep(1.0)
    await rmsg.edit(error.format("🕐"))
    await asyncio.sleep(1.0)
    try:
        await rmsg.delete()
    except Exception:
        await rmsg.edit(error.replace("{}", "").lstrip())
    try:
        await umsg.delete()
    except Exception:
        pass
