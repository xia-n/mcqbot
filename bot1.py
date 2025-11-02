import discord
from discord.ext import commands
import json
import random
import asyncio
import os

# --- Intents ---
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

# --- Load Database ---
with open("database.json", "r", encoding="utf-8") as f:
    database = json.load(f)

# --- Leaderboard ---
LEADERBOARD_FILE = "leaderboard.json"
if os.path.exists(LEADERBOARD_FILE):
    with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
        leaderboard = json.load(f)
else:
    leaderboard = {}

def save_leaderboard():
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(leaderboard, f, indent=2)

# --- Settings (channel restriction) ---
SETTINGS_FILE = "settings.json"
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        settings = json.load(f)
else:
    settings = {}

def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

# --- Helper Functions ---
def pick_random_question():
    paper = random.choice(list(database.keys()))
    qkeys = list(database[paper]["questions"].keys())
    akeys = list(database[paper]["answers"].keys())

    qnum = random.choice(qkeys)
    qpath = database[paper]["questions"][qnum]

    # Safe modulus mapping
    q_index = int(qnum) % len(akeys)
    akey = akeys[q_index]
    ans = database[paper]["answers"][akey]["answer"]

    return paper, qnum, qpath, ans

# --- Emojis ---
emojis = ["🇦", "🇧", "🇨", "🇩"]
next_emojis = ["🇾", "🇳"]
stop_emoji = "❌"

# --- Solo Quiz Mode ---
async def ask_question(ctx, user_id):
    paper, qnum, qpath, correct = pick_random_question()
    file = discord.File(qpath, filename="q.png")
    msg = await ctx.send(content=f"**Question {qnum} ({paper})**\nReact 🇦 🇧 🇨 🇩 to answer.\nMods can react ❌ to stop.", file=file)

    for e in emojis + [stop_emoji]:
        await msg.add_reaction(e)

    stopped = False

    def check(reaction, user):
        nonlocal stopped
        if reaction.emoji == stop_emoji:
            if user.guild_permissions.manage_guild or user == ctx.guild.owner:
                stopped = True
                return True
        return reaction.emoji in emojis and user.id == user_id and reaction.message.id == msg.id

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=300, check=check)
        if stopped:
            await ctx.send("🛑 Quiz stopped by a moderator.")
            return

        answer = ["A", "B", "C", "D"][emojis.index(reaction.emoji)]
        if answer == correct:
            leaderboard.setdefault(str(user.id), {"points": 0, "wins": 0})
            leaderboard[str(user.id)]["points"] += 1
            save_leaderboard()
            await ctx.send(f"✅ Correct! You now have {leaderboard[str(user.id)]['points']} points.")
        else:
            await ctx.send(f"❌ Wrong! The correct answer was **{correct}**.")
    except asyncio.TimeoutError:
        await ctx.send("⏱️ Question expired silently.")
        return

    if stopped:
        return

    # Next question prompt
    next_msg = await ctx.send("React 🇾 for next question or 🇳 to stop. Mods can react ❌ to end quiz.")
    for e in next_emojis + [stop_emoji]:
        await next_msg.add_reaction(e)

    def next_check(reaction, user):
        nonlocal stopped
        if reaction.emoji == stop_emoji:
            if user.guild_permissions.manage_guild or user == ctx.guild.owner:
                stopped = True
                return True
        return reaction.emoji in next_emojis and user.id == user_id and reaction.message.id == next_msg.id

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=60, check=next_check)
        if stopped:
            await ctx.send("🛑 Quiz stopped by a moderator.")
            return
        if reaction.emoji == "🇾":
            await ask_question(ctx, user_id)
        else:
            await ctx.send("Thanks for playing! 👋")
    except asyncio.TimeoutError:
        await ctx.send("Session timed out.")

