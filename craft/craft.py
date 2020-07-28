import argparse
import os
import pathlib
import shutil
import tarfile
import tempfile

import docker
import yaml
from docker import APIClient

from craft.utils import create_name


def run_container(config):
    client = docker.from_env()
    if config.get('code', None):
        path_to_code = pathlib.Path(config['code'].get('folder', None))

        attempts = 10
        for _ in range(attempts):
            container_name = create_name(config['info']['container_name'])
            if container_name in map(lambda x: x.name, client.containers.list()):
                continue
            config['docker-run']['name'] = container_name
            break
        else:
            raise IndexError(f"Can't create unique name in {attempts} attempts")

        if 'working_dir' not in config['docker-run']:
            config['docker-run']['working_dir'] = "/" + path_to_code.name

    for image in client.images.list():
        if config["docker-run"]['image'] in image.tags:
            break
    else:
        print(f"Unable to find image {config['docker-run']['image']} locally. Pulling from dockerhub.")
        client.images.pull(config["docker-run"]['image'])

    host_config = APIClient().create_host_config(**config.get('host_config', {}))
    container_id = client.api.create_container(**config['docker-run'],
                                               host_config=host_config
                                               )
    container = client.containers.get(container_id)
    if config.get('code', None):
        path_to_code = pathlib.Path(config['code'].get('folder', None))
        with tempfile.TemporaryFile() as temp:
            file = tarfile.open(fileobj=temp, mode="w")
            file.add(path_to_code, arcname=path_to_code.name + "/", recursive=True)
            file.close()
            temp.seek(0)
            with temp as file:
                container.put_archive(data=file, path='/')
    container.start()
    container.logs()
    os.system(f"docker logs -f {container.name}")
    # os.system(f"docker exec  -ti {container.name} bash")


def main():
    parser = argparse.ArgumentParser(description=""" Craft tool to run your experiments with docker """)
    parser.add_argument('mode', type=str, help='path to yaml config', choices=['run', 'create'])
    parser.add_argument('config', type=str, help='path to yaml config')
    args = parser.parse_args()
    if args.mode == 'run':
        with open(args.config, "r") as config_file:
            config = yaml.load(config_file, yaml.FullLoader)

        run_container(config=config)
    elif args.mode == 'create':
        if pathlib.Path(args.config).exists():
            raise FileExistsError(f"{args.config} already exists")
        src = str(pathlib.Path(__file__).parents[0] / "basic_config.yaml")
        shutil.copyfile(src=src, dst=args.config)


if __name__ == '__main__':
    main()
