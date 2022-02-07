import asyncio
from typing import Optional, TYPE_CHECKING, Any

try:
    import nextcord
except ModuleNotFoundError:
    import disnake as nextcord

from . import channel

if TYPE_CHECKING:
    from bot_base import BotBase


class Meta:
    """
    Used to inject functionality into multiple
    class's and reduce code duplication
    """

    def __init__(self, wrapped_item, bot: "BotBase"):
        self._wrapped_item = wrapped_item
        self._wrapped_bot = bot

        if isinstance(wrapped_item, type(self)):
            self._wrapped_item = wrapped_item._wrapped_item

    # def __getattr__(self, item):
    #     attr = getattr(self._wrapped_item, item, MISSING)
    #     if attr is MISSING:
    #         raise AttributeError(item)
    #
    #     return attr

    # @property
    # def __class__(self):
    #     return type(self._wrapped_item)

    def __instancecheck__(self, instance):
        return isinstance(instance, type(self._wrapped_item))

    def __subclasscheck__(self, subclass):
        return issubclass(subclass, self._wrapped_item)

    def __eq__(self, other: Any) -> bool:
        """
        If other is not of this type, or the type
        we wrap its False.
        If other is not us, but what we wrap then
        compare them as applicable.
        If other is same type as us, compare
        what we both wrap.
        """
        if not isinstance(other, (type(self._wrapped_item), type(self))):
            return False

        if isinstance(other, type(self._wrapped_item)):
            return other.id == self._wrapped_item.id

        return other._wrapped_item.id == self._wrapped_item.id

    def __hash__(self):
        return hash(self._wrapped_item)

    async def prompt(
        self,
        message: str,
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
        fmt = f"{message}\n\nReact with \N{WHITE HEAVY CHECK MARK} to confirm or \N{CROSS MARK} to deny."

        # Ensure we can gather author id
        try:
            author_id = (
                author_id or self.author.id or self.id
            )  # self.id for User/Member
        except AttributeError:
            if issubclass(type(self), channel.WrappedChannel):
                raise RuntimeError(
                    "Expected author_id when using prompt on a TextChannel"
                )

            author_id = self.id

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
            await self._wrapped_bot.wait_for(
                "raw_reaction_add", check=check, timeout=timeout
            )
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
        reply: bool = False,
        contain_timestamp: bool = True,
        include_command_invoker: bool = True,
        **kwargs,
    ) -> nextcord.Message:
        """Wraps a string to send formatted as an embed"""
        from bot_base.context import BotContext

        target = target or (
            self.message  # ctx, reply=True
            if reply and isinstance(self, BotContext)
            else self.channel  # ctx, reply=False
            if isinstance(self, BotContext)
            else self  # Anything else (member.send)
        )

        embed = nextcord.Embed(description=desc)

        if color:
            embed.colour = color

        if contain_timestamp and isinstance(self, BotContext):
            # Doesnt work on Channels, Users, Members
            embed.timestamp = self.message.created_at

        if include_command_invoker and not isinstance(self, channel.WrappedChannel):
            try:
                text = self.author.display_name
                icon_url = self.author.avatar.url
            except AttributeError:
                text = self.display_name
                icon_url = self.avatar.url

            embed.set_footer(text=text, icon_url=icon_url)

        if reply and isinstance(target, nextcord.Message):
            return await target.reply(embed=embed, **kwargs)
        else:
            return await target.send(embed=embed, **kwargs)

    async def get_input(
        self,
        title: str = None,
        description: str = None,
        *,
        timeout: int = 100,
        delete_after: bool = True,
        author_id=None,
    ) -> Optional[str]:
        from bot_base.context import BotContext

        if title and not description:
            embed = nextcord.Embed(
                title=title,
            )
        elif not title and description:
            embed = nextcord.Embed(
                description=description,
            )
        elif title and description:
            embed = nextcord.Embed(
                title=title,
                description=description,
            )
        else:
            raise RuntimeError("Expected at-least title or description")

        sent = await self.send(embed=embed)
        val = None

        try:
            author_id = (
                author_id or self.author.id or self.id
            )  # or self.id for User/Member
        except AttributeError:
            if issubclass(type(self), channel.WrappedChannel):
                raise RuntimeError(
                    "Expected author_id when using prompt on a TextChannel"
                )

            author_id = self.id

        try:
            if issubclass(type(self), channel.WrappedChannel):
                check = (
                    lambda message: message.author.id == author_id
                    and message.channel.id == self.id,
                )
            elif isinstance(self, BotContext):
                if not self.guild:
                    check = (
                        lambda message: message.author.id == author_id
                        and not message.guild
                    )
                else:
                    check = (
                        lambda message: message.author.id == author_id
                        and message.channel.id == self.channel.id
                    )
            else:
                check = (
                    lambda message: message.author.id == author_id and not message.guild
                )

            msg = await self._wrapped_bot.wait_for(
                "message", timeout=timeout, check=check
            )

            if msg:
                val = msg.content
        except asyncio.TimeoutError:
            if delete_after:
                await sent.delete()

            return val

        try:
            if delete_after:
                await sent.delete()
                await msg.delete()
        finally:
            return val
