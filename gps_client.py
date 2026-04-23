import json
import threading
import time
from typing import Dict

import websocket

from solver import build_satellite_data, trilateration_analytic, trilateration_numeric


class GPSDataStore:
    def __init__(self):
        self.lock = threading.Lock()
        self.status = "disconnected"
        self.raw_messages: Dict[str, dict] = {}
        self.satellites = []
        self.analytic_position = None
        self.numeric_position = None
        self.last_message = None

    def update_from_message(self, message: dict):
        satellite_id = message.get("id")
        if satellite_id is None:
            return

        with self.lock:
            self.last_message = message

            x = message.get("x")
            y = message.get("y")
            sent_at = message.get("sentAt")
            received_at = message.get("receivedAt")

            # оновлюємо супутник лише якщо повідомлення повністю валідне
            if x is not None and y is not None and sent_at is not None and received_at is not None:
                self.raw_messages[satellite_id] = message

            messages_list = list(self.raw_messages.values())
            satellites = build_satellite_data(messages_list)

            self.satellites = satellites
            self.analytic_position = trilateration_analytic(satellites)
            self.numeric_position = trilateration_numeric(satellites)
            self.status = "connected"

    def get_data(self):
        with self.lock:
            return {
                "status": self.status,
                "satellites": list(self.satellites),
                "analyticPosition": self.analytic_position,
                "numericPosition": self.numeric_position,
                "lastMessage": self.last_message,
            }

    def set_status(self, status: str):
        with self.lock:
            self.status = status


class GPSWebSocketClient:
    def __init__(self, url: str, store: GPSDataStore):
        self.url = url
        self.store = store
        self.thread = None

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.store.update_from_message(data)
        except Exception as e:
            self.store.set_status(f"message parse error: {e}")

    def on_error(self, ws, error):
        self.store.set_status(f"error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.store.set_status("disconnected")

    def on_open(self, ws):
        self.store.set_status("connected")

    def run_forever(self):
        while True:
            try:
                self.store.set_status("connecting")
                ws = websocket.WebSocketApp(
                    self.url,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close,
                )
                ws.run_forever()
            except Exception as e:
                self.store.set_status(f"connection failed: {e}")

            time.sleep(3)

    def start(self):
        self.thread = threading.Thread(target=self.run_forever, daemon=True)
        self.thread.start()