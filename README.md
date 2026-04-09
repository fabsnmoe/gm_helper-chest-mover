# GermanMiner Chest Mover

Ein einfaches Python-Desktopprogramm mit grafischer Oberfläche zum Verschieben von Items zwischen gesicherten Kisten auf dem Minecraft-Server **GermanMiner** über die offizielle API.

Das Tool richtet sich an Spieler, die Kisteninhalte bequem per API verwalten möchten, ohne jede Anfrage manuell ausführen zu müssen.  
Unterstützt werden das Auslesen von Inventaren, das Verschieben einzelner Slots und das automatische Verschieben kompletter Kisteninhalte.

---

## Funktionen

- Anzeige des Inventars einer Kiste über Koordinaten oder Presets
- Verschieben eines einzelnen Slots von einer Kiste in eine andere
- Verschieben aller belegten Slots einer Kiste in freie Slots einer Zielkiste
- Verwaltung von Presets für häufig verwendete Kistenpositionen
- Speicherung des API-Keys in einer lokalen Konfigurationsdatei
- Optionales Nachladen von Chunks über `loadChunks`
- API-Test direkt aus der Oberfläche
- Detailliertes Log für erfolgreiche und fehlgeschlagene Transfers

---

## Voraussetzungen

- **Windows**
- **Python 3.11 oder neuer** empfohlen
- Ein gültiger **GermanMiner API-Key**
- Zwei installierte Python-Pakete:
  - `requests`
  - `customtkinter`

---

## Python installieren

### 1. Python herunterladen
Lade Python von der offiziellen Website herunter:

https://www.python.org/downloads/

Empfohlen wird eine aktuelle Version von Python 3.

### 2. Bei der Installation wichtig
Beim Installieren von Python unter Windows unbedingt diese Option aktivieren:

- `Add Python to PATH`

Danach kann Python direkt in der Konsole verwendet werden.

### 3. Installation prüfen
Öffne danach die Windows-Konsole (`cmd`) oder PowerShell und gib ein:

```bash
python --version
```

oder falls nötig:

```bash
py --version
```

Wenn eine Python-Version angezeigt wird, ist Python korrekt installiert.

---

## Benötigte Pakete installieren

Öffne im Projektordner eine Konsole und installiere die Abhängigkeiten mit:

```bash
pip install requests customtkinter
```

Falls `pip` nicht erkannt wird, probiere:

```bash
py -m pip install requests customtkinter
```

---

## Projektstruktur

Ein typischer Projektaufbau sieht so aus:

```text
GermanMiner-Chest-Mover/
│
├── main.py
├── gui.py
├── client.py
├── services.py
├── config.py
└── README.md
```

Je nach deinem Aufbau können die Dateinamen leicht abweichen.  
Wichtig ist, dass alle Python-Dateien im selben Projektordner liegen.

---

## API-Key erstellen

Auf GermanMiner kann der API-Key ingame erzeugt bzw. verwaltet werden.

Dazu auf dem Server den passenden Befehl verwenden, zum Beispiel:

```text
/gmapi
```

Den erzeugten API-Key trägst du später in den Programmeinstellungen ein.

---

## Programm starten

Wechsle in der Konsole in den Projektordner und starte das Programm mit:

```bash
python main.py
```

oder alternativ:

```bash
py main.py
```

Wenn alles korrekt installiert ist, öffnet sich die grafische Oberfläche.

---

## Erste Einrichtung

Beim ersten Start solltest du zuerst die Einstellungen öffnen.

### Schritte:
1. Programm starten
2. Auf **„Einstellungen“** klicken
3. Deinen **GermanMiner API-Key** eintragen
4. Optional `loadChunks` standardmäßig aktivieren
5. Einstellungen speichern
6. Mit **„API testen“** prüfen, ob die Verbindung funktioniert

Wenn der Test erfolgreich ist, ist das Programm einsatzbereit.

---

## Bedienung

### Quelle und Ziel auswählen
Für **Quelle** und **Ziel** kannst du jeweils zwei Modi nutzen:

- **Preset**  
  Gespeicherte Kistenpositionen mit Namen
- **Manuell**  
  Direkte Eingabe von `X`, `Y` und `Z`

---

## Presets verwenden

Presets sind gespeicherte Koordinaten für häufig genutzte Kisten.

### Beispiel:
- `lager_erde`
- `shop_output`
- `farm_input`

In den Einstellungen kannst du:
- neue Presets speichern
- bestehende Presets laden
- Presets löschen

Damit musst du Koordinaten nicht jedes Mal neu eingeben.

---

## Inventar laden

Mit **„Inventar laden“** wird der Inhalt der ausgewählten Kiste über die API abgefragt und angezeigt.

Die Anzeige enthält unter anderem:
- Slot
- Itemname
- Anzahl
- ID
- Meta

So kannst du direkt sehen, welche Items sich in welcher Kiste befinden.

---

