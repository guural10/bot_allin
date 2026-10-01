from __future__ import annotations
import discord

async def get_all_members(guild: discord.Guild) -> list[discord.Member]:
    """Pobiera pełną listę członków z API Discorda."""
    return [member async for member in guild.fetch_members(limit=None)]

def member_record(member: discord.Member) -> dict:
    roles = [r for r in member.roles if not r.is_default()]
    roles.sort(key=lambda r: r.position, reverse=True)
    return {
        "discord_id": member.id,
        "username": member.name,
        "global_name": member.global_name or "",
        "display_name": member.display_name,
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        "account_created_at": member.created_at.isoformat(),
        "roles": [{"id": r.id, "name": r.name, "position": r.position} for r in roles],
        "role_count": len(roles),
        "is_bot": member.bot,
    }
