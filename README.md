# audio2face-3d-nim

Custom Docker image for NVIDIA Audio2Face-3D NIM with pre-compiled gRPC protos and FastAPI HTTP bridge.

## What this does

Runs inside Modal with GPU. Accepts HTTP POST audio, calls NIM's gRPC server internally, returns blendshape data.

## Deploy

1. Push to GitHub
2. Add repo secrets: `DOCKERHUB_USERNAME=mhdrasal`, `DOCKERHUB_TOKEN=<your-token>`
3. Actions builds `mhdrasal/nim-a2f:latest` automatically
4. In your Modal project: `modal deploy modal_nim.py`