## Einzelnen Slot verschieben

Wenn du nur einen bestimmten Slot verschieben möchtest:

1. Quelle laden
2. In der Quellliste den gewünschten Slot anklicken
3. Das Programm übernimmt Slot, Itemname und Anzahl automatisch
4. Optional den Zielslot eintragen
5. Auf **„Item verschieben“** klicken

### Beispiel
Wenn in der Quellkiste auf Slot `0` ein Stack Erde liegt, kannst du diesen gezielt in die Zielkiste verschieben.

---

## Ganze Kiste verschieben

Mit **„Alles verschieben“** werden alle belegten Slots der Quellkiste nacheinander in freie Slots der Zielkiste verschoben.

Dabei gilt:
- Jeder Quellslot wird einzeln verarbeitet
- Für jedes Item wird ein freier Zielslot gesucht
- Bereits belegte Zielslots werden übersprungen
- Erfolge und Fehler werden im Log angezeigt

Das ist praktisch, um eine Kiste vollständig in eine andere zu übertragen.

---

## Log-Ausgabe

Im unteren Bereich des Programms befindet sich ein Logfenster.

Dort siehst du:
- API-Status
- geladene Inventare
- erfolgreiche Transfers
- fehlgeschlagene Transfers
- Fehlermeldungen der API

Beispiel:

```text
[20:15:57] [INFO] Starte Move-All ...
[20:15:58] [OK] Verschoben: Quelle Slot 0 -> Ziel Slot 0 | 50x Erde
[20:15:58] [OK] Verschoben: Quelle Slot 1 -> Ziel Slot 1 | 46x Kartoffeln
```

---

## Wichtige Hinweise

### 1. Gesicherte Blöcke erforderlich
Die GermanMiner-API arbeitet nur mit Blöcken, die korrekt gesichert sind.

### 2. Gleiches Grundstück
Das Verschieben von Items funktioniert nur dann, wenn sich Quelle und Ziel auf einem gültigen Grundstück befinden, auf dem die API-Operation erlaubt ist.

### 3. Chunk-Laden
Falls eine Kiste nicht geladen ist, kann `loadChunks` helfen.  
Dabei können je nach API zusätzliche Requests verbraucht werden.

### 4. Spezialitems
Manche Items besitzen besondere Metadaten, Lore oder Hash-Werte.  
Diese können sich beim Stapeln oder Verschieben anders verhalten als normale Standarditems.

---

## Fehlerbehebung

### Python startet nicht
Prüfe:

```bash
python --version
```

Wenn nichts gefunden wird, ist Python nicht korrekt installiert oder nicht im PATH.

---

### `pip` wird nicht erkannt
Dann stattdessen:

```bash
py -m pip install requests customtkinter
```

---

### API-Test schlägt fehl
Prüfe:
- Ist der API-Key korrekt?
- Wurde der Key vollständig kopiert?
- Ist die Internetverbindung aktiv?
- Ist die API erreichbar?

---

### Inventar wird nicht geladen
Prüfe:
- Stimmen die Koordinaten?
- Ist die Kiste gesichert?
- Ist der Chunk geladen?
- Ist `loadChunks` aktiviert?

---

### Transfer schlägt fehl
Prüfe:
- Quelle und Ziel korrekt gewählt?
- Richtiger Slot ausgewählt?
- Genug Items im Quellslot vorhanden?
- Zielkiste erreichbar?
- Zielslot frei oder passend?
- Beide Kisten auf einem erlaubten Grundstück?

---

## Für Entwickler

Das Projekt ist grob in folgende Teile aufgeteilt:

- `client.py`  
  Kommunikation mit der GermanMiner-API
- `services.py`  
  Geschäftslogik für Inventare und Transfers
- `gui.py`  
  Grafische Oberfläche mit CustomTkinter
- `config.py`  
  Lokale Konfiguration, API-Key und Presets

---

## Mögliche Erweiterungen

- Export als `.exe` für Windows
- Drag-and-drop zwischen Inventarlisten
- Automatische Aktualisierung nach jedem Transfer
- Detailansicht für Spezialitems mit Lore/Hash/Enchantments
- Erweiterte Filter- und Suchfunktionen
- CLI-Version ohne GUI

---

## Haftungsausschluss

Dieses Projekt ist ein inoffizielles Hilfsprogramm zur Nutzung der GermanMiner-API.  
Es steht in keiner offiziellen Verbindung zum Serverteam, sofern nicht ausdrücklich anders angegeben.

Bitte nutze das Tool verantwortungsvoll und beachte die Regeln des Servers.

---

## Lizenz

Du kannst hier deine gewünschte Lizenz eintragen, zum Beispiel:

- MIT License
- Apache 2.0
- GNU GPL v3

Beispiel:

```text
MIT License
```

---

## Danke

Wenn dir das Projekt hilft, freue ich mich über einen Stern im Repository oder über Verbesserungsvorschläge per Pull Request.
