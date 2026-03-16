"""
Scanner
=======
Walks a target folder, classifies each file (text via NLP,
image via OpenCV), and moves it into an organized output tree.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path

from organizer import classifier, vision
from organizer.database import Database, FileRecord

logger = logging.getLogger(__name__)


class Scanner:
    def __init__(
        self,
        target_folder: Path,
        config: dict,
        db: Database,
        dry_run: bool = False,
    ):
        self.target_folder = target_folder
        self.config = config
        self.db = db
        self.dry_run = dry_run

        self.output_folder = Path(config["output_folder"])
        self.text_exts = set(config["file_handling"]["supported_text_extensions"])
        self.image_exts = set(config["file_handling"]["supported_image_extensions"])
        self.max_bytes = config["file_handling"]["max_file_size_mb"] * 1024 * 1024
        self.skip_hidden = config["file_handling"]["skip_hidden"]

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def run(self) -> dict:
        """Scan, classify, and organize all files. Returns summary stats."""
        run_id = self.db.start_run()
        files_found = 0
        files_moved = 0

        for file_path in self._iter_files():
            files_found += 1

            if self.db.already_processed(str(file_path)):
                logger.debug(f"Skipping (already processed): {file_path.name}")
                continue

            record = self._process_file(file_path)
            if record is None:
                continue

            self.db.upsert_file(record)

            if not self.dry_run:
                moved = self._move_file(file_path, record.destination)
                if moved:
                    self.db.mark_moved(str(file_path), record.destination)
                    files_moved += 1
            else:
                logger.info(f"[DRY RUN] Would move '{file_path.name}' → {record.destination}")

        self.db.finish_run(run_id, files_found, files_moved)
        stats = {"files_found": files_found, "files_moved": files_moved}
        self._log_summary(stats)
        return stats

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _iter_files(self):
        """Yield all eligible file paths from the target folder."""
        for path in self.target_folder.rglob("*"):
            if not path.is_file():
                continue
            if self.skip_hidden and path.name.startswith("."):
                continue
            if path.stat().st_size > self.max_bytes:
                logger.warning(f"Skipping large file ({path.stat().st_size // 1024 // 1024} MB): {path.name}")
                continue
            if path.suffix.lower() in self.text_exts | self.image_exts:
                yield path

    def _process_file(self, file_path: Path) -> FileRecord | None:
        """Classify one file and build a FileRecord."""
        suffix = file_path.suffix.lower()
        is_image = suffix in self.image_exts

        try:
            if is_image:
                label, confidence = vision.classify_image(file_path)
                img_hash = vision.compute_image_hash(file_path)
                # Duplicate check
                existing_hashes = self.db.get_image_hashes()
                for h in existing_hashes:
                    if vision.images_are_similar(img_hash, h):
                        label = "duplicate"
                        logger.info(f"Duplicate image detected: {file_path.name}")
                        break
            else:
                text = classifier.extract_text(file_path)
                if text is None:
                    logger.warning(f"Could not extract text from {file_path.name}, skipping.")
                    return None
                label, confidence = classifier.classify(
                    text=text,
                    candidate_labels=self.config["classifier"]["candidate_labels"],
                    model_name=self.config["classifier"]["model"],
                    confidence_threshold=self.config["classifier"]["confidence_threshold"],
                )
                img_hash = None

            destination = self._build_destination(file_path, label)

            return FileRecord(
                file_path=str(file_path),
                file_name=file_path.name,
                extension=suffix,
                size_bytes=file_path.stat().st_size,
                label=label,
                confidence=round(confidence, 4),
                image_hash=img_hash,
                destination=str(destination),
                scanned_at=datetime.utcnow().isoformat(),
                moved=False,
            )

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}", exc_info=True)
            return None

    def _build_destination(self, file_path: Path, label: str) -> Path:
        """
        Build the destination path:
          <output_folder>/<label>/<YYYY-MM>/<filename>
        Appends a numeric suffix if the filename already exists.
        """
        month_dir = datetime.utcnow().strftime("%Y-%m")
        dest_dir = self.output_folder / label / month_dir
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest = dest_dir / file_path.name
        if dest.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            counter = 1
            while dest.exists():
                dest = dest_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        return dest

    def _move_file(self, src: Path, dest: str) -> bool:
        """Move src to dest. Returns True on success."""
        try:
            shutil.move(str(src), dest)
            logger.info(f"Moved: {src.name}  →  {dest}")
            return True
        except Exception as e:
            logger.error(f"Failed to move {src.name}: {e}")
            return False

    def _log_summary(self, stats: dict):
        db_stats = self.db.get_stats()
        logger.info(
            f"\n{'─'*40}\n"
            f"  Scan complete\n"
            f"  Files found   : {stats['files_found']}\n"
            f"  Files moved   : {stats['files_moved']}\n"
            f"  Total in DB   : {db_stats['total_files']}\n"
            f"  All-time moved: {db_stats['files_moved']}\n"
            f"{'─'*40}"
        )
