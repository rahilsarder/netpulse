# NetPulse – ISP Destination Monitoring & Alerting Platform

## Overview

NetPulse is a network monitoring and alerting platform built for ISP operations.

Primary goal:

Continuously monitor destinations from ISP infrastructure and instantly detect:

- high latency
- packet loss
- destination unreachable
- route instability

Then:

- alert immediately via Telegram
- generate automatic traceroute diagnostics
- store historical metrics
- visualize data in a modern NOC dashboard

---

# Main Use Cases

Monitor:

- upstream transit providers
- IX peers
- BGP next-hop routers
- Cloudflare DNS
- Google DNS
- Netflix/OpenConnect cache
- Facebook CDN
- YouTube CDN
- customer critical services
- internal POP/core routers

Detect:

- latency spikes
- intermittent packet loss
- complete outage
- unstable route path
- route degradation

---

# Tech Stack

## Backend

- Python 3.12+
- Flask
- Flask-SocketIO
- APScheduler / background workers
- SQLite initially
- PostgreSQL later
- ping3
- mtr
- traceroute
- requests

## Frontend

- React
- Vite
- TailwindCSS
- shadcn/ui
- Heroicons
- Recharts

## Realtime

- WebSocket

## Deployment

- Ubuntu server
- Docker-ready

---

# Core Monitoring Features

---

## 1. Destination Probes

Admin can create probes.

Example:

```json
{
  "name": "Cloudflare DNS",
  "host": "1.1.1.1",
  "group": "Public DNS",
  "probe_interval": 5,
  "latency_threshold": 80,
  "packet_loss_threshold": 5,
  "enabled": true
}
```

Supported:

- IP
- hostname
- TCP endpoint
- HTTP endpoint
- DNS

Examples:

- 1.1.1.1
- 8.8.8.8
- upstream router IP
- IX peer IP
- CDN IP

---

## 2. Probe Engine

Run continuously.

Each cycle:

- ICMP ping x5
- calculate:
  - minimum latency
  - average latency
  - maximum latency
  - jitter
  - packet loss %
- save timestamp

Statuses:

- UP
- DEGRADED
- DOWN

---

## 3. Historical Storage

Store every probe result.

Example:

```json
{
  "target": "1.1.1.1",
  "latency_avg": 14,
  "latency_max": 20,
  "jitter": 2,
  "packet_loss": 0,
  "status": "UP",
  "timestamp": "2026-05-27T15:00:00"
}
```

Retention:

- raw data → 30 days
- aggregated hourly → 1 year

---

# UI Requirements

Important:

Modern premium NOC dashboard.

Design:

- dark mode first
- Tailwind
- clean layout
- smooth animations
- glassmorphism cards
- subtle glow
- responsive
- fast rendering

---

# Dashboard

Top KPI cards:

- total probes
- active incidents
- targets down
- degraded targets
- average latency
- average packet loss

Example:

```
Targets: 47
Down: 2
Degraded: 3
Avg latency: 12ms
Packet loss active: 1
```

---

## Real-time Probe Table

Columns:

- target name
- IP/host
- group
- source location
- status
- latency
- jitter
- packet loss
- last checked
- traceroute button

Filters:

- group
- status
- location

Search bar

Status colors:

Green → UP

Yellow → DEGRADED

Red → DOWN

---

# Historical Graphs

Target detail page:

Charts:

## Latency

- 15 min
- 1 hour
- 24 hour
- 7 day

## Packet loss

## Jitter

## Availability %

Show incident markers:

Example:

“Packet loss started 2:31 PM”

Realtime updates via websocket.

---

# Probe Detail Page

Show:

- target info
- current status
- latency
- packet loss
- jitter
- graphs
- recent incidents
- route history
- traceroute history

---

# Telegram Alerting

Bot config:

```env
BOT_TOKEN=
CHAT_ID=
```

---

## Alert Rules

Trigger when:

### High latency

Latency > threshold

For 3 consecutive checks

### Packet loss

Loss > threshold

For 2 consecutive checks

### Down

100% packet loss

### Recovery

Target returns healthy

Cooldown:

5 minutes

---

# Telegram Message Format

Example:

```text
🚨 INCIDENT DETECTED

Target: Cloudflare DNS
IP: 1.1.1.1
Group: Public DNS

Status: HIGH LATENCY

Average latency: 118 ms
Maximum latency: 140 ms
Packet loss: 12%
Jitter: 21 ms

Detected:
3:12 PM

Probe source:
Kaliganj POP

Next hop:
Transit-A

ASN:
AS13335

Dashboard:
http://monitor.local/targets/1
```

---

# Automatic Trace Report

When incident occurs:

Run:

```bash
mtr -r -c 10 target
```

Collect:

- hop number
- IP
- hostname
- latency
- packet loss

Telegram example:

```text
📡 TRACE REPORT

Target:
1.1.1.1

1 10.x.x.x       1ms
2 172.x.x.x      2ms
3 transit-a      5ms
4 upstream       13ms
5 cloudflare   120ms LOSS 18%

Likely issue:
Hop 5 latency spike detected
```

Save trace history.

Show in UI.

---

# Incident Center

Pages:

## Active incidents

## Resolved incidents

Fields:

- target
- source
- started
- resolved
- duration
- issue type
- trace report

Filters:

- date
- target
- source
- status

---

# Multi-Probe Source Support

Sources:

- Core router
- Kaliganj POP
- Dhaka POP
- Cache node

Example:

```json
{
  "source": "Kaliganj POP",
  "target": "1.1.1.1"
}
```

Need:

Compare latency from different probe locations.

Same target:

multiple sources.

---

# Logging

Store:

- probe logs
- incidents
- telegram delivery logs
- trace history
- failures

---

# Future Features

Later:

- ASN lookup
- prefix geolocation
- BGP path compare
- MikroTik integration
- syslog correlation
- traffic correlation
- AI anomaly detection
- upstream recommendation

---

# Suggested Project Structure

```bash
backend/
  app.py
  models.py
  database.py
  monitor.py
  telegram.py
  traceroute.py
  websocket.py

frontend/
  src/
    pages/
    components/
    charts/
    hooks/
    api/
```

---

# Cursor Build Prompt

Build this project step-by-step.

Order:

1. Flask backend
2. SQLite models
3. probe engine
4. Telegram alerts
5. traceroute integration
6. REST API
7. websocket
8. React frontend
9. Tailwind modern NOC UI
10. historical charts
11. incident center
12. multi-source probes

Requirements:

- clean architecture
- reusable components
- production-ready code
- fast UI
- dark mode first
- scalable
- easy deployment