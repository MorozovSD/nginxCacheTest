import time

from nginx import config
from nginx.nginx import Nginx, DIFFERENT_PARAMETER, DELTA


def test_cache_similar():
    with Nginx() as nginx:
        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_different():
    with Nginx() as nginx:
        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.get(parameters=DIFFERENT_PARAMETER)
        assert response.headers["X-Cache-Status"] == "MISS"


def test_cache_similar_speed():
    with Nginx() as nginx:
        response_miss = nginx.get()
        assert response_miss.headers["X-Cache-Status"] == "MISS"

        response_hit = nginx.get()
        assert response_hit.headers["X-Cache-Status"] == "HIT"

        response_miss_time = response_miss.elapsed.total_seconds()
        response_hit_time = response_hit.elapsed.total_seconds()
        assert response_hit_time < response_miss_time


def test_cache_similar_clean_timeout():
    with Nginx() as nginx:
        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "HIT"

        time.sleep(config.VALID_TIMEOUT + DELTA)

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "EXPIRED"


def test_cache_similar_clean_timeout_rehit():
    with Nginx() as nginx:
        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "HIT"

        time.sleep(config.VALID_TIMEOUT + DELTA)

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "EXPIRED"

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_bypass():
    with Nginx(config=config.BYPASS) as nginx:
        response = nginx.get(headers={"X-Bypass-Cache": "1"})
        assert response.headers["X-Cache-Status"] == "BYPASS"

        response = nginx.get(headers={"X-Bypass-Cache": "1"})
        assert response.headers["X-Cache-Status"] == "BYPASS"


def test_cache_bypass_off_header():
    with Nginx(config=config.BYPASS) as nginx:
        response = nginx.get(headers={"X-Bypass-Cache": "0"})
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.get(headers={"X-Bypass-Cache": "1"})
        assert response.headers["X-Cache-Status"] == "BYPASS"

        response = nginx.get(headers={"X-Bypass-Cache": "0"})
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_bypass_no_header():
    with Nginx(config=config.BYPASS) as nginx:
        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_error_response_4xx():
    with Nginx() as nginx:
        response = nginx.get(location='error_4xx')
        assert response.status_code == 418
        assert "X-Cache-Status" not in response.headers

        response = nginx.get(location='error_4xx')
        assert response.status_code == 418
        assert "X-Cache-Status" not in response.headers


def test_cache_error_response_5xx():
    with Nginx() as nginx:
        response = nginx.get(location='error_5xx')
        assert response.status_code == 500
        assert "X-Cache-Status" not in response.headers

        response = nginx.get(location='error_5xx')
        assert response.status_code == 500
        assert "X-Cache-Status" not in response.headers


def test_cache_reload():
    with Nginx() as nginx:
        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "MISS"

        nginx.container.exec_run(f'bash -c "nginx -s reload"')
        time.sleep(DELTA)

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_delete_cache():
    with Nginx() as nginx:
        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "MISS"
        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "HIT"

        nginx.container.exec_run(f'bash -c "find /var/cache/nginx -type f -delete"')
        time.sleep(DELTA)

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "MISS"
        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_inactive_timeout():
    with Nginx(config=config.INACTIVE) as nginx:
        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "HIT"

        time.sleep(config.VALID_TIMEOUT + 5)  # 5s as delta

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "MISS"


def test_cache_readonly_after_cache():
    with Nginx() as nginx:
        response = nginx.get()
        assert response.status_code == 200
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.get()
        assert response.status_code == 200
        assert response.headers["X-Cache-Status"] == "HIT"

        nginx.container.exec_run("chmod 000 /var/cache/nginx")

        response = nginx.get()
        assert response.status_code == 500
        assert "X-Cache-Status" not in response.headers


def test_cache_readonly_before_cache():
    with Nginx() as nginx:
        nginx.container.exec_run("chmod 000 /var/cache/nginx")

        response = nginx.get()
        assert response.status_code == 500
        assert "X-Cache-Status" not in response.headers

        nginx.container.exec_run("chmod 755 /var/cache/nginx")

        response = nginx.get()
        assert response.status_code == 200
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.get()
        assert response.status_code == 200
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_change_server_content_no_refresh():
    with Nginx() as nginx:

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "MISS"
        assert response.text == "Hello from upstream server"

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "HIT"
        assert response.text == "Hello from upstream server"

        nginx.container.exec_run("nginx -s quit")

        nginx.change_server_response()

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "HIT"
        assert response.text == "Hello from upstream server"


def test_cache_change_server_content_refresh():
    with Nginx() as nginx:
        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "MISS"
        assert response.text == "Hello from upstream server"

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "HIT"
        assert response.text == "Hello from upstream server"

        nginx.change_server_response()
        time.sleep(config.VALID_TIMEOUT + DELTA)

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "EXPIRED"
        assert response.text == "Changed response from upstream server"

        response = nginx.get()
        assert response.headers["X-Cache-Status"] == "HIT"
        assert response.text == "Changed response from upstream server"


