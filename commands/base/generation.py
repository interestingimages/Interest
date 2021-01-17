from concurrent.futures import ThreadPoolExecutor
from functools import partial
from hentai import Hentai
from pathlib import Path
from re import findall
from PIL import Image
import aiofiles
import categen
import asyncio
import shutil
import json


executor = ThreadPoolExecutor(10)
modes = ["doujin"]


async def submit_cmdparse(text: str) -> dict:
    text = text.split(" ")
    meta = {"mode": "doujin", "time": None, "desc": ""}

    if len(text) == 1:
        return None

    elif len(text) == 2:
        meta["command"] = text[0]

        if text[1].startswith(tuple(modes)):
            return None

        else:
            meta["hid"] = int(text[1])

    elif len(text) == 3:
        meta["command"] = text[0]

        if text[1].startswith(tuple(modes)):
            meta["mode"] = "doujin"

            if "+time=" in text[1]:
                meta["time"] = text[1].split("+time=")[1]

            meta["hid"] = int(text[2])

        else:
            meta["hid"] = int(text[1])
            meta["desc"] = text[2]

    else:
        meta["command"] = text[0]
        if text[1].startswith(tuple(modes)):
            if "+time=" in text[1]:
                meta["time"] = text[1].split("+time=")[1]
                meta["mode"] = text[1].split("+time=")[0]
            else:
                meta["mode"] = text[1]
            meta["hid"] = int(text[2])
            meta["desc"] = " ".join(text[3:])

        else:
            meta["hid"] = int(text[1])
            meta["desc"] = " ".join(text[2:])

    return meta


async def submit(
    catalogue_path: Path,
    version_id: str,
    submitter: str,
    submitter_id: int,
    hid: int,
    image: Image = None,
    desc: str = "",
    platform: str = "Telegram",
    slink_override: str = "<[slink]>",
) -> dict:
    pattern = "ii.*-...-......"
    entries = [d.name for d in catalogue_path.glob("*") if d.is_dir()]
    entries = [findall(pattern, d)[0] for d in entries if len(findall(pattern, d)) == 1]
    entries = [d[2:].split("-") for d in entries]
    entries = [(vid, int(eid), int(hid)) for vid, eid, hid in entries]

    if hid in [einfo[2] for einfo in entries]:
        return 1

    if not Hentai.exists(hid):
        return 2

    _eids = [einfo[1] for einfo in entries]
    if _eids != []:
        eid = max(_eids) + 1
    else:
        eid = 1

    eid = ("0" * (3 - len(str(eid)))) + str(eid)
    entry_path = catalogue_path.joinpath(f"ii{version_id}-{eid}-{hid}/")

    loop = asyncio.get_running_loop()

    await aiofiles.os.mkdir(entry_path)

    catentry = await loop.run_in_executor(
        executor, partial(categen.CatalogueEntry, eid, hid, desc)
    )

    entry_meta = {
        "submitter": submitter_id,
        "platform": platform,
        "upvotes": [submitter_id],
        "downvotes": [],
    }

    async with aiofiles.open(entry_path.joinpath("meta.json"), "w") as metafile:
        await metafile.write(json.dumps(entry_meta))

    catentry.submission = f"Community Submission by {submitter}"
    catentry.formatting_map["slink"] = slink_override
    catentry.rating = "<[vote]>% Upvoted"

    await loop.run_in_executor(executor, catentry.entry, platform)
    await loop.run_in_executor(
        executor, partial(catentry.thumbnail, preview=image, suppress=True)
    )

    async with aiofiles.open(entry_path.joinpath("entry.txt"), "w") as entryfile:
        await entryfile.write(catentry._entry)

    await loop.run_in_executor(
        executor, catentry._thumbnail.save, entry_path.joinpath("thumbnail.png")
    )

    return {
        "ids": [version_id, eid, hid],
        "url": catentry.doujin.url,
        "entry": catentry._entry.replace("<[vote]>", "100"),
        "thumb": entry_path.joinpath("thumbnail.png"),
        "path": entry_path,
        "meta": entry_meta,
    }


async def meta_out(meta: dict, ids: dict, mid: int, entry_path: Path) -> None:
    meta["message_id"] = mid
    async with aiofiles.open(entry_path.joinpath("meta.json"), "w") as metafile:
        await metafile.write(json.dumps(meta))

    lookup_path = entry_path.parent.joinpath("lookup/")
    if not lookup_path.exists():
        await aiofiles.os.mkdir(lookup_path)

    eid = ("0" * (3 - len(str(ids)))) + str(ids[1])

    async with aiofiles.open(lookup_path.joinpath(str(mid)), "w") as lookupfile:
        await lookupfile.write(f"ii{ids[0]}-{eid}-{ids[2]}")


async def remove(eid: int, catalogue_path: Path, submitter_id: int) -> dict:
    loop = asyncio.get_running_loop()
    pattern = "ii.*-...-......"
    entries = [d.name for d in catalogue_path.glob("*") if d.is_dir()]
    entries = [findall(pattern, d)[0] for d in entries if len(findall(pattern, d)) == 1]
    entries = [d[2:].split("-") for d in entries]
    entries = [(vid, int(eid), int(hid)) for vid, eid, hid in entries]

    eids = [entry[1] for entry in entries]
    if eid not in eids:
        return 1

    else:
        result = entries[eids.index(eid)]
        eid = ("0" * (3 - len(str(result[1])))) + str(result[1])
        entry_path = catalogue_path.joinpath(f"ii{result[0]}-{eid}-{result[2]}/")

        metafile = await aiofiles.open(entry_path.joinpath("meta.json"), "r")
        metadata = await loop.run_in_executor(
            executor, json.loads, await metafile.read()
        )
        metafile.close()

        mid_lookup = catalogue_path.joinpath(f'lookup/{metadata["message_id"]}')
        if mid_lookup.exists():
            await aiofiles.os.remove(mid_lookup)

        if metadata["submitter"] == submitter_id:
            await loop.run_in_executor(
                executor, partial(shutil.rmtree, entry_path, ignore_errors=True)
            )

        else:
            return 2

        return metadata


async def vote(
    mid: int, uid: int, catalogue_path: Path, target: str = "upvotes"
) -> str:
    loop = asyncio.get_running_loop()

    lookup_query = [
        int(f.name) for f in catalogue_path.joinpath("lookup/").glob("*") if f.is_file()
    ]
    if mid in lookup_query:
        async with aiofiles.open(
            catalogue_path.joinpath(f"lookup/{mid}"), "r"
        ) as lookupfile:
            entry = await lookupfile.read()

        entryfile = await aiofiles.open(
            catalogue_path.joinpath(f"{entry}/entry.txt"), "r", encoding="utf-8"
        )
        entrytext = await entryfile.read()

        async with aiofiles.open(
            catalogue_path.joinpath(f"{entry}/meta.json"), "r"
        ) as metafile:
            metadata = await loop.run_in_executor(
                executor, json.loads, await metafile.read()
            )

        oppmode = "downvotes" if target == "upvotes" else "upvotes"

        if uid not in metadata[target]:
            metadata[target].append(uid)

        if uid in metadata[oppmode]:
            metadata[oppmode].remove(uid)

        async with aiofiles.open(
            catalogue_path.joinpath(f"{entry}/meta.json"), "w"
        ) as metafile:
            await metafile.write(
                await loop.run_in_executor(executor, json.dumps, metadata)
            )

        await entryfile.close()
        await metafile.close()

        if len(metadata["downvotes"]) == 0:
            vote_perc = 100
        else:
            vote_perc = round(
                len(metadata["upvotes"]) / len(metadata["downvotes"]) * 100
            )

        return entrytext.replace("<[vote]>", str(vote_perc))

    else:
        return None
