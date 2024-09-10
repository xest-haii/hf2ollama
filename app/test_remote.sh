#!/bin/sh

OPENAI_BASE_URL="${OPENAI_BASE_URL:-http://localhost:8000/v1}"
OPENAI_API_KEY="${OPENAI_API_KEY:-openai}"
MODEL="${MODEL:-LGAI-EXAONE/EXAONE-3.0-7.8B-Instruct}"
SYSTEM_MESSAGE="${SYSTEM_MESSAGE:-You are a helpful assistant.}"
USER_MESSAGE="${USER_MESSAGE:-Hi}"
STREAM="${STREAM:-0}"
VERBOSE="${VERBOSE:-0}"

CURL=curl
if [ ${VERBOSE} -ne 0 ]; then
	CURL="${CURL} -v"
fi

echo "* /v1/models"
time ${CURL} ${OPENAI_BASE_URL}/models
echo

echo "* /v1/chat/completions"
time ${CURL} ${OPENAI_BASE_URL}/chat/completions \
	-H "Content-Type: application/json" \
	-d @- <<EOF
{
	"model": "${MODEL}",
	"messages": [
		{
			"role": "system",
			"content": "${SYSTEM_MESSAGE}"
		},
		{
			"role": "user",
			"content": "${USER_MESSAGE}"
		}
	],
	"stream": ${STREAM}
}
EOF
echo
