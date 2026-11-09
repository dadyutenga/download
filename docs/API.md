# API

Interactive OpenAPI documentation: `/docs`; machine schema: `/openapi.json`.

* `POST /api/v1/media/analyze` — JSON `{"url":"https://x.com/user/status/123"}`. Returns opaque `reference`, `title`, `thumbnail`, `duration`, and `qualities` (`id`, `label`, `height`). References expire after 10 minutes or FILE_TTL_SECONDS, whichever is shorter. The reference is a secret capability; keep it private.
* `POST /api/v1/downloads` — JSON `{"reference":"…","quality":"best"}`. Returns 202 with job snapshot and a secret `token`. Only returned once; keep in memory.
* `GET /api/v1/downloads/{id}` — snapshot: `status` (queued/downloading/completed/failed/cancelled), `percent` (nullable), byte counts, speed, error, expiry timestamp.
* `GET /api/v1/downloads/{id}/events` — SSE `progress` events containing the same snapshot, plus comment heartbeats. Maximum three streams per job. Use fetch streaming with Authorization, rather than EventSource query credentials.
* `GET /api/v1/downloads/{id}/file` — MP4 attachment, completed jobs only. Supports byte ranges through Starlette FileResponse.
* `DELETE /api/v1/downloads/{id}` — 204; cancels worker and deletes its file. Repeated cancellation is harmless until job expiry.
* `GET /api/v1/health` — process health and FFmpeg presence.

Job endpoints require `Authorization: Bearer <token>`. The file endpoint also accepts `?token=` so Android DownloadManager can fetch the attachment. Never log full request URLs or forward these links to analytics. API responses are `Cache-Control: no-store`. Expiry is measured from job creation, including queue time. Unknown/expired credentials return 404. A not-ready file returns 409. User errors use `{"error":{"message":"…"}}`; Pydantic validation returns the same error envelope with status 422. Busy workers/queue and extraction errors return 503; rate limits return 429 with Retry-After.
