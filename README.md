# AllStarLink ⇔ Zello Bridge

This tool allows Zello Free or Zello Work channels to be connected to USRP, enabling bridging of amateur radio networks to the Zello network.

Tested with:

* [AllStarLink](https://www.allstarlink.org/) `chan_usrp`
* [DVSwitch](https://dvswitch.groups.io/g/main?) `Analog_Bridge`
* [MMDVM\_CM](https://github.com/juribeparada/MMDVM_CM) `USRP2DMR` and `USRP2YSF`
* [SvxLink](https://www.svxlink.org/) via a third-party USRP module

The original inspiration for this project was the work done by [Rob G4ZWH](https://www.qrz.com/db/G4ZWH) to build a public Zello bridge to the [FreeSTAR](https://freestar.network/) network using SIP softphones and the Zello Windows client. This was well received but had limitations. [Matt G4IYT](https://www.qrz.com/db/G4IYT) later rebuilt the bridge as a dedicated service using the [Zello Channels API](https://github.com/zelloptt/zello-channel-api/blob/master/API.md).

Current users of the bridge include:

* [FreeSTAR](https://freestar.network)
* [CumbriaCQ.com](https://cumbriacq.com/)
* [235 Alive](https://235alive.com)

The bridge does not require significant resources. The FreeSTAR bridge runs on a VPS with 1 VCPU and 1GB RAM, and performs well on both AMD64 and ARM platforms.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Dependencies](#dependencies)
  - [Install with pip + venv](#install-with-pip--venv)
  - [Install with setup.py (deprecated)](#deprecated-install-with-setuppy)
  - [Docker](#docker)
    - [Build](#build)
    - [Run with Compose](#run-with-compose)
    - [Multiple instances (one per channel)](#multiple-instances-one-per-channel)
- [Setup Service](#setup-service)
  - [Common Parameters](#common-parameters-used-in-both-free-and-work)
  - [Zello Free Example](#zello-free-example)
  - [Zello Work Example](#zello-work-example)
  - [Optional Parameters](#optional-parameters)
  - [Enable and Start Service](#enable-and-start-service)
- [AllStarLink Setup](#allstarlink-setup)
  - [Configure `rpt.conf`](#configure-rptconf)
  - [`privatenodes.txt` (Supermon/AllScan)](#privatenodestxt-supermonallscan)
  - [Allmon3 Overrides (`web.ini`)](#allmon3-overrides-webini)
- [Credits](#credits)

---

## Prerequisites

The bridge needs a Zello account to log into. This account represents the “user” speaking whenever traffic is sent from AllStarLink into Zello.

**Recommended setup:**

1. Create a dedicated Zello account for the bridge (do not use your personal account).
2. Ensure this account has permission to **talk** and **listen** in your Zello channel.
3. Convert this account into a developer account by logging into the [Zello Developers Console](https://developers.zello.com/).
4. Under **Keys**, click **Add Key**. Save both the **Issuer** and the **Private Key**.

> The private key is long. Copy the entire contents and save them to a `.key` file (for example, `/opt/asl-zello-bridge/zello.key`). You will reference this file in your service configuration.

---

## Installation

These instructions were tested with Debian 12. Adjust as needed for other systems.

There are three installation methods:

* **pip + venv (recommended):** modern, isolated, avoids interfering with system packages.
* **setup.py (deprecated):** used in early versions, but may break system dependencies.
* **docker:** containerized deployment on Docker/Podman/Kubernetes.

> The `setup.py` method is deprecated in favor of `pip + venv`. Users have reported issues on Debian 12 and Ubuntu 24. If you installed with `setup.py`, it will still work, but upgrading is recommended.

### Dependencies

```bash
apt-get install libogg-dev libopusenc-dev libflac-dev libopusfile-dev libopus-dev libvorbis-dev libopus0 git
```

### Install with pip + venv

Install Python dependencies:

```bash
apt-get install python3-venv python3-pip
```

Download code:

```bash
cd /opt
git clone https://github.com/mattmelling/asl-zello-bridge.git
```

Create venv:

```bash
mkdir -p /opt/asl-zello-bridge/venv
python3 -m venv /opt/asl-zello-bridge/venv
```

Install `pyogg` from source:

```bash
git clone https://github.com/TeamPyOgg/PyOgg.git
cd PyOgg
/opt/asl-zello-bridge/venv/bin/python setup.py install
```

Install the bridge:

```bash
cd /opt/asl-zello-bridge
/opt/asl-zello-bridge/venv/bin/pip3 install .
```

### \[DEPRECATED] Install with setup.py

Install `pyogg`:

```bash
git clone https://github.com/TeamPyOgg/PyOgg.git
cd PyOgg
sudo python setup.py install
```

Install the bridge:

```bash
git clone https://github.com/mattmelling/asl-zello-bridge.git
cd asl-zello-bridge
sudo python3 setup.py install
```

At this point, `asl_zello_bridge` should be on your `$PATH`.

---

## Setup Service

If you installed with `setup.py`, adjust `asl-zello-bridge.service` to point to where the script is installed:

```bash
sudo cp asl-zello-bridge.service /etc/systemd/system/
sudo systemctl edit asl-zello-bridge.service
```

When the editor opens, set environment variables under `[Service]`.

### Common Parameters (used in both Free and Work)

```ini
[Service]
# IP where this program listens for USRP RX audio (usually localhost)
Environment=USRP_BIND=127.0.0.1

# IP where this program sends USRP TX audio (usually localhost)
Environment=USRP_HOST=127.0.0.1

# UDP port for audio received from USRP/AllStarLink
# 34001 is ASL default (rxchannel = USRP/127.0.0.1:34001:32001)
Environment=USRP_RXPORT=34001

# UDP port for audio sent back into USRP/AllStarLink
# 32001 is ASL default
Environment=USRP_TXPORT=32001

# Zello username (case-sensitive)
Environment=ZELLO_USERNAME=myuser

# Zello password
Environment=ZELLO_PASSWORD=mypass

# Zello channel name (must match exactly, case-sensitive)
Environment=ZELLO_CHANNEL="My Test Channel"
```

### Zello Free Example

```ini
[Service]
# USRP parameters
Environment=USRP_BIND=127.0.0.1
Environment=USRP_HOST=127.0.0.1
Environment=USRP_RXPORT=34001
Environment=USRP_TXPORT=32001

# Zello credentials
Environment=ZELLO_USERNAME=myuser
Environment=ZELLO_PASSWORD=mypass
Environment=ZELLO_CHANNEL="My Test Channel"

# Zello Free variables
Environment=ZELLO_PRIVATE_KEY=/opt/asl-zello-bridge/zello.key
Environment=ZELLO_ISSUER=my-issuer-id
Environment=ZELLO_WS_ENDPOINT=wss://zello.io/ws
```

### Zello Work Example

```ini
[Service]
# USRP parameters
Environment=USRP_BIND=127.0.0.1
Environment=USRP_HOST=127.0.0.1
Environment=USRP_RXPORT=34001
Environment=USRP_TXPORT=32001

# Zello credentials
Environment=ZELLO_USERNAME=myuser
Environment=ZELLO_PASSWORD=mypass
Environment=ZELLO_CHANNEL="My Test Channel"

# Zello Work variables
Environment=ZELLO_API_ENDPOINT=https://mynetwork.zellowork.com
Environment=ZELLO_WS_ENDPOINT=wss://zellowork.io/ws/mynetwork
```

### Optional Parameters

```ini
# Log level
Environment=LOG_LEVEL=DEBUG

# Log format (see Python logging docs)
Environment=LOG_FORMAT="%(levelname)s:%(name)s:%(message)s"

# RX audio gain in dB
Environment=USRP_GAIN_RX_DB=0

# TX audio gain in dB
Environment=USRP_GAIN_TX_DB=0
```

### Enable and Start Service

```bash
sudo systemctl enable asl-zello-bridge.service
sudo systemctl start asl-zello-bridge.service
```

---

## AllStarLink Setup

### Configure `rpt.conf`

Set up a node with a USRP channel in ASL (`asl-menu` can add a new node number). Example `rpt.conf`:

```ini
[1001](node-main)
rxchannel = USRP/127.0.0.1:34001:32001
duplex = 0       ; Half duplex, no telemetry or hang time
linktolink = yes ; Force full-duplex even with duplex=0
hangtime = 0     ; Disable hangtime
althangtime = 0  ; Disable alt hangtime
telemdefault = 0 ; Disable telemetry
nounkeyct = 1    ; Disable courtesy tone
wait_times = wait-times-1001 ; Point to wait-times-1001 stanza

[wait-times-1001]
telemwait = 0 ; Disable telemetry wait time
idwait = 0    ; Disable ID wait time
unkeywait = 0 ; Disable unkey wait time
```

This creates node `1001` on your server with a USRP rxchannel for your Zello bridge to connect to. You can then link node `1001` to other nodes as desired.

### `privatenodes.txt` (Supermon/AllScan)

To make node `1001` display nicely in Supermon/AllScan, add an entry to `/etc/asterisk/privatenodes.txt`:

```
Node | Callsign | Description   | Location
1001 | MyCall   | Zello Channel | QTH
```

Append the entry:

```bash
echo "1001|MyCall|Zello Channel|QTH" | sudo tee -a /etc/asterisk/privatenodes.txt
```

Install support for privatenodes:

```bash
sudo apt install asl3-update-nodelist
```

### Allmon3 Overrides (`web.ini`)

`privatenodes.txt` is not used by Allmon3. To override labels in Allmon3, add the line to the `[node-overrides]` section of `/etc/allmon3/web.ini`.

Append if the section already exists:

```bash
sudo sed -i '/^\[node-overrides\]/a 1001 = MyCall Zello Channel QTH' /etc/allmon3/web.ini
```

Restart Allmon3:

```bash
sudo systemctl restart allmon3
```

If `[node-overrides]` does not exist, create it and add the line:

```bash
sudo sh -c 'grep -q "^\[node-overrides\]" /etc/allmon3/web.ini || echo "[node-overrides]" >> /etc/allmon3/web.ini'
echo "1001 = MyCall Zello Channel QTH" | sudo tee -a /etc/allmon3/web.ini
sudo systemctl restart allmon3
```

Resulting section:

```ini
[node-overrides]
1001 = MyCall Zello Channel QTH
```

---

## Docker

### Build

```bash
docker build -t asl-zello-bridge .
```

The image is multi-stage: PyOgg is installed from a pinned commit of the upstream repository (override with `--build-arg PYOGG_REF=<ref>`), and the final image runs as a non-root user with only the runtime Opus/Ogg libraries.

### Run with Compose

```bash
cp bridge.env.example bridge.env   # then edit bridge.env
mkdir -p keys                      # place zello.key here (Zello Free)
docker compose up -d --build
docker compose logs -f
```

The compose file:

* reads container configuration from `bridge.env` (override the path with `BRIDGE_ENV_FILE=/path/to/file`),
* publishes UDP `34001` on the host (override with `USRP_PUBLISH_PORT=`),
* mounts `./keys` into the container at `/keys` read-only (override with `KEYS_DIR=`).

Point your AllStarLink node at the published port:

```ini
rxchannel = USRP/127.0.0.1:34001:32001
```

When Asterisk/AllStarLink runs on the Docker host, keep `USRP_HOST=host.docker.internal` in `bridge.env` (the compose file maps it to the host gateway). If Asterisk runs on another machine, set `USRP_HOST` to that address instead.

Plain `docker run` equivalent (Zello Free example):

```bash
docker run --rm -it \
  --add-host host.docker.internal:host-gateway \
  -e USRP_BIND=0.0.0.0 \
  -e USRP_HOST=host.docker.internal \
  -e USRP_RXPORT=34001 \
  -e USRP_TXPORT=32001 \
  -e ZELLO_WS_ENDPOINT=wss://zello.io/ws \
  -e ZELLO_CHANNEL="My Test Channel" \
  -e ZELLO_PRIVATE_KEY=/keys/zello.key \
  -e ZELLO_USERNAME=myuser \
  -e ZELLO_PASSWORD=mypass \
  -e ZELLO_ISSUER=my-issuer-id \
  -v "$PWD/zello.key:/keys/zello.key:ro" \
  -p 34001:34001/udp \
  asl-zello-bridge
```

### Multiple instances (one per channel)

Run one isolated Compose project per Zello channel. Each instance needs its own env file, a unique published UDP host port, and its own `-p` project name:

```bash
mkdir -p instances keys

cp bridge.env.example instances/node1000.env   # edit values

BRIDGE_ENV_FILE=instances/node1000.env USRP_PUBLISH_PORT=34001 \
  docker compose -p zello-node1000 up -d --build

cp bridge.env.example instances/node1001.env   # edit values

BRIDGE_ENV_FILE=instances/node1001.env USRP_PUBLISH_PORT=34002 \
  docker compose -p zello-node1001 up -d --build
```

Inside each env file `USRP_RXPORT` can stay `34001` because containers are network-isolated from each other; only the published port differs. Point node `1001` at `127.0.0.1:34001:32001` and node `1002` at `127.0.0.1:34002:32001`.

Each instance is managed independently:

```bash
BRIDGE_ENV_FILE=instances/node1000.env docker compose -p zello-node1000 logs -f
BRIDGE_ENV_FILE=instances/node1001.env docker compose -p zello-node1001 restart
```

#### Host networking variant

If you prefer no address translation (for example, Asterisk requires `127.0.0.1`), use `network_mode: host` via an override file such as `docker-compose.host.yml`:

```yaml
services:
  bridge:
    build: .
    restart: unless-stopped
    init: true
    network_mode: host
    env_file:
      - ${BRIDGE_ENV_FILE:-bridge.env}
    volumes:
      - ${KEYS_DIR:-./keys}:/keys:ro
```

```bash
BRIDGE_ENV_FILE=instances/node1000.env \
  docker compose -f docker-compose.host.yml -p zello-node1000 up -d --build
```

With host networking every instance shares the host network stack, so `USRP_RXPORT` and `USRP_TXPORT` must be **unique per instance** (and match that node's `rxchannel`), while `USRP_BIND=127.0.0.1` and `USRP_HOST=127.0.0.1` become valid again.

This also works with Kubernetes or any container runtime.

---

## Credits

`asl-zello-bridge` is built and maintained by [Matt G4IYT](https://www.qrz.com/db/G4IYT)

Special thanks to:

* [Rob G4ZWH](https://www.qrz.com/db/G4ZWH) for inspiration and FreeSTAR bridge hosting
* [Shane M0VUB](https://www.qrz.com/db/M0VUB) for support on behalf of FreeSTAR
* [Lee M0LLC](https://www.qrz.com/db/M0LLC) for early adoption and CumbriaCQ testing
* [Piotr G0TWP](https://www.qrz.com/db/G0TWP) for SvxLink testing and bug discovery