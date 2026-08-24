# syntax=docker/dockerfile:1

ARG PYOGG_REF=4118fc40067eb475468726c6bccf1242abfc24fc

FROM python:3.12-slim-bookworm AS builder

ARG PYOGG_REF

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY . /src

# Resolve PyOgg from the pinned commit together with the bridge package in a
# single resolver run so both come from one consistent dependency set.
RUN pip install --no-cache-dir \
    "/src" \
    "pyogg @ git+https://github.com/TeamPyOgg/PyOgg.git@${PYOGG_REF}"

FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libogg0 \
        libopus0 \
        libopusenc0 \
        libopusfile0 \
        libflac12 \
        libvorbis0a \
        libvorbisenc2 \
        libvorbisfile3 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --no-create-home --uid 999 bridge

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:${PATH}"

USER bridge

CMD ["asl-zello-bridge"]
