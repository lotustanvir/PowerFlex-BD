"""PowerFlex BD v2 — Production Validation Suite"""
import requests
import json
import time
import sys

BASE = "http://127.0.0.1:8000"
results = []
failures = []


def test(name, method, path, expect_status=200, timeout=60):
    url = f"{BASE}{path}"
    try:
        start = time.time()
        r = getattr(requests, method)(url, timeout=timeout)
        elapsed = time.time() - start
        data = r.json() if "application/json" in r.headers.get("content-type", "") else None
        ok = r.status_code == expect_status
        results.append((name, ok, r.status_code, elapsed, data))
        status = "PASS" if ok else f"FAIL (got {r.status_code})"
        print(f"  {status} [{r.status_code}] {name} ({elapsed:.2f}s)")
        if not ok:
            print(f"    Expected {expect_status}, got {r.status_code}")
            failures.append(name)
        return data
    except Exception as e:
        results.append((name, False, 0, 0, None))
        print(f"  FAIL [ERR] {name}: {e}")
        failures.append(name)
        return None


# ═══════════════════════════════════════════
# PHASE 1: ENDPOINT STRESS TEST
# ═══════════════════════════════════════════
print("=" * 60)
print("PHASE 1: ENDPOINT STRESS TEST")
print("=" * 60)
print()

d = test("Root", "get", "/")
d = test("Health", "get", "/api/health")
if d:
    print(f"    status={d.get('status')}  services={list(d.get('services', {}).keys())}")

d = test("Grid Live", "get", "/api/grid/live")
if d:
    snap = d.get("grid_snapshot", {})
    print(f"    connected={d.get('connected')}  keys={list(snap.keys())[:8]}")

d = test("Solar Live", "get", "/api/solar/live")
if d:
    print(f"    source={d.get('source')}  forecasts={len(d.get('forecasts', []))}")

d = test("Wind Live", "get", "/api/wind/live")
if d:
    print(f"    source={d.get('source')}  forecasts={len(d.get('forecasts', []))}")

d = test("LoadShield Live", "get", "/api/loadshield/live")
if d:
    print(f"    grid_demand={d.get('grid_demand_mw')}  deficit={d.get('deficit_mw')}")
    print(f"    status={d.get('status')}  action={d.get('action')}")

d = test("Demand Forecast", "get", "/api/demand/forecast")
if d:
    print(f"    hourly_forecast={len(d.get('hourly_forecast', []))}  daily_forecast={len(d.get('daily_forecast', []))}")

d = test("Resources Live", "get", "/api/resources/live")
if d:
    print(f"    solar={d.get('solar', {}).get('capacity_mw')}  wind={d.get('wind', {}).get('capacity_mw')}")

d = test("Biomass Live", "get", "/api/resources/biomass/live")
if d:
    print(f"    units={d.get('unit_count')}  capacity={d.get('total_capacity_mw')}")

d = test("Waste Live", "get", "/api/resources/waste/live")
if d:
    print(f"    plants={d.get('plant_count')}  capacity={d.get('total_capacity_mw')}")

d = test("Nuclear", "get", "/api/resources/nuclear")
if d:
    print(f"    plants={len(d.get('plants', []))}")

d = test("Solar Forecast", "get", "/api/solar/forecast")
if d:
    print(f"    forecasts={len(d.get('forecasts', []))}")

d = test("Wind Forecast", "get", "/api/wind/forecast")
if d:
    print(f"    forecasts={len(d.get('forecasts', []))}")

d = test("PGCB Status", "get", "/api/pgcb/status")
if d:
    print(f"    live={d.get('live')}  source={d.get('source')}")


# ═══════════════════════════════════════════
# PHASE 2: CACHE HIT/MISS VERIFICATION
# ═══════════════════════════════════════════
print()
print("=" * 60)
print("PHASE 2: CACHE HIT/MISS VERIFICATION")
print("=" * 60)
print()

# First call — cache miss
start1 = time.time()
r1 = requests.get(f"{BASE}/api/grid/live", timeout=30)
t1 = time.time() - start1
d1 = r1.json()

