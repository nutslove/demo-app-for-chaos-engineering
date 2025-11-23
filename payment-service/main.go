package main

import (
	"context"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"go.opentelemetry.io/contrib/instrumentation/github.com/gin-gonic/gin/otelgin"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc"
	"go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/log/global"
	otlog "go.opentelemetry.io/otel/log"
	"go.opentelemetry.io/otel/propagation"
	sdklog "go.opentelemetry.io/otel/sdk/log"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
	"go.opentelemetry.io/otel/trace"
)

var (
	tracer trace.Tracer
	logger otlog.Logger
)

type PaymentRequest struct {
	OrderID     int     `json:"order_id"`
	Amount      float64 `json:"amount"`
	CardNumber  string  `json:"card_number"`
}

func initTelemetry(ctx context.Context) (func(), error) {
	res, err := resource.New(ctx,
		resource.WithAttributes(
			semconv.ServiceName("payment-service"),
			semconv.ServiceVersion("1.0.0"),
		),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create resource: %w", err)
	}

	traceExporter, err := otlptracegrpc.New(ctx,
		otlptracegrpc.WithEndpoint("otel-collector:4317"),
		otlptracegrpc.WithInsecure(),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create trace exporter: %w", err)
	}

	tracerProvider := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(traceExporter),
		sdktrace.WithResource(res),
	)
	otel.SetTracerProvider(tracerProvider)
	otel.SetTextMapPropagator(propagation.TraceContext{})
	tracer = tracerProvider.Tracer("payment-service-tracer")

	metricExporter, err := otlpmetricgrpc.New(ctx,
		otlpmetricgrpc.WithEndpoint("otel-collector:4317"),
		otlpmetricgrpc.WithInsecure(),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create metric exporter: %w", err)
	}

	meterProvider := sdkmetric.NewMeterProvider(
		sdkmetric.WithReader(sdkmetric.NewPeriodicReader(metricExporter)),
		sdkmetric.WithResource(res),
	)
	otel.SetMeterProvider(meterProvider)

	logExporter, err := otlploggrpc.New(ctx,
		otlploggrpc.WithEndpoint("otel-collector:4317"),
		otlploggrpc.WithInsecure(),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create log exporter: %w", err)
	}

	loggerProvider := sdklog.NewLoggerProvider(
		sdklog.WithProcessor(sdklog.NewBatchProcessor(logExporter)),
		sdklog.WithResource(res),
	)
	global.SetLoggerProvider(loggerProvider)
	logger = loggerProvider.Logger("payment-service-logger")

	cleanup := func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		tracerProvider.Shutdown(ctx)
		meterProvider.Shutdown(ctx)
		loggerProvider.Shutdown(ctx)
	}

	return cleanup, nil
}

func emitLog(ctx context.Context, severity otlog.Severity, message string, attrs ...attribute.KeyValue) {
	span := trace.SpanFromContext(ctx)
	spanCtx := span.SpanContext()

	logAttrs := make([]otlog.KeyValue, len(attrs)+2)
	for i, attr := range attrs {
		logAttrs[i] = otlog.String(string(attr.Key), attr.Value.AsString())
	}
	logAttrs[len(attrs)] = otlog.String("trace_id", spanCtx.TraceID().String())
	logAttrs[len(attrs)+1] = otlog.String("span_id", spanCtx.SpanID().String())

	var record otlog.Record
	record.SetTimestamp(time.Now())
	record.SetSeverity(severity)
	record.SetBody(otlog.StringValue(message))
	record.AddAttributes(logAttrs...)

	logger.Emit(ctx, record)
}

func main() {
	ctx := context.Background()
	cleanup, err := initTelemetry(ctx)
	if err != nil {
		log.Fatalf("Failed to initialize telemetry: %v", err)
	}
	defer cleanup()

	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())
	r.Use(otelgin.Middleware("payment-service"))

	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "healthy"})
	})

	r.POST("/payment/process", func(c *gin.Context) {
		ctx := c.Request.Context()
		span := trace.SpanFromContext(ctx)
		traceID := span.SpanContext().TraceID().String()

		var req PaymentRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			emitLog(ctx, otlog.SeverityError, fmt.Sprintf("Invalid request: %v - trace_id: %s", err, traceID))
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		emitLog(ctx, otlog.SeverityInfo, fmt.Sprintf("Processing payment for Order %d - trace_id: %s", req.OrderID, traceID),
			attribute.Int("order.id", req.OrderID),
			attribute.Float64("amount", req.Amount),
		)

		chaosScenario := c.GetHeader("X-Chaos-Scenario")

		// Chaos: Gateway Timeout
		if chaosScenario == "payment-timeout" || chaosScenario == "black-friday" {
			if rand.Float32() < 0.3 { // 30% chance
				emitLog(ctx, otlog.SeverityWarn, fmt.Sprintf("Simulating payment gateway timeout - trace_id: %s", traceID))
				time.Sleep(5 * time.Second)
				c.JSON(http.StatusGatewayTimeout, gin.H{"error": "Payment gateway timed out"})
				return
			}
		}

		// Chaos: Payment Declined (Card number ending in 00)
		if len(req.CardNumber) >= 2 && req.CardNumber[len(req.CardNumber)-2:] == "00" {
			emitLog(ctx, otlog.SeverityWarn, fmt.Sprintf("Payment declined for card ending in 00 - trace_id: %s", traceID))
			c.JSON(http.StatusPaymentRequired, gin.H{"error": "Payment declined by issuer"})
			return
		}

		// Simulate processing time
		time.Sleep(time.Duration(rand.Intn(500)+100) * time.Millisecond)

		emitLog(ctx, otlog.SeverityInfo, fmt.Sprintf("Payment successful for Order %d - trace_id: %s", req.OrderID, traceID))
		c.JSON(http.StatusOK, gin.H{
			"success":        true,
			"transaction_id": fmt.Sprintf("txn_%d_%d", req.OrderID, time.Now().Unix()),
			"message":        "Payment processed successfully",
		})
	})

	srv := &http.Server{
		Addr:    ":8082",
		Handler: r,
	}

	go func() {
		log.Println("Payment service listening on port 8082")
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		log.Fatalf("Server forced to shutdown: %v", err)
	}
}
