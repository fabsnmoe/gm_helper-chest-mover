# client.py
from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from config import get_api_key


BASE_URL = "https://api.germanminer.de/v2/"
TIMEOUT = 10


class APIError(Exception):
    """Fachlicher API-Fehler."""


class NetworkError(Exception):
    """Netzwerk-/Transportfehler."""


class GermanMinerClient:
    """
    Einfacher API-Client für die GermanMiner API v2.

    Grundlage laut Dokumentation:
    - Jede Anfrage benötigt den Parameter 'key'
    - Antworten kommen als JSON
    - Bei Fehlern ist success=false und error enthält die Meldung
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or get_api_key()
        self.session = requests.Session()

    def api_request(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
    ) -> Any:
        """
        Führt eine API-Anfrage aus und wertet success/error robust aus.
        """
        url = BASE_URL + path.lstrip("/")
        request_params = {"key": self.api_key}

        if params:
            request_params.update(params)

        try:
            if method.upper() == "POST":
                response = self.session.post(url, data=request_params, timeout=TIMEOUT)
            else:
                response = self.session.get(url, params=request_params, timeout=TIMEOUT)

            response.raise_for_status()
        except requests.RequestException as exc:
            raise NetworkError(f"Netzwerkfehler bei {url}: {exc}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise APIError("Die API hat keine gültige JSON-Antwort geliefert.") from exc

        if not isinstance(payload, dict):
            raise APIError("Die API-Antwort hat ein unerwartetes Format.")

        if payload.get("success") is False:
            raise APIError(str(payload.get("error", "Unbekannter API-Fehler.")))

        if payload.get("success") is True:
            return payload.get("data", True)

        if "data" in payload:
            return payload["data"]

        return payload

    def ping(self) -> Any:
        """
        Prüft den API-Key über api/info.
        """
        return self.api_request("api/info")

    def get_inventory(self, x: int, y: int, z: int, load_chunks: bool = False) -> Any:
        """
        Liest das Inventar eines gesicherten Blocks aus.

        Laut Doku:
        - Block muss gesichert sein
        - loadChunks=true lädt bei Bedarf den Chunk
        """
        return self.api_request(
            "world/inventory",
            {
                "x": x,
                "y": y,
                "z": z,
                "loadChunks": str(load_chunks).lower(),
            },
        )

    def clear_inventory(self, x: int, y: int, z: int, load_chunks: bool = False) -> Any:
        """
        Leert das Inventar eines Blocks.
        """
        return self.api_request(
            "world/clear/inventory",
            {
                "x": x,
                "y": y,
                "z": z,
                "loadChunks": str(load_chunks).lower(),
            },
        )

    def move_item(
        self,
        from_x: int,
        from_y: int,
        from_z: int,
        to_x: int,
        to_y: int,
        to_z: int,
        source_slot: int,
        target_slot: int,
        amount: int,
        load_chunks: bool = False,
    ) -> Any:
        """
        Verschiebt Items slotbasiert von einem gesicherten Block in einen anderen.

        Laut GermanMiner-Tutorial:
        - amount = Anzahl
        - fromSlot = Slot, von dem bewegt wird
        - toSlot = Slot, in den bewegt wird
        """
        return self.api_request(
            "world/move/item",
            {
                "fromX": from_x,
                "fromY": from_y,
                "fromZ": from_z,
                "toX": to_x,
                "toY": to_y,
                "toZ": to_z,
                "amount": int(amount),
                "fromSlot": int(source_slot),
                "toSlot": int(target_slot),
                "loadChunks": str(load_chunks).lower(),
            },
        )