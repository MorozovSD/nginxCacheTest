VALID_TIMEOUT = 10

DEFAULT = f"""
events {{
    worker_connections  1024;
}}
http {{
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=10g inactive=60m;
    server {{
        listen 8080;
        location / {{
            proxy_pass http://localhost:8081;
            proxy_cache my_cache;
            proxy_cache_valid 200 {VALID_TIMEOUT}s;
            proxy_cache_valid any {VALID_TIMEOUT}s;
            proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
            add_header X-Cache-Status $upstream_cache_status;
        }}
    }}
    server {{
        listen 8081;
        location / {{
            return 200 'Hello from upstream server';
            add_header Content-Type text/plain;
            add_header X-Upstream-Response 1;   
        }}
        location /error_4xx {{
            return 418 'I’m a teapot';
            add_header Content-Type text/plain;
            add_header X-Upstream-Response 1;   
        }}
        location /error_5xx {{
            return 500 '"Internal" Server Error ';
            add_header Content-Type text/plain;
            add_header X-Upstream-Response 1;   
        }}
    }}
}}
"""

BYPASS = """
events {
    worker_connections  1024;
}
http {
    proxy_cache_path /var/cache/nginx  levels=1:2 keys_zone=my_cache:10m max_size=10g inactive=60m;
    server {
        listen 8080;
        location / {
            proxy_pass http://localhost:8081;
            proxy_cache my_cache;
            proxy_cache_valid 200 1h;
            proxy_cache_valid any 1m;
            proxy_cache_bypass $http_x_bypass_cache;
            proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
            add_header X-Cache-Status $upstream_cache_status;
            add_header X-Bypass-Cache $http_x_bypass_cache;
        }
    }
    server {
        listen 8081;
        location / {
            return 200 'Hello from upstream server';
            add_header Content-Type text/plain;
            add_header X-Upstream-Response 1;   
        }
    }
}
"""

INACTIVE = f"""
events {{
    worker_connections  1024;
}}
http {{
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=10g inactive={VALID_TIMEOUT}s;
    server {{
        listen 8080;
        location / {{
            proxy_pass http://localhost:8081;
            proxy_cache my_cache;
            proxy_cache_valid 200 1h;
            proxy_cache_valid any 1h;
            proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
            add_header X-Cache-Status $upstream_cache_status;
        }}
    }}
    server {{
        listen 8081;
        location / {{
            return 200 'Hello from upstream server';
            add_header Content-Type text/plain;
            add_header X-Upstream-Response 1;   
        }}
    }}
}}
"""