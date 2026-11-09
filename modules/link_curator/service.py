from typing import Optional, Tuple
from adapters.llm.base import LLMProvider
from adapters.llm.gemini import GeminiProvider
from core.config import settings
from core.logger import get_logger
from fetchers.chain import FetcherChain
from fetchers.normalizer import URLNormalizer
from modules.link_curator.prompts import SYSTEM_ANALYSIS_INSTRUCTION, build_curation_prompt
from modules.link_curator.schemas import CuratedItemAnalysis
from renderers.whatsapp_reply import WhatsAppReplyRenderer

logger = get_logger("link_curator_service")

class LinkCuratorService:
    """Core domain service for Link Curator module."""

    def __init__(self, llm: Optional[LLMProvider] = None, chain: Optional[FetcherChain] = None) -> None:
        self.llm = llm or GeminiProvider()
        self.fetcher_chain = chain or FetcherChain()

    async def process_incoming_text(self, text: str) -> Tuple[bool, str]:
        """Process an incoming message.
        
        Returns:
            (has_curated_link: bool, reply_message: str)
        """
        urls = URLNormalizer.extract_urls(text)
        if not urls:
            # Free-form conversation / query
            logger.info("No URLs found in message; treating as free conversation/question.")
            try:
                system_prompt = (
                    "Kamu adalah asisten Link Curator pribadi yang ramah, santai, dan kritis dalam Bahasa Indonesia. "
                    "Jawab pertanyaan pengguna secara ringkas, to the point, dan informatif."
                )
                answer = await self.llm.generate_text(text, system_instruction=system_prompt)
                return False, answer
            except Exception as e:
                logger.error(f"Error handling free-form text with LLM: {e}")
                return False, f"Halo! Aku Link Curator. Kirimkan tautan web, artikel, atau ketik `/bantuan` untuk melihat daftar perintah yang tersedia."

        # Take primary URL
        target_url = urls[0]
        logger.info(f"Processing URL: {target_url}")

        # Execute fetcher chain
        fetch_result = await self.fetcher_chain.execute(target_url)

        if not fetch_result.is_usable:
            logger.warning(f"Could not extract usable content from {target_url} ({fetch_result.error_message})")
            msg = WhatsAppReplyRenderer.format_fetch_failed(
                url=target_url,
                platform=fetch_result.platform,
                reason=fetch_result.error_message
            )
            return False, msg

        # Analyze using LLM
        logger.info(f"Sending extracted content ({len(fetch_result.text_content)} chars) to LLM...")
        try:
            prompt = build_curation_prompt(
                url=fetch_result.normalized_url,
                platform=fetch_result.platform,
                text_content=fetch_result.text_content
            )
            analysis: CuratedItemAnalysis = await self.llm.generate_structured(
                prompt=prompt,
                schema=CuratedItemAnalysis,
                system_instruction=SYSTEM_ANALYSIS_INSTRUCTION
            )

            reply = WhatsAppReplyRenderer.format_analysis(analysis)
            return True, reply

        except Exception as e:
            logger.exception(f"Error during LLM curation analysis: {e}")
            return False, f"⚠️ Gagal menganalisis konten: {str(e)}"
