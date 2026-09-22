#!/usr/bin/env python3
import re

with open('/etc/nginx/sites-available/portfolio') as f:
    content = f.read()

# 如果末尾有多余的 }，删掉（之前追加失败留下的）
lines = content.rstrip().split('\n')
while lines and lines[-1].strip() == '}':
    lines.pop()
content = '\n'.join(lines) + '\n'

jev_config = '''
    # ============================================================
    # Jev Agent Routing Demo (端口 8888)
    # ============================================================
    location = /jev { return 301 /jev/; }
    location /jev/ {
        proxy_pass http://127.0.0.1:8888/;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 全站 HSTS（强化安全）
    add_header Strict-Transport-Security "max-age=31536000" always;
}
'''

# 把原来的 location / { ... } 到结尾替换掉
content = re.sub(
    r'\n    location / \{.*$',
    jev_config,
    content,
    flags=re.DOTALL
)

with open('/etc/nginx/sites-available/portfolio', 'w') as f:
    f.write(content)

print('OK: nginx config updated')
