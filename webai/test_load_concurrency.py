"""
Concurrent High-Load & Load Testing Simulation for OrgChat AI
Simulates high concurrent user traffic to measure Requests Per Second (RPS), Average Latency, and Error Rate.
Usage:
    python test_load_concurrency.py
"""
import sys
import os
import time
import concurrent.futures
import statistics

os.environ["FLASK_ENV"] = "testing"

try:
    from app_server import create_app
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app_server import create_app


def run_load_simulation(num_users=100, requests_per_user=5):
    app = create_app()
    app.config["TESTING"] = True
    
    total_requests = num_users * requests_per_user
    print(f"🚀 Simulating {num_users} concurrent users (Total Requests: {total_requests})...")
    
    latencies = []
    success_count = 0
    error_count = 0
    
    def user_session(user_id):
        nonlocal success_count, error_count
        client = app.test_client()
        with client.session_transaction() as sess:
            sess["user"] = f"load_user_{user_id}"
            sess["org_id"] = 1
            
        endpoints = ["/api/ping", "/api/version", "/api/status"]
        
        user_latencies = []
        for i in range(requests_per_user):
            endpoint = endpoints[i % len(endpoints)]
            t0 = time.time()
            try:
                res = client.get(endpoint)
                elapsed = (time.time() - t0) * 1000 # ms
                user_latencies.append(elapsed)
                if res.status_code == 200:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
        return user_latencies

    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [executor.submit(user_session, i) for i in range(num_users)]
        for f in concurrent.futures.as_completed(futures):
            latencies.extend(f.result())
            
    total_time = time.time() - start_time
    rps = total_requests / total_time if total_time > 0 else 0
    avg_latency = statistics.mean(latencies) if latencies else 0
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else avg_latency
    
    print("\n==========================================================")
    print(" 📊 LOAD TESTING & SIMULATION RESULTS")
    print("==========================================================")
    print(f"✔️ Total Requests Processed: {len(latencies)}")
    print(f"✔️ Successful Responses (200 OK): {success_count}")
    print(f"❌ Failed Requests: {error_count}")
    print(f"⏱️ Total Duration: {total_time:.2f} seconds")
    print(f"⚡ Throughput (RPS): {rps:.2f} req/sec")
    print(f"📈 Average Latency: {avg_latency:.2f} ms")
    print(f"📉 P95 Latency (95% requests): {p95_latency:.2f} ms")
    print("==========================================================")


if __name__ == "__main__":
    run_load_simulation(num_users=50, requests_per_user=10)
