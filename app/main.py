import os
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.routes import animal_router, api_key_router
from app.constants import DEFAULT_JAEGER_ENDPOINT

app = FastAPI()

# Tracing
provider = TracerProvider()
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
 
@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}

FastAPIInstrumentor.instrument_app(app)