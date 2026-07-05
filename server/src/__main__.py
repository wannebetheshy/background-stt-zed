import uvicorn

from src.config import settings


def main() -> None:
    uvicorn.run("src.app:app", host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
