import os
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.routes import animal_router, api_key_router, internal_router
from app.constants import DEFAULT_JAEGER_ENDPOINT

app = FastAPI()

# Tracing
provider = TracerProvider()
enable_tracing = os.getenv("ENABLE_TRACING", "false").lower() == "true"
if enable_tracing:
    exporter = OTLPSpanExporter(
        endpoint=os.getenv("JAEGER_ENDPOINT", DEFAULT_JAEGER_ENDPOINT),
        insecure=True,
    )
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Route
app.include_router(animal_router, prefix="/api")
app.include_router(api_key_router, prefix="/api")
app.include_router(internal_router, prefix="/api")


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}


# Export the trace
FastAPIInstrumentor.instrument_app(app)
