import json
import os

from openai import OpenAI


OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'http://localhost:8000/v1')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'openai')
MODEL = os.getenv('MODEL', 'LGAI/EXAONE_EXAONE-3.0-7.8B-Instruct')
SYSTEM_MESSAGE = os.getenv('SYSTEM_MESSAGE', 'You are a helpful assistant.')
USER_MESSAGE = os.getenv('USER_MESSAGE', 'Hi')
STREAM = bool(os.getenv('STREAM', False))
VERBOSE = bool(os.getenv('VERBOSE', False))

client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
response = client.chat.completions.create(
  model=MODEL,
  messages=[
    {
      'role': 'system',
      'content': SYSTEM_MESSAGE,
    },
    {
      'role': 'user',
      'content': USER_MESSAGE,
    },
  ],
  stream=STREAM,
)

if STREAM:
  for chunk in response:
    if VERBOSE:
      print(chunk.to_json())
    else:
      print(chunk.choices[0].delta.content, end='', flush=True)
  print('', flush=True)
else:
  if VERBOSE:
    print(response.to_json())
  else:
    print(response.choices[0].message.content)
