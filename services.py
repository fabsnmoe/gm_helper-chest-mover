# services.py
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from client import GermanMinerClient
from config import ConfigError, get_presets


def resolve_location(
    preset_name: str | None = None,
    x: int | None = None,
    y: int | None = None,
    z: int | None = None,
) -> tuple[int, int, int]:
    if preset_name:
        presets = get_presets()
        if preset_name not in presets:
            raise ConfigError(f"Preset '{preset_name}' wurde nicht gefunden.")
        p = presets[preset_name]
        return int(p["x"]), int(p["y"]), int(p["z"])

    if x is None or y is None or z is None:
        raise ConfigError("Bitte Preset oder vollständige Koordinaten angeben.")

    return int(x), int(y), int(z)


def _safe_get(d: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in d:
            return d[key]
    return default


def normalize_inventory(inventory_data: Any) -> List[Dict[str, Any]]:
    """
    Normalisiert die Antwort von world/inventory defensiv.

    Laut GermanMiner-Tutorial ist die Inventar-Antwort slotbasiert und enthält
    typischerweise Slotnummer, Anzahl, ID, Meta, Hash, Lore und Enchantments.
    """

    def normalize_entry(entry: dict, fallback_slot=None) -> dict | None:
        if not isinstance(entry, dict):
            return None

        slot = (
            entry.get("slot")
            if "slot" in entry else
            entry.get("index")
            if "index" in entry else
            entry.get("position")
            if "position" in entry else
            fallback_slot
        )

        amount = (
            entry.get("amount")
            if "amount" in entry else
            entry.get("count")
            if "count" in entry else
            entry.get("quantity")
            if "quantity" in entry else
            1
        )

        try:
            amount = int(amount)
        except (TypeError, ValueError):
            amount = 1

        item_id = _safe_get(entry, "id", "itemId", "typeId", default=None)
        meta = _safe_get(entry, "meta", "durability", default=None)
        hash_value = entry.get("hash")
        lore = entry.get("lore")
        enchantments = _safe_get(entry, "enchantments", "enchants", default=None)

        display_name = _safe_get(entry, "name", "item", "material", "type", default=None)

        if not display_name:
            if item_id is not None and meta is not None:
                display_name = f"ID:{item_id} META:{meta}"
            elif item_id is not None:
                display_name = f"ID:{item_id}"
            else:
                display_name = "UNKNOWN"

        return {
            "slot": slot if slot is not None else "-",
            "item": str(display_name),
            "amount": amount,
            "id": item_id if item_id is not None else "-",
            "meta": meta if meta is not None else "-",
            "hash": hash_value if hash_value is not None else "-",
            "lore": lore if lore is not None else "",
            "enchantments": enchantments if enchantments is not None else [],
            "raw": entry,
        }

    if inventory_data is None:
        return []

    rows: List[Dict[str, Any]] = []

    if isinstance(inventory_data, dict):
        for key in ("items", "inventory", "contents", "slots", "data"):
            value = inventory_data.get(key)

            if isinstance(value, list):
                for idx, entry in enumerate(value):
                    norm = normalize_entry(entry, fallback_slot=idx)
                    if norm:
                        rows.append(norm)
                return rows

            if isinstance(value, dict):
                for slot_key, entry in value.items():
                    try:
                        fallback_slot = int(slot_key)
                    except (ValueError, TypeError):
                        fallback_slot = slot_key
                    norm = normalize_entry(entry, fallback_slot=fallback_slot)
                    if norm:
                        rows.append(norm)
                return rows

        norm = normalize_entry(inventory_data)
        return [norm] if norm else []

    if isinstance(inventory_data, list):
        for idx, entry in enumerate(inventory_data):
            norm = normalize_entry(entry, fallback_slot=idx)
            if norm:
                rows.append(norm)
        return rows

    return []


def group_inventory(rows: Iterable[Dict[str, Any]]) -> List[Tuple[str, int, int]]:
    """
    Rückgabe: (item_name, amount, slot)
    """
    grouped: List[Tuple[str, int, int]] = []
    for row in rows:
        try:
            slot = int(row["slot"])
        except (ValueError, TypeError):
            continue
        grouped.append((str(row["item"]), int(row["amount"]), slot))
    return grouped


def inventory_contains_slot(rows: Iterable[Dict[str, Any]], slot: int, amount: int) -> bool:
    for row in rows:
        try:
            row_slot = int(row["slot"])
            row_amount = int(row["amount"])
        except (ValueError, TypeError):
            continue
        if row_slot == slot and row_amount >= amount:
            return True
    return False


def get_occupied_slots(rows: Iterable[Dict[str, Any]]) -> set[int]:
    occupied: set[int] = set()
    for row in rows:
        try:
            occupied.add(int(row["slot"]))
        except (ValueError, TypeError):
            continue
    return occupied


def find_next_free_slot(occupied_slots: set[int], max_slots: int = 54) -> int | None:
    for slot in range(max_slots):
        if slot not in occupied_slots:
            return slot
    return None


class GermanMinerService:
    def __init__(self, client: GermanMinerClient | None = None) -> None:
        self.client = client or GermanMinerClient()

    def ping(self) -> Any:
        return self.client.ping()

    def load_inventory(
        self, x: int, y: int, z: int, load_chunks: bool = False
    ) -> List[Dict[str, Any]]:
        data = self.client.get_inventory(x, y, z, load_chunks=load_chunks)
        return normalize_inventory(data)

    def move_single_item(
        self,
        source: tuple[int, int, int],
        target: tuple[int, int, int],
        source_slot: int,
        amount: int,
        target_slot: int = 0,
        load_chunks: bool = False,
        precheck: bool = True,
    ) -> Any:
        if amount <= 0:
            raise ValueError("Die Anzahl muss größer als 0 sein.")

        if precheck:
            rows = self.load_inventory(*source, load_chunks=load_chunks)
            if not inventory_contains_slot(rows, source_slot, amount):
                raise ValueError(
                    f"Im Quellslot {source_slot} sind nicht genügend Items vorhanden."
                )

        return self.client.move_item(
            from_x=source[0],
            from_y=source[1],
            from_z=source[2],
            to_x=target[0],
            to_y=target[1],
            to_z=target[2],
            source_slot=source_slot,
            target_slot=target_slot,
            amount=int(amount),
            load_chunks=load_chunks,
        )

    def move_all_items(
        self,
        source: tuple[int, int, int],
        target: tuple[int, int, int],
        load_chunks: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Verschiebt alle belegten Slots der Quellkiste in freie Slots der Zielkiste.
        """
        source_rows = self.load_inventory(*source, load_chunks=load_chunks)
        target_rows = self.load_inventory(*target, load_chunks=load_chunks)

        grouped = group_inventory(source_rows)
        occupied_target_slots = get_occupied_slots(target_rows)

        results: List[Dict[str, Any]] = []

        for item_name, amount, source_slot in grouped:
            target_slot = find_next_free_slot(occupied_target_slots, max_slots=54)

            if target_slot is None:
                results.append(
                    {
                        "item": item_name,
                        "amount": amount,
                        "slot": source_slot,
                        "target_slot": None,
                        "success": False,
                        "error": "Kein freier Zielslot mehr vorhanden.",
                    }
                )
                continue

            try:
                self.client.move_item(
                    from_x=source[0],
                    from_y=source[1],
                    from_z=source[2],
                    to_x=target[0],
                    to_y=target[1],
                    to_z=target[2],
                    source_slot=source_slot,
                    target_slot=target_slot,
                    amount=amount,
                    load_chunks=load_chunks,
                )

                occupied_target_slots.add(target_slot)

                results.append(
                    {
                        "item": item_name,
                        "amount": amount,
                        "slot": source_slot,
                        "target_slot": target_slot,
                        "success": True,
                        "error": None,
                    }
                )
            except Exception as exc:
                results.append(
                    {
                        "item": item_name,
                        "amount": amount,
                        "slot": source_slot,
                        "target_slot": target_slot,
                        "success": False,
                        "error": str(exc),
                    }
                )

        return results