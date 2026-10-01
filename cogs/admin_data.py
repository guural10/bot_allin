from __future__ import annotations
import logging
import discord
from discord import app_commands
from discord.ext import commands
from services.member_data import get_all_members, member_record
from services.excel_export import export_members_xlsx, export_roles_xlsx, export_changes_xlsx, export_access_xlsx
from services.snapshots import save_snapshot, list_snapshots, load_snapshot, compare
from services.access_audit import visible_channels_for_member, members_with_channel_access

logger = logging.getLogger(__name__)

async def admin_only(interaction: discord.Interaction) -> bool:
    return bool(interaction.user.guild_permissions.administrator)

class AdminData(commands.Cog):
    def __init__(self, bot: commands.Bot): self.bot = bot

    async def records(self, guild: discord.Guild):
        return [member_record(m) for m in await get_all_members(guild)]

    @app_commands.command(name="export_members", description="Eksportuje wszystkich członków serwera do XLSX.")
    @app_commands.check(admin_only)
    async def export_members(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        records = await self.records(interaction.guild)
        path = export_members_xlsx(interaction.guild.name, records)
        await interaction.followup.send(f"Gotowe: {len(records)} członków.", file=discord.File(path), ephemeral=True)

    @app_commands.command(name="export_roles", description="Eksportuje role i relację użytkownik–rola do XLSX.")
    @app_commands.check(admin_only)
    async def export_roles(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        records = await self.records(interaction.guild)
        path = export_roles_xlsx(interaction.guild.roles, records)
        await interaction.followup.send("Gotowe.", file=discord.File(path), ephemeral=True)

    @app_commands.command(name="role_members", description="Pokazuje członków posiadających wskazaną rolę.")
    @app_commands.describe(role="Rola do sprawdzenia")
    @app_commands.check(admin_only)
    async def role_members(self, interaction: discord.Interaction, role: discord.Role):
        members = sorted(role.members, key=lambda m: m.display_name.casefold())
        text = "\n".join(f"• {m.display_name} (@{m.name}) — `{m.id}`" for m in members) or "Brak członków."
        if len(text) > 1800:
            text = text[:1800] + "\n…\nUżyj /export_roles, aby otrzymać pełną listę."
        await interaction.response.send_message(f"**{role.name} — {len(members)} osób**\n{text}", ephemeral=True)

    @app_commands.command(name="missing_role", description="Pokazuje członków bez wskazanej roli.")
    @app_commands.describe(role="Rola do sprawdzenia")
    @app_commands.check(admin_only)
    async def missing_role(self, interaction: discord.Interaction, role: discord.Role):
        members = sorted((m for m in interaction.guild.members if role not in m.roles), key=lambda m: m.display_name.casefold())
        text = "\n".join(f"• {m.display_name} (@{m.name})" for m in members) or "Wszyscy mają tę rolę."
        if len(text) > 1800: text = text[:1800] + "\n…"
        await interaction.response.send_message(f"**Bez roli {role.name} — {len(members)} osób**\n{text}", ephemeral=True)

    @app_commands.command(name="member", description="Pokazuje dane członka serwera.")
    @app_commands.describe(member="Członek serwera")
    @app_commands.check(admin_only)
    async def member(self, interaction: discord.Interaction, member: discord.Member):
        roles = [r.name for r in member.roles if not r.is_default()]
        embed = discord.Embed(title=member.display_name)
        embed.add_field(name="Username", value=member.name, inline=True)
        embed.add_field(name="Discord ID", value=str(member.id), inline=True)
        embed.add_field(name="Konto od", value=discord.utils.format_dt(member.created_at, "F"), inline=False)
        embed.add_field(name="Na serwerze od", value=discord.utils.format_dt(member.joined_at, "F") if member.joined_at else "brak danych", inline=False)
        embed.add_field(name=f"Role ({len(roles)})", value="; ".join(roles) or "brak", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="stats", description="Podstawowe statystyki członków i ról.")
    @app_commands.check(admin_only)
    async def stats(self, interaction: discord.Interaction):
        g = interaction.guild
        humans = sum(not m.bot for m in g.members)
        bots = sum(m.bot for m in g.members)
        no_roles = sum(len(m.roles) == 1 for m in g.members)
        await interaction.response.send_message(
            f"**{g.name}**\nCzłonkowie: **{g.member_count}**\nLudzie: **{humans}**\nBoty: **{bots}**\nRole (bez @everyone): **{len(g.roles)-1}**\nBez dodatkowej roli: **{no_roles}**",
            ephemeral=True)

    @app_commands.command(name="snapshot", description="Zapisuje aktualny snapshot członków i ról.")
    @app_commands.check(admin_only)
    async def snapshot(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        records = await self.records(interaction.guild)
        path = save_snapshot(interaction.guild.id, interaction.guild.name, records, kind="manual")
        await interaction.followup.send(f"Snapshot zapisany: `{path.name}` ({len(records)} członków).", ephemeral=True)

    @app_commands.command(name="changes", description="Porównuje dwa ostatnie snapshoty i generuje XLSX.")
    @app_commands.check(admin_only)
    async def changes(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        paths = list_snapshots(interaction.guild.id)
        if len(paths) < 2:
            await interaction.followup.send("Potrzebuję co najmniej dwóch snapshotów. Użyj /snapshot dwa razy w różnych momentach.", ephemeral=True)
            return
        changes = compare(load_snapshot(paths[-2]), load_snapshot(paths[-1]))
        path = export_changes_xlsx(changes)
        summary = f"Dołączyli: **{len(changes['joined'])}** | Odeszli: **{len(changes['left'])}** | Zmiany ról: **{len(changes['role_changes'])}**"
        await interaction.followup.send(summary, file=discord.File(path), ephemeral=True)

    @app_commands.command(name="access", description="Pokazuje kanały, które wskazany użytkownik może zobaczyć.")
    @app_commands.describe(member="Członek serwera")
    @app_commands.check(admin_only)
    async def access(self, interaction: discord.Interaction, member: discord.Member):
        channels = visible_channels_for_member(interaction.guild, member)
        groups: dict[str, list[str]] = {}
        for channel in channels:
            category = channel.category.name if channel.category else "Bez kategorii"
            groups.setdefault(category, []).append(f"• {channel.mention if hasattr(channel, 'mention') else channel.name}")
        lines = [f"**Dostęp: {member.display_name} (@{member.name}) — {len(channels)} kanałów**"]
        for category, items in groups.items():
            lines.append(f"\n**{category}**")
            lines.extend(items)
        text = "\n".join(lines)
        if len(text) > 1900:
            text = text[:1850] + "\n…\nPełny obraz dostępu pobierzesz przez `/export_access`."
        await interaction.response.send_message(text, ephemeral=True)

    @app_commands.command(name="channel_access", description="Pokazuje użytkowników, którzy mogą zobaczyć wskazany kanał.")
    @app_commands.describe(channel="Kanał do sprawdzenia")
    @app_commands.check(admin_only)
    async def channel_access(self, interaction: discord.Interaction, channel: discord.TextChannel):
        members = members_with_channel_access(channel)
        text = "\n".join(f"• {m.display_name} (@{m.name}) — `{m.id}`" for m in members) or "Brak użytkowników z dostępem."
        if len(text) > 1800:
            text = text[:1750] + "\n…\nPełną listę pobierzesz przez `/export_access`."
        await interaction.response.send_message(f"**Dostęp do #{channel.name} — {len(members)} osób**\n{text}", ephemeral=True)

    @app_commands.command(name="export_access", description="Eksportuje efektywny dostęp użytkowników do kanałów do XLSX.")
    @app_commands.check(admin_only)
    async def export_access(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        path = export_access_xlsx(interaction.guild)
        await interaction.followup.send(
            "Gotowe. Arkusz `Access Matrix` pokazuje użytkownik × kanał, a `Access List` pełną relację.",
            file=discord.File(path), ephemeral=True
        )

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            msg = "Ta komenda jest dostępna tylko dla administratorów serwera."
            if interaction.response.is_done(): await interaction.followup.send(msg, ephemeral=True)
            else: await interaction.response.send_message(msg, ephemeral=True)
            return
        logger.exception("Błąd komendy %s", getattr(interaction.command, "name", "unknown"), exc_info=error)
        msg = "❌ Nie udało się wykonać komendy. Szczegóły błędu zostały zapisane w Terminalu."
        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except discord.HTTPException:
            logger.exception("Nie udało się wysłać komunikatu o błędzie na Discordzie.")

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminData(bot))
