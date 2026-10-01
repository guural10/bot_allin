from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SNAPSHOT_DIR = Path("data/snapshots")
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def save_snapshot(guild_id: int, guild_name: str, records: list[dict], *, kind: str = "manual") -> Path:
    now_utc = datetime.now(timezone.utc)
    payload = {
        "guild_id": guild_id,
        "guild_name": guild_name,
        "created_at": now_utc.isoformat(),
        "kind": kind,
        "members": records,
    }
    path = SNAPSHOT_DIR / f"{guild_id}_{now_utc:%Y-%m-%d_%H-%M-%S-%f}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def list_snapshots(guild_id: int, *, kind: str | None = None) -> list[Path]:
    paths = sorted(SNAPSHOT_DIR.glob(f"{guild_id}_*.json"))
    if kind is None:
        return paths
    result: list[Path] = []
    for path in paths:
        try:
            if load_snapshot(path).get("kind", "manual") == kind:
                result.append(path)
        except (OSError, json.JSONDecodeError):
            continue
    return result


def load_snapshot(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compare(old: dict, new: dict) -> dict:
    old_map = {str(m["discord_id"]): m for m in old["members"]}
    new_map = {str(m["discord_id"]): m for m in new["members"]}

    joined = sorted(
        (new_map[i] for i in new_map.keys() - old_map.keys()),
        key=lambda m: (m.get("display_name") or m.get("username") or "").casefold(),
    )
    left = sorted(
        (old_map[i] for i in old_map.keys() - new_map.keys()),
        key=lambda m: (m.get("display_name") or m.get("username") or "").casefold(),
    )

    role_changes = []
    for i in old_map.keys() & new_map.keys():
        old_roles = {str(r["id"]): r["name"] for r in old_map[i].get("roles", [])}
        new_roles = {str(r["id"]): r["name"] for r in new_map[i].get("roles", [])}
        added_ids = new_roles.keys() - old_roles.keys()
        removed_ids = old_roles.keys() - new_roles.keys()
        added = sorted((new_roles[rid] for rid in added_ids), key=str.casefold)
        removed = sorted((old_roles[rid] for rid in removed_ids), key=str.casefold)
        if added or removed:
            m = new_map[i]
            role_changes.append({
                "discord_id": m["discord_id"],
                "username": m["username"],
                "display_name": m["display_name"],
                "added": added,
                "removed": removed,
            })

    role_changes.sort(key=lambda m: (m.get("display_name") or m.get("username") or "").casefold())
    return {"joined": joined, "left": left, "role_changes": role_changes}


def _member_label(member: dict) -> str:
    display = member.get("display_name") or member.get("username") or str(member.get("discord_id", "?"))
    username = member.get("username") or "?"
    return f"{display} (@{username})"


def format_daily_report(guild_name: str, changes: dict, created_at: str, timezone_name: str = "Europe/Warsaw") -> list[str]:
    """Build Discord-safe report chunks (each <= ~1900 chars)."""
    try:
        dt = datetime.fromisoformat(created_at).astimezone(ZoneInfo(timezone_name))
        date_label = dt.strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        date_label = created_at[:10] if created_at else ""

    joined = changes["joined"]
    left = changes["left"]
    role_changes = changes["role_changes"]

    lines = [
        f"📊 **Dzienny raport zmian — {guild_name} — {date_label}**",
        "",
        f"🟢 Dołączyli: **{len(joined)}**",
        f"🔴 Odeszli: **{len(left)}**",
        f"🏷️ Użytkownicy ze zmianami ról: **{len(role_changes)}**",
    ]

    if not joined and not left and not role_changes:
        lines += ["", "Brak zmian od poprzedniego automatycznego snapshotu."]
    else:
        if joined:
            lines += ["", "**🟢 Dołączyli**"] + [f"• {_member_label(m)}" for m in joined]
        if left:
            lines += ["", "**🔴 Odeszli**"] + [f"• {_member_label(m)}" for m in left]
        if role_changes:
            lines += ["", "**🏷️ Zmiany ról**"]
            for c in role_changes:
                additions = f"+ {', '.join(c['added'])}" if c["added"] else ""
                removals = f"- {', '.join(c['removed'])}" if c["removed"] else ""
                details = " | ".join(x for x in (additions, removals) if x)
                lines.append(f"• {_member_label(c)}: {details}")

    chunks: list[str] = []
    current = ""
    for line in lines:
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > 1900 and current:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks
