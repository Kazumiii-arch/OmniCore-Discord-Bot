from datetime import timedelta
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from utils import embeds
from utils.timefmt import format_duration, parse_duration

MAX_TIMEOUT = timedelta(days=28)  # Discord's limit


def hierarchy_error(ctx: commands.Context, member: discord.Member) -> Optional[str]:
    """Return why `ctx.author` may not moderate `member`, or None if it's allowed."""
    guild = ctx.guild
    if member.id == ctx.author.id:
        return "You can't use this on yourself."
    if member.id == guild.me.id:
        return "I can't moderate myself."
    if member.id == guild.owner_id:
        return "The server owner can't be moderated."
    if ctx.author.id != guild.owner_id and member.top_role >= ctx.author.top_role:
        return f"{member.mention} has a role equal to or higher than yours."
    if member.top_role >= guild.me.top_role:
        return f"My highest role must be above {member.mention}'s highest role."
    return None


def audit_reason(ctx: commands.Context, reason: str) -> str:
    return f"{ctx.author} ({ctx.author.id}): {reason}"[:512]


async def try_dm(member: discord.Member, text: str) -> None:
    try:
        await member.send(text)
    except discord.HTTPException:
        pass  # DMs closed; not a reason to stop the action


class Moderation(commands.Cog):
    """Keep your server safe."""

    emoji = "🛡️"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    @commands.hybrid_command(description="Kick a member from the server.")
    @app_commands.default_permissions(kick_members=True)
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *,
                   reason: str = "No reason provided") -> None:
        """Kick a member from the server."""
        if problem := hierarchy_error(ctx, member):
            await ctx.send(embed=embeds.error(problem, "Can't kick"), ephemeral=True)
            return
        await try_dm(member, f"You were kicked from **{ctx.guild.name}**. Reason: {reason}")
        await member.kick(reason=audit_reason(ctx, reason))
        await ctx.send(embed=embeds.success(f"Kicked {member.mention}\n**Reason:** {reason}", "Member kicked"))

    @commands.hybrid_command(description="Ban a member from the server.")
    @app_commands.default_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *,
                  reason: str = "No reason provided") -> None:
        """Ban a member and delete their last 24h of messages."""
        if problem := hierarchy_error(ctx, member):
            await ctx.send(embed=embeds.error(problem, "Can't ban"), ephemeral=True)
            return
        await try_dm(member, f"You were banned from **{ctx.guild.name}**. Reason: {reason}")
        await member.ban(reason=audit_reason(ctx, reason), delete_message_seconds=86400)
        await ctx.send(embed=embeds.success(f"Banned {member.mention}\n**Reason:** {reason}", "Member banned"))

    @commands.hybrid_command(description="Unban a user by ID.")
    @app_commands.default_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user: discord.User, *,
                    reason: str = "No reason provided") -> None:
        """Unban a user by their ID."""
        try:
            await ctx.guild.unban(user, reason=audit_reason(ctx, reason))
        except discord.NotFound:
            await ctx.send(embed=embeds.error(f"{user} isn't banned.", "Not banned"), ephemeral=True)
            return
        await ctx.send(embed=embeds.success(f"Unbanned **{user}**", "User unbanned"))

    @commands.hybrid_command(aliases=["mute"], description="Time out a member, e.g. 10m, 2h, 1d.")
    @app_commands.default_permissions(moderate_members=True)
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout(self, ctx: commands.Context, member: discord.Member, duration: str, *,
                      reason: str = "No reason provided") -> None:
        """Time out a member. Duration examples: 30s, 10m, 2h, 1d (max 28d)."""
        delta = parse_duration(duration)
        if delta is None:
            await ctx.send(embed=embeds.error("Use a duration like `10m`, `2h` or `1d`.", "Invalid duration"),
                           ephemeral=True)
            return
        if delta > MAX_TIMEOUT:
            await ctx.send(embed=embeds.error("Timeouts can be at most 28 days.", "Too long"), ephemeral=True)
            return
        if problem := hierarchy_error(ctx, member):
            await ctx.send(embed=embeds.error(problem, "Can't time out"), ephemeral=True)
            return
        await member.timeout(delta, reason=audit_reason(ctx, reason))
        await ctx.send(embed=embeds.success(
            f"{member.mention} timed out for **{format_duration(delta)}**\n**Reason:** {reason}", "Member timed out"))

    @commands.hybrid_command(aliases=["unmute"], description="Remove a member's timeout.")
    @app_commands.default_permissions(moderate_members=True)
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def untimeout(self, ctx: commands.Context, member: discord.Member) -> None:
        """Remove a member's timeout."""
        if not member.is_timed_out():
            await ctx.send(embed=embeds.warning(f"{member.mention} isn't timed out."), ephemeral=True)
            return
        if problem := hierarchy_error(ctx, member):
            await ctx.send(embed=embeds.error(problem, "Can't remove timeout"), ephemeral=True)
            return
        await member.timeout(None, reason=audit_reason(ctx, "Timeout removed"))
        await ctx.send(embed=embeds.success(f"Removed the timeout for {member.mention}", "Timeout removed"))

    @commands.hybrid_command(aliases=["clear"], description="Delete recent messages (1-100).")
    @app_commands.default_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def purge(self, ctx: commands.Context, amount: commands.Range[int, 1, 100]) -> None:
        """Delete the last 1-100 messages in this channel (messages older than 14 days are skipped)."""
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
            deleted = await ctx.channel.purge(limit=amount)
            await ctx.send(embed=embeds.success(f"Deleted **{len(deleted)}** message(s)."), ephemeral=True)
        else:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 removes the command message too
            await ctx.send(embed=embeds.success(f"Deleted **{max(len(deleted) - 1, 0)}** message(s)."),
                           delete_after=5)

    @commands.hybrid_command(description="Set slowmode for this channel in seconds (0 to disable).")
    @app_commands.default_permissions(manage_channels=True)
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, seconds: commands.Range[int, 0, 21600]) -> None:
        """Set slowmode for this channel (0 turns it off, max 6 hours)."""
        if not isinstance(ctx.channel, discord.TextChannel):
            await ctx.send(embed=embeds.error("Slowmode only works in text channels."), ephemeral=True)
            return
        await ctx.channel.edit(slowmode_delay=seconds, reason=audit_reason(ctx, "Slowmode changed"))
        text = "Slowmode disabled." if seconds == 0 else f"Slowmode set to **{seconds}s**."
        await ctx.send(embed=embeds.success(text, "Slowmode updated"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))
