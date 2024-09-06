ARG UBUNTU_VERSION=22.04
ARG CUDA_VERSION=12.1.1

########
# base #
########

FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION} AS base

ARG UID=1000
ARG GID=1000
ARG USER=app
ARG JOBS=1

ENV PATH="/home/${USER}/.local/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_USER=1

# https://github.com/abetlen/llama-cpp-python/blob/main/docker/cuda_simple/Dockerfile
ENV APT_PKGS="git build-essential \
python3 python3-pip gcc wget \
ocl-icd-opencl-dev opencl-headers clinfo \
libclblast-dev libopenblas-dev \
"

RUN apt update && \
    apt install -y ${APT_PKGS} && \
    mkdir -p /etc/OpenCL/vendors && \
    echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd && \
    groupadd -g ${GID} ${USER} && \
    useradd --create-home --no-log-init -u ${UID} -g ${GID} ${USER}

USER ${USER}
WORKDIR /home/${USER}

#########
# build #
#########

FROM base AS build

ENV PIP_PKGS_FOR_DOWNLOAD="huggingface_hub"
ENV PIP_PKGS_FOR_LLAMAFY="torch numpy transformers accelerate"
ENV PIP_PKGS_FOR_CONVERT="-r llama.cpp/requirements/requirements-convert_hf_to_gguf.txt"
ENV CUDA_DOCKER_ARCH=all
ENV GGML_CUDA=1

RUN pip install ${PIP_PKGS_FOR_DOWNLOAD} ${PIP_PKGS_FOR_LLAMAFY} && \
    git clone https://github.com/ggerganov/llama.cpp && \
    pip install ${PIP_PKGS_FOR_CONVERT} && \
    make -j${JOBS} -C llama.cpp llama-quantize

COPY ./app /home/${USER}
CMD ["/bin/bash"]

##########
# server #
##########

FROM base AS server

ENV PIP_PKGS_FOR_SERVER="pytest cmake scikit-build setuptools fastapi uvicorn \
sse-starlette pydantic-settings starlette-context llama-cpp-python \
openai \
"
ENV CMAKE_ARGS="-DGGML_CUDA=on"
ENV CMAKE_BUILD_PARALLEL_LEVEL=${JOBS}
ENV HOST=0.0.0.0

RUN pip install ${PIP_PKGS_FOR_SERVER}

COPY ./app /home/${USER}
CMD ["python3", "server.py"]
