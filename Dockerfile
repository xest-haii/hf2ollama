FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ARG UID=1000
ARG GID=1000
ARG USER=app

RUN \
	groupadd -g ${GID} ${USER} && \
	useradd --create-home --no-log-init -u ${UID} -g ${GID} ${USER}
USER ${USER}

WORKDIR /home/app

# for download
RUN pip install --user huggingface_hub

# for llamafy
RUN pip install --user torch numpy transformers accelerate

# for convert and quantize
RUN git clone https://github.com/ggerganov/llama.cpp
RUN pip install --user -r llama.cpp/requirements/requirements-convert_hf_to_gguf.txt
RUN make -C llama.cpp llama-quantize

# for server
RUN make -C llama.cpp llama-server
RUN pip install --user fastapi openai pydantic uvicorn

COPY ./app /home/app
ENV PATH="/home/app/.local/bin:$PATH"
CMD ["/usr/bin/bash"]
