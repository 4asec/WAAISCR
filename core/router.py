import inspect
import shlex
from typing import Any, Callable, Coroutine, Dict, List, Optional
from pydantic import BaseModel
from core.logger import get_logger

logger = get_logger("command_router")

class CommandMetadata(BaseModel):
    name: str
    description: str
    usage: str = ""
    module: str = "core"
    aliases: List[str] = []

CommandHandler = Callable[..., Coroutine[Any, Any, str]]

class CommandContext:
    def __init__(
        self,
        sender: str,
        jid: str,
        is_group: bool,
        raw_message: Dict[str, Any],
        args: List[str],
        text: str
    ):
        self.sender = sender
        self.jid = jid
        self.is_group = is_group
        self.raw_message = raw_message
        self.args = args
        self.text = text

class CommandRouter:
    """Registry-based command router. Modules register their own commands with decorators."""

    def __init__(self) -> None:
        self._commands: Dict[str, CommandHandler] = {}
        self._metadata: Dict[str, CommandMetadata] = {}

    def register(
        self,
        name: str,
        description: str,
        usage: str = "",
        module: str = "general",
        aliases: Optional[List[str]] = None
    ) -> Callable[[CommandHandler], CommandHandler]:
        """Decorator to register a command handler."""
        def decorator(func: CommandHandler) -> CommandHandler:
            cmd_name = name.lower().lstrip("/")
            meta = CommandMetadata(
                name=cmd_name,
                description=description,
                usage=usage or f"/{cmd_name}",
                module=module,
                aliases=[a.lower().lstrip("/") for a in (aliases or [])]
            )
            self._commands[cmd_name] = func
            self._metadata[cmd_name] = meta

            for alias in meta.aliases:
                self._commands[alias] = func
                self._metadata[alias] = meta

            logger.info(f"Registered command '/{cmd_name}' for module '{module}'")
            return func
        return decorator

    def get_all_commands(self) -> Dict[str, CommandMetadata]:
        """Return unique command metadata for generating /bantuan."""
        unique_meta: Dict[str, CommandMetadata] = {}
        for key, meta in self._metadata.items():
            if meta.name not in unique_meta:
                unique_meta[meta.name] = meta
        return unique_meta

    async def dispatch(self, text: str, context: CommandContext) -> Optional[str]:
        """Parse and dispatch command. Returns reply string or None if not a command."""
        trimmed = text.strip()
        if not trimmed.startswith("/"):
            return None

        parts = trimmed.split(maxsplit=1)
        cmd_part = parts[0][1:].lower()
        arg_string = parts[1] if len(parts) > 1 else ""

        handler = self._commands.get(cmd_part)
        if not handler:
            return f"Perintah `/{cmd_part}` tidak dikenali. Ketik `/bantuan` untuk melihat daftar perintah yang tersedia."

        try:
            # Parse arguments cleanly with shlex fallback
            try:
                args = shlex.split(arg_string)
            except ValueError:
                args = arg_string.split()
            context.args = args
            context.text = arg_string

            return await handler(context)
        except Exception as e:
            logger.exception(f"Error executing command '/{cmd_part}': {e}")
            return f"Terjadi kesalahan saat memproses perintah `/{cmd_part}`: {str(e)}"

# Global command router singleton
router = CommandRouter()
