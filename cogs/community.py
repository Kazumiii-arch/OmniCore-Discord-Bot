import random
import time
from typing import Optional

import discord
from discord.ext import commands, tasks

from utils import embeds
from utils.storage import JsonStore

XP_MIN, XP_MAX = 15, 25
XP_COOLDOWN = 60  # seconds between XP gains per member, to stop spam farming


def xp_to_next(level: int) -> int:
    return 5 * level ** 2 + 50 * level + 100


def level_from_xp(xp: int):
    """Return (level, xp into current level, xp needed for next level)."""
    level = 0
    while xp >= xp_to_next(level):
        xp -= xp_to_next(level)
        level += 1
    return level, xp, xp_to_next(level)


def progress_bar(current: int, total: int, size: int = 12) -> str:
    filled = round(size * current / total) if total else 0
    return "▰" * filled + "▱" * (size - filled)


class Community(commands.Cog):
    """Leveling and leaderboards."""

    emoji = "🏆"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.store = JsonStore(bot.data_dir / "levels.json")
        self._cooldowns = {}
        self._dirty = False

    async def cog_load(self) -> None:
        self.autosave.start()

    async def cog_unload(self) -> None:
        self.autosave.cancel()
        if self._dirty:
            await self.store.save()

    @tasks.loop(seconds=60)
    async def autosave(self) -> None:
        if self._dirty:
            self._dirty = False
            await self.store.save()

    def _guild(self, guild_id: int) -> dict:
        return self.store.data.setdefault(str(guild_id), {})

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        key = (message.guild.id, message.author.id)
        now = time.monotonic()
        if now - self._cooldowns.get(key, 0) < XP_COOLDOWN:
            return
        self._cooldowns[key] = now

        users = self._guild(message.guild.id)
        old_xp = users.get(str(message.author.id), 0)
        new_xp = old_xp + random.randint(XP_MIN, XP_MAX)
        users[str(message.author.id)] = new_xp
        self._dirty = True

        old_level, new_level = level_from_xp(old_xp)[0], level_from_xp(new_xp)[0]
        if new_level > old_level:
            embed = embeds.info("🎉  Level up!", f"{message.author.mention} reached **level {new_level}**!")
            embed.set_thumbnail(url=message.author.display_avatar.url)
            try:
                await message.channel.send(embed=embed)
            except discord.HTTPException:
                pass

    @commands.hybrid_command(aliases=["level", "lvl", "xp"], description="Show your level and XP.")
    @commands.guild_only()
    async def rank(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        """Show your level and XP (or someone else's)."""
        member = member or ctx.author
        users = self._guild(ctx.guild.id)
        total = users.get(str(member.id), 0)
        level, current, needed = level_from_xp(total)
        ranking = sorted(users.items(), key=lambda kv: kv[1], reverse=True)
        position = next((i for i, (uid, _) in enumerate(ranking, 1) if uid == str(member.id)), None)

        embed = embeds.info(f"{member.display_name}'s rank")
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Level", value=f"**{level}**")
        embed.add_field(name="Rank", value=f"**#{position}**" if position else "Unranked")
        embed.add_field(name="Total XP", value=f"{total:,}")
        embed.add_field(name="Progress", value=f"{progress_bar(current, needed)}  {current:,} / {needed:,} XP",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=["lb", "top"], description="Show the server's top 10.")
    @commands.guild_only()
    async def leaderboard(self, ctx: commands.Context) -> None:
        """Show the server's top 10 most active members."""
        users = self._guild(ctx.guild.id)
        top = sorted(users.items(), key=lambda kv: kv[1], reverse=True)[:10]
        if not top:
            await ctx.send(embed=embeds.warning("Nobody has earned XP yet. Start chatting!"))
            return
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for i, (uid, xp) in enumerate(top, 1):
            lines.append(f"{medals.get(i, f'`#{i}`')} <@{uid}> · Level **{level_from_xp(xp)[0]}** · {xp:,} XP")
        embed = embeds.info(f"🏆  {ctx.guild.name} Leaderboard", "\n".join(lines))
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Community(bot))
