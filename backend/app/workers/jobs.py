import multiprocessing as mp
import queue
import shutil
import threading
import time
import secrets
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from app.services import media

class JobError(Exception): pass

def child_extract(url, channel):
    try: channel.put(('done', media.extract(url)))
    except Exception: channel.put(('error', 'This public post could not be read. It may be unavailable, protected, or blocked by X.'))

def child_download(url, directory, limit, channel):
    def progress(data):
        downloaded = data.get('downloaded_bytes') or 0
        total = data.get('total_bytes') or data.get('total_bytes_estimate')
        if downloaded > limit or (total and total > limit): raise JobError('Video exceeds the file size limit.')
        channel.put(('progress', {'downloaded_bytes': downloaded, 'total_bytes': total,
                                 'speed': data.get('speed'), 'percent': min(99, downloaded / total * 100) if total else None}))
    try:
        media.download(url, Path(directory), progress, limit)
        channel.put(('done', None))
    except Exception:
        channel.put(('error', 'Download failed. The source may have expired or exceeded the size limit. Try analyzing the post again.'))

@dataclass
class Job:
    id: str
    token: str
    title: str
    quality: str
    source: str
    directory: Path
    created: float = field(default_factory=time.time)
    ttl: int = 1800
    state: str = 'queued'
    progress: dict = field(default_factory=lambda: {'percent': None, 'downloaded_bytes': 0, 'total_bytes': None, 'speed': None})
    error: str | None = None
    file: Path | None = None
    cancelled: threading.Event = field(default_factory=threading.Event)
    lock: threading.RLock = field(default_factory=threading.RLock)
    def snapshot(self):
        with self.lock:
            return {'id': self.id, 'title': self.title, 'quality': self.quality, 'status': self.state,
                    **self.progress, 'error': self.error, 'expires_at': self.created + self.ttl}

