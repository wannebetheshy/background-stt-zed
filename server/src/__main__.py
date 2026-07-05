import logging
import sys

import uvicorn

from src.config import settings

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        stream=sys.stderr,
        force=True,
    )
    logging.getLogger("src").setLevel(logging.INFO)

    uvicorn.run(
        "src.app:app",
        host=settings.host,
        port=settings.port,
        log_level="info",
        log_config=None,
    )


if __name__ == "__main__":
    main()
