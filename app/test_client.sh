#!/bin/sh -x

OPENAI_BASE_URL="${OPENAI_BASE_URL:-http://localhost:8000/v1}"
OPENAI_API_KEY="${OPENAI_API_KEY:-openai}"
MODEL="${MODEL:-LGAI-EXAONE_EXAONE-3.0-7.8B-Instruct}"
SYSTEM_MESSAGE="${SYSTEM_MESSAGE:-You are a helpful assistant.}"
USER_MESSAGE="${USER_MESSAGE:-Hi}"
STREAM="${STREAM:-false}"

curl -v ${OPENAI_BASE_URL}/chat/completions \
	-H "Content-Type: application/json" \
       	-d "{
		\"model\": \"${MODEL}\",
		\"messages\": [
			{
				\"role\": \"system\",
				\"content\": \"${SYSTEM_MESSAGE}\"
			},
			{
				\"role\": \"user\",
				\"content\": \"${USER_MESSAGE}\"
			}
		],
		\"stream\": ${STREAM}
	}"
