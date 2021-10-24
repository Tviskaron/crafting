import argparse
import os
import pathlib
import shutil
import tempfile

import docker
import yaml

from docker import APIClient
from docker.models.containers import Container
from docker.types import Mount

import config_validation
from .config_validation import Cfg, Code, MountVolume
from .utils import PatchedTarfile


def run_container(cfg: Cfg = Cfg()) -> None:
    client = docker.from_env()

    for image in client.images.list():
        if cfg.container.image in image.tags:
            break
    else:
        print('Pulling image:', cfg.container.image)
        client.images.pull(cfg.container.image)
    if not cfg.container.working_dir:
        cfg.container.working_dir = str(pathlib.Path("/") / pathlib.Path(cfg.code.folder).absolute().name)

    for path in cfg.code.volume_attach:
        target = pathlib.Path(cfg.container.working_dir) / path
        source = pathlib.Path(path).absolute()
        mount = MountVolume(target=str(target), source=str(source), read_only=True, type='bind')
        cfg.host_config.mounts.append(Mount(**mount.dict()))

    host_config = APIClient().create_host_config(**cfg.host_config.dict())
    container_id = client.api.create_container(**cfg.container.dict(), host_config=host_config)

    container: Container = client.containers.get(container_id)

    cfg.update_forward_refs()
    if cfg.code.folder:
        path_to_code = pathlib.Path(cfg.code.folder)
        with tempfile.TemporaryFile() as temp:
            # file = tarfile.open(fileobj=temp, mode="w")
            path = PatchedTarfile.open(fileobj=temp, mode="w")

            ignore = list(map(os.path.abspath, cfg.code.volume_attach))
            path.add(str(path_to_code), arcname=path_to_code.name + "/", recursive=True, ignore=ignore)
            path.close()
            temp.seek(0)
            with temp as path:
                container.put_archive(data=path, path=cfg.container.working_dir)

    container.start()
    if cfg.container.command == 'bash':
        os.system(f"docker attach  {container.id}")
    else:
        os.system("docker logs -f " + container.name)


def main():
    parser = argparse.ArgumentParser(description=""" Craft tool to run your experiments with docker """)
    parser.add_argument('mode', type=str, help='path to yaml config', choices=['run', 'create'])
    parser.add_argument('config', type=str, help='path to yaml config')
    args = parser.parse_args()
    if args.mode == 'run':
        with open(args.config, "r") as config_file:
            config = yaml.safe_load(config_file)
        run_container(cfg=Cfg(**config))
    # elif args.mode == 'create':
    #     if pathlib.Path(args.config).exists():
    #         raise FileExistsError("already exists")
    #     src = str(pathlib.Path(__file__).parents[0] / "basic_config.yaml")
    #     shutil.copyfile(src=src, dst=args.config)


if __name__ == '__main__':
    main()
