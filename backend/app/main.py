import asyncio
import json
import logging
import re
import shutil
import time
from collections import OrderedDict, deque
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator
from app.core.config import Settings
from app.core.security import normalize_url
from app.workers.jobs import Manager, JobError

log = logging.getLogger('xsave')
logging.basicConfig(level=logging.INFO, format='%(message)s')

class Analyze(BaseModel):
    url: str = Field(max_length=2048)
    @field_validator('url')
    @classmethod
    def valid_url(cls, value): return normalize_url(value)

class Create(BaseModel):
    reference: str = Field(min_length=20, max_length=100)
    quality: str = Field(default='best', max_length=20)

def create_app(settings=None, manager_factory=Manager):
    settings = settings or Settings()
    @asynccontextmanager
    async def lifespan(app):
        app.state.manager = manager_factory(settings)
        yield
        await asyncio.to_thread(app.state.manager.close)
    app = FastAPI(title='X Video Downloader', version='1.0.0', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors), allow_methods=['GET', 'POST', 'DELETE'], allow_headers=['Authorization', 'Content-Type'])
    requests = OrderedDict()
    streams = {}

    @app.middleware('http')
    async def limits(request, call_next):
        if request.method == 'POST':
            try:
                if int(request.headers.get('content-length', '0')) > 4096: return JSONResponse({'error': {'message': 'Request too large.'}}, 413)
            except ValueError: return JSONResponse({'error': {'message': 'Invalid request length.'}}, 400)
            # Read with a real bound even when Content-Length is absent/chunked.
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 4096: return JSONResponse({'error': {'message': 'Request too large.'}}, 413)
            request._body = bytes(body)
            ip = request.client.host if request.client else 'unknown'
            now = time.monotonic()
            history = requests.setdefault(ip, deque())
            while history and now - history[0] > 60: history.popleft()
            if len(history) >= settings.rate_limit: return JSONResponse({'error': {'message': 'Too many requests. Wait a minute.'}}, 429, headers={'Retry-After': '60'})
            history.append(now)
            requests.move_to_end(ip)
            while len(requests) > 10000: requests.popitem(last=False)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        first = exc.errors()[0]
        message = first.get('msg', 'Invalid request.').removeprefix('Value error, ')
        return JSONResponse({'error': {'message': message}}, 422)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc): return JSONResponse({'error': {'message': exc.detail}}, exc.status_code)

    @app.exception_handler(JobError)
    async def job_error(request, exc): return JSONResponse({'error': {'message': str(exc)}}, 503)

    def owned(request, job_id):
        bearer = request.headers.get('authorization', '')
        token = bearer[7:] if bearer.startswith('Bearer ') else request.query_params.get('token', '')
        try: return request.app.state.manager.get(job_id, token)
        except KeyError: raise HTTPException(404, 'Download not found or expired.')

    @app.get('/api/v1/health')
    def health(): return {'status': 'ok', 'ffmpeg': shutil.which('ffmpeg') is not None}

    @app.post('/api/v1/media/analyze')
    def analyze(body: Analyze, request: Request):
        return request.app.state.manager.analyze(body.url)

    @app.post('/api/v1/downloads', status_code=202)
    def create(body: Create, request: Request):
        try: job = request.app.state.manager.create(body.reference, body.quality)
        except KeyError: raise HTTPException(404, 'Analysis expired. Paste the link again.')
        except ValueError as exc: raise HTTPException(400, str(exc))
        log.info(json.dumps({'event': 'job_created', 'job_id': job.id}))
        return {**job.snapshot(), 'token': job.token}

    @app.get('/api/v1/downloads/{job_id}')
    def status(job_id: str, request: Request): return owned(request, job_id).snapshot()

    @app.delete('/api/v1/downloads/{job_id}', status_code=204)
    def cancel(job_id: str, request: Request):
        request.app.state.manager.cancel(owned(request, job_id))

    @app.get('/api/v1/downloads/{job_id}/events')
    async def events(job_id: str, request: Request):
        job = owned(request, job_id)
        if streams.get(job_id, 0) >= 3: raise HTTPException(429, 'Too many progress connections.')
        streams[job_id] = streams.get(job_id, 0) + 1
        async def generate():
            previous = None
            try:
                while not await request.is_disconnected():
                    if time.time() >= job.created + settings.ttl: break
                    state = job.snapshot()
                    encoded = json.dumps(state)
                    if encoded != previous:
                        yield f'event: progress\ndata: {encoded}\n\n'
                        previous = encoded
                    else: yield ': heartbeat\n\n'
                    if state['status'] in ('completed', 'failed', 'cancelled'): break
                    await asyncio.sleep(0.4)
            finally:
                streams[job_id] -= 1
                if not streams[job_id]: streams.pop(job_id)
        return StreamingResponse(generate(), media_type='text/event-stream', headers={'X-Accel-Buffering': 'no'})

    @app.get('/api/v1/downloads/{job_id}/file')
    def file(job_id: str, request: Request):
        job = owned(request, job_id)
        with job.lock:
            if job.state != 'completed' or not job.file: raise HTTPException(409, 'Video is not ready.')
            if job.file.is_symlink() or job.file.resolve().parent != job.directory.resolve() or not job.file.is_file():
                raise HTTPException(404, 'Video file expired.')
            name = re.sub(r'[^\w .-]', '', job.title, flags=re.ASCII).strip(' .')[:80] or 'X video'
            return FileResponse(job.file, media_type='video/mp4', filename=f'{name}.mp4')
    return app

app = create_app()
