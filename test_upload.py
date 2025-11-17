import requests

URL = "http://127.0.0.1:8002/upload"
F = "sample_resume.pdf"   # is file ka path

with open(F, "rb") as fh:
    files = {"file": (F, fh, "application/pdf")}
    r = requests.post(URL, files=files, timeout=30)
    print("HTTP", r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text)
