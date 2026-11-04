FROM python:3.12-slim

# The official image ships without .pyc files, and the sandbox filesystem is read-only, so without
# this every import recompiles from source on every run (~700 ms of CPU charged to the user).
RUN python -m compileall -q /usr/local/lib/python3.12

COPY harness.py /harness/harness.py
ENTRYPOINT ["python3", "-B", "-I", "/harness/harness.py"]
