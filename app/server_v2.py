import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, StreamingResponse
from llama_cpp import Llama
from pydantic import BaseModel


class ChatMessage(BaseModel):
  role: str
  content: str


class ChatCompletionRequest(BaseModel):
  model: str
  messages: List[ChatMessage]
  stream: Optional[bool] = False


class ModelProvider:
  DIR_MODELS = os.getenv('DIR_MODELS', '/models')
  MODEL_SUFFIX = os.getenv('MODEL_SUFFIX', '-Llamafied-Q4_K_M.gguf')
  MODEL_LIFETIME = int(os.getenv('MODEL_LIFETIME', 3600))
  SERVER_PORT = int(os.getenv('SERVER_PORT', 8000))

  providers = {}

  def __init__(self, model_name, model_path):
    self.model_name = model_name
    self.model_path = model_path
    self.model_ctime = os.path.getctime(model_path)
    self.lock = asyncio.Lock()
    self.model = None
    self.last_used = 0

  @classmethod
  async def providers_init(cls):
    for owner in sorted(os.listdir(cls.DIR_MODELS)):
      dir_path = os.path.join(cls.DIR_MODELS, owner)
      if os.path.isdir(dir_path):
        for file_name in sorted(os.listdir(dir_path)):
          if file_name.endswith(cls.MODEL_SUFFIX):
            model_name = f'{owner}/{file_name.replace(cls.MODEL_SUFFIX, "")}'
            model_path = os.path.join(cls.DIR_MODELS, owner, file_name)
            cls.providers[model_name] = cls(model_name, model_path)
    asyncio.create_task(cls.providers_monitor())

  @classmethod
  async def providers_monitor(cls):
    while True:
      await asyncio.sleep(60)
      now = time.time()
      for model_provider in cls.providers.values():
        async with model_provider.lock:
          if model_provider.model and now - model_provider.last_used > cls.MODEL_LIFETIME:
            await model_provider.unload()

  async def load(self):
    self.last_used = time.time()
    if self.model is None:
      self.model = Llama(model_path=self.model_path, n_gpu_layers=-1, verbose=False)
      logging.info(f'Model {self.model_name} is loaded')

  async def unload(self):
    self.last_used = 0
    if self.model is not None:
      self.model = None
      logging.info(f'Model {self.model_name} is unloaded')

  def sync_chat_completions(self, request):
    return self.model.create_chat_completion(
      model=request.model,
      messages=[m.dict() for m in request.messages],
      stream=request.stream,
    )

  async def stream_response(self, request):
    for chunk in self.sync_chat_completions(request):
      await asyncio.sleep(0)
      choice = chunk.get('choices', [{}])[0]
      delta = choice.get('delta', {})
      if delta.get('content'):
        yield 'data: {}\n\n'.format(json.dumps(chunk))
      if choice.get('finish_reason'):
        yield 'data: [DONE]\n\n'

  @classmethod
  @asynccontextmanager
  async def lifespan(cls, app):
    logging.basicConfig(level=logging.INFO)
    await cls.providers_init()
    try:
      yield
    finally:
      for model_provider in cls.providers.values():
        async with model_provider.lock:
          await model_provider.unload()


app = FastAPI(lifespan=ModelProvider.lifespan)

@app.get('/v1/models')
def models():
  response = {
    'object': 'list',
    'data': [],
  }
  for model_provider in ModelProvider.providers.values():
    response['data'].append({
      'id': model_provider.model_name,
      'created': int(model_provider.model_ctime),
      'object': 'model',
      'owned_by': 'system',
    })

  return Response(content=json.dumps(response), media_type='application/json')

@app.post('/v1/chat/completions')
async def chat_completions(request: ChatCompletionRequest):
  model_provider = ModelProvider.providers.get(request.model)
  if model_provider is None:
    raise HTTPException(status_code=400, detail='Invalid model')

  try:
    async with model_provider.lock:
      await model_provider.load()

    if request.stream:
      return StreamingResponse(model_provider.stream_response(request), media_type='text/event-stream')
    else:
      response = model_provider.sync_chat_completions(request)
      return Response(content=json.dumps(response), media_type='application/json')

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
  uvicorn.run(app, host='0.0.0.0', port=ModelProvider.SERVER_PORT)
