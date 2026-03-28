import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)



def cleanup_files():
    # Define directories
    ROOT_DIR = Path(os.getcwd())
    DATA_DIR = ROOT_DIR / "data"
    LOGS_DIR = ROOT_DIR / "logs"
    DEBUG_DIR = LOGS_DIR / "debug"

    # Create directories
    for directory in [DATA_DIR, LOGS_DIR, DEBUG_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

    # Move files
    for file in ROOT_DIR.iterdir():
        if not file.is_file():
            continue

        # Move .jsonl files to data/
        if file.suffix == ".jsonl" and file.name.startswith("data_"):
            destination = DATA_DIR / file.name
            shutil.move(str(file), str(destination))
            logger.info(f"Moved {file.name} to data/")

        # Move .log files to logs/
        elif file.suffix == ".log":
            destination = LOGS_DIR / file.name
            shutil.move(str(file), str(destination))
            logger.info(f"Moved {file.name} to logs/")

        # Move .txt files to logs/debug/ (excluding requirements.txt)
        elif file.suffix == ".txt" and file.name != "requirements.txt":
            destination = DEBUG_DIR / file.name
            shutil.move(str(file), str(destination))
            logger.info(f"Moved {file.name} to logs/debug/")

    logger.info("Cleanup complete!")


if __name__ == "__main__":
    cleanup_files()
