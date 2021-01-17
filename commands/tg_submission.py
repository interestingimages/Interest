from pyrogram import Client, filters, types, errors
from .base import generation
from random import randint
from aiofiles import os
from . import tg_utils
from PIL import Image
import traceback


@Client.on_message(filters.command(commands=["submit", "submit@iinterestingbot"]))
async def submit(client: Client, message: types.Message):
    """Submit a Community Catalogue Entry

    **Parameters**
    `<mode> <hid> <desc>`

    `mode` ‣ Submission Mode
    `hid ` ‣ Doujin ID
    `desc` ‣ Description

    **Example**
    `doujin 300000 xdxd funni`
    This submits the doujin 30000 with
    'xdxd funni' as the description.

    `doujin+time=1618906800 300000`
    This submits the doujin 30000 with
    no description, and will be scheduled
    for 4/20/2021 SGT, represented as UNIX
    time.

    **Notes**
    The thumbnail will show the doujin
    thumbnail as a default, but can be
    overriden by having the command as
    a caption of an image.
    """
    submitter_name = "@" + message.from_user.username
    submitter_id = message.from_user.id

    if message.text is None:
        response = await generation.submit_cmdparse(message.caption)
    else:
        response = await generation.submit_cmdparse(message.text)

    if response is None:
        await tg_utils._3smsg(client, message, "Not enough or too many arguments! {}")

    else:
        temp_photo_file = f"{randint(10000, 99999)}.png"
        temp_photo_path = client.cache_path.joinpath(temp_photo_file)
        if message.photo is None:
            tg_utils._3smsg(client, message, "Please provide an image! {}")

        else:
            await client.download_media(
                message=message,
                file_name=str(temp_photo_path),
            )
            photo = Image.open(temp_photo_path).convert("RGBA")

            try:
                opmsg = await client.send_message(
                    message.chat.id, "Working on it! This will take a while."
                )
                result = await generation.submit(
                    catalogue_path=client.catalogue_path,
                    version_id=client.version_id,
                    submitter=submitter_name,
                    submitter_id=submitter_id,
                    hid=response["hid"],
                    image=photo,
                    desc=response["desc"],
                    platform="Telegram",
                    slink_override="[<[slink]>](<[link]>)",
                )

                if result == 1:
                    await tg_utils._3smsg(
                        client,
                        message,
                        "Doujin either already exists or is planned! {}",
                        opmsg,
                    )

                elif result == 2:
                    await tg_utils._3smsg(
                        client, message, "Invalid doujin ID! {}", opmsg
                    )

                else:
                    await opmsg.delete()

                    res_msg = await client.send_photo(
                        chat_id=client.channel,
                        photo=result["thumb"],
                        caption=result["entry"],
                        parse_mode="Markdown",
                        reply_markup=types.InlineKeyboardMarkup(
                            [
                                [
                                    types.InlineKeyboardButton(
                                        "👍", callback_data="upvote"
                                    ),
                                    types.InlineKeyboardButton(
                                        "👎", callback_data="downvote"
                                    ),
                                ]
                            ]
                        ),
                    )

                    await generation.meta_out(
                        meta=result["meta"],
                        ids=result["ids"],
                        mid=res_msg.message_id,
                        entry_path=result["path"],
                    )

            except Exception as e:
                gen_err = "**Woops. Something went wrong.**\n\n**Traceback**\n```"
                for line in "".join(
                    traceback.format_exception(None, e, e.__traceback__)
                ).splitlines():
                    gen_err += f"{line}\n"
                gen_err += "```\n**Response Dictionary**\n"
                for key, pair in response.items():
                    gen_err += f"`{key}` : `{pair}`\n"
                gen_err += "\nPlease report this to the developer!"

                await client.send_message(message.chat.id, gen_err)

    if message.photo is not None:
        await os.remove(temp_photo_path)


@Client.on_message(filters.command(commands=["remove", "remove@iinterestingbot"]))
async def remove(client: Client, message: types.Message):
    """Revoke a published Catalogue Entry
    from the Catalogue Database and delete
    the associated message in the
    interesting images channel.

    **Parameters**
    `<eid>`

    `eid` ‣ Entry ID (e.g. 001)
    """
    resp = message.text.split(" ")

    if len(resp) > 1:
        try:
            int(resp[1])

        except ValueError:
            await tg_utils._3smsg(client, message, "Invalid parameter! {}")

        meta = await generation.remove(
            eid=int(resp[1]),
            catalogue_path=client.catalogue_path,
            submitter_id=message.from_user.id,
        )

        if meta == 1:
            await tg_utils._3smsg(client, message, "Invalid parameter! {}")

        elif meta == 2:
            await tg_utils._3smsg(client, message, "Illegal operation! {}")

        else:
            await client.delete_messages(
                chat_id=client.channel, message_ids=meta["message_id"]
            )

    else:
        await tg_utils._3smsg(client, message, "Not enough parameters! {}")


@Client.on_callback_query()
async def _vote(client: Client, callback: types.CallbackQuery):
    resp = await generation.vote(
        mid=callback.message.message_id,
        uid=callback.from_user.id,
        catalogue_path=client.catalogue_path,
        target="downvotes" if callback.data == "downvote" else "upvotes",
    )

    await callback.answer("Voted!", show_alert=True)

    if resp is not None:
        try:
            await callback.message.edit_caption(
                resp,
                parse_mode="Markdown",
                reply_markup=types.InlineKeyboardMarkup(
                    [
                        [
                            types.InlineKeyboardButton("👍", callback_data="upvote"),
                            types.InlineKeyboardButton("👎", callback_data="downvote"),
                        ]
                    ]
                ),
            )
        except errors.exceptions.bad_request_400.MessageNotModified:
            pass
