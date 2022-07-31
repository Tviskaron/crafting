import os
from time import sleep

import yaml

from crafting.config_validation import Code, Cfg, Container
from crafting.main import run_container


def test_basics():
    cfg = Cfg(container=Container(command='echo crafting'))
    container = run_container(cfg=cfg)
    sleep(0.1), print(container.logs())


def test_environment_keys():
    test_key = 'TEST_ENV_KEY'
    yaml_config = f"""
container:
  command: "env"
  image: python:3.9-slim-buster
  tty: true
  environment:
    - "{test_key}=0"
code:
    connect_to_logs: False
"""
    cfg = Cfg(**yaml.safe_load(yaml_config))
    container = run_container(cfg=cfg)
    sleep(0.1)
    import re
    assert re.search(test_key, str(container.logs()))


def test_env_keys_forwarding():
    test_key = 'TEST_ENV_KEY'
    os.environ[test_key] = test_key
    cfg = Cfg(container=Container(command='env'), code=Code(forward_environment_keys=[test_key], connect_to_logs=False))
    container = run_container(cfg=cfg)
    import re
    sleep(0.1)
    assert re.search(test_key, str(container.logs()))
