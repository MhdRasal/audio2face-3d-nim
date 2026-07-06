import modal
import json

app = modal.App("audio2face-3d-nim")

cache_volume = modal.Volume.from_name("nim-cache", create_if_missing=True)
workspace_volume = modal.Volume.from_name("nim-workspace", create_if_missing=True)

PROTO_DIR = "/app/protos"
PB2_DIR = "/app/protos/_pb2"

nim_image = (
    modal.Image.from_registry(
        "nvcr.io/nim/nvidia/audio2face-3d:latest",
        secret=modal.Secret.from_name("nvcr-secret"),
    )
    .pip_install(
        "grpcio-tools>=1.64.0",
        "fastapi[standard]",
        index_url="https://pypi.org/simple",
    )
    .add_local_dir(
        "deps/Audio2Face-3D-Samples/proto/protobuf_files",
        remote_path=PROTO_DIR,
    )
    .run_commands(
        f"mkdir -p {PB2_DIR} && "
        f"python -m grpc_tools.protoc "
        f"--proto_path={PROTO_DIR} "
        f"--python_out={PB2_DIR} "
        f"--grpc_python_out={PB2_DIR} "
        f"{PROTO_DIR}/nvidia_ace.services.a2f_controller.v1.proto "
        f"{PROTO_DIR}/nvidia_ace.controller.v1.proto "
        f"{PROTO_DIR}/nvidia_ace.a2f.v1.proto "
        f"{PROTO_DIR}/nvidia_ace.animation_data.v1.proto "
        f"{PROTO_DIR}/nvidia_ace.animation_id.v1.proto "
        f"{PROTO_DIR}/nvidia_ace.audio.v1.proto "
        f"{PROTO_DIR}/nvidia_ace.status.v1.proto "
        f"{PROTO_DIR}/nvidia_ace.emotion_with_timecode.v1.proto "
        f"{PROTO_DIR}/nvidia_ace.emotion_aggregate.v1.proto"
    )
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
