from __future__ import annotations
import discord


def visible_channels_for_member(guild: discord.Guild, member: discord.Member) -> list[discord.abc.GuildChannel]:
    """Return guild channels the member can view according to Discord permission resolution."""
    channels = []
    for channel in guild.channels:
        if isinstance(channel, discord.CategoryChannel):
            continue
        try:
            if channel.permissions_for(member).view_channel:
                channels.append(channel)
        except (AttributeError, TypeError):
            continue
    return sorted(channels, key=lambda c: (c.category.position if c.category else -1, c.position, c.name.casefold()))


def members_with_channel_access(channel: discord.abc.GuildChannel) -> list[discord.Member]:
    members = [m for m in channel.guild.members if channel.permissions_for(m).view_channel]
    return sorted(members, key=lambda m: m.display_name.casefold())


def channel_label(channel: discord.abc.GuildChannel) -> str:
    category = channel.category.name if getattr(channel, "category", None) else "Bez kategorii"
    return f"{category} / {channel.name}"
