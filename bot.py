import asyncio
import contextlib
import io
import logging
import os
import textwrap
from traceback import format_exception

import disnake as disnake
from disnake.ext import commands

from bot_base import BotBase
from bot_base.paginators.disnake_paginator import DisnakePaginator

logging.basicConfig(level=logging.INFO)
logging.getLogger("bot_base.cogs.invite_tracking").setLevel(logging.DEBUG)


async def main():
    bot = BotBase(
        command_prefix="t.",
        mongo_url=os.environ["MONGO_URL"],
        mongo_database_name="my_bot",
        load_builtin_commands=True,
        intents=disnake.Intents.all(),
    )

    @bot.event
    async def on_ready():
        print("I'm up.")

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

    def clean_code(content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:])[:-3]
        else:
            return content

    @bot.command(name="eval", aliases=["exec"])
    @commands.is_owner()
    async def _eval(ctx, *, code):
        """
        Evaluates given code.
        """
        code = clean_code(code)

        local_variables = {
            "commands": commands,
            "bot": bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
        }

        stdout = io.StringIO()

        try:
            with contextlib.redirect_stdout(stdout):
                exec(
                    f"async def func():\n{textwrap.indent(code, '    ')}",
                    local_variables,
                )

                obj = await local_variables["func"]()
                result = f"{stdout.getvalue()}\n-- {obj}\n"

        except Exception as e:
            result = "".join(format_exception(e, e, e.__traceback__))

        async def format_page(code, page_number):
            embed = disnake.Embed(title=f"Eval for {ctx.author.name}")
            embed.description = f"```{code}```"

            embed.set_footer(text=f"Page {page_number}")
            return embed

        paginator: DisnakePaginator = DisnakePaginator(
            1,
            [result[i : i + 2000] for i in range(0, len(result), 2000)],
        )
        paginator.format_page = format_page
        await paginator.start(context=ctx)

    bot.load_extension("bot_base.cogs.invite_tracking")
    await bot.start(os.environ["TOKEN"])


asyncio.run(main())
