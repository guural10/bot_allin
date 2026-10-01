# Discord Admin Bot — read-only reporting

Bot służy wyłącznie do odczytu i raportowania danych członków/rol. Nie nadaje ani nie odbiera ról, nie zmienia nicków, nie kickuje i nie banuje.

## Funkcje
- `/export_members` — XLSX z pełną listą członków.
- `/export_roles` — XLSX: arkusz ról + relacja użytkownik–rola.
- `/role_members <rola>` — osoby z rolą.
- `/missing_role <rola>` — osoby bez roli.
- `/member <osoba>` — dane pojedynczego członka.
- `/stats` — podstawowe statystyki.
- `/snapshot` — ręczny snapshot JSON.
- `/changes` — porównanie dwóch ostatnich snapshotów + XLSX.
- Automatyczny snapshot raz dziennie; opcjonalny raport zmian na wskazany kanał.

## 1. Instalacja
Wymagany Python 3.11+.

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS/Linux:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Discord Developer Portal
1. Utwórz aplikację i bota w Discord Developer Portal.
2. W ustawieniach bota włącz **Server Members Intent**.
3. Skopiuj token bota. Nie publikuj go i nie commituj do Git.
4. W OAuth2 / instalacji dodaj bota do serwera z minimalnymi uprawnieniami potrzebnymi do widzenia serwera i używania komend aplikacji. Bot nie potrzebuje `Administrator` ani `Manage Roles`.

## 3. Konfiguracja
Skopiuj `.env.example` jako `.env` i uzupełnij:

```env
DISCORD_TOKEN=...
GUILD_ID=123456789012345678
SNAPSHOT_HOUR=6
SNAPSHOT_MINUTE=0
TIMEZONE=Europe/Warsaw
REPORT_CHANNEL_ID=
```

`GUILD_ID` jest zalecane podczas testów, bo komendy dla konkretnego serwera synchronizują się szybciej. `REPORT_CHANNEL_ID` pozostaw puste, jeśli nie chcesz automatycznych wiadomości.

## 4. Uruchomienie
```bash
python bot.py
```

## XLSX i Google Sheets
`/export_members` tworzy płaski arkusz `Members`: jeden członek = jeden wiersz. Role są rozdzielone średnikiem.

`/export_roles` tworzy:
- `Roles` — lista ról i liczba członków,
- `Role Members` — relacja jeden wiersz = jedno przypisanie użytkownik–rola.

Pliki lokalne trafiają do `exports/`. Snapshoty trafiają do `data/snapshots/`.

## Bezpieczeństwo
- `.env` jest ignorowany przez Git.
- Wszystkie komendy są ograniczone do administratorów serwera.
- Bot nie zawiera operacji modyfikujących członków ani role.
