# OmniCore Discord Bot

OmniCore is an all-in-one Discord bot for moderation, utility, leveling and reminders. Every command works as both a prefix command (`!ping`) and a slash command (`/ping`), and every reply uses clean, color-coded embeds.

## Features

- **Moderation**: kick, ban, unban, timeout, purge and slowmode, with role-hierarchy checks so moderators can't act on people above them.
- **Utility**: server info, user info, avatars and quick polls.
- **Leveling**: members earn XP for chatting (once per minute to stop spam), with level-up messages, `/rank` progress bars and a top-10 leaderboard.
- **Reminders**: `/remind 2h stretch`, saved to disk so they survive restarts.
- **Stats**: uptime, servers, latency and most-used commands.
- **Smart help**: `/help` only lists the commands *you* can use.
- **Safe by default**: friendly error messages, and user text can never ping `@everyone` or roles.

## Setup

Requires **Python 3.9+**.

### 1. Create the bot in Discord
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications), create an application and open **Bot**.
2. Click **Reset Token** and copy it.
3. Under **Privileged Gateway Intents**, turn on **Server Members Intent** and **Message Content Intent**.
4. Under **OAuth2 → URL Generator**, tick `bot` and `applications.commands`, then the permissions: Kick Members, Ban Members, Moderate Members, Manage Messages, Manage Channels, Read Message History, Add Reactions, Embed Links, Send Messages. Open the URL to invite the bot.
5. In your server's role settings, drag the bot's role **above** the roles it should moderate.

### 2. Install
```bash
git clone https://github.com/Kazumiii-arch/OmniCore-Discord-Bot.git
cd OmniCore-Discord-Bot
python -m venv venv
# Windows: venv\Scripts\activate    macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure
Copy `.env.example` to `.env` and fill it in:
```env
DISCORD_BOT_TOKEN=your_token_here
OWNER_IDS=            # optional, comma-separated user IDs
BOT_PREFIX=!
LOG_LEVEL=INFO
```

### 4. Run
```bash
python bot.py
```
Then, in your server, run `!sync here` once to register slash commands instantly (or `!sync` for all servers, which can take up to an hour).

## Commands

| Category | Command | What it does |
|---|---|---|
| 🧭 Core | `help [command]` | List commands or show details for one |
| | `ping` | Bot latency |
| | `about` | Bot info and uptime |
| | `sync [here]` | *Owner only.* Register slash commands |
| 🛡️ Moderation | `kick <member> [reason]` | Kick a member |
| | `ban <member> [reason]` | Ban a member (deletes their last 24h of messages) |
| | `unban <user id> [reason]` | Unban a user |
| | `timeout <member> <duration> [reason]` | Time out, e.g. `10m`, `2h`, `1d` (max 28d). Alias `mute` |
| | `untimeout <member>` | Remove a timeout. Alias `unmute` |
| | `purge <1-100>` | Bulk-delete messages. Alias `clear` |
| | `slowmode <seconds>` | Set channel slowmode (0 = off) |
| 🧰 Utility | `serverinfo` | Server details |
| | `userinfo [member]` | Member details |
| | `avatar [user]` | Full-size avatar |
| | `poll <question>` | 👍 / 👎 poll |
| 🏆 Community | `rank [member]` | Level and XP progress. Alias `level` |
| | `leaderboard` | Server top 10. Alias `lb` |
| ⏰ Productivity | `remind <duration> <text>` | Set a reminder |
| | `reminders` | List your reminders |
| | `cancelreminder <id>` | Cancel a reminder |
| 📈 Analytics | `stats` | Usage statistics |

## Project structure

```text
OmniCore-Discord-Bot/
├── bot.py            # startup, intents, global error handling
├── cogs/             # one file per command category (auto-loaded)
├── utils/            # embed styles, JSON storage, duration parsing
├── data/             # created at runtime: levels.json, reminders.json
├── .env.example
└── requirements.txt
```

To add a feature, drop a new file in `cogs/` with an `async def setup(bot)` function; it's loaded automatically.

## Troubleshooting

- **"Enable Server Members Intent..."** in the logs: turn on both privileged intents (step 1.3).
- **Slash commands don't appear**: run `!sync here`, then restart your Discord client.
- **"My highest role must be above..."**: move the bot's role higher in Server Settings → Roles.

## License

MIT. See [LICENSE](LICENSE).
