# Discord Admin Bot — v2

Bot pozostaje read-only względem członków i ról Discorda.

## Nowości v2
- automatyczny snapshot raz dziennie o godzinie z `.env`,
- automatyczne snapshoty są oznaczone osobno od ręcznych `/snapshot`,
- raport dzienny porównuje wyłącznie kolejne snapshoty automatyczne,
- raport pokazuje szczegółowo: nowych członków, osoby które odeszły oraz dodane/odebrane role,
- raport jest wysyłany także wtedy, gdy nie było zmian,
- pierwszy automatyczny snapshot tworzy punkt odniesienia i nie zgłasza fałszywych zmian,
- długie raporty są dzielone na kilka wiadomości Discorda,
- błędy automatycznego zadania trafiają do Terminala i nie zatrzymują kolejnych wykonań.

## Konfiguracja `.env`
Zachowaj obecny `DISCORD_TOKEN`. Ustaw dodatkowo:

```env
SNAPSHOT_HOUR=6
SNAPSHOT_MINUTE=0
TIMEZONE=Europe/Warsaw
REPORT_CHANNEL_ID=123456789012345678
```

`REPORT_CHANNEL_ID` to ID kanału administracyjnego, na który mają trafiać raporty. Aby skopiować ID kanału w Discordzie, włącz Tryb deweloperski, kliknij kanał prawym przyciskiem i wybierz „Kopiuj identyfikator kanału”.

## Uruchomienie
```bash
source .venv/bin/activate
python bot.py
```

Ręczne `/snapshot` i `/changes` nadal działają. `/changes` porównuje dwa ostatnie snapshoty dowolnego typu; raport automatyczny porównuje dwa ostatnie snapshoty typu `automatic`.

## v3 — audyt dostępów
Nowe komendy administratora (read-only):
- `/access @użytkownik` — kanały widoczne dla użytkownika.
- `/channel_access #kanał` — użytkownicy mogący zobaczyć kanał.
- `/export_access` — XLSX z macierzą użytkownik × kanał oraz relacyjną listą dostępów.

Dostęp jest liczony przez efektywne uprawnienie Discord `View Channel`, z uwzględnieniem ról i nadpisań kanału. Bot niczego nie modyfikuje.
