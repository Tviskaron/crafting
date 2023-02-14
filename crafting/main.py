import argparse
import os
import pathlib
import tempfile
import warnings

import docker
import yaml

from docker import APIClient
from docker.models.containers import Container
from docker.types import Mount

from .config_validation import Cfg, MountVolume
from .utils import PatchedTarfile, get_folder_size


def add_files_from_code_folder(container: Container, cfg: Cfg):
    if cfg.code.folder is None:
        return

    path_to_code = pathlib.Path(cfg.code.folder)

    for path in path_to_code.iterdir():
        file_size_warning_mb = 100
        file_size_error_mb = 1000
        mb_to_bytes = 1024 * 1024

        message_text = f'File/folder {path} is exceeding {file_size_warning_mb} MB. '\
                       f'Consider adding it as volume to run.yaml file:'


        if get_folder_size(path, max_size=file_size_warning_mb) > file_size_error_mb:
            raise ValueError(message_text + f'\n    volumes: [{path}]') from None

        if get_folder_size(path, max_size=file_size_warning_mb * mb_to_bytes) > mb_to_bytes * file_size_warning_mb:
            warnings.warn(message_text + f'\n    volumes: [{path}]')


    with tempfile.TemporaryFile() as temp:
        path = PatchedTarfile.open(fileobj=temp, mode="w")

        ignore = list(map(os.path.abspath, cfg.code.volumes)) + list(map(os.path.abspath, cfg.code.ignore))
        path.add(str(path_to_code), arcname=path_to_code.name + "/", recursive=True, ignore=ignore)
        path.close()
        temp.seek(0)
        with temp as path:
            container.put_archive(data=path, path=cfg.container.working_dir)


def run_container(cfg: Cfg = Cfg()) -> Container:
    client = docker.from_env()

    if cfg.container.command == 'bash' and cfg.container.stdin_open is None:
        cfg.container.stdin_open = True

    for image in client.images.list():
        if cfg.container.image in image.tags:
            break
    else:
        print('Pulling image:', cfg.container.image)
        client.images.pull(cfg.container.image)
    if cfg.code.folder and not cfg.container.working_dir:
        cfg.container.working_dir = str(pathlib.Path("/") / pathlib.Path(cfg.code.folder).absolute().name)

    # forward environment variables into container
    for key in cfg.code.forward_environment_keys:
        if key in os.environ:
            cfg.container.environment.append(f'{key}={os.environ[key]}')

    for path in cfg.code.volumes:
        target = pathlib.Path(cfg.container.working_dir) / path
        source = pathlib.Path(path).absolute()
        mount = MountVolume(target=str(target), source=str(source), read_only=True, type='bind')
        cfg.host_config.mounts.append(Mount(**mount.dict()))

    host_config = APIClient().create_host_config(**cfg.host_config.dict())
    container_id = client.api.create_container(**cfg.container.dict(), host_config=host_config)

    container: Container = client.containers.get(container_id)

    cfg.update_forward_refs()

    add_files_from_code_folder(container, cfg)

    container.start()

    if cfg.container.command == 'bash':
        os.system(f"docker attach  {container.id} ")
    else:
        if cfg.code.connect_to_logs:
            os.system("docker logs -f " + container.name)

    return container


def main():
    parser = argparse.ArgumentParser(description="""Crafting a tool to run ML/RL experiments in docker containers""",
                                     usage="crafting <CONFIG>.yaml\n(if CONFIG doesn't exist it will be created)")
    parser.add_argument('CONFIG', type=str, help='path to yaml config', default='here.yaml', )

    args = parser.parse_args()
    if not pathlib.Path(args.CONFIG).exists():
        print('Creating new config:', args.CONFIG)
        with open(args.CONFIG, "w") as f:
            yaml.dump(Cfg().dict(), f)
    else:
        with open(args.CONFIG, "r") as config_file:
            config = yaml.safe_load(config_file)
        run_container(cfg=Cfg(**config))


if __name__ == '__main__':
    main()
