import json
import os

from llama_cpp import Llama

MODEL = os.getenv('MODEL', 'LGAI-EXAONE/EXAONE-3.0-7.8B-Instruct')
SYSTEM_MESSAGE = os.getenv('SYSTEM_MESSAGE', 'You are a helpful assistant.')
USER_MESSAGE = os.getenv('USER_MESSAGE', 'Hi')
STREAM = bool(os.getenv('STREAM', False))
VERBOSE = bool(os.getenv('VERBOSE', False))

llm = Llama(
  model_path=os.path.join('/models/', f'{MODEL}-Llamafied-Q4_K_M.gguf'),
  n_gpu_layers=-1,
)

response = llm.create_chat_completion_openai_v1(
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
