import os
import asyncio
import logging

import disnake as disnake

from bot_base import BotBase

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def main():
    bot = BotBase(
        command_prefix="t.",
        mongo_url=os.environ["MONGO_URL"],
        mongo_database_name="my_bot",
        load_builtin_commands=True,
        load_invite_tracking=True,
        intents=disnake.Intents.all(),
    )

    @bot.event
    async def on_ready():
        log.info("I'm up")

    @bot.command()
    async def echo(ctx):
        await ctx.message.delete()

        text = await ctx.get_input("What should I say?", timeout=5)

        if not text:
            return await ctx.send("You said nothing!")

        await ctx.send(text)

    @bot.command()
    async def ping(ctx):
        await ctx.send_basic_embed("Pong!")

    await bot.start(os.environ["TOKEN"])


asyncio.run(main())
