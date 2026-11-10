# Architecture Documentation - Link Curator Ecosystem

## 1. High-Level Design Principles

The Link Curator project is built as the foundational module of an extensible personal AI ecosystem. Key architectural tenets:

1. **Strict Core-Module Decoupling**:
   - `core/` contains no knowledge of links, themes, or curation.
   - It only manages event subscriptions (`core.bus`), command registration & dispatching (`core.router`), whitelist verification (`core.security`), and configuration (`core.config`).
2. **Channel Pluggability (`ChannelAdapter`)**:
   - The messaging gateway interface is agnostic.
   - Initial implementation: `WhatsAppBaileysAdapter` (talking over local HTTP to a Node.js microservice running `@whiskeysockets/baileys`).
   - `WhatsAppCloudAdapter` stub is provided for plug-and-play migration to official Meta Cloud APIs.
3. **LLM Agnosticism (`LLMProvider`)**:
   - Generic abstract base class with integrated TokenBucket rate-limiting and exponential backoff retry.
   - Implementations: `GeminiProvider` (with native JSON schema structured outputs) and `OllamaProvider` (local models stub).
4. **Fetcher Pipeline (`FetcherChain`)**:
   - An ordered fallback chain executing the fastest, least intrusive fetchers first (Trafilatura/oEmbed/public API) before falling back to heavier mechanisms (Playwright browser session) or requesting human input.
5. **Prompt Injection Boundary Protection**:
   - All external contents are wrapped in XML tags `<untrusted_content>` with strict neutralization of closing tags. System instructions explicitly dictate treating untrusted content strictly as passive data.

---

## 2. Component Diagram

```
                 [ User WhatsApp ]
                        │
                        ▼
            [ Baileys Gateway Service ] (Node.js :3001)
                        │ HTTP Webhook
                        ▼
     ┌──────────────────────────────────────┐
     │           FastAPI Server             │
     │      (renderers/web_dashboard)      │
     └──────────────────┬───────────────────┘
                        │
                        ▼
     ┌──────────────────────────────────────┐
     │            Security Guard            │
     │        (Whitelist Verification)      │
     └──────────────────┬───────────────────┘
                        │
          ┌─────────────┴─────────────┐
          │ (is command '/')          │ (is content / text)
          ▼                           ▼
┌──────────────────┐        ┌─────────────────────────┐
│  Command Router  │        │   LinkCuratorService    │
│  (core/router)   │        │ (modules/link_curator)  │
└──────────────────┘        └────────────┬────────────┘
                                         │
                        ┌────────────────┴────────────────┐
                        ▼                                 ▼
              ┌──────────────────┐              ┌──────────────────┐
              │   FetcherChain   │              │   LLMProvider    │
              │ (Trafilatura/API)│              │ (Gemini/Ollama)  │
              └──────────────────┘              └──────────────────┘
```

---

## 3. Storage Architecture

- **Engine**: SQLAlchemy 2.0 AsyncEngine (`aiosqlite`).
- **Database**: SQLite with FTS5 virtual tables.
- **Portability**: Database URI configurable via `DATABASE_URL` in `.env` or `config.yaml` to switch to PostgreSQL without code modifications.
- **Prefix Isolation**: Tables belonging to Link Curator use the `lc_` prefix.
