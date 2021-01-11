from pyrogram import Client, filters
from .base import generation

# from aiofiles import open
from pathlib import Path


@Client.on_message(filters.command(commands=["submit", "submit@iinterestingbot"]))
async def submit(client, message):
    """Submit a Community Catalogue Entry"""
    print(client.uwu)
    # await client.send_message(message.chat.id, general.start(), parse_mode="Markdown")
    # Path("../../catalogue")


@Client.on_message(filters.command(commands=["revoke", "revoke@iinterestingbot"]))
async def revoke(client, message):
    pass
