import logging
import os

from bot_base import BotBase

bot = BotBase(
    command_prefix="!", mongo_url=os.environ["MONGO_URL"], mongo_database_name="my_bot"
)

logging.basicConfig(level=logging.INFO)


@bot.event
async def on_ready():
    print("We oN!")


@bot.command()
async def test(ctx):
    await ctx.channel.send_basic_embed(f"I am a custom method mwahahaah!")


bot.run(os.environ["TOKEN"])
