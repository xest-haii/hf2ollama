#!/bin/sh -e

download() {
	huggingface-cli download ${HF_MODEL_ID} --local-dir=${MODEL_OFFICIAL}
}

llamafy() {
	python llamafy.py ${MODEL_OFFICIAL} ${MODEL_LLAMAFIED}
}

convert() {
	python llama.cpp/convert_hf_to_gguf.py \
		${MODEL_LLAMAFIED} \
		--outfile ${MODEL_CONVERTED} \
		--outtype auto
}

quantize() {
	llama.cpp/llama-quantize \
		${MODEL_CONVERTED} \
		${MODEL_QUANTIZED} \
		${QUANTIZE_METHOD}
}

modelfile() {
	if [ ! -f "${OLLAMA_MODEL_FILE_TEMPLATE}" ]; then
		echo "Error: ${OLLAMA_MODEL_FILE_TEMPLATE} not found"
		exit 1
	fi
	echo "FROM `basename ${MODEL_QUANTIZED}`" > ${OLLAMA_MODEL_FILE}
	echo "" >> ${OLLAMA_MODEL_FILE}
	cat ${OLLAMA_MODEL_FILE_TEMPLATE} >> ${OLLAMA_MODEL_FILE}
	if [ -f "${MODEL_OFFICIAL}/LICENSE" ]; then
		echo "LICENSE \"`cat ${MODEL_OFFICIAL}/LICENSE`\"" >> ${OLLAMA_MODEL_FILE}
	fi
}

case $1 in
download|llamafy|convert|quantize|modelfile)
	$1
	;;
*)
	echo "Invalid argument: $1"
	exit 1
	;;
esac
