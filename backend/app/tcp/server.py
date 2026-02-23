import asyncio
import json
import logging
from typing import Dict

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.ingestion_service import ingestion_service

logger = logging.getLogger(__name__)


class TCPServer:
    def __init__(self, host: str | None = None, port: int | None = None):
        self.host = host or settings.TCP_HOST
        self.port = port or settings.TCP_PORT
        self.server = None

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        address = writer.get_extra_info("peername")
        try:
            raw = await reader.read(8192)
            if not raw:
                writer.write(b'{"status":"error","message":"empty payload"}\n')
                await writer.drain()
                return

            payload = json.loads(raw.decode())
            result = await self.process_sensor_data(payload, source_ip=address[0] if address else None)

            writer.write((json.dumps(result) + "\n").encode())
            await writer.drain()
        except json.JSONDecodeError:
            writer.write(b'{"status":"error","message":"invalid json"}\n')
            await writer.drain()
        except Exception as exc:
            logger.error("TCP handler failed for %s: %s", address, exc)
            writer.write((json.dumps({"status": "error", "message": str(exc)}) + "\n").encode())
            await writer.drain()
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def process_sensor_data(self, payload: Dict, source_ip: str | None = None):
        db = SessionLocal()
        try:
            device_id = payload.get("device_id")
            if not device_id:
                raise ValueError("Missing device_id")
            if payload.get("value") is None:
                raise ValueError("Missing value")

            return ingestion_service.process_reading(
                db,
                device_id=device_id,
                protocol="tcp",
                payload=payload,
                api_key=payload.get("api_key"),
                enforce_api_key=False,
                source_ip=source_ip,
            )
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    async def start(self):
        try:
            self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
            sockets = ", ".join(str(sock.getsockname()) for sock in self.server.sockets or [])
            logger.info("TCP server listening on %s", sockets)
            async with self.server:
                await self.server.serve_forever()
        except OSError as e:
            if e.errno == 98 or "address already in use" in str(e).lower():
                logger.info("TCP port %s already in use, skipping TCP server", self.port)
            else:
                logger.warning("TCP server failed to start: %s", e)
        except Exception as e:
            logger.warning("TCP server error: %s", e)

    def stop(self):
        if self.server:
            self.server.close()
            logger.info("TCP server stopped")


tcp_server = TCPServer()
