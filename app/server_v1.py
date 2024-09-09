import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from typing import List, Optional

import openai
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel


class ChatMessage(BaseModel):
  role: str
  content: str


class ChatCompletionRequest(BaseModel):
  model: str
  messages: List[ChatMessage]
  stream: Optional[bool] = False


class ModelServer:
  DIR_MODELS = os.getenv('DIR_MODELS', '/models')
  MODEL_SUFFIX = os.getenv('MODEL_SUFFIX', '-Llamafied-Q4_K_M.gguf')
  SERVER_PORT = int(os.getenv('SERVER_PORT', 8000))
  SERVER_CMD = os.getenv('SERVER_CMD', '/usr/bin/python3 -m llama_cpp.server')
  SERVER_LIFETIME = int(os.getenv('SERVER_LIFETIME', 3600))

  servers = {}

  def __init__(self, model_name, model_path, port):
    self.model_name = model_name
    self.model_path = model_path
    self.model_ctime = os.path.getctime(model_path)
    self.port = port
    self.process = None
    self.last_used = 0

    self.agent = openai.AsyncOpenAI(
      base_url=f'http://localhost:{port}/v1',
      api_key='openai',
      max_retries=1,
    )

  @classmethod
  async def servers_init(cls):
    port = cls.SERVER_PORT + 1
    for owner in sorted(os.listdir(cls.DIR_MODELS)):
      dir_path = os.path.join(cls.DIR_MODELS, owner)
      if os.path.isdir(dir_path):
        for file_name in sorted(os.listdir(dir_path)):
          if file_name.endswith(cls.MODEL_SUFFIX):
            model_name = f'{owner}/{file_name.replace(cls.MODEL_SUFFIX, "")}'
            model_path = os.path.join(cls.DIR_MODELS, owner, file_name)
            cls.servers[model_name] = cls(model_name, model_path, port)
            port += 1
    asyncio.create_task(cls.servers_monitor())

  @classmethod
  async def servers_monitor(cls):
    while True:
      await asyncio.sleep(60)
      now = time.time()
      for model_server in cls.servers.values():
        if model_server.process and now - model_server.last_used > cls.SERVER_LIFETIME:
          await model_server.stop()

  async def start(self):
    self.last_used = time.time()
    if self.process is None:
      command = [
        *self.SERVER_CMD.split(' '),
        '--model', self.model_path,
        '--host', '0.0.0.0',
        '--port', str(self.port),
        '--n_gpu_layers', '-1',
      ]
      self.process = await asyncio.create_subprocess_exec(*command)

      for _ in range(100):
        try:
          await self.agent.models.list(timeout=0.1)
          break
        except openai.APIConnectionError as ex:
          pass

  async def stop(self):
    self.last_used = 0
    if self.process is not None:
      self.process.terminate()
      await self.process.wait()
      self.process = None

  async def chat_completions(self, request):
    return await self.agent.chat.completions.create(
      model=request.model,
      messages=[m.dict() for m in request.messages],
      stream=request.stream,
    )

  @classmethod
  @asynccontextmanager
  async def lifespan(cls, app):
    await cls.servers_init()
    yield
    for model_server in cls.servers:
      await model_server.stop()


app = FastAPI(lifespan=ModelServer.lifespan)

@app.get('/v1/models')
async def models():
  response = {
    'object': 'list',
    'data': [],
  }
  for model_server in ModelServer.servers.values():
    response['data'].append({
      'id': model_server.model_name,
      'created': int(model_server.model_ctime),
      'object': 'model',
      'owned_by': 'system',
    })

  return Response(content=json.dumps(response), media_type='application/json')

@app.post('/v1/chat/completions')
async def chat_completions(request: ChatCompletionRequest):
  model_server = ModelServer.servers.get(request.model)
  if model_server is None:
    raise HTTPException(status_code=400, detail='Invalid model')

  await model_server.start()

  response = await model_server.chat_completions(request)
  if request.stream:
    async def stream_response():
      async for chunk in response:
        data = chunk.to_dict()
        choice = data.get('choices', [{}])[0]
        delta = choice.get('delta', {})
        if delta.get('content'):
          yield 'data: {}\n\n'.format(json.dumps(data))
        if choice.get('finish_reason'):
          yield 'data: [DONE]\n\n'

    return StreamingResponse(stream_response(), media_type='text/event-stream')

  return Response(content=response.json(), media_type='application/json')


if __name__ == '__main__':
  uvicorn.run(app, host='0.0.0.0', port=ModelServer.SERVER_PORT)