# Second call — should be cache hit (faster)
start2 = time.time()
r2 = requests.get(f"{BASE}/api/grid/live", timeout=30)
t2 = time.time() - start2
d2 = r2.json()

print(f"  Grid:    MISS={t1:.3f}s  HIT={t2:.3f}s  speedup={t1/t2:.1f}x")
if t2 < t1:
    print("    PASS — Cache hit is faster")
else:
    print("    WARN — Cache hit not faster (may be first-load overhead)")
    failures.append("Cache grid speedup")

# Solar cache
start1 = time.time()
r1 = requests.get(f"{BASE}/api/solar/live", timeout=30)
t1 = time.time() - start1
start2 = time.time()
r2 = requests.get(f"{BASE}/api/solar/live", timeout=30)
t2 = time.time() - start2
print(f"  Solar:   MISS={t1:.3f}s  HIT={t2:.3f}s  speedup={t1/t2:.1f}x")

# LoadShield cache (depends on grid cache)
start1 = time.time()
r1 = requests.get(f"{BASE}/api/loadshield/live", timeout=60)
t1 = time.time() - start1
start2 = time.time()
r2 = requests.get(f"{BASE}/api/loadshield/live", timeout=60)
t2 = time.time() - start2
print(f"  Shield:  MISS={t1:.3f}s  HIT={t2:.3f}s  speedup={t1/t2:.1f}x")

# Verify data consistency across cache hits
if d1.get("grid_snapshot", {}).get("total_load_mw") == d2.get("grid_snapshot", {}).get("total_load_mw"):
    print("    PASS — Cached data is consistent")
else:
    print("    FAIL — Cached data differs between calls")
    failures.append("Cache consistency")


# ═══════════════════════════════════════════
# PHASE 3: LOADSHIELD CORRECTNESS
# ═══════════════════════════════════════════
print()
print("=" * 60)
print("PHASE 3: LOADSHIELD CORRECTNESS")
print("=" * 60)
print()

d = requests.get(f"{BASE}/api/loadshield/live", timeout=60).json()

# Required fields
required = [
    "timestamp", "status", "grid_demand_mw", "grid_supply_mw",
    "solar_forecast_mw", "wind_forecast_mw", "deficit_mw",
    "load_reduction_mw", "battery_power_mw", "flexible_demand_mw",
    "action", "resource_analysis"
]
missing = [f for f in required if f not in d]
if missing:
    print(f"  FAIL — Missing fields: {missing}")
    failures.append("LoadShield missing fields")
else:
    print(f"  PASS — All {len(required)} required fields present")

# Validate numeric fields
num_fields = ["grid_demand_mw", "grid_supply_mw", "solar_forecast_mw",
              "wind_forecast_mw", "deficit_mw", "load_reduction_mw",
              "battery_power_mw", "flexible_demand_mw"]
for f in num_fields:
    v = d.get(f)
    if v is not None and not isinstance(v, (int, float)):
        print(f"  FAIL — {f} is not numeric: {v}")
        failures.append(f"LoadShield {f} type")

# Validate action enum
valid_actions = [
    "NORMAL", "LOAD_SHEDDING", "LOAD_SHEDDING_IMMINENT",
    "BATTERY_CHARGING", "BATTERY_DISCHARGING",
    "FLEXIBLE_DEMAND_STANDBY", "FLEXIBLE_DEMAND_ACTIVE",
    "OVERGENERATION", "ABNORMAL_GRID"
]
if d.get("action") in valid_actions:
    print(f"  PASS — action='{d['action']}' is valid enum")
else:
    print(f"  FAIL — action='{d.get('action')}' not in valid set")
    failures.append("LoadShield action enum")

# Validate status enum
valid_status = [
    "SUPPLY_SUFFICIENT", "SUPPLY_DEFICIT", "DATA_INCOMPLETE",
    "WAITING_FOR_GRID_DATA", "ERROR"
]
if d.get("status") in valid_status:
    print(f"  PASS — status='{d['status']}' is valid enum")
else:
    print(f"  FAIL — status='{d.get('status')}' not in valid set")
    failures.append("LoadShield status enum")

