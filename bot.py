import asyncio
import logging
import os
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from utils import embeds

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", "!").strip() or "!"
OWNER_IDS = {int(x) for x in os.getenv("OWNER_IDS", "").split(",") if x.strip().isdigit()}
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Resolved relative to this file, so the bot works no matter where it's started from.
COGS_DIR = BASE_DIR / "cogs"
DATA_DIR = BASE_DIR / "data"

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("OmniCore")


class OmniCore(commands.Bot):
    """Main OmniCore bot."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True  # privileged: needed for prefix commands and XP
        intents.members = True  # privileged: needed for member lookups and user info

        super().__init__(
            command_prefix=commands.when_mentioned_or(PREFIX),
            intents=intents,
            help_command=None,  # replaced by the embed help in cogs/core.py
            case_insensitive=True,
            owner_ids=OWNER_IDS,  # empty = use the application owner
            activity=discord.Activity(type=discord.ActivityType.listening, name=f"{PREFIX}help"),
            # Never let user-supplied text (reasons, reminders, polls) ping @everyone or roles.
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=False),
        )
        self.prefix = PREFIX
        self.data_dir = DATA_DIR
        self.start_time = discord.utils.utcnow()

    async def setup_hook(self) -> None:
        self.data_dir.mkdir(exist_ok=True)
        if not COGS_DIR.exists():
            logger.warning("Cog directory '%s' was not found; skipping extension load.", COGS_DIR)
            return
        for path in sorted(COGS_DIR.glob("*.py")):
            if path.name.startswith("_"):
                continue
            extension = f"cogs.{path.stem}"
            try:
                await self.load_extension(extension)
                logger.info("Loaded cog: %s", extension)
            except Exception:
                logger.exception("Failed to load cog: %s", extension)

    async def on_ready(self) -> None:
        logger.info("Online as %s (%s) in %d server(s) | discord.py %s",
                    self.user, self.user.id, len(self.guilds), discord.__version__)

    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        # Unwrap the real error from invoke/hybrid wrappers.
        while isinstance(error, (commands.CommandInvokeError, commands.HybridCommandError,
                                 app_commands.CommandInvokeError)) and getattr(error, "original", None):
            error = error.original

        if isinstance(error, commands.CommandNotFound):
            return

        prefix = ctx.clean_prefix
        if isinstance(error, commands.MissingRequiredArgument) and ctx.command:
            usage = f"{prefix}{ctx.command.qualified_name} {ctx.command.signature}".strip()
            embed = embeds.error(f"Missing **{error.param.name}**.\nUsage: `{usage}`", "Missing argument")
        elif isinstance(error, commands.CommandOnCooldown):
            embed = embeds.warning(f"Slow down! Try again in **{error.retry_after:.1f}s**.", "On cooldown")
        elif isinstance(error, commands.MissingPermissions):
            embed = embeds.error(f"You need: **{_perms(error.missing_permissions)}**", "Missing permissions")
        elif isinstance(error, commands.BotMissingPermissions):
            embed = embeds.error(f"I need: **{_perms(error.missing_permissions)}**", "I'm missing permissions")
        elif isinstance(error, commands.NotOwner):
            embed = embeds.error("Only the bot owner can use this command.", "Not allowed")
        elif isinstance(error, commands.NoPrivateMessage):
            embed = embeds.error("This command only works inside a server.", "Server only")
        elif isinstance(error, (commands.BadArgument, commands.UserInputError, app_commands.TransformerError)):
            embed = embeds.error(str(error), "Invalid input")
        elif isinstance(error, (commands.CheckFailure, app_commands.CheckFailure)):
            embed = embeds.error("You can't use this command here.", "Not allowed")
        elif isinstance(error, discord.Forbidden):
            embed = embeds.error("Discord blocked that action. Check my role position and channel permissions.",
                                 "I'm missing permissions")
        else:
            logger.error("Unhandled error in %s", ctx.command, exc_info=error)
            embed = embeds.error("An unexpected error occurred. It has been logged.")

        try:
            await ctx.send(embed=embed, ephemeral=True)
        except discord.HTTPException:
            pass


def _perms(names) -> str:
    return ", ".join(name.replace("_", " ").replace("guild", "server").title() for name in names)


async def main() -> None:
    if not TOKEN:
        raise SystemExit("DISCORD_BOT_TOKEN is missing. Copy .env.example to .env and add your token.")

    bot = OmniCore()
    async with bot:
        try:
            await bot.start(TOKEN)
        except discord.LoginFailure:
            logger.critical("Discord rejected the token. Reset it in the Developer Portal and update .env.")
        except discord.PrivilegedIntentsRequired:
            logger.critical("Enable 'Server Members Intent' and 'Message Content Intent' under "
                            "Bot settings in the Discord Developer Portal, then restart.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down.")
