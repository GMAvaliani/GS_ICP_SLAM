FROM pytorch/pytorch:2.0.0-cuda11.8-cudnn8-devel

WORKDIR /workspace

# System dependencies
RUN apt-get update && apt-get install -y \
    git cmake build-essential libpcl-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone your repo
RUN git clone https://github.com/GMAvaliani/GS_ICP_SLAM.git
WORKDIR /workspace/GS_ICP_SLAM

# Submodules
RUN git submodule update --init --recursive

# Python deps
RUN pip install -r requirements.txt
RUN pip install submodules/diff-gaussian-rasterization
RUN pip install submodules/simple-knn

# FastGICP
RUN cd submodules/fast_gicp && mkdir build && cd build && cmake .. && make -j \
    && cd .. && python setup.py install --user

# RunPod SDK + API utils
RUN pip install runpod fastapi uvicorn requests

# Entrypoint
CMD ["python", "-u", "handler.py"]
