"""Shared helpers. Everything is configured by environment variables or CLI flags; no machine-specific paths."""
import glob, json, os, pathlib, re, shutil, subprocess, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_URL = os.environ.get("LLM_URL", "http://127.0.0.1:8081")


def chat(url, messages, max_tokens, temperature=0.0, extra=None, timeout=3600):
    """POST to an OpenAI-compatible /v1/chat/completions endpoint (llama.cpp's server) and return the JSON reply."""
    body = {"model": "x", "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
    body.update(extra or {})
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def cpu_temp_c():
    """CPU package/core temperature in C, or None if it can't be read (works for Intel coretemp and AMD k10temp)."""
    for hw in glob.glob("/sys/class/hwmon/hwmon*"):
        try:
            name = pathlib.Path(hw, "name").read_text().strip()
            if name in ("coretemp", "k10temp", "zenpower"):
                vals = [int(pathlib.Path(p).read_text()) / 1000 for p in glob.glob(hw + "/temp*_input")]
                if vals:
                    return round(max(vals))
        except (OSError, ValueError):
            continue
    return None


def cpu_max_mhz():
    """Highest current core clock in MHz (a snapshot), or None if cpufreq isn't available."""
    vals = []
    for p in glob.glob("/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq"):
        try:
            vals.append(int(pathlib.Path(p).read_text()) / 1000)
        except (OSError, ValueError):
            pass
    return round(max(vals)) if vals else None


def fmt(v, unit=""):
    return "" if v is None else f"{v}{unit}"