# Validate resource_analysis
ra = d.get("resource_analysis", {})
if isinstance(ra, dict) and len(ra) > 0:
    print(f"  PASS — resource_analysis has {len(ra)} keys")
    # Check battery and flexible_demand are marked PROTOTYPE
    bat = ra.get("battery", {})
    flex = ra.get("flexible_demand", {})
    if bat.get("status") == "PROTOTYPE":
        print("  PASS — battery marked PROTOTYPE")
    else:
        print(f"  WARN — battery status='{bat.get('status')}' (expected PROTOTYPE)")
    if flex.get("status") == "PROTOTYPE":
        print("  PASS — flexible_demand marked PROTOTYPE")
    else:
        print(f"  WARN — flexible_demand status='{flex.get('status')}' (expected PROTOTYPE)")
else:
    print(f"  FAIL — resource_analysis empty or missing")
    failures.append("LoadShield resource_analysis")

# Deficit logic: if deficit > 0, action should not be NORMAL
deficit = d.get("deficit_mw", 0) or 0
action = d.get("action", "")
if deficit > 0 and action == "NORMAL":
    print(f"  WARN — deficit={deficit} but action=NORMAL (may indicate data issue)")
else:
    print(f"  PASS — deficit/action consistency OK")


# ═══════════════════════════════════════════
# PHASE 4: 9-RESOURCE CORRECTNESS
# ═══════════════════════════════════════════
print()
print("=" * 60)
print("PHASE 4: 9-RESOURCE CORRECTNESS")
print("=" * 60)
print()

d = requests.get(f"{BASE}/api/resources/live", timeout=60).json()

expected_resources = ["solar", "wind", "hydro", "gas", "coal", "nuclear", "biomass", "oil", "import"]
present = list(d.keys())
print(f"  Resources returned: {present}")

for res in expected_resources:
    if res in present:
        rd = d[res]
        cap = rd.get("capacity_mw")
        gen = rd.get("generation_mw")
        print(f"  PASS — {res}: capacity={cap}  generation={gen}")
    else:
        print(f"  FAIL — {res} missing from resources/live")
        failures.append(f"9-resource missing {res}")

# Nuclear must not present installed as generation
nuc = d.get("nuclear", {})
if nuc:
    status = nuc.get("status", "")
    if status == "UNDER_COMMISSIONING":
        gen = nuc.get("generation_mw")
        if gen is None or gen == 0:
            print("  PASS — Nuclear UNDER_COMMISSIONING with no generation")
        else:
            print(f"  FAIL — Nuclear UNDER_COMMISSIONING but generation={gen}")
            failures.append("Nuclear generation leak")
    else:
        print(f"  INFO — Nuclear status={status}")

# Check no fabricated values (should have DATA_UNAVAILABLE or WAITING_FOR_GRID_DATA patterns)
for res in expected_resources:
    rd = d.get(res, {})
    status = rd.get("status", "")
    if status in ("DATA_UNAVAILABLE", "WAITING_FOR_GRID_DATA"):
        print(f"  PASS — {res}: correctly marked {status}")
    elif rd.get("capacity_mw") is not None:
        print(f"  INFO — {res}: has real data (capacity={rd.get('capacity_mw')})")


# ═══════════════════════════════════════════
# PHASE 5: HEALTH CHECK INTEGRITY
# ═══════════════════════════════════════════
print()
print("=" * 60)
print("PHASE 5: HEALTH CHECK INTEGRITY")
print("=" * 60)
print()

d = requests.get(f"{BASE}/api/health", timeout=30).json()
services = d.get("services", {})
modules = d.get("modules", {})

if d.get("status") in ("healthy", "degraded"):
    print(f"  PASS — Health status={d['status']}")
else:
    print(f"  FAIL — Health status={d.get('status')}")
    failures.append("Health status invalid")

for svc_name, svc_data in services.items():
    if isinstance(svc_data, dict):
        cache = svc_data.get("cache", {})
        print(f"  {svc_name}: entries={cache.get('entries', '?')}  hits={cache.get('hits', '?')}  misses={cache.get('misses', '?')}")
    else:
        print(f"  {svc_name}: {svc_data}")

print(f"  Modules: {list(modules.keys())}")


