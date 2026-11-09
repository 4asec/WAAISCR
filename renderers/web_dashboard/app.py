import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict
from fastapi import BackgroundTasks, FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from adapters.channel.whatsapp_baileys import WhatsAppBaileysAdapter
from adapters.llm.gemini import GeminiProvider
from adapters.storage.db import init_db
from core.config import settings
from core.logger import get_logger
from core.router import CommandContext, router
from core.security import SecurityGuard
from modules.link_curator.service import LinkCuratorService
import modules.link_curator.commands  # Ensure commands are registered

logger = get_logger("fastapi_app")

wa_adapter = WhatsAppBaileysAdapter()
curator_service = LinkCuratorService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Link Curator core services...")
    await init_db()
    yield
    logger.info("Shutting down Link Curator services...")
    await wa_adapter.close()

app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    lifespan=lifespan
)

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for local monitoring, dashboard, and IoT/ESP32 devices."""
    wa_status = await wa_adapter.get_status()
    is_wa_ok = wa_status.get("status") == "connected"

    return {
        "status": "ok" if is_wa_ok else "degraded",
        "app": {
            "name": settings.app.name,
            "version": settings.app.version,
            "env": settings.app.env
        },
        "whatsapp": wa_status,
        "auth_method": settings.whatsapp.auth_method
    }

async def handle_incoming_message_task(data: Dict[str, Any]) -> None:
    """Async background worker for handling incoming WhatsApp events."""
    try:
        sender = data.get("sender", "")
        jid = data.get("jid", "")
        is_group = data.get("is_group", False)
        text = (data.get("text") or "").strip()
        key = data.get("key", {})

        # Ignore messages sent by bot itself
        if data.get("from_me"):
            return

        if not text:
            return

        # 1. Whitelist Security Guard Check
        if not SecurityGuard.is_sender_allowed(sender):
            return

        logger.info(f"Received whitelisted message from {sender} (is_group={is_group}): {text[:60]}")

        # 2. Group behavior handling
        target_reply_jid = sender if is_group else jid
        if is_group:
            # React with 👀 to indicate received & processing
            await wa_adapter.send_reaction(to=jid, key_or_id=key, emoji="👀")

        # 3. Check if command (starts with '/')
        if text.startswith("/"):
            ctx = CommandContext(
                sender=sender,
                jid=jid,
                is_group=is_group,
                raw_message=data,
                args=[],
                text=text
            )
            reply = await router.dispatch(text, ctx)
            if reply:
                await wa_adapter.send_message(to=target_reply_jid, text=reply)
                if is_group:
                    await wa_adapter.send_reaction(to=jid, key_or_id=key, emoji="✅")
            return

        # 4. Process link or free-form text via Link Curator Service
        has_curated, reply = await curator_service.process_incoming_text(text)

        # 5. Send result
        await wa_adapter.send_message(to=target_reply_jid, text=reply)

        # In groups, mark complete with ✅
        if is_group:
            await wa_adapter.send_reaction(to=jid, key_or_id=key, emoji="✅")

    except Exception as e:
        logger.exception(f"Error handling WhatsApp message task: {e}")

@app.post("/api/webhook/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """Webhook called by local Node.js Baileys gateway when new message arrives."""
    payload = await request.json()
    background_tasks.add_task(handle_incoming_message_task, payload)
    return {"status": "received"}

@app.get("/", response_class=HTMLResponse)
async def dashboard_index():
    """Simple web dashboard home page."""
    wa_status = await wa_adapter.get_status()
    status_class = "connected" if wa_status.get("status") == "connected" else "disconnected"

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Link Curator - Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 2rem; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .card {{ background: #1e293b; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid #334155; }}
        h1 {{ margin-top: 0; color: #38bdf8; }}
        .badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: bold; font-size: 0.875rem; }}
        .badge.connected {{ background: #166534; color: #bbf7d0; }}
        .badge.disconnected {{ background: #991b1b; color: #fecaca; }}
        code {{ background: #334155; padding: 0.2rem 0.4rem; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Link Curator Dashboard</h1>
        <div class="card">
            <h3>Status Koneksi WhatsApp</h3>
            <p>Status: <span class="badge {status_class}">{wa_status.get('status', 'unknown').upper()}</span></p>
            <p>Metode Auth: <code>{settings.whatsapp.auth_method.upper()}</code></p>
            <p>Gateway Endpoint: <code>{settings.whatsapp.gateway_url}</code></p>
        </div>
        <div class="card">
            <h3>Konfigurasi Inti</h3>
            <p>Model AI: <code>{settings.llm.model}</code> ({settings.llm.provider})</p>
            <p>Whitelist: <code>{len(settings.whitelist.phone_numbers)} nomor aktif</code></p>
            <p>Endpoint Health: <a href="/health" style="color: #38bdf8;">/health</a></p>
        </div>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html)
