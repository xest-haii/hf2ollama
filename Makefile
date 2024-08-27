DIR_ROOT := $(CURDIR)
DIR_APP := $(DIR_ROOT)/app
DIR_MODELS := $(DIR_ROOT)/models
DIR_STAMPS := $(DIR_ROOT)/stamps

DOCKER_IMAGE := $(notdir $(DIR_ROOT))-$(USER)
UID := $(shell id -u)
GID := $(shell id -g)

HF_CACHE := .cache/huggingface
HF_MODEL_ID_DEFAULT := LGAI-EXAONE/EXAONE-3.0-7.8B-Instruct
HF_MODEL_ID ?= $(HF_MODEL_ID_DEFAULT)
HF_MODEL_NAME := $(subst /,_,$(HF_MODEL_ID))

QUANTIZE_METHOD_DEFAULT := Q4_K_M
QUANTIZE_METHOD ?= $(QUANTIZE_METHOD_DEFAULT)
MODEL_OFFICIAL := /models/$(HF_MODEL_ID)
MODEL_LLAMAFIED := /models/$(HF_MODEL_ID)-Llamafied
MODEL_CONVERTED := /models/$(HF_MODEL_ID)-Llamafied.gguf
MODEL_QUANTIZED := /models/$(HF_MODEL_ID)-LLamafied-$(QUANTIZE_METHOD).gguf

OLLAMA_IMAGE := ollama/ollama
OLLAMA_MODEL_DEFAULT := exaone3
OLLAMA_MODEL ?= $(OLLAMA_MODEL_DEFAULT)
OLLAMA_MODEL_FILE_TEMPLATE := Modelfile.$(HF_MODEL_NAME)
OLLAMA_MODEL_FILE := $(MODEL_QUANTIZED).modelfile
OLLAMA_HOST_DEFAULT := http://localhost:11434
OLLAMA_HOST ?= $(OLLAMA_HOST_DEFAULT)

define HELP_HEADING
echo
echo "$(1)"
printf "%$$(echo -n $(1) | wc -c)s\n" | sed "s/ /-/g"
endef

define HELP
printf "* %-20s : %s\n" $(1) $(2)
endef

define DOCKER_BUILD
docker build \
	-t $(DOCKER_IMAGE) \
	--build-arg UID=$(UID) \
	--build-arg GID=$(GID) \
	$(DIR_ROOT)
endef

define DOCKER_RUN
docker run \
	--rm \
	--gpus all \
	-v $(HOME)/$(HF_CACHE):/root/$(HF_CACHE) \
	-v ./models:/models \
	-e UID=$(UID) \
	-e GID=$(GID) \
	-e HF_MODEL_ID=$(HF_MODEL_ID) \
	-e QUANTIZE_METHOD=$(QUANTIZE_METHOD) \
	-e MODEL_OFFICIAL=$(MODEL_OFFICIAL) \
	-e MODEL_LLAMAFIED=$(MODEL_LLAMAFIED) \
	-e MODEL_CONVERTED=$(MODEL_CONVERTED) \
	-e MODEL_QUANTIZED=$(MODEL_QUANTIZED) \
	-e OLLAMA_MODEL_FILE_TEMPLATE=$(OLLAMA_MODEL_FILE_TEMPLATE) \
	-e OLLAMA_MODEL_FILE=$(OLLAMA_MODEL_FILE) \
	$(DOCKER_IMAGE) \
	./main.sh $(1)
endef

define DOCKER_OLLAMA_RUN
docker run \
	--rm \
	-it \
	-v ./models:/models \
	-e OLLAMA_HOST=$(OLLAMA_HOST) \
	$(OLLAMA_IMAGE) \
	$(1)
endef

ifeq ($(V),)
.SILENT:
endif

.PHONY: all help build download llamafy convert quantize create run \
	force-build force-download force-llamafy force-convert force-quantize \
	clean distclean

all: help

help:
	$(call HELP_HEADING,"Environment Variables")
	$(call HELP,HF_MODEL_ID,"Hugging Face Model ID (default: $(HF_MODEL_ID_DEFAULT))")
	$(call HELP,QUANTIZE_METHOD,"Quantize method (default: $(QUANTIZE_METHOD_DEFAULT))")
	$(call HELP,OLLAMA_MODEL,"Ollama model name (default: $(OLLAMA_MODEL_DEFAULT))")
	$(call HELP,OLLAMA_HOST,"Ollama host url (default: $(OLLAMA_HOST_DEFAULT))")
	$(call HELP_HEADING,"Targets")
	$(call HELP,"make build","Build a docker image for building")
	$(call HELP,"make download","Download the official model from Hugging Face")
	$(call HELP,"make llamafy","Llamafy the official model")
	$(call HELP,"make convert","Convert the Llamafied model to a gguf model")
	$(call HELP,"make quantize","Quantize the gguf model")
	$(call HELP,"make create","Create a model that can be used in Ollama")
	$(call HELP,"make run","Run Ollama CLI")
	$(call HELP,"make clean","Delete the docker images for building")
	$(call HELP,"make distclean","Delete the docker images for building and all the files generated")
	echo

build: $(DIR_STAMPS)/built
$(DIR_STAMPS)/built: Dockerfile $(DIR_APP)/*
	$(call DOCKER_BUILD)
	touch $@

download: build $(DIR_STAMPS)/downloaded.$(HF_MODEL_NAME)
$(DIR_STAMPS)/downloaded.$(HF_MODEL_NAME):
	$(call DOCKER_RUN,download)
	touch $@

llamafy: download $(DIR_STAMPS)/llamafied.$(HF_MODEL_NAME)
$(DIR_STAMPS)/llamafied.$(HF_MODEL_NAME):
	$(call DOCKER_RUN,llamafy)
	touch $@

convert: llamafy $(DIR_STAMPS)/converted.$(HF_MODEL_NAME)
$(DIR_STAMPS)/converted.$(HF_MODEL_NAME):
	$(call DOCKER_RUN,convert)
	touch $@

quantize: convert $(DIR_STAMPS)/quantized.$(HF_MODEL_NAME)
$(DIR_STAMPS)/quantized.$(HF_MODEL_NAME):
	$(call DOCKER_RUN,quantize)
	touch $@

modelfile: build
	$(call DOCKER_RUN,modelfile)

create: quantize modelfile
	$(call DOCKER_OLLAMA_RUN,create $(OLLAMA_MODEL) -f $(OLLAMA_MODEL_FILE))

run:
	$(call DOCKER_OLLAMA_RUN,run $(OLLAMA_MODEL))

clean:
	docker rmi $(DOCKER_IMAGE) $(OLLAMA_IMAGE)

distclean: clean
	rm -rf $(DIR_MODELS)/*
