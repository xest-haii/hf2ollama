#!/usr/bin/env python3.10

from openai import OpenAI

from test_client import TestClient


class TestRemote(TestClient):
  def __init__(self):
    super().__init__({'model': self.MODEL})
    agent = OpenAI(base_url=self.OPENAI_BASE_URL, api_key=self.OPENAI_API_KEY)
    self._models_list = agent.models.list
    self._chat_completions = agent.chat.completions.create


if __name__ == '__main__':
  test = TestRemote()
  test.models_list()
  test.chat_completions()
