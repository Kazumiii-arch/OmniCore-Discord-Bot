import asyncio
import logging
import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OWNER_IDS = [int(owner_id) for owner_id in os.getenv("OWNER_IDS", "").split(",") if owner_id.strip()]
COGS_DIR = Path("cogs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("OmniCore")


class OmniCore(commands.Bot):
    """Main OmniCore bot."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.reactions = True
        intents.guilds = True

        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=intents,
            help_command=None,
            case_insensitive=True,
        )
        self.owner_ids = set(OWNER_IDS)

    async def setup_hook(self) -> None:
        if not COGS_DIR.exists():
            logger.warning("Cog directory '%s' was not found; skipping extension load.", COGS_DIR)
            return

        logger.info("Loading cogs from %s", COGS_DIR)
        for path in sorted(COGS_DIR.glob("*.py")):
            if path.name == "__init__.py":
                continue
            extension = f"{COGS_DIR.name}.{path.stem}"
            try:
                await self.load_extension(extension)
                logger.info("Loaded cog: %s", extension)
            except Exception:
                logger.exception("Failed to load cog: %s", extension)

    async def on_ready(self) -> None:
        logger.info("Bot online as %s (%s)", self.user, self.user.id if self.user else "unknown")
        logger.info("Discord.py version: %s", discord.__version__)
        logger.info("Connected to %d guild(s)", len(self.guilds))
        await self.change_presence(activity=discord.Game(name="!help | OmniCore"))

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        latency_ms = round(self.latency * 1000)
        await ctx.reply(f"Pong! `{latency_ms}ms`")

    @commands.command(name="about")
    async def about(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title="OmniCore",
            description="An all-in-one Discord bot focused on moderation, utility, and community tools.",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Servers", value=str(len(self.guilds)), inline=True)
        embed.add_field(name="Prefix", value="`!`", inline=True)
        embed.set_footer(text="Built with discord.py")
        await ctx.reply(embed=embed)

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync(self, ctx: commands.Context) -> None:
        synced = await self.tree.sync()
        await ctx.reply(f"Synced {len(synced)} application command(s).")

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing a required argument. Use `!help {ctx.command.name}` for info.")
            return
        if isinstance(error, commands.NotOwner):
            await ctx.send("You do not have permission to use that command.")
            return
        logger.exception("Unhandled command error", exc_info=error)
        await ctx.send("An unexpected error occurred. Please try again later.")


async def main() -> None:
    if not TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN is missing from the environment.")

    bot = OmniCore()
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())