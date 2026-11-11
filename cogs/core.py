import platform
from typing import Optional

import discord
from discord.ext import commands

from utils import embeds
from utils.timefmt import format_duration

REPO_URL = "https://github.com/Kazumiii-arch/OmniCore-Discord-Bot"


class Core(commands.Cog):
    """Help, bot info and owner tools."""

    emoji = "🧭"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="help", description="Show all commands or details for one.")
    async def help_command(self, ctx: commands.Context, *, command: Optional[str] = None) -> None:
        """Show all commands, or details for a single command."""
        prefix = ctx.clean_prefix

        if command:
            cmd = self.bot.get_command(command.lower().removeprefix(prefix).strip())
            if cmd is None or cmd.hidden:
                await ctx.send(embed=embeds.error(f"No command called `{command}`.", "Not found"), ephemeral=True)
                return
            embed = embeds.info(f"{prefix}{cmd.qualified_name}", cmd.help or cmd.description or "No description.")
            usage = f"{prefix}{cmd.qualified_name} {cmd.signature}".strip()
            embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
            if cmd.aliases:
                embed.add_field(name="Aliases", value=", ".join(f"`{a}`" for a in cmd.aliases), inline=False)
            await ctx.send(embed=embed)
            return

        embed = embeds.info("OmniCore Commands",
                            f"Prefix: `{self.bot.prefix}` · Slash commands also work: type `/`")
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        for name, cog in sorted(self.bot.cogs.items()):
            usable = []
            for cmd in cog.get_commands():
                if cmd.hidden:
                    continue
                try:
                    if await cmd.can_run(ctx):
                        usable.append(cmd)
                except commands.CommandError:
                    continue
            if usable:
                emoji = getattr(cog, "emoji", "•")
                embed.add_field(name=f"{emoji}  {name}",
                                value=" ".join(f"`{c.name}`" for c in sorted(usable, key=lambda c: c.name)),
                                inline=False)

        embed.set_footer(text=f"{prefix}help <command> for details · OmniCore")
        await ctx.send(embed=embed)

    @commands.hybrid_command(description="Check the bot's latency.")
    async def ping(self, ctx: commands.Context) -> None:
        """Check the bot's latency."""
        ms = round(self.bot.latency * 1000)
        status = "🟢" if ms < 150 else "🟡" if ms < 350 else "🔴"
        await ctx.send(embed=embeds.info("🏓  Pong!", f"{status} Websocket latency: **{ms}ms**"))

    @commands.hybrid_command(description="Information about OmniCore.")
    async def about(self, ctx: commands.Context) -> None:
        """Information about OmniCore."""
        uptime = format_duration(discord.utils.utcnow() - self.bot.start_time)
        embed = embeds.info("OmniCore",
                            "An all-in-one Discord bot for moderation, utility, leveling and reminders.")
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)))
        embed.add_field(name="Uptime", value=uptime)
        embed.add_field(name="Prefix", value=f"`{self.bot.prefix}` or `/`")
        embed.add_field(name="Library", value=f"discord.py {discord.__version__}")
        embed.add_field(name="Python", value=platform.python_version())
        embed.add_field(name="Source", value=f"[GitHub]({REPO_URL})")
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, scope: Optional[str] = None) -> None:
        """Sync slash commands. `sync` = global (can take up to an hour), `sync here` = this server instantly."""
        if scope == "here" and ctx.guild:
            self.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await self.bot.tree.sync(guild=ctx.guild)
            where = "this server"
        else:
            synced = await self.bot.tree.sync()
            where = "globally"
        await ctx.send(embed=embeds.success(f"Synced **{len(synced)}** slash command(s) {where}."))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Core(bot))