class Manager:
    def __init__(self, settings):
        self.settings = settings
        self.root = settings.data_dir.resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.lock = threading.RLock()
        self.jobs = {}
        self.pending_count = 0
        self.analyses = {}
        self.analysis_slots = threading.BoundedSemaphore(settings.workers)
        self.pool = ThreadPoolExecutor(max_workers=settings.workers, thread_name_prefix='download')
        self.stop = threading.Event()
        self.sweeper = threading.Thread(target=self.sweep, daemon=True)
        self.sweeper.start()
        # Processes cannot survive a server restart. Remove stale isolated job directories.
        for path in self.root.glob('job-*'):
            if path.is_dir() and not path.is_symlink(): shutil.rmtree(path)

    def run_process(self, target, args, job=None):
        ctx = mp.get_context('spawn')
        channel = ctx.Queue(maxsize=64)
        process = ctx.Process(target=target, args=(*args, channel), daemon=True)
        process.start()
        deadline = time.monotonic() + self.settings.timeout
        result = None
        try:
            while True:
                if self.stop.is_set() or (job and job.cancelled.is_set()): raise JobError('Cancelled')
                if time.monotonic() > deadline: raise JobError('The operation timed out. Please try again.')
                if job:
                    size = sum(p.stat().st_size for p in job.directory.glob('*') if p.is_file())
                    if size > self.settings.max_file_bytes: raise JobError('Video exceeds the file size limit.')
                    if shutil.disk_usage(self.root).free < self.settings.disk_reserve: raise JobError('Storage is temporarily full.')
                try: kind, value = channel.get(timeout=0.2)
                except queue.Empty:
                    if not process.is_alive(): raise JobError('The media worker stopped unexpectedly.')
                    continue
                if kind == 'progress' and job:
                    with job.lock: job.progress = value
                elif kind == 'error': raise JobError(value)
                elif kind == 'done':
                    result = value
                    break
            return result
        finally:
            if process.is_alive(): process.terminate()
            process.join(timeout=3)
            if process.is_alive(): process.kill(); process.join()
            channel.close()

    def analyze(self, url):
        if not self.analysis_slots.acquire(blocking=False): raise JobError('Analysis is busy. Please try again shortly.')
        try:
            metadata, formats = self.run_process(child_extract, (url,))
            reference = secrets.token_urlsafe(32)
            with self.lock:
                self.expire()
                if len(self.analyses) >= self.settings.max_jobs * 5: raise JobError('Analysis cache is full. Please try again later.')
                self.analyses[reference] = (time.time(), metadata, formats)
            return {'reference': reference, **metadata}
        finally: self.analysis_slots.release()

    def create(self, reference, quality):
        with self.lock:
            self.expire()
            entry = self.analyses.get(reference)
            if not entry: raise KeyError('Analysis expired. Paste the post link again.')
            _, metadata, formats = entry
            if quality not in {q['id'] for q in metadata['qualities']}: raise ValueError('Choose an available quality.')
            if len(self.jobs) >= self.settings.max_jobs or self.pending_count >= self.settings.max_jobs: raise JobError('Download queue is full. Try again later.')
            if shutil.disk_usage(self.root).free < self.settings.disk_reserve + self.settings.max_file_bytes * self.settings.workers:
                raise JobError('Storage is temporarily full.')
            selected = formats[0] if quality == 'best' else next(f for f in formats if str(f.get('height')) == quality)
            if (selected.get('filesize') or 0) > self.settings.max_file_bytes: raise ValueError('Video exceeds the file size limit.')
            identifier = secrets.token_hex(16)
            directory = self.root / f'job-{identifier}'
            directory.mkdir(mode=0o700)
            job = Job(identifier, secrets.token_urlsafe(32), metadata['title'], quality, selected['url'], directory)
            job.ttl = self.settings.ttl
            self.jobs[identifier] = job
            self.pending_count += 1
            self.pool.submit(self.execute, job)
            return job

    def execute(self, job):
        try:
            with job.lock:
                if job.cancelled.is_set(): return
                job.state = 'downloading'
            self.run_process(child_download, (job.source, str(job.directory), self.settings.max_file_bytes), job)
            path = job.directory / 'video.mp4'
            if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= self.settings.max_file_bytes:
                raise JobError('No valid video file was produced.')
            with job.lock:
                if job.cancelled.is_set(): raise JobError('Cancelled')
                job.file = path
                job.state = 'completed'
                job.progress = {'percent': 100, 'downloaded_bytes': path.stat().st_size, 'total_bytes': path.stat().st_size, 'speed': None}
        except Exception as exc:
            with job.lock:
                job.state = 'cancelled' if job.cancelled.is_set() else 'failed'
                job.error = None if job.cancelled.is_set() else str(exc) if isinstance(exc, JobError) else 'Download failed.'
        finally:
            with self.lock: self.pending_count -= 1
            if job.state != 'completed': shutil.rmtree(job.directory, ignore_errors=True)

    def get(self, identifier, token):
        with self.lock:
            job = self.jobs.get(identifier)
            if not job or time.time() - job.created >= self.settings.ttl or not secrets.compare_digest(job.token, token):
                raise KeyError('Download not found or expired.')
            return job

    def cancel(self, job):
        with job.lock:
            job.cancelled.set()
            job.state = 'cancelled'
        # Worker removes active files after terminating its child.
        if job.file: shutil.rmtree(job.directory, ignore_errors=True)

    def expire(self):
        now = time.time()
        with self.lock:
            for key, job in list(self.jobs.items()):
                if now - job.created >= self.settings.ttl:
                    self.cancel(job)
                    self.jobs.pop(key)
            self.analyses = {k: v for k, v in self.analyses.items() if now - v[0] < min(600, self.settings.ttl)}

    def sweep(self):
        while not self.stop.wait(5): self.expire()

    def close(self):
        self.stop.set()
        with self.lock:
            for job in self.jobs.values(): self.cancel(job)
        self.pool.shutdown(wait=True, cancel_futures=True)
        self.sweeper.join(timeout=6)
        for job in self.jobs.values(): shutil.rmtree(job.directory, ignore_errors=True)
