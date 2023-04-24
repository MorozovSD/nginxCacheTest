import requests
import docker
import os
import time

from nginx.config import DEFAULT

PARAMETER = {'p': 'parameter'}
DIFFERENT_PARAMETER = {'p': 'Other parameter'}
DELTA = 2


class Nginx:
    def __init__(self, config=DEFAULT):
        self.config = config
        self.docker = docker.from_env()

    @staticmethod
    def send(location='', parameters=None, headers=None):
        parameters = parameters or PARAMETER
        headers = headers or None
        return requests.Session().get(f"http://localhost:8080/{location}", params=parameters, headers=headers)

    def __enter__(self):
        uniq_srt = f'{int(time.time())}'
        with open(f"nginx_{uniq_srt}.conf", "w") as f:
            f.write(self.config)

        self.container = self.docker.containers.run(
            "nginx:latest",
            command=["nginx", "-g", "daemon off;"],
            ports={"8080/tcp": 8080},
            volumes={
                f"{os.getcwd()}/tmp/nginx_cache_{uniq_srt}/": {"bind": "/tmp/nginx_cache", "mode": "rw"},
                f"{os.getcwd()}/nginx_{uniq_srt}.conf": {"bind": "/etc/nginx/nginx.conf", "mode": "rw"},
            },
            remove=True,
            detach=True,
        )
        time.sleep(1)  # Waiting container started
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.remove(force=True)
