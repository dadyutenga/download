import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.getenv('DATA_DIR', str(Path(tempfile.gettempdir()) / 'x-video-downloader')))
    max_file_bytes: int = int(os.getenv('MAX_FILE_BYTES', '209715200'))
    max_jobs: int = int(os.getenv('MAX_JOBS', '20'))
    workers: int = int(os.getenv('DOWNLOAD_WORKERS', '2'))
    ttl: int = int(os.getenv('FILE_TTL_SECONDS', '1800'))
    timeout: int = int(os.getenv('JOB_TIMEOUT_SECONDS', '180'))
    disk_reserve: int = int(os.getenv('DISK_RESERVE_BYTES', '536870912'))
    rate_limit: int = int(os.getenv('RATE_LIMIT_PER_MINUTE', '20'))
    cors: tuple[str, ...] = tuple(os.getenv('CORS_ORIGINS', 'http://localhost:5173,https://localhost,http://localhost').split(','))

    def __post_init__(self):
        if min(self.max_file_bytes, self.max_jobs, self.workers, self.ttl, self.timeout, self.rate_limit) < 1:
            raise ValueError('Resource limits must be positive')
