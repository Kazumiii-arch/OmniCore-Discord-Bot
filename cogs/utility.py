from typing import Optional

import discord
from discord.ext import commands

from utils import embeds

fmt = discord.utils.format_dt


class Utility(commands.Cog):
    """Handy server and user tools."""

    emoji = "🧰"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(aliases=["server", "si"], description="Show information about this server.")
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context) -> None:
        """Show information about this server."""
        g = ctx.guild
        embed = embeds.info(g.name, g.description)
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        embed.add_field(name="Owner", value=f"<@{g.owner_id}>")
        embed.add_field(name="Created", value=fmt(g.created_at, "R"))
        embed.add_field(name="Members", value=f"{g.member_count:,}")
        embed.add_field(name="Channels", value=f"💬 {len(g.text_channels)} · 🔊 {len(g.voice_channels)}")
        embed.add_field(name="Roles", value=str(len(g.roles) - 1))
        embed.add_field(name="Boosts", value=f"Level {g.premium_tier} · {g.premium_subscription_count or 0}")
        embed.set_footer(text=f"Server ID: {g.id}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=["whois", "ui"], description="Show information about a member.")
    @commands.guild_only()
    async def userinfo(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        """Show information about a member (defaults to you)."""
        member = member or ctx.author
        roles = [r.mention for r in reversed(member.roles) if r != ctx.guild.default_role]
        shown = " ".join(roles[:10]) + (f" +{len(roles) - 10} more" if len(roles) > 10 else "")

        embed = embeds.info(member.display_name, member.mention)
        if member.color.value:
            embed.color = member.color
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Username", value=str(member))
        embed.add_field(name="Account created", value=fmt(member.created_at, "R"))
        embed.add_field(name="Joined server", value=fmt(member.joined_at, "R") if member.joined_at else "Unknown")
        embed.add_field(name=f"Roles ({len(roles)})", value=shown or "None", inline=False)
        if member.bot:
            embed.add_field(name="Bot", value="🤖 Yes")
        embed.set_footer(text=f"User ID: {member.id}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=["av", "pfp"], description="Show someone's avatar.")
    async def avatar(self, ctx: commands.Context, user: Optional[discord.User] = None) -> None:
        """Show someone's avatar in full size (defaults to you)."""
        user = user or ctx.author
        embed = embeds.info(f"{user.display_name}'s avatar")
        embed.set_image(url=user.display_avatar.with_size(1024).url)
        embed.description = f"[Open original]({user.display_avatar.url})"
        await ctx.send(embed=embed)

    @commands.hybrid_command(description="Start a quick yes/no poll.")
    @commands.guild_only()
    @commands.bot_has_permissions(add_reactions=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def poll(self, ctx: commands.Context, *, question: str) -> None:
        """Start a quick 👍 / 👎 poll."""
        embed = embeds.info("📊  Poll", question[:4000])
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        message = await ctx.send(embed=embed)
        for emoji in ("👍", "👎"):
            await message.add_reaction(emoji)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Utility(bot))
