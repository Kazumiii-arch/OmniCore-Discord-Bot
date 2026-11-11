import logging
import time

import discord
from discord.ext import commands, tasks

from utils import embeds
from utils.storage import JsonStore
from utils.timefmt import parse_duration

MAX_REMINDERS_PER_USER = 25
MAX_DAYS = 365

logger = logging.getLogger("OmniCore.reminders")


class Productivity(commands.Cog):
    """Reminders that survive restarts."""

    emoji = "⏰"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.store = JsonStore(bot.data_dir / "reminders.json", default={"next_id": 1, "reminders": []})

    @property
    def items(self) -> list:
        return self.store.data["reminders"]

    async def cog_load(self) -> None:
        self.check_reminders.start()

    async def cog_unload(self) -> None:
        self.check_reminders.cancel()

    @tasks.loop(seconds=15)
    async def check_reminders(self) -> None:
        now = time.time()
        due = [r for r in self.items if r["due"] <= now]
        if not due:
            return
        for reminder in due:
            self.items.remove(reminder)
            try:
                await self._deliver(reminder)
            except Exception:  # never let one bad reminder stop the loop
                logger.exception("Failed to deliver reminder %s", reminder.get("id"))
        await self.store.save()

    @check_reminders.before_loop
    async def _wait_ready(self) -> None:
        await self.bot.wait_until_ready()

    async def _deliver(self, reminder: dict) -> None:
        embed = embeds.info("⏰  Reminder", reminder["text"])
        if reminder.get("created"):
            embed.add_field(name="Set", value=f"<t:{int(reminder['created'])}:R>")
        mention = f"<@{reminder['user_id']}>"
        channel = self.bot.get_channel(reminder["channel_id"])
        try:
            if channel is not None:
                await channel.send(mention, embed=embed)
                return
        except discord.HTTPException:
            pass
        try:  # fall back to DM if the channel is gone or locked
            user = await self.bot.fetch_user(reminder["user_id"])
            await user.send(embed=embed)
        except discord.HTTPException:
            pass

    @commands.hybrid_command(aliases=["remindme"], description="Set a reminder, e.g. 10m take a break.")
    async def remind(self, ctx: commands.Context, duration: str, *, text: str) -> None:
        """Set a reminder. Example: `remind 1h30m check the oven`"""
        delta = parse_duration(duration)
        if delta is None:
            await ctx.send(embed=embeds.error("Use a duration like `10m`, `2h`, `1d` or `1h30m`.",
                                              "Invalid duration"), ephemeral=True)
            return
        if delta.days > MAX_DAYS:
            await ctx.send(embed=embeds.error(f"Reminders can be at most {MAX_DAYS} days away."), ephemeral=True)
            return
        if sum(r["user_id"] == ctx.author.id for r in self.items) >= MAX_REMINDERS_PER_USER:
            await ctx.send(embed=embeds.error(f"You already have {MAX_REMINDERS_PER_USER} reminders."),
                           ephemeral=True)
            return

        due = time.time() + delta.total_seconds()
        reminder_id = self.store.data["next_id"]
        self.store.data["next_id"] += 1
        self.items.append({
            "id": reminder_id,
            "user_id": ctx.author.id,
            "channel_id": ctx.channel.id,
            "created": time.time(),
            "due": due,
            "text": text[:1500],
        })
        await self.store.save()
        when = discord.utils.format_dt(discord.utils.utcnow() + delta, "R")
        await ctx.send(embed=embeds.success(f"I'll remind you {when}.\n> {text[:200]}", f"Reminder #{reminder_id} set"))

    @commands.hybrid_command(description="List your upcoming reminders.")
    async def reminders(self, ctx: commands.Context) -> None:
        """List your upcoming reminders."""
        mine = sorted((r for r in self.items if r["user_id"] == ctx.author.id), key=lambda r: r["due"])
        if not mine:
            await ctx.send(embed=embeds.warning("You have no upcoming reminders."), ephemeral=True)
            return
        lines = [f"`#{r['id']}` <t:{int(r['due'])}:R> · {r['text'][:80]}" for r in mine]
        embed = embeds.info("⏰  Your reminders", "\n".join(lines))
        embed.set_footer(text=f"{ctx.clean_prefix}cancelreminder <id> to remove one · OmniCore")
        await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(aliases=["delreminder"], description="Cancel one of your reminders.")
    async def cancelreminder(self, ctx: commands.Context, reminder_id: int) -> None:
        """Cancel one of your reminders by its ID."""
        for r in self.items:
            if r["id"] == reminder_id and r["user_id"] == ctx.author.id:
                self.items.remove(r)
                await self.store.save()
                await ctx.send(embed=embeds.success(f"Cancelled reminder #{reminder_id}."), ephemeral=True)
                return
        await ctx.send(embed=embeds.error(f"You don't have a reminder #{reminder_id}."), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Productivity(bot))
