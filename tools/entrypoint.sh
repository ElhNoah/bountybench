#!/bin/bash

dockerd >&1 2>&1 &

# Wait for Docker daemon to start
while (! docker stats --no-stream >/dev/null 2>&1); do
	echo "Waiting for Docker to launch..."
	sleep 1
done

chmod +x /app/tools/code_navigator.py
ln -s /app/tools/code_navigator.py /usr/local/bin/code-nav

exec "$@"