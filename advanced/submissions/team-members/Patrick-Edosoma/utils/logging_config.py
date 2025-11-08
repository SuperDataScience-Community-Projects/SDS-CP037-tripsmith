import logging


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logging for the app.

    Args:
        level (int): Logging level constant from logging.

    Returns:
        None

    Notes:
        Centralized to ensure consistent formatter across modules.
    """
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    logging.basicConfig(level=level, format=fmt)
