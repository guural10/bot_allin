from __future__ import annotations
import asyncio
import logging
from datetime import time
from zoneinfo import ZoneInfo
import discord
from discord.ext import commands, tasks
from config import settings
from services.member_data import get_all_members, member_record
from services.snapshots import save_snapshot, list_snapshots, load_snapshot, compare, format_daily_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.members = True


class AdminBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

    async def setup_hook(self):
        await self.load_extension("cogs.admin_data")
        if settings.guild_id:
            guild = discord.Object(id=settings.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()
        daily_snapshot.start()


bot = AdminBot()


@bot.event
async def on_ready():
    logger.info("Zalogowano jako %s (ID: %s)", bot.user, bot.user.id)
    logger.info(
        "Automatyczny snapshot: %02d:%02d (%s); kanał raportów: %s",
        settings.snapshot_hour,
        settings.snapshot_minute,
        settings.timezone,
        settings.report_channel_id or "wyłączony",
    )


@tasks.loop(time=time(settings.snapshot_hour, settings.snapshot_minute, tzinfo=ZoneInfo(settings.timezone)))
async def daily_snapshot():
    for guild in bot.guilds:
        try:
            previous_auto = list_snapshots(guild.id, kind="automatic")
            members = await get_all_members(guild)
            records = [member_record(m) for m in members]
            path = save_snapshot(guild.id, guild.name, records, kind="automatic")
            logger.info("Automatyczny snapshot %s: %s (%d członków)", guild.name, path.name, len(records))

            if not settings.report_channel_id:
                continue

            channel = guild.get_channel(settings.report_channel_id)
            if not isinstance(channel, discord.TextChannel):
                logger.warning("REPORT_CHANNEL_ID=%s nie wskazuje kanału tekstowego na serwerze %s", settings.report_channel_id, guild.name)
                continue

            if not previous_auto:
                await channel.send(
                    f"📸 **Pierwszy automatyczny snapshot — {guild.name}**\n"
                    f"Zapisano stan **{len(records)}** członków. Raport zmian pojawi się po następnym automatycznym snapshocie."
                )
                continue

            changes = compare(load_snapshot(previous_auto[-1]), load_snapshot(path))
            current = load_snapshot(path)
            for chunk in format_daily_report(guild.name, changes, current["created_at"], settings.timezone):
                await channel.send(chunk)
        except Exception:
            logger.exception("Nie udało się wykonać automatycznego snapshotu/raportu dla serwera %s", guild.name)


@daily_snapshot.before_loop
async def before_daily_snapshot():
    await bot.wait_until_ready()


async def main():
    if not settings.token:
        raise RuntimeError("Brak DISCORD_TOKEN w pliku .env")
    async with bot:
        await bot.start(settings.token)


if __name__ == "__main__":
    asyncio.run(main())
