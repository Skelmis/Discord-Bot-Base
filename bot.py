import logging
import os

from bot_base import BotBase

bot = BotBase(
    command_prefix="!", mongo_url=os.environ["MONGO_URL"], mongo_database_name="my_bot"
)

logging.basicConfig(level=logging.INFO)


@bot.event
async def on_ready():
    print("I'm up.")


@bot.command()
async def echo(ctx):
    await ctx.delete()

    text = await ctx.get_input("What should I say?")

    if not text:
        return await ctx.send("You said nothing!")

    await ctx.send(text)


bot.run(os.environ["TOKEN"])
