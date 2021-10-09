from typing import Optional

import discord

from . import channel


# noinspection PyUnresolvedReferences
class Meta:
    """
    Used to inject functionality into multiple
    class's and reduce code duplication
    """

    async def prompt(
        self,
        message,
        *,
        timeout=60.0,
        delete_after=True,
        author_id=None,
    ):
        """An interactive reaction confirmation dialog.
        Parameters
        -----------
        message: str
            The message to show along with the prompt.
        timeout: float
            How long to wait before returning.
        delete_after: bool
            Whether to delete the confirmation message after we're done.
        author_id: Optional[int]
            The member who should respond to the prompt. Defaults to the author of the
            Context's message.
        Returns
        --------
        Optional[bool]
            ``True`` if explicit confirm,
            ``False`` if explicit deny,
            ``None`` if deny due to timeout

        Taken from R.Danny
        """
        if not self.channel.permissions_for(self.me).add_reactions:
            raise RuntimeError("Bot does not have Add Reactions permission.")
        fmt = f"{message}\n\nReact with \N{WHITE HEAVY CHECK MARK} to confirm or \N{CROSS MARK} to deny."

        # Ensure we can gather author id
        try:
            author_id = author_id or self.author.id
        except AttributeError:
            if issubclass(type(self), channel.WrappedChannel):
                raise RuntimeError(
                    "Expected author_id when using prompt on a TextChannel"
                )

        msg = await self.send(fmt)
        confirm = None

        def check(payload):
            nonlocal confirm
            if payload.message_id != msg.id or payload.user_id != author_id:
                return False
            codepoint = str(payload.emoji)
            if codepoint == "\N{WHITE HEAVY CHECK MARK}":
                confirm = True
                return True
            elif codepoint == "\N{CROSS MARK}":
                confirm = False
                return True
            return False

        for emoji in ("\N{WHITE HEAVY CHECK MARK}", "\N{CROSS MARK}"):
            await msg.add_reaction(emoji)
        try:
            await self.bot.wait_for("raw_reaction_add", check=check, timeout=timeout)
        except asyncio.TimeoutError:
            confirm = None
        try:
            if delete_after:
                await msg.delete()
        finally:
            return confirm

    async def send_basic_embed(
        self,
        desc: str,
        *,
        color=None,
        target=None,
        contain_timestamp: bool = True,
        include_command_invoker: bool = True,
    ):
        """Wraps a string to send formatted as an embed"""
        target = target or self.channel

        embed = discord.Embed(description=desc)

        if color:
            embed.colour = color

        if contain_timestamp and not isinstance(self, channel.WrappedChannel):
            embed.timestamp = self.message.created_at

        if include_command_invoker and not isinstance(self, channel.WrappedChannel):
            embed.set_footer(
                text=self.author.display_name, icon_url=self.author.avatar_url
            )

        return await target.send(embed=embed)

    async def get_input(
        self,
        contentOne: int = "Please enter your desired input",
        contentTwo: int = "\uFEFF",
        *,
        timeout: int = 100,
        delete_after: bool = True,
        author_id=None,
    ) -> Optional[str]:
        embed = discord.Embed(
            title=f"{contentOne}",
            description=f"{contentTwo}",
        )
        sent = await self.send(embed=embed)
        val = None

        try:
            author_id = author_id or self.author.id
        except AttributeError:
            if issubclass(type(self), channel.WrappedChannel):
                raise RuntimeError(
                    "Expected author_id when using prompt on a TextChannel"
                )

        try:
            msg = await self.bot.wait_for(
                "message",
                timeout=timeout,
                check=lambda message: message.author.id == author_id,
            )
            if msg:
                val = msg.content
        except asyncio.TimeoutError:
            return val

        try:
            if delete_after:
                await sent.delete()
                await msg.delete()
        finally:
            return val
