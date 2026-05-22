"""
Quick smoke test for the Tempo API.

Before running, create a test user:
  cd backend && python manage.py shell -c \
    "from django.contrib.auth.models import User; User.objects.create_user('testuser', password='testpass123')"

Then run (with venv active):
  python test_api.py
"""

import json
import sys
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8000/api"
USERNAME = "testuser"
PASSWORD = "testpass123"

passed = 0
failed = 0


def req(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, json.loads(raw) if raw else None


def check(label, status, expected, body=None):
    global passed, failed
    ok = status == expected
    mark = "OK" if ok else "FAIL"
    print(f"  [{mark}] {label} (HTTP {status})")
    if not ok:
        print(f"       response: {body}")
        failed += 1
    else:
        passed += 1
    return ok


# ── Auth ──────────────────────────────────────────────────────────────────────
print("\n── Auth ──")
status, body = req("POST", "/auth/token/", {"username": USERNAME, "password": PASSWORD})
if not check("obtain JWT token", status, 200, body):
    print(f"\n  No user found. Run this first:")
    print(f"  cd backend && python manage.py shell -c \"from django.contrib.auth.models import User; User.objects.create_user('{USERNAME}', password='{PASSWORD}')\"")
    sys.exit(1)
token = body["access"]

status, body = req("POST", "/auth/token/refresh/", {"refresh": body["refresh"]})  # reuse body before reassignment
check("refresh token", status, 200, body)

# ── Habits CRUD ───────────────────────────────────────────────────────────────
print("\n── Habits ──")
status, body = req("POST", "/habits/", {"name": "Read", "description": "Read books", "period": "daily", "time": 30}, token)
check("create daily habit", status, 201, body)
daily_id = body.get("id")

status, body = req("POST", "/habits/", {"name": "Exercise", "period": "weekly", "time": 180}, token)
check("create weekly habit", status, 201, body)
weekly_id = body.get("id")

status, body = req("GET", "/habits/", token=token)
if check("list habits", status, 200, body):
    count_ok = len(body) == 2
    print(f"  [{'OK' if count_ok else 'FAIL'}] habit count == 2 (got {len(body)})")
    passed += count_ok
    failed += not count_ok

status, body = req("GET", f"/habits/{daily_id}/", token=token)
check("get habit by id", status, 200, body)

status, body = req("PATCH", f"/habits/{daily_id}/", {"name": "Read books", "time": 45}, token)
if check("patch habit", status, 200, body):
    name_ok = body.get("name") == "Read books"
    time_ok = body.get("time") == 45
    print(f"  [{'OK' if name_ok else 'FAIL'}] name updated")
    print(f"  [{'OK' if time_ok else 'FAIL'}] time updated")
    passed += name_ok + time_ok
    failed += (not name_ok) + (not time_ok)

# ── Timing ────────────────────────────────────────────────────────────────────
print("\n── Timing ──")
status, body = req("GET", "/timing/", token=token)
check("list all timings", status, 200, body)

status, body = req("GET", f"/timing/{daily_id}/", token=token)
if check("get timing", status, 200, body):
    expected_secs = 45 * 60
    tr_ok = body.get("time_remaining") == expected_secs
    running_ok = body.get("is_running") is False
    print(f"  [{'OK' if tr_ok else 'FAIL'}] time_remaining == {expected_secs}s (got {body.get('time_remaining')})")
    print(f"  [{'OK' if running_ok else 'FAIL'}] is_running == False")
    passed += tr_ok + running_ok
    failed += (not tr_ok) + (not running_ok)

status, body = req("PUT", f"/timing/{daily_id}/", {"time_remaining": 45 * 60, "is_running": True}, token)
if check("start timer", status, 200, body):
    running_ok = body.get("is_running") is True
    print(f"  [{'OK' if running_ok else 'FAIL'}] is_running == True")
    passed += running_ok
    failed += not running_ok

status, body = req("PUT", f"/timing/{daily_id}/", {"time_remaining": 2000, "is_running": False}, token)
if check("pause timer", status, 200, body):
    tr_ok = body.get("time_remaining") == 2000
    running_ok = body.get("is_running") is False
    print(f"  [{'OK' if tr_ok else 'FAIL'}] time_remaining == 2000")
    print(f"  [{'OK' if running_ok else 'FAIL'}] is_running == False")
    passed += tr_ok + running_ok
    failed += (not tr_ok) + (not running_ok)

# ── Auth enforcement ──────────────────────────────────────────────────────────
print("\n── Auth enforcement ──")
status, body = req("GET", "/habits/")
check("reject unauthenticated request", status, 401, body)

status, body = req("GET", f"/habits/{daily_id}/", token="bad.token.value")
check("reject invalid token", status, 401, body)

# ── Cleanup ───────────────────────────────────────────────────────────────────
print("\n── Cleanup ──")
status, _ = req("DELETE", f"/habits/{daily_id}/", token=token)
check("delete daily habit", status, 204)
status, _ = req("DELETE", f"/habits/{weekly_id}/", token=token)
check("delete weekly habit", status, 204)

status, body = req("GET", "/habits/", token=token)
if check("list habits after delete", status, 200, body):
    empty_ok = len(body) == 0
    print(f"  [{'OK' if empty_ok else 'FAIL'}] habit list is empty (got {len(body)})")
    passed += empty_ok
    failed += not empty_ok

# ── Summary ───────────────────────────────────────────────────────────────────
total = passed + failed
print(f"\n{'─' * 40}")
print(f"  {passed}/{total} checks passed", "✓" if failed == 0 else "✗")
if failed:
    sys.exit(1)
