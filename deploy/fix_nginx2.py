#!/usr/bin/env python3

with open('/etc/nginx/sites-available/portfolio') as f:
    content = f.read()

# 在 "return 301 https://$host$request_uri;" 后面加一个 } 闭合 80 端口的 server 块
content = content.replace(
    '    return 301 https://$host$request_uri;\n\nserver {',
    '    return 301 https://$host$request_uri;\n}\n\nserver {'
)

with open('/etc/nginx/sites-available/portfolio', 'w') as f:
    f.write(content)

print('OK')