# --- Competitive Mode ---
async def competitive_mode(ctx):
    paper = random.choice(list(database.keys()))
    qkeys = list(database[paper]["questions"].keys())
    akeys = list(database[paper]["answers"].keys())
    scores = {}
    attempted_users = set()
    stopped = False

    await ctx.send(f"🏁 Competitive round started! Paper: **{paper}**\nMods can react ❌ at any question to stop.")

    for qnum in qkeys:
        if stopped:
            break

        qpath = database[paper]["questions"][qnum]
        q_index = int(qnum) % len(akeys)
        akey = akeys[q_index]
        correct = database[paper]["answers"][akey]["answer"]

        file = discord.File(qpath, filename="q.png")
        msg = await ctx.send(f"**Question {qnum}**\nReact 🇦 🇧 🇨 🇩 to answer.", file=file)

        for e in emojis + [stop_emoji]:
            await msg.add_reaction(e)

        def check(reaction, user):
            nonlocal stopped
            if reaction.emoji == stop_emoji:
                if user.guild_permissions.manage_guild or user == ctx.guild.owner:
                    stopped = True
                    return True
            return reaction.emoji in emojis and not user.bot and str(user.id) not in attempted_users and reaction.message.id == msg.id

        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60, check=check)
            if stopped:
                await ctx.send("🛑 Competitive quiz stopped by a moderator.")
                break

            attempted_users.add(str(user.id))
            answer = ["A", "B", "C", "D"][emojis.index(reaction.emoji)]
            if answer == correct:
                scores.setdefault(str(user.id), 0)
                scores[str(user.id)] += 1
                await ctx.send(f"{user.display_name} got it ✅!")
            else:
                await ctx.send(f"{user.display_name} got it ❌!")
        except asyncio.TimeoutError:
            await ctx.send(f"(Question {qnum} expired)")

    if stopped:
        await ctx.send("⚠️ Round stopped. Wins not counted. Points remain saved.")
        return

    if not scores:
        await ctx.send("No one answered correctly this round.")
        return

    # If not stopped, calculate winner
    winner_id, max_score = max(scores.items(), key=lambda x: x[1])
    leaderboard.setdefault(winner_id, {"points": 0, "wins": 0})
    leaderboard[winner_id]["wins"] += 1
    save_leaderboard()
    await ctx.send(f"🏆 Winner: <@{winner_id}> with {max_score} correct answers!")

# --- Commands ---
@bot.command()
@commands.has_permissions(manage_guild=True)
async def setquizchannel(ctx, channel: discord.TextChannel):
    """Set the channel where quizzes are allowed."""
    settings[str(ctx.guild.id)] = {"quiz_channel": channel.id}
    save_settings()
    await ctx.send(f"✅ Quiz channel set to {channel.mention}")

def check_channel(ctx):
    guild_id = str(ctx.guild.id)
    if guild_id in settings:
        allowed_channel = settings[guild_id]["quiz_channel"]
        if ctx.channel.id != allowed_channel:
            raise commands.CheckFailure(f"⚠️ You can only use quiz commands in <#{allowed_channel}>.")
    else:
        raise commands.CheckFailure("❌ This server hasn’t set a quiz channel yet. Ask a mod to use `/setquizchannel`.")

@bot.command()
@commands.check(check_channel)
async def quiz(ctx):
    """Start solo quiz mode."""
    await ask_question(ctx, ctx.author.id)

@bot.command()
@commands.check(check_channel)
async def competitive(ctx):
    """Start competitive mode for everyone."""
    await competitive_mode(ctx)

@bot.command()
async def leaderboard_cmd(ctx):
    """Show leaderboard."""
    if not leaderboard:
        await ctx.send("No data yet.")
        return
    msg = "\n".join(f"<@{uid}>: {data['points']} pts | {data['wins']} wins"
                    for uid, data in leaderboard.items())
    await ctx.send(f"🏅 **Leaderboard**:\n{msg}")

# --- Error Handling ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(str(error))
    else:
        raise error

# --- Run Bot ---
bot.run("TOKEN")
