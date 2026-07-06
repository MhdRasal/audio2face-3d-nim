FROM nvcr.io/nim/nvidia/audio2face-3d:latest

RUN pip install --no-cache-dir \
    --index-url https://pypi.org/simple \
    "grpcio-tools>=1.64.0" \
    "fastapi[standard]"

COPY deps/Audio2Face-3D-Samples/proto/protobuf_files /app/protos/

RUN mkdir -p /app/protos/_pb2 && \
    python -m grpc_tools.protoc \
    --proto_path=/app/protos \
    --python_out=/app/protos/_pb2 \
    --grpc_python_out=/app/protos/_pb2 \
    /app/protos/nvidia_ace.services.a2f_controller.v1.proto \
    /app/protos/nvidia_ace.controller.v1.proto \
    /app/protos/nvidia_ace.a2f.v1.proto \
    /app/protos/nvidia_ace.animation_data.v1.proto \
    /app/protos/nvidia_ace.animation_id.v1.proto \
    /app/protos/nvidia_ace.audio.v1.proto \
    /app/protos/nvidia_ace.status.v1.proto \
    /app/protos/nvidia_ace.emotion_with_timecode.v1.proto \
    /app/protos/nvidia_ace.emotion_aggregate.v1.proto

RUN touch /app/protos/_pb2/__init__.py

COPY bridge_server.py /app/bridge_server.py
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
