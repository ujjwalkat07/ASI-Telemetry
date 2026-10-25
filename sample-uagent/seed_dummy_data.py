"""Utility script to seed dummy telemetry metrics and LLM traces from dummy_data.json into the ASI-Telemetry backend."""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error
import uuid
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# Load local .env
load_dotenv(Path(__file__).parent / ".env")

API_KEY = os.getenv("ASI_API_KEY", "asi_live_b615b841f19106d7a72743cfce900a65")
BACKEND_URL = os.getenv("TELEMETRY_BACKEND_URL", "https://asi-telemetry-backend.vercel.app").rstrip("/")
DUMMY_DATA_FILE = Path(__file__).parent / "dummy_data.json"


def post_json(endpoint: str, data: dict):
    url = f"{BACKEND_URL}{endpoint}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        try:
            body = json.loads(err.read().decode("utf-8"))
        except Exception:
            body = err.reason
        return err.code, body
    except Exception as exc:
        return 0, str(exc)


def seed_data(include_metrics: bool = True, include_traces: bool = True, delay: float = 0.2):
    if not DUMMY_DATA_FILE.exists():
        print(f"[ERROR] Dummy data file not found at: {DUMMY_DATA_FILE}")
        return False

    with open(DUMMY_DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    metrics = data.get("dummy_metrics", [])
    traces = data.get("dummy_llm_traces", [])

    print("=" * 65)
    print("🌱 Seeding Dummy Telemetry Data into ASI-Telemetry Backend")
    print(f"• Backend URL: {BACKEND_URL}")
    print(f"• API Key:     {API_KEY[:14]}...")
    print(f"• Metrics:     {len(metrics)} records")
    print(f"• LLM Traces:  {len(traces)} records")
    print("=" * 65)

    metric_success = 0
    trace_success = 0

    # 1. Ingest Metrics
    if include_metrics:
        print("\n📊 Ingesting Tool & System Metrics into /api/metrics...")
        for idx, metric in enumerate(metrics, start=1):
            now_str = datetime.now(timezone.utc).isoformat()
            metric_payload = {
                **metric,
                "timestamp": now_str,
                "api_key": API_KEY,
            }
            status, res = post_json("/api/metrics", metric_payload)
            if status in (200, 201):
                metric_success += 1
                icon = "✅" if metric.get("status") == "success" else "⚠️"
                print(f"  {icon} [{idx}/{len(metrics)}] {metric.get('func_name', 'metric')} ({metric.get('status')}) -> Ingested")
            else:
                print(f"  ❌ [{idx}/{len(metrics)}] {metric.get('func_name')}: Status {status} - {res}")
            if delay > 0:
                time.sleep(delay)

    # 2. Ingest LLM Traces
    if include_traces:
        print("\n🧠 Ingesting LLM Traces into /api/llm/traces...")
        for idx, trace in enumerate(traces, start=1):
            now_str = datetime.now(timezone.utc).isoformat()
            trace_payload = {
                **trace,
                "id": str(uuid.uuid4()),
                "trace_id": str(uuid.uuid4()),
                "span_id": str(uuid.uuid4()),
                "start_time": now_str,
                "end_time": now_str,
                "api_key": API_KEY,
            }
            status, res = post_json("/api/llm/traces", trace_payload)
            if status in (200, 201):
                trace_success += 1
                icon = "✅" if trace.get("status") == "success" else "🚨"
                print(f"  {icon} [{idx}/{len(traces)}] {trace.get('name')} [{trace.get('model')}] -> Ingested")
            else:
                print(f"  ❌ [{idx}/{len(traces)}] {trace.get('name')}: Status {status} - {res}")
            if delay > 0:
                time.sleep(delay)

    print("\n" + "=" * 65)
    print(f"🎉 Seeding Complete! Successfully ingested:")
    print(f"   • {metric_success}/{len(metrics)} Metrics")
    print(f"   • {trace_success}/{len(traces)} LLM Traces")
    print(f"View live at your ASI-Telemetry Dashboard or via ASI:One Chat.")
    print("=" * 65)
    return True


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Seed dummy telemetry data into ASI-Telemetry")
    parser.add_argument("--only-metrics", action="store_true", help="Only seed metric records")
    parser.add_argument("--only-traces", action="store_true", help="Only seed LLM trace records")
    parser.add_argument("--stream", action="store_true", help="Continuously emit dummy records to simulate live agent activity")
    parser.add_argument("--interval", type=float, default=2.0, help="Interval in seconds between stream events")
    args = parser.parse_args()

    inc_metrics = not args.only_traces
    inc_traces = not args.only_metrics

    if args.stream:
        print(f"🔁 Starting dummy telemetry live stream (Interval: {args.interval}s)... Press Ctrl+C to stop.")
        iteration = 1
        try:
            while True:
                print(f"\n--- Stream Cycle #{iteration} ---")
                seed_data(include_metrics=inc_metrics, include_traces=inc_traces, delay=0.1)
                iteration += 1
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n🛑 Stream stopped by user.")
    else:
        seed_data(include_metrics=inc_metrics, include_traces=inc_traces)


if __name__ == "__main__":
    main()
