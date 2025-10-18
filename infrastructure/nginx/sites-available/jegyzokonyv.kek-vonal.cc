server {
    root /var/www/html;
    index index.html index.htm index.nginx-debian.html;
    server_name jegyzokonyv.kek-vonal.cc;

    location / {
        proxy_pass http://localhost:8055;
        include proxy_params;
    }

    location /n8n/ {
        proxy_pass http://localhost:5678/;
        include proxy_params;

        # WebSocket headers
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Additional headers for WebSocket
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Disable buffering to improve real-time communication
        proxy_buffering off;

        # Timeout settings for WebSocket connections
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /dashboard/ {
        proxy_pass http://localhost:8501/;
        include proxy_params;
        
        # Rewrite path
        rewrite ^/dashboard/(.*)$ /$1 break;

        # WebSocket headers (required for Streamlit)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Additional headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Disable buffering for real-time updates
        proxy_buffering off;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    listen [::]:443 ssl ipv6only=on; # managed by Certbot
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/jegyzokonyv.kek-vonal.cc/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/jegyzokonyv.kek-vonal.cc/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}

server {
    if ($host = jegyzokonyv.kek-vonal.cc) {
        return 301 https://$host$request_uri;
    } # managed by Certbot

    listen 80 default_server;
    listen [::]:80 default_server;
    server_name jegyzokonyv.kek-vonal.cc;
    return 404; # managed by Certbot
}
