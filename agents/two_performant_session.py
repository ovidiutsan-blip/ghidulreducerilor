"""Sesiune 2Performant partajată între agenți (feed import, link validator, codes).

Rezolvă furtuna de 429 din pipeline:
- UN singur login per run (token cache pe disc — data/.2p_session.json, gitignored),
  refolosit de toți agenții care rulează în același job.
- Backoff exponențial cu jitter la 429 (respectă Retry-After dacă există).
- Throttle client-side între request-uri (min MIN_INTERVAL secunde).
- Circuit breaker: după MAX_CONSECUTIVE_429 rate-limit-uri consecutive, orice
  apel ulterior ridică TwoPerformantRateLimited imediat — agenții tratează asta
  ca "skip run", fără să mai lovească API-ul.

Utilizare:
    from two_performant_session import api_get, TwoPerformantRateLimited
    data = api_get("affiliate/product_feeds", params={"page": 1})
"""
from __future__ import annotations
import os, json, time, random
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.2performant.com"
BASE = Path(__file__).resolve().parent.parent
TOKEN_CACHE_PATH = BASE / "data" / ".2p_session.json"

MIN_INTERVAL = 1.2           # secunde minime între request-uri API
MAX_RETRIES_429 = 3          # retry-uri per request la 429
MAX_CONSECUTIVE_429 = 6      # după atâtea 429 consecutive => circuit deschis
MAX_LOGIN_ATTEMPTS = 2       # login-ul e și el rate-limited; nu insista
TOKEN_TTL_SECONDS = 12 * 3600  # cache-ul de token e considerat valid 12h


def _clean_env(key: str, default: str = "") -> str:
    return os.getenv(key, default).lstrip("﻿").strip()


EMAIL    = _clean_env("TWO_PERFORMANT_EMAIL")
PASSWORD = _clean_env("TWO_PERFORMANT_PASSWORD")


class TwoPerformantRateLimited(Exception):
    """API-ul 2Performant e rate-limited; agenții trebuie să sară peste run."""


class _State:
    token: str = _clean_env("TWO_PERFORMANT_ACCESS_TOKEN")
    client: str = _clean_env("TWO_PERFORMANT_CLIENT_ID")
    uid: str = _clean_env("TWO_PERFORMANT_UID", EMAIL or "")
    last_request_ts: float = 0.0
    consecutive_429: int = 0
    circuit_open: bool = False
    login_attempts: int = 0


_state = _State()


def _load_token_cache() -> bool:
    """Încarcă tokenul salvat de un agent anterior din același run. True dacă valid."""
    try:
        raw = json.loads(TOKEN_CACHE_PATH.read_text(encoding="utf-8"))
        if time.time() - raw.get("ts", 0) > TOKEN_TTL_SECONDS:
            return False
        if raw.get("token") and raw.get("client"):
            _state.token = raw["token"]
            _state.client = raw["client"]
            _state.uid = raw.get("uid", _state.uid)
            return True
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return False


def _save_token_cache() -> None:
    try:
        TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_CACHE_PATH.write_text(json.dumps({
            "token": _state.token, "client": _state.client,
            "uid": _state.uid, "ts": time.time(),
        }), encoding="utf-8")
    except OSError:
        pass  # cache-ul e best-effort


def _throttle() -> None:
    wait = _state.last_request_ts + MIN_INTERVAL - time.time()
    if wait > 0:
        time.sleep(wait)
    _state.last_request_ts = time.time()


def _backoff_sleep(attempt: int, resp: requests.Response | None) -> None:
    retry_after = 0.0
    if resp is not None:
        try:
            retry_after = float(resp.headers.get("Retry-After", 0))
        except (TypeError, ValueError):
            retry_after = 0.0
    delay = max(retry_after, (2 ** attempt) * 5) + random.uniform(0, 2)
    print(f"[2p-session] 429 — backoff {delay:.0f}s (attempt {attempt + 1}/{MAX_RETRIES_429})")
    time.sleep(delay)


