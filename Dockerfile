FROM pytorch/pytorch:2.0.0-cuda11.8-cudnn8-devel

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    git cmake build-essential libpcl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/GMAvaliani/GS_ICP_SLAM.git
WORKDIR /workspace/GS_ICP_SLAM

RUN git submodule update --init --recursive

RUN pip install -r requirements.txt
RUN pip install submodules/diff-gaussian-rasterization
RUN pip install submodules/simple-knn

RUN cd submodules/fast_gicp && mkdir build && cd build && cmake .. && make -j \
    && cd .. && python setup.py install --user

RUN pip install runpod fastapi uvicorn requests

CMD ["python", "-u", "handler.py"]
