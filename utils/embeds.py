"""Shared embed styles so every OmniCore reply looks consistent."""

import discord

BRAND = discord.Color.from_rgb(88, 101, 242)
SUCCESS = discord.Color.from_rgb(67, 181, 129)
ERROR = discord.Color.from_rgb(237, 66, 69)
WARNING = discord.Color.from_rgb(250, 166, 26)

FOOTER = "OmniCore"


def _base(title, description, color) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text=FOOTER)
    return embed


def info(title: str, description: str = None) -> discord.Embed:
    return _base(title, description, BRAND)


def success(description: str, title: str = "Done") -> discord.Embed:
    return _base(f"✅  {title}", description, SUCCESS)


def error(description: str, title: str = "Something went wrong") -> discord.Embed:
    return _base(f"❌  {title}", description, ERROR)


def warning(description: str, title: str = "Heads up") -> discord.Embed:
    return _base(f"⚠️  {title}", description, WARNING)