def _record_429() -> None:
    _state.consecutive_429 += 1
    if _state.consecutive_429 >= MAX_CONSECUTIVE_429:
        _state.circuit_open = True
        print(f"[2p-session] Circuit OPEN după {_state.consecutive_429} × 429 consecutive — skip restul apelurilor.")


def _record_success() -> None:
    _state.consecutive_429 = 0


def login(force: bool = False) -> None:
    """Login DeviseTokenAuth cu protecție anti-spam: max MAX_LOGIN_ATTEMPTS/proces."""
    if _state.circuit_open:
        raise TwoPerformantRateLimited("circuit open — nu mai încercăm login")
    if not force and _state.token and _state.client:
        return
    if not force and _load_token_cache():
        print("[2p-session] Token reutilizat din cache disc.")
        return
    if not EMAIL or not PASSWORD:
        raise ValueError("Lipsesc TWO_PERFORMANT_EMAIL / TWO_PERFORMANT_PASSWORD.")
    if _state.login_attempts >= MAX_LOGIN_ATTEMPTS:
        raise TwoPerformantRateLimited(f"login abandonat după {_state.login_attempts} încercări")

    for attempt in range(MAX_RETRIES_429):
        _state.login_attempts += 1
        if _state.login_attempts > MAX_LOGIN_ATTEMPTS:
            raise TwoPerformantRateLimited("prea multe încercări de login în acest proces")
        _throttle()
        resp = requests.post(
            f"{API_BASE}/users/sign_in",
            json={"user": {"email": EMAIL, "password": PASSWORD}},
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=20,
        )
        if resp.status_code == 429:
            _record_429()
            if _state.circuit_open:
                raise TwoPerformantRateLimited("sign_in rate-limited (429), circuit open")
            _backoff_sleep(attempt, resp)
            continue
        resp.raise_for_status()
        _record_success()
        _state.token = resp.headers.get("access-token", "")
        _state.client = resp.headers.get("client", "")
        _state.uid = resp.headers.get("uid", EMAIL)
        if not _state.token:
            raise ValueError(f"Login HTTP {resp.status_code} dar access-token absent din headers.")
        _save_token_cache()
        print(f"[2p-session] Login OK — uid={_state.uid}")
        return
    raise TwoPerformantRateLimited("sign_in rate-limited (429) după toate retry-urile")


def auth_headers() -> dict:
    if not _state.token or not _state.client:
        login()
    return {
        "access-token": _state.token,
        "token-type":   "Bearer",
        "client":       _state.client,
        "uid":          _state.uid,
        "Accept":       "application/json",
        "Content-Type": "application/json",
    }


def _safe_json(r: requests.Response):
    return json.loads(r.content.decode("utf-8-sig"))


def api_get(path: str, params: dict | None = None, timeout: int = 30):
    """GET autenticat cu throttle + backoff 429 + circuit breaker.
    Întoarce JSON-ul parsat. Ridică TwoPerformantRateLimited când circuit-ul e deschis.
    """
    if _state.circuit_open:
        raise TwoPerformantRateLimited("circuit open")
    url = f"{API_BASE}/{path.lstrip('/')}"
    for attempt in range(MAX_RETRIES_429 + 1):
        _throttle()
        r = requests.get(url, headers=auth_headers(), params=params, timeout=timeout)
        if r.status_code == 429:
            _record_429()
            if _state.circuit_open:
                raise TwoPerformantRateLimited(f"429 pe {path}, circuit open")
            if attempt < MAX_RETRIES_429:
                _backoff_sleep(attempt, r)
                continue
            raise TwoPerformantRateLimited(f"429 persistent pe {path}")
        if r.status_code == 401:
            # token expirat — un singur re-login apoi retry
            print("[2p-session] 401 — token expirat, re-login...")
            _state.token = ""
            login(force=True)
            continue
        r.raise_for_status()
        _record_success()
        return _safe_json(r)
    raise TwoPerformantRateLimited(f"retry-uri epuizate pe {path}")
