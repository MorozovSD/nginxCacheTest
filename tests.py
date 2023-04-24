import time

from nginx import config
from nginx.nginx import Nginx, DIFFERENT_PARAMETER, DELTA


def test_cache_similar():
    with Nginx() as nginx:
        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_different():
    with Nginx() as nginx:
        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.send(parameters=DIFFERENT_PARAMETER)
        assert response.headers["X-Cache-Status"] == "MISS"


def test_cache_similar_speed():
    with Nginx() as nginx:
        response_miss = nginx.send()
        assert response_miss.headers["X-Cache-Status"] == "MISS"

        response_hit = nginx.send()
        assert response_hit.headers["X-Cache-Status"] == "HIT"

        response_miss_time = response_miss.elapsed.total_seconds()
        response_hit_time = response_hit.elapsed.total_seconds()
        assert response_hit_time < response_miss_time


def test_cache_similar_clean_timeout():
    with Nginx() as nginx:
        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "HIT"

        time.sleep(config.VALID_TIMEOUT + DELTA)

        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "EXPIRED"


def test_cache_similar_clean_timeout_rehit():
    with Nginx() as nginx:
        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "HIT"

        time.sleep(config.VALID_TIMEOUT + DELTA)

        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "EXPIRED"

        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_bypass():
    with Nginx(config=config.BYPASS) as nginx:
        response = nginx.send(headers={"X-Bypass-Cache": "1"})
        assert response.headers["X-Cache-Status"] == "BYPASS"

        response = nginx.send(headers={"X-Bypass-Cache": "1"})
        assert response.headers["X-Cache-Status"] == "BYPASS"


def test_cache_bypass_off_header():
    with Nginx(config=config.BYPASS) as nginx:
        response = nginx.send(headers={"X-Bypass-Cache": "0"})
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.send(headers={"X-Bypass-Cache": "1"})
        assert response.headers["X-Cache-Status"] == "BYPASS"

        response = nginx.send(headers={"X-Bypass-Cache": "0"})
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_bypass_no_header():
    with Nginx(config=config.BYPASS) as nginx:
        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_error_response_4xx():
    with Nginx() as nginx:
        response = nginx.send(location='error_4xx')
        assert response.status_code == 418
        assert "X-Cache-Status" not in response.headers

        response = nginx.send(location='error_4xx')
        assert response.status_code == 418
        assert "X-Cache-Status" not in response.headers


def test_cache_error_response_5xx():
    with Nginx() as nginx:
        response = nginx.send(location='error_5xx')
        assert response.status_code == 500
        assert "X-Cache-Status" not in response.headers

        response = nginx.send(location='error_5xx')
        assert response.status_code == 500
        assert "X-Cache-Status" not in response.headers


def test_cache_reload():
    with Nginx() as nginx:
        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "MISS"

        nginx.container.exec_run(f'bash -c "nginx -s reload"')
        time.sleep(DELTA)

        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_delete_cache():
    with Nginx() as nginx:
        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "MISS"
        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "HIT"

        nginx.container.exec_run(f'bash -c "find /var/cache/nginx -type f -delete"')
        time.sleep(DELTA)

        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "MISS"
        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "HIT"


def test_cache_inactive_timeout():
    with Nginx(config=config.INACTIVE) as nginx:
        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "MISS"

        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "HIT"

        time.sleep(config.VALID_TIMEOUT + 5)  # 5s as delta

        response = nginx.send()
        assert response.headers["X-Cache-Status"] == "MISS"
