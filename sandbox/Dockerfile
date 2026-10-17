FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MPLBACKEND=Agg
ENV MPLCONFIGDIR=/tmp/matplotlib

RUN pip install --no-cache-dir \
    pandas \
    numpy \
    matplotlib \
    seaborn

WORKDIR /workspace