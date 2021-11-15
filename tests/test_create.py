import yaml

from config_validation import Code, Cfg, Container
from main import run_container


def test_creation():
    code = Code(folder='.', volume_attach=['./big_folder/hello/'])
    cfg = Cfg(code=code, container=Container(command='bash'))
    run_container(cfg=cfg)