# ═══════════════════════════════════════════
# PHASE 6: STALE DATA VERIFICATION
# ═══════════════════════════════════════════
print()
print("=" * 60)
print("PHASE 6: STALE DATA VERIFICATION")
print("=" * 60)
print()

# Check grid service stale fallback
d = requests.get(f"{BASE}/api/grid/live", timeout=30).json()
source = d.get("source", "")
print(f"  Grid source: {source}")
if "cache" in source.lower() or "stale" in source.lower():
    print("  PASS — Grid serving from cache/stale (expected when PGCB is slow)")
elif "pgcb" in source.lower():
    print("  PASS — Grid serving fresh PGCB data")
else:
    print(f"  INFO — Grid source={source}")

# Check solar stale fallback
d = requests.get(f"{BASE}/api/solar/live", timeout=30).json()
source = d.get("source", "")
print(f"  Solar source: {source}")
if "cache" in source.lower() or "stale" in source.lower():
    print("  PASS — Solar serving from cache/stale")
elif "open-meteo" in source.lower():
    print("  PASS — Solar serving fresh Open-Meteo data")
else:
    print(f"  INFO — Solar source={source}")


# ═══════════════════════════════════════════
# PHASE 7: PERFORMANCE BENCHMARK
# ═══════════════════════════════════════════
print()
print("=" * 60)
print("PHASE 7: PERFORMANCE BENCHMARK")
print("=" * 60)
print()

endpoints = [
    ("Health", "/api/health"),
    ("Grid", "/api/grid/live"),
    ("Solar", "/api/solar/live"),
    ("Wind", "/api/wind/live"),
    ("LoadShield", "/api/loadshield/live"),
    ("Resources", "/api/resources/live"),
    ("Biomass", "/api/resources/biomass/live"),
    ("Waste", "/api/resources/waste/live"),
    ("Nuclear", "/api/resources/nuclear"),
    ("Demand", "/api/demand/forecast"),
    ("Solar FC", "/api/solar/forecast"),
    ("Wind FC", "/api/wind/forecast"),
    ("PGCB", "/api/pgcb/status"),
]

print(f"  {'Endpoint':<16} {'Cached':>10} {'Fresh':>10} {'Speedup':>8}")
print(f"  {'-'*16} {'-'*10} {'-'*10} {'-'*8}")

for name, path in endpoints:
    times = []
    for i in range(2):
        start = time.time()
        try:
            r = requests.get(f"{BASE}{path}", timeout=60)
            elapsed = time.time() - start
            times.append(elapsed)
        except Exception:
            times.append(99)
    if len(times) == 2 and times[1] < times[0]:
        speedup = times[0] / max(times[1], 0.001)
        print(f"  {name:<16} {times[0]:>9.3f}s {times[1]:>9.3f}s {speedup:>7.1f}x")
    else:
        print(f"  {name:<16} {times[0]:>9.3f}s {times[1]:>9.3f}s {'--':>8}")

# Total endpoint count
print(f"\n  Total endpoints tested: {len(results)}")


# ═══════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════
print()
print("=" * 60)
print("VALIDATION SUMMARY")
print("=" * 60)
print()

passed = sum(1 for _, ok, _, _, _ in results if ok)
total = len(results)
print(f"  Endpoints:  {passed}/{total} passed")
print(f"  Failures:   {len(failures)}")
if failures:
    print(f"  Failed items: {failures}")

# Check no localhost self-calls remain
import subprocess
result = subprocess.run(
    ["grep", "-r", "127.0.0.1:8000", "backend/"],
    capture_output=True, text=True, cwd=r"D:\fontend and backend dev\PowerFlex-BD"
)
self_calls = [l for l in result.stdout.splitlines() if "import" not in l and "#" not in l and "localhost" not in l.lower() and "127.0.0.1:8000" in l]
print(f"\n  Localhost self-calls in backend/: {len(self_calls)}")
if self_calls:
    for l in self_calls[:5]:
        print(f"    {l}")
else:
    print("    PASS — No localhost self-calls found")

print()
if not failures:
    print("  ALL VALIDATION CHECKS PASSED")
else:
    print(f"  {len(failures)} ISSUES FOUND — see above")
print()
