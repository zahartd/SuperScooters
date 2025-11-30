from prometheus_client import Counter, Histogram, Gauge, start_http_server, REGISTRY
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import uuid
import time

METRICS = {
    'api_requests_total': Counter(
        'api_requests_total',
        'Total API requests',
        ['method', 'endpoint', 'status']
    ),
    'api_latency_seconds': Histogram(
        'api_latency_seconds',
        'API latency distributions',
        ['method', 'endpoint'],
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
    ),
    'api_errors_total': Counter(
        'api_errors_total',
        'Total API errors',
        ['method', 'endpoint', 'error_type']
    ),
    'offer_conversions_total': Counter(
        'offer_conversions_total',
        'Offer to order conversions',
        ['status']
    ),
    'payment_success_rate': Gauge(
        'payment_success_rate',
        'Successful payment rate'
    ),
    'payment_failures_total': Counter(
        'payment_failures_total',
        'Failed payment attempts',
        ['reason']
    ),
    'cache_hit_ratio': Gauge(
        'cache_hit_ratio',
        'Cache hit ratio for order details'
    ),
    'external_call_duration': Histogram(
        'external_call_duration_seconds',
        'External service call durations',
        ['service'],
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5]
    ),
    'offer_calculation_duration': Histogram(
        'offer_calculation_duration_seconds',
        'Offer calculation duration',
        buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0]
    ),
    'money_hold_success_total': Counter(
        'money_hold_success_total',
        'Successful hold money operations'
    ),
}


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        endpoint = request.url.path
        method = request.method
        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
            status = str(response.status_code)
            METRICS['api_requests_total'].labels(method=method, endpoint=endpoint, status=status).inc()
        except Exception as e:
            METRICS['api_errors_total'].labels(method=method, endpoint=endpoint, error_type=type(e).__name__).inc()
            raise
        finally:
            duration = time.time() - start_time
            METRICS['api_latency_seconds'].labels(method=method, endpoint=endpoint).observe(duration)
        return response

def measure_external_call(service_name: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start
                METRICS['external_call_duration'].labels(service=service_name).observe(elapsed)
        return wrapper
    return decorator

logger = structlog.get_logger()
def start_metrics_server(port: int = 8001):
    start_http_server(port)
    logger.info("Prometheus metrics server started on port %d", port)