import modal
import json

app = modal.App("audio2face-3d-nim")

cache_volume = modal.Volume.from_name("nim-cache", create_if_missing=True)
workspace_volume = modal.Volume.from_name("nim-workspace", create_if_missing=True)

# Modal builds the Docker image (has enough disk space, unlike GitHub Actions free tier)
nim_image = modal.Image.from_dockerfile(
    "Dockerfile",
    context_local_dir=".",
    secret=modal.Secret.from_name("nvcr-secret"),
)

_light_image = modal.Image.debian_slim(python_version="3.12").pip_install("fastapi[standard]")


@app.function(
    image=nim_image,
    gpu="L40S",
    secrets=[modal.Secret.from_name("nvcr-secret")],
    timeout=3600,
    scaledown_window=300,
    max_containers=1,
    volumes={
        "/opt/nim/.cache": cache_volume,
        "/opt/nim/workspace": workspace_volume
    }
)
@modal.web_server(port=8080, startup_timeout=600)
def process_audio():
    import socket
    import time

    print("[modal] Waiting for bridge server on port 8080...", flush=True)
    for _ in range(300):
        try:
            s = socket.create_connection(("localhost", 8080), timeout=2)
            s.close()
            print("[modal] Bridge server ready", flush=True)
            break
        except (ConnectionRefusedError, OSError):
            time.sleep(1)
    else:
        print("[modal] ERROR: Bridge server did not start within 300s", flush=True)
        return

    while True:
        time.sleep(60)


@app.function(
    image=_light_image,
    timeout=10,
)
@modal.fastapi_endpoint(method="GET")
async def health():
    from fastapi.responses import Response as FastResponse
    return FastResponse(content='{"status":"ok"}', media_type="application/json")
