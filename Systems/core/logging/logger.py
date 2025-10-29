import logging, os
level = getattr(logging, os.getenv("LOG_LEVEL","INFO").upper(), logging.INFO)
logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("swiftdevbot")
