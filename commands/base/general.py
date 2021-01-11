import platform


def start() -> str:
    return "Use /help for a list of commands!"


def info() -> str:
    add = " (Python)" if platform.python_implementation() != "CPython" else ""
    return (
        "**Interest**\n"
        "by @biconcavedskull\n"
        "\n"
        f"**Server**: {platform.system()} {platform.release()} "
        f"({platform.architecture()[0]})\n"
        f"**Python**{add}: {platform.python_version()}\n"
        "\n"
        f"**interesting images Source Code Repositories**\n"
        f"[PrintingPress](https://github.com/interestingimages/PrintingPress) "
        "- Image Manipulation\n"
        f"[categen](https://github.com/interestingimages/categen) "
        "- Catalogue Entry Generation\n"
        f"[Interest](https://github.com/interestingimages/Interest) "
        "- Telegram Interface for categen, with goodies"
    )
