# OmniCore Discord Bot

OmniCore is an all-in-one Discord bot for moderation, utility, and community management. It is designed to be clean to run, easy to extend, and ready for real server use.

## Highlights

- Moderation tools for day-to-day server management
- Utility commands for quick server assistance
- Community features for engagement and retention
- A cleaner startup path with safer configuration handling
- Easy extension loading through cogs
- Basic built-in commands such as `ping`, `about`, and owner-only command sync

## Getting Started

### 1) Clone the repository
```bash
git clone https://github.com/Kazumiii-arch/OmniCore-Discord-Bot.git
cd OmniCore-Discord-Bot
```

### 2) Create a virtual environment and install dependencies
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3) Configure environment variables
Create a `.env` file in the project root and add:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
OWNER_IDS=123456789012345678,234567890123456789
LOG_LEVEL=INFO
```

### 4) Run the bot
```bash
python bot.py
```

## Included Commands

- `!ping` — shows latency
- `!about` — shows a clean bot info card
- `!sync` — syncs application commands for the bot owner

## Project Structure

```text
OmniCore-Discord-Bot/
├── bot.py
├── cogs/
├── requirements.txt
└── README.md
```

## Planned Expansion Ideas

- Slash command framework for modern Discord UX
- Moderation logs and audit helpers
- Ticketing and support workflows
- Reaction roles and onboarding tools
- Scheduled announcements and reminders
- Persistent configuration storage
- Server analytics and usage insights

## Notes

- The bot now fails fast if `DISCORD_BOT_TOKEN` is missing.
- Missing `cogs/` folders are handled safely during startup.
- Logs are written in a structured format for easier debugging.

## Contributing

Pull requests are welcome. Keep changes focused, documented, and testable.

## License

This project is licensed under the MIT License.