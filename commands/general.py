from pyrogram import Client, filters
from .base import general


@Client.on_message(filters.command(commands=["start", "start@iinterestingbot"]))
async def start(client, message):
    """Start the bot"""
    await client.send_message(message.chat.id, general.start(), parse_mode="Markdown")


@Client.on_message(filters.command(commands=["info", "info@iinterestingbot"]))
async def info(client, message):
    """Display information about Interest"""
    await client.send_message(message.chat.id, general.info(), parse_mode="Markdown")
