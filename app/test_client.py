import json
import os
import timeit


class TestClient:
  OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'http://localhost:8000/v1')
  OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'openai')
  MODEL = os.getenv('MODEL', 'LGAI-EXAONE/EXAONE-3.0-7.8B-Instruct')
  SYSTEM_MESSAGE = os.getenv('SYSTEM_MESSAGE', 'You are a helpful assistant.')
  USER_MESSAGE = os.getenv('USER_MESSAGE', 'Hi')
  STREAM = os.getenv('STREAM', '') in ['1', 'True', 'true', 'y', 'yes']
  VERBOSE = os.getenv('VERBOSE', '') in ['1', 'True', 'true', 'y', 'yes']

  def __init__(self, chat_params={}):
    self._models_list = lambda: []
    self._chat_completions = lambda: None
    self._chat_params = {
      'messages': [
        {
          'role': 'system',
          'content': self.SYSTEM_MESSAGE,
        },
        {
          'role': 'user',
          'content': self.USER_MESSAGE,
        },
      ],
      'stream': self.STREAM,
    }
    self._chat_params.update(chat_params)

  def models_list(self):
    def _func():
      print('* /v1/models')
      response = self._models_list()
      for model in response.data:
        if self.VERBOSE:
          print(model.to_json())
        else:
          print(model.id)

    print('#', timeit.timeit(_func, number=1), end='\n\n')

  def chat_completions(self):
    def _func():
      print('* /v1/chat/completions')
      response = self._chat_completions(**self._chat_params)
      if self.STREAM:
        for chunk in response:
          if self.VERBOSE:
            print(chunk.to_json())
          else:
            print(chunk.choices[0].delta.content, end='', flush=True)
        print('', flush=True)
      else:
        if self.VERBOSE:
          print(response.to_json())
        else:
          print(response.choices[0].message.content)

    print('#', timeit.timeit(_func, number=1), end='\n\n')
