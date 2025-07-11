from discord.ext import commands

class Community(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def level(self, ctx):
        """Checks your current level (placeholder)."""
        await ctx.send(f"{ctx.author.mention}, you are currently level 1! (Feature coming soon!)")

async def setup(bot):
    await bot.add_cog(Community(bot))
