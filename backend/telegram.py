from __future__ import annotations

from typing import Optional

import requests
from flask import current_app

from config import settings
from database import db
from models import TelegramDeliveryLog


class TelegramNotifier:
    def __init__(self) -> None:
        self._bot_token = settings.telegram_bot_token
        self._chat_id = settings.telegram_chat_id

    @property
    def enabled(self) -> bool:
        return bool(self._bot_token and self._chat_id)

    def send_message(
        self, message: str, message_type: str, incident_id: Optional[int] = None
    ) -> None:
        if not self.enabled:
            self._save_log(
                incident_id=incident_id,
                message_type=message_type,
                status="SKIPPED",
                response=None,
                error="Telegram credentials are not configured.",
            )
            return

        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        payload = {"chat_id": self._chat_id, "text": message}

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            self._save_log(
                incident_id=incident_id,
                message_type=message_type,
                status="SENT",
                response=response.text,
                error=None,
            )
        except requests.RequestException as exc:
            current_app.logger.exception("Telegram send failed.")
            self._save_log(
                incident_id=incident_id,
                message_type=message_type,
                status="FAILED",
                response=getattr(exc.response, "text", None),
                error=str(exc),
            )

    def _save_log(
        self,
        incident_id: Optional[int],
        message_type: str,
        status: str,
        response: Optional[str],
        error: Optional[str],
    ) -> None:
        db.session.add(
            TelegramDeliveryLog(
                incident_id=incident_id,
                message_type=message_type,
                status=status,
                response=response,
                error=error,
            )
        )
        db.session.commit()
