from inspect import getmembers, isfunction  # noqa: F401
from pyrogram import Client, filters
from setuptools import find_packages
from pkgutil import iter_modules
from pathlib import Path
import colorama
import semver

from internals import config
import commands  # noqa: F401

cfore, _, cstyle, creset = (
    colorama.Fore,
    colorama.Back,
    colorama.Style,
    colorama.Style.RESET_ALL,
)
colorama.init(autoreset=True)
version = semver.VersionInfo.parse("1.0.0")
config = config.Config(
    "./config.toml",
    default={
        "General": {"catalogue_path": "catalogue/"},
        "Telegram": {"api_id": "", "api_hash": "", "token": ""},
    },
)
catalogue_path = (
    Path(__file__).absolute().parent.joinpath(config["General"]["catalogue_path"])
)
cache_path = Path(__file__).absolute().parent.joinpath(config["General"]["cache_path"])
version_id = "5_3"

if not catalogue_path.exists():
    import os

    os.mkdir(catalogue_path)


def cmd_docstrings(prefix: str):
    # This looks through the commands package and gets every command alongside
    # its docstring, to construct a help string to be returned

    cmds = [("General", "help", "Display a list of commands\n\n")]
    path = "."
    for pkg in find_packages(path):
        for info in iter_modules([str(path) + "/" + pkg.replace(".", "/")]):
            if not info.ispkg and "commands" in str(info.module_finder):
                for name, _ in eval(f"getmembers({pkg}.{info.name}, isfunction)"):
                    if not name.startswith("_"):
                        cmds.append(
                            [
                                info.name.replace(prefix, "").capitalize(),
                                name,
                                eval(f"{pkg}.{info.name}.{name}.__doc__"),
                            ]
                        )

    parsed = {}
    for group, command_name, docstring in cmds:
        if parsed.get(group) is None:
            parsed[group] = []

        parsed[group].append((command_name, docstring))

    help_str = "**Command List**\n\n"
    for group, payload in parsed.items():
        help_str += f"**{group}**\n"

        for command_name, docstring in payload:
            help_str += f"‣ /{command_name}\n"

            docstring = docstring if docstring is not None else ""

            for line in docstring.splitlines():
                help_str += f"    {line.lstrip()}\n"

            if not docstring.rstrip(" ").endswith("\n"):
                help_str += "\n"

    return help_str


def main():
    help_str = cmd_docstrings(prefix="tg_")

    client = Client(
        "interest",
        api_id=str(config["Telegram"]["api_id"]),
        api_hash=config["Telegram"]["api_hash"],
        bot_token=config["Telegram"]["token"],
        app_version=f"interest {version}",
        plugins=dict(root="commands"),
    )

    client.channel = config["Telegram"]["channel"]
    client.catalogue_path = catalogue_path
    client.version_id = version_id
    client.cache_path = cache_path
    client.version = version

    @client.on_message(filters.command(commands=["help", "help@iinterestingbot"]))
    async def help(client, message):
        await client.send_message(message.chat.id, help_str, parse_mode="Markdown")

    client.run()


if __name__ == "__main__":
    print(
        f"{cstyle.BRIGHT}interesting images{creset} Interest Bot {version}\n\n"
        f"{cstyle.BRIGHT}Establishing Client Connection{creset}\n"
        f'  MTProto API ID   : {str(config["Telegram"]["api_id"])[:-3]}XXX\n'
        f'  MTProto API Hash : {str(config["Telegram"]["api_hash"])[:-10]}XXXXXXXXXX\n'
        "  Bot Token        : "
        f'{config["Telegram"]["token"].split(":")[0][:-5]}XXXXX:'
        f'{config["Telegram"]["token"].split(":")[1][:-5]}XXXXX.\n\n'
        f"{cstyle.BRIGHT}Configuration{creset}\n"
        f"  Catalogue Path   : {catalogue_path}\n"
    )

    main()
