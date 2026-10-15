"""OpenTelemetry for the Ring API.

The SDK is constructed only when ``OTEL_EXPORTER_OTLP_ENDPOINT`` is set.
No console exporter and no metrics. ``service.name`` is ``ring-api``.
Worker traces stay on the Cloudflare observability block in
``react/wrangler.jsonc``; this module does not add a second exporter.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from fastapi import FastAPI

SERVICE_NAME = "ring-api"


def log_event(msg: str, **fields: Any) -> None:
    """Write one structured stdout line (``service`` and ``msg``)."""
    payload: dict[str, Any] = {
        "service": SERVICE_NAME,
        "msg": msg,
        **fields,
    }
    sys.stdout.write(json.dumps(payload, default=str) + "\n")
    sys.stdout.flush()


def install(app: FastAPI) -> None:
    """Instrument ``app`` when an OTLP HTTP endpoint is configured."""
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        log_event("OpenTelemetry endpoint is set but the SDK is not installed")
        return

    resource = Resource.create({"service.name": SERVICE_NAME})
    provider = TracerProvider(resource=resource)
    # The exporter reads OTEL_EXPORTER_OTLP_ENDPOINT itself.
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    log_event("OpenTelemetry export enabled")
