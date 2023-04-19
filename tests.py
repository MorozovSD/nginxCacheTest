from contextlib import contextmanager

import requests
import docker
import time
import os

from nginx_conf import VALID_TIMEOUT, DEFAULT, BYPASS

PARAMETER = {'p': 'parameter'}
DIFFERENT_PARAMETER = {'p': 'Other parameter'}
DELTA = 1


def send_request_to_nginx(parameters=None, headers=None):
    parameters = parameters or PARAMETER
    headers = headers or None
    return requests.Session().get(f"http://localhost:8080/", params=parameters, headers=headers)


@contextmanager
def create_nginx_container(conf=DEFAULT):
    docker_client = docker.from_env()

    uniq_srt = f'{int(time.time())}'
    with open(f"nginx_{uniq_srt}.conf", "w") as f:
        f.write(conf)

    container = docker_client.containers.run(
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
    try:
        yield container
    finally:
        container.remove(force=True)


def test_cache_similar():
    with create_nginx_container():
        response = send_request_to_nginx()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = send_request_to_nginx()
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_different():
    with create_nginx_container():
        response = send_request_to_nginx()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = send_request_to_nginx(parameters=DIFFERENT_PARAMETER)
        assert response.headers["X-Cache-Status"] == "MISS"


def test_cache_similar_speed():
    with create_nginx_container():
        response_miss = send_request_to_nginx()
        assert response_miss.headers["X-Cache-Status"] == "MISS"

        response_hit = send_request_to_nginx()
        assert response_hit.headers["X-Cache-Status"] == "HIT"

        response_miss_time = response_miss.elapsed.total_seconds()
        response_hit_time = response_hit.elapsed.total_seconds()
        assert response_hit_time < response_miss_time


def test_cache_similar_clean_timeout():
    with create_nginx_container():
        response = send_request_to_nginx()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = send_request_to_nginx()
        assert response.headers["X-Cache-Status"] == "HIT"

        time.sleep(VALID_TIMEOUT + DELTA)

        response = send_request_to_nginx()
        assert response.headers["X-Cache-Status"] == "EXPIRED"


def test_cache_similar_clean_timeout_rehit():
    with create_nginx_container():
        response = send_request_to_nginx()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = send_request_to_nginx()
        assert response.headers["X-Cache-Status"] == "HIT"

        time.sleep(VALID_TIMEOUT + DELTA)

        response = send_request_to_nginx()
        assert response.headers["X-Cache-Status"] == "EXPIRED"

        response = send_request_to_nginx()
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_bypass():
    with create_nginx_container(conf=BYPASS):
        response = send_request_to_nginx(headers={"X-Bypass-Cache": "1"})
        assert response.headers["X-Cache-Status"] == "BYPASS"

        response = send_request_to_nginx(headers={"X-Bypass-Cache": "1"})
        assert response.headers["X-Cache-Status"] == "BYPASS"


def test_cache_bypass_off_header():
    with create_nginx_container(conf=BYPASS):
        response = send_request_to_nginx(headers={"X-Bypass-Cache": "0"})
        assert response.headers["X-Cache-Status"] == "MISS"

        response = send_request_to_nginx(headers={"X-Bypass-Cache": "1"})
        assert response.headers["X-Cache-Status"] == "BYPASS"

        response = send_request_to_nginx(headers={"X-Bypass-Cache": "0"})
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_bypass_no_header():
    with create_nginx_container(conf=BYPASS):
        response = send_request_to_nginx()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = send_request_to_nginx()
        assert response.headers["X-Cache-Status"] == "HIT"
