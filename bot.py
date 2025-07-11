import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Bot Configuration ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OWNER_IDS = [int(id) for id in os.getenv("OWNER_IDS", "").split(',') if id]
COGS_DIR = "cogs"

class OmniCore(commands.Bot):
    """The main Bot class for OmniCore."""
    def __init__(self):
        # Define intents required for the bot's features
        intents = discord.Intents.default()
        intents.message_content = True  # Required for message content-based commands/features
        intents.members = True          # Required for tracking member joins/leaves and roles
        intents.reactions = True        # Required for reaction roles/polls
        
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"), # Or your preferred prefix
            intents=intents,
            help_command=None, # We can create a custom one later
            case_insensitive=True
        )
        self.owner_ids = OWNER_IDS

    async def setup_hook(self):
        """This is called when the bot is preparing to start up."""
        print("--- Loading Cogs ---")
        for filename in os.listdir(COGS_DIR):
            # Load all .py files in the cogs directory, excluding __init__.py
            if filename.endswith(".py") and filename != "__init__.py":
                cog_name = f"{COGS_DIR}.{filename[:-3]}"
                try:
                    await self.load_extension(cog_name)
                    print(f"✅ Loaded Cog: {cog_name}")
                except Exception as e:
                    print(f"❌ Failed to load cog {cog_name}: {e}")
        
        # You can add database connection setup here later
        # await self.connect_database()
        
    async def on_ready(self):
        """Event that fires when the bot is fully connected and ready."""
        print("--- Bot is Online ---")
        print(f"Logged in as: {self.user.name} | {self.user.id}")
        print(f"Discord.py Version: {discord.__version__}")
        print(f"Serving {len(self.guilds)} guilds.")
        print("-----------------------")
        
        # Set a custom presence
        await self.change_presence(activity=discord.Game(name="!help | OmniCore"))

    # You might want a global error handler
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return # Don't send a message for commands that don't exist
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing a required argument. Use `!help {ctx.command.name}` for info.")
        elif isinstance(error, commands.NotOwner):
            await ctx.send("You do not have permission to use this command.")
        else:
            print(f"An unhandled error occurred: {error}")
            await ctx.send("An unexpected error occurred. Please try again later.")

async def main():
    """Main function to create and run the bot."""
    bot = OmniCore()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
