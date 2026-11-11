from collections import Counter

import discord
from discord.ext import commands

from utils import embeds
from utils.timefmt import format_duration


class Analytics(commands.Cog):
    """Bot usage statistics."""

    emoji = "📈"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.usage = Counter()

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context) -> None:
        if ctx.command:
            self.usage[ctx.command.qualified_name] += 1

    @commands.hybrid_command(aliases=["botstats"], description="Show bot usage statistics.")
    async def stats(self, ctx: commands.Context) -> None:
        """Show bot usage statistics since the last restart."""
        uptime = format_duration(discord.utils.utcnow() - self.bot.start_time)
        members = sum(g.member_count or 0 for g in self.bot.guilds)
        top = self.usage.most_common(5)

        embed = embeds.info("📈  OmniCore Stats")
        embed.add_field(name="Uptime", value=uptime)
        embed.add_field(name="Servers", value=f"{len(self.bot.guilds):,}")
        embed.add_field(name="Members", value=f"{members:,}")
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms")
        embed.add_field(name="Commands run", value=f"{sum(self.usage.values()):,}")
        embed.add_field(name="Most used",
                        value="\n".join(f"`{name}` × {count}" for name, count in top) or "Nothing yet",
                        inline=False)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Analytics(bot))
