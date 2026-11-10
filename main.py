import sys
from pathlib import Path
import uvicorn
from core.config import settings
from core.logger import get_logger

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = get_logger("main")

def main():
    logger.info(f"Starting {settings.app.name} v{settings.app.version}...")
    uvicorn.run(
        "renderers.web_dashboard.app:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
