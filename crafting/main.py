import argparse
import os
import pathlib
import sys
import tempfile
import warnings

import docker
import yaml

from docker import APIClient
from docker.models.containers import Container
from docker.types import Mount

from .config_validation import Cfg, MountVolume
from .utils import PatchedTarfile, get_size_by_path


def check_folder_sizes(path, ignore, size_warning_error=128, size_error=512):
    total_size = 0
    for path in path.iterdir():
        mb_to_bytes = 1024 * 1024

        size = get_size_by_path(path, ignore=ignore, max_size=size_error * mb_to_bytes)

        message_text = "\n".join(
            [("Folder" if path.is_dir() else "File") + f" {path} is too big (>{size // mb_to_bytes}MB).",
             f"Consider adding it to volumes or ignore it in code settings. ",
             f"E.g. volumes: ['{path}'] or ignore: ['{path}']",
             ])

        if total_size > size_error * mb_to_bytes:
            sys.tracebacklimit = 0
            raise ValueError(f"Total size of code folder is too big (<{size // mb_to_bytes}MB).")

        if size >= size_error * mb_to_bytes:
            sys.tracebacklimit = 0
            raise ValueError(message_text)
        else:
            if size >= size_warning_error * mb_to_bytes:
                warnings.warn(message_text)
        total_size += size


def add_files_from_code_folder(container: Container, cfg: Cfg):
    # if code folder is not specified, do nothing
    if cfg.code.folder is None:
        return

    path_to_code = pathlib.Path(cfg.code.folder)

    ignore = list(map(os.path.abspath, cfg.code.volumes)) + list(map(os.path.abspath, cfg.code.ignore))
    # make sure that code folder is not too big
    check_folder_sizes(path_to_code, ignore)

    # add files from code folder to container via tarfile
    with tempfile.TemporaryFile() as temp:
        path = PatchedTarfile.open(fileobj=temp, mode="w")

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

    for path in cfg.code.volumes + cfg.code.rw_volumes:
        is_read_only = path in cfg.code.volumes
        target = pathlib.Path(cfg.container.working_dir) / path
        source = pathlib.Path(path).absolute()
        mount = MountVolume(target=str(target), source=str(source), read_only=is_read_only, type='bind')
        cfg.host_config.mounts.append(Mount(**mount.dict()))

    if cfg.code.set_gid_uid:
        image = client.images.get(cfg.container.image)
        default_user = image.attrs.get('Config', {}).get('User')
        if not default_user:
            default_user = 'root'
        uid = os.getuid()
        gid = os.getgid()

        cfg.container.user = f"{default_user}:{uid}:{gid}"
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
