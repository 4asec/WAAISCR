# Changelog

All notable changes to the Link Curator project will be documented in this file.

## [0.1.0] - 2026-11-06 (Fase 1: Kerangka Core, WhatsApp Gateway & MVP Kurasi)

### Added
- **Project Structure**: Modular ecosystem under `D:\Project Kodingan Raffa\link-curator`.
- **Core Architecture**:
  - `core.bus`: Asyncio Event Bus for decoupled internal event dispatching.
  - `core.router`: Registry-based Command Router with decorator `@router.register`.
  - `core.security`: Whitelist validator & Prompt Injection boundary sanitizer (`<untrusted_content>`).
  - `core.logger`: Structured logger with automated secret masking (scrubbing API keys & tokens).
  - `core.config`: Pydantic BaseSettings loader reading `config.yaml` and `.env`.
- **WhatsApp Gateway & Adapters**:
  - Node.js Baileys microservice supporting **QR Code** and **8-digit Pairing Code** (`auth_method: qr | pairing`).
  - Automatic reconnect with exponential backoff on transient disconnects.
  - Automated session purges on `loggedOut` status with clear terminal notifications.
  - Full isolation behind `ChannelAdapter` with `WhatsAppBaileysAdapter` and `WhatsAppCloudAdapter` stub.
- **LLM Provider System**:
  - Interface `LLMProvider` with TokenBucket rate limiter (RPM/TPM) and exponential backoff retry on HTTP 429/503.
  - `GeminiProvider` using direct Gemini REST API with native Pydantic JSON schema generation.
  - `OllamaProvider` stub for future local LLM usage.
- **Content Fetcher Pipeline**:
  - `fetchers.normalizer`: URL extractor, query tracking stripper, platform detector (YouTube, TikTok, GitHub, Reddit, etc.), and SHA-256 deduplication hashing.
  - `fetchers.public_api`: Trafilatura article reader + BeautifulSoup OpenGraph metadata + GitHub & Reddit API fast extractors.
  - `fetchers.chain`: Priority fallback chain runner.
- **Link Curator Service & Renderers**:
  - `modules.link_curator.service`: URL parsing, fetcher orchestration, and structured LLM analysis.
  - `renderers.whatsapp_reply`: Meta AI style responses with configurable badge `🔹` and `*term*` highlighting.
  - `renderers.web_dashboard`: FastAPI app with `/health` endpoint and local status dashboard.
- **Automated Tests**:
  - Pytest test suite covering router, normalizer, fetcher chain, security boundaries, and whitelist verification.
- **Documentation**:
  - Comprehensive `README.md` with WhatsApp linking walkthrough (QR & Pairing code) and 14-day inactivity rules.
  - `docs/ARCHITECTURE.md`, `docs/ADDING_A_MODULE.md`, and `docs/COMMANDS.md`.
