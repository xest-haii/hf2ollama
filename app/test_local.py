#!/usr/bin/env python3.10

import os

from llama_cpp import Llama

from server import ModelProvider
from test_client import TestClient


class TestLocal(TestClient):
  def __init__(self):
    super().__init__()
    agent = Llama(
      model_path=os.path.join(ModelProvider.DIR_MODELS, f'{self.MODEL}{ModelProvider.MODEL_SUFFIX}'),
      n_gpu_layers=-1,
      verbose=self.VERBOSE,
    )
    self._chat_completions = agent.create_chat_completion_openai_v1


if __name__ == '__main__':
  test = TestLocal()
  test.chat_completions()
