"""Shared HTTP client for BizMate frontend → backend communication."""

import os

import requests
import streamlit as st

API_BASE = os.getenv("BIZMATE_API_URL", "http://localhost:8000")


def _handle_error(exc: Exception) -> None:
    if isinstance(exc, requests.ConnectionError):
        st.error("⚠️ Cannot connect to the backend. Make sure the API server is running on port 8000.")
    elif isinstance(exc, requests.Timeout):
        st.error("Request timed out. The server may be busy — please try again.")
    elif isinstance(exc, requests.HTTPError):
        try:
            detail = exc.response.json().get("detail", str(exc))
        except Exception:
            detail = str(exc)
        st.error(f"API error: {detail}")
    else:
        st.error(f"Unexpected error: {exc}")


def api_get(endpoint: str) -> dict | list | None:
    try:
        r = requests.get(f"{API_BASE}{endpoint}", timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        _handle_error(exc)
        return None


def api_post(endpoint: str, json=None, data=None, files=None) -> dict | None:
    try:
        r = requests.post(
            f"{API_BASE}{endpoint}", json=json, data=data, files=files, timeout=90
        )
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        _handle_error(exc)
        return None


def api_delete(endpoint: str) -> bool:
    try:
        r = requests.delete(f"{API_BASE}{endpoint}", timeout=15)
        r.raise_for_status()
        return True
    except Exception as exc:
        _handle_error(exc)
        return False
