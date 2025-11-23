module payment-service

go 1.21

require (
	github.com/gin-gonic/gin v1.9.1
	go.opentelemetry.io/contrib/instrumentation/github.com/gin-gonic/gin/otelgin v0.46.1
	go.opentelemetry.io/otel v1.21.0
	go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc v1.21.0
	go.opentelemetry.io/otel/sdk v1.21.0
	go.opentelemetry.io/otel/trace v1.21.0
    go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc v0.44.0
    go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc v0.0.0-20231117231234-761467453086
    go.opentelemetry.io/otel/log v0.0.0-20231117231234-761467453086
    go.opentelemetry.io/otel/sdk/log v0.0.0-20231117231234-761467453086
    go.opentelemetry.io/otel/sdk/metric v1.21.0
)
