import json
import sys
import socket
import time
import base64 as b64mod

from fastapi import FastAPI, Request
from fastapi.responses import Response

app = FastAPI()

sys.path.insert(0, "/app/protos/_pb2")


def wait_for_grpc(host="localhost", port=52000, timeout=300):
    start = time.time()
    while time.time() - start < timeout:
        try:
            s = socket.create_connection((host, port), timeout=2)
            s.close()
            return True
        except (ConnectionRefusedError, OSError):
            time.sleep(2)
    return False


def call_grpc_a2f(audio_bytes: bytes) -> list:
    import grpc
    import nvidia_ace.services.a2f_controller.v1_pb2 as pb2
    import nvidia_ace.services.a2f_controller.v1_pb2_grpc as pb2_grpc
    import nvidia_ace.controller.v1_pb2 as ctrl_pb2
    import nvidia_ace.a2f.v1_pb2 as a2f_pb2
    import nvidia_ace.audio.v1_pb2 as audio_pb2

    channel = grpc.insecure_channel("localhost:52000")
    stub = pb2_grpc.A2FControllerServiceStub(channel)

    audio_header = audio_pb2.AudioHeader(
        audio_format=audio_pb2.AudioHeader.AUDIO_FORMAT_PCM,
        channel_count=1,
        samples_per_second=16000,
        bits_per_sample=16,
    )

    def stream_msgs():
        yield ctrl_pb2.AudioStream(
            audio_stream_header=ctrl_pb2.AudioStreamHeader(audio_header=audio_header)
        )
        yield ctrl_pb2.AudioStream(
            audio_with_emotion=a2f_pb2.AudioWithEmotion(audio_buffer=audio_bytes)
        )
        yield ctrl_pb2.AudioStream(
            end_of_audio=ctrl_pb2.AudioStream.EndOfAudio()
        )

    responses = stub.ProcessAudioStream(stream_msgs())
    frames = []
    for response in responses:
        if response.HasField("animation_data") and response.animation_data.skel_animation:
            skel = response.animation_data.skel_animation
            names = list(skel.blend_shapes) if skel.blend_shapes else []
            for bs in skel.blend_shape_weights:
                bs_map = {}
                for i, val in enumerate(bs.values):
                    key = names[i] if i < len(names) else f"bs_{i}"
                    bs_map[key] = round(float(val), 4)
                frames.append({
                    "timestampMs": int(bs.time_code * 1000),
                    "blendshapes": bs_map
                })
            break
    channel.close()
    return frames


@app.get("/health")
async def health():
    return Response(content='{"status":"ok"}', media_type="application/json")


@app.post("/process-audio")
async def process_audio(request: Request):
    if not wait_for_grpc(timeout=300):
        return Response(
            content=json.dumps({"error": "NIM gRPC server not ready"}),
            status_code=503,
            media_type="application/json"
        )

    content_type = request.headers.get("content-type", "")
    body = await request.body()

    if len(body) == 0:
        return Response(
            content=json.dumps({"error": "No audio data"}),
            status_code=400,
            media_type="application/json"
        )

    if "application/json" in content_type:
        try:
            payload = json.loads(body)
            audio_data = b64mod.b64decode(payload["audio"])
        except Exception as e:
            return Response(
                content=json.dumps({"error": f"Invalid JSON: {e}"}),
                status_code=400,
                media_type="application/json"
            )
    else:
        audio_data = body

    try:
        frames = call_grpc_a2f(audio_data)
    except Exception as e:
        return Response(
            content=json.dumps({"error": str(e)}),
            status_code=500,
            media_type="application/json"
        )

    return Response(
        content=json.dumps({"frames": frames}),
        media_type="application/json"
    )
