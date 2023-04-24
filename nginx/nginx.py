import requests
import docker
import os
import time

from nginx.config import DEFAULT

PARAMETER = {'p': 'parameter'}
DIFFERENT_PARAMETER = {'p': 'Other parameter'}
DELTA = 1


class Nginx:
    def __init__(self, config=DEFAULT):
        self.config = config
        self.docker = docker.from_env()
        self.config_name = f"nginx_{int(time.time())}.conf"

    @staticmethod
    def get(location='', parameters=None, headers=None):
        parameters = parameters or PARAMETER
        headers = headers or None
        return requests.Session().get(f"http://localhost:8080/{location}", params=parameters, headers=headers)

    def __enter__(self):
        with open(self.config_name, "w") as f:
            f.write(self.config)

        self.container = self.docker.containers.run(
            "nginx:latest",
            command=['sh', '-c', 'nginx && sleep infinity'],
            ports={"8080/tcp": 8080},
            volumes={
                f"{os.getcwd()}/tmp/nginx_cache_{int(time.time())}/": {"bind": "/tmp/nginx_cache", "mode": "rw"},
                f"{os.getcwd()}/{self.config_name}": {"bind": "/etc/nginx/nginx.conf", "mode": "rw"},
            },
            remove=True,
            detach=True,
        )
        time.sleep(1)  # Waiting container started
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.remove(force=True)


    def change_server_response(self):
        self.container.exec_run('nginx -s quit')

        with open(self.config_name, 'r') as file:
            filedata = file.read()

            filedata = filedata.replace('Hello from upstream server', 'Changed response from upstream server')

        with open(self.config_name, 'w') as file:
            file.write(filedata)

        time.sleep(1)
        self.container.exec_run("nginx")
