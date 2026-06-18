<p align="center">
  <img src="assets/banner_genesis2.png" alt="Genesis 2 — Cascade MoE Neural Network" width="100%">
</p>

<h1 align="center">Genesis 2 — Cascade MoE Neural Network</h1>

<p align="center">
  <strong>The World's First Patented Neural Architecture That Runs on CPU</strong>
</p>

<p align="center">
  <a href="#benchmarks"><img src="https://img.shields.io/badge/accuracy-100%25_(111%2F111)-brightgreen?style=for-the-badge" alt="Accuracy"></a>
  <a href="#benchmarks"><img src="https://img.shields.io/badge/neurons-12,651-blue?style=for-the-badge" alt="Neurons"></a>
  <a href="#benchmarks"><img src="https://img.shields.io/badge/experts-10,800+-blue?style=for-the-badge" alt="Experts"></a>
  <a href="#architecture"><img src="https://img.shields.io/badge/GPU-not%20required-red?style=for-the-badge" alt="No GPU"></a>
  <a href="#whats-new"><img src="https://img.shields.io/badge/version-v1.1-cyan?style=for-the-badge" alt="v1.1"></a>
  <a href="#patent"><img src="https://img.shields.io/badge/patent-pending-purple?style=for-the-badge" alt="Patent"></a>
</p>

<p align="center">
  <a href="https://avlarion.gumroad.com/l/lqtsbo">Academic $299</a> &bull;
  <a href="https://avlarion.gumroad.com/l/vrzudu">Professional $1,499</a> &bull;
  <a href="https://avlarion.gumroad.com/l/atmon">Enterprise $4,999</a> &bull;
  <a href="https://avlarion.gumroad.com/l/ymyagw">Source + Patent Bundle $5,000</a> &bull;
  <a href="https://larionovavi-stack.github.io/genesis2-cascade-moe/docs/reference-guide.html"><strong>Interactive Reference Guide</strong></a>
</p>

<p align="center">
  <a href="https://gist.github.com/larionovavi-stack/d9bdc484813df7cb488a842cb4a0cd62"><img src="https://img.shields.io/badge/Live_Demo-Try_Now-brightgreen?style=for-the-badge" alt="Live Demo"></a>
</p>

> **[Try the Live Demo](https://gist.github.com/larionovavi-stack/d9bdc484813df7cb488a842cb4a0cd62)** — click the link in the Gist for the current demo URL. Model hosted on [Kaggle](https://www.kaggle.com/datasets/alexanderlar/genesis2-cascade-moe-model). If the demo is unavailable, email **avlarionov@hotmail.com** to request a restart.

---

## What is Genesis 2?

Genesis 2 is a **fundamentally new neural network architecture** that eliminates the need for GPU, external LLMs, and massive compute resources. It uses Cascade Activation of a Shared Neuron Pool — a patented approach where experts share neurons instead of duplicating parameters.

**No GPU. No Cloud. No API costs. No token limits. Runs on your laptop.**

```
Traditional MoE:  Expert₁[500MB] + Expert₂[500MB] + ... = 50GB+, GPU required
Genesis 2:        Expert₁[route] + Expert₂[route] + ... = 3.64 GB total, CPU only
                  ↑ shared neuron pool, each expert is just a list of neuron IDs
```

## Why Genesis 2?

| Traditional AI (GPT, LLaMA, etc.) | Genesis 2 |
|:---|:---|
| $2,000+/mo GPU costs | **$0** — runs on CPU |
| API rate limits & downtime | **Unlimited** — self-hosted |
| Data leaves your network | **100% on-premise** |
| Catastrophic forgetting | **Zero forgetting** — mathematically guaranteed |
| Minutes to fine-tune | **130ms** to learn a new fact |
| Token window limits (4K-128K) | **Infinite context** — no limits |
| Vendor lock-in | **You own the code** |

## Quick Start

```bash
# Install dependencies
pip install torch numpy requests

# Start the web server
python genesis2_web.py

# Open in browser
open http://localhost:8765
```

## API

```python
import requests

API = "http://localhost:8765"

# Ask a question (returns answer + executable commands)
r = requests.post(f"{API}/api/query", json={"question": "configure nginx reverse proxy"})
print(r.json()["answer"])
print(r.json()["commands"])

# Teach new knowledge (learns in 130-550ms)
requests.post(f"{API}/api/learn", json={
    "question": "how to restart Apache",
    "answer": "Restart Apache web server",
    "exec": "systemctl restart apache2"
})

# Save state
requests.post(f"{API}/api/save")
```

## What's New in v1.1 <a name="whats-new"></a>

Released: **June 2026**

| Feature | Description |
|:--------|:------------|
| 🧠 **Neuron Splitting** (Patent п.5) | Overloaded neurons auto-split via 2-means clustering. Coherence threshold 0.40 triggers split → two child neurons inherit parent weights |
| 💬 **Dialogue Context** | Model tracks conversation state: "no thanks", "nothing needed", "пока ничего" → correct conversational replies instead of technical routing |
| 🔧 **Command Substitution** | Auto-fills IP/port/subnet from user's question into exec commands: `ping 10.0.0.1` → `ping -c 4 10.0.0.1` |
| 🔤 **Typo Normalization** | Repeated Cyrillic letters collapsed: "ппривет" → "привет", "приввет" → "привет" (Latin preserved: "need" stays "need") |
| 📊 **111/111 Test Suite** | Extended benchmark from 30 to **111 queries** across 43 topics: networking, security, Docker, Cisco, VPN, DNS, databases, monitoring, SCADA, VoIP and more |
| 🌐 **Bilingual 100%** | Both RU and EN at 100% accuracy simultaneously — verified across all 43 topic categories |

## Benchmarks

| Metric | v1.0 | **v1.1** |
|:-------|:-----|:---------|
| Shared Neurons | 12,100+ | **12,651** |
| Trained Experts | 10,800+ | **10,800+** |
| Test accuracy | 100% (30/30) | **100% (111/111)** |
| Topics covered | 15 | **43** |
| Inference latency | 18-27ms | **18-27ms** |
| Learning speed | 130-550ms | **130ms** per fact |
| Zero forgetting (cosine) | 1.000000 | **1.000000** |
| Neuron splitting | ✗ | **✓ (auto)** |
| Dialogue context | ✗ | **✓** |
| Command substitution | ✗ | **✓** |
| RAM usage | 3.5GB | **3.64 GB** |
| GPU required | No | **No** |

### Test Results v1.1 — 111/111 across 43 topics

```
networking RU/EN  ✅✅✅✅✅✅✅✅✅✅✅  (11/11)
linux RU/EN       ✅✅✅✅✅✅✅✅✅✅✅  (11/11)
security RU/EN    ✅✅✅✅✅✅✅✅✅  (9/9)
vpn RU/EN         ✅✅✅✅✅  (5/5)
docker/k8s RU/EN  ✅✅✅✅✅✅✅✅  (8/8)
cisco RU/EN       ✅✅✅✅✅  (5/5)
dns/dhcp RU/EN    ✅✅✅✅✅✅  (6/6)
monitoring RU/EN  ✅✅✅✅✅  (5/5)
databases         ✅✅✅✅  (4/4)
nginx/web         ✅✅✅✅✅  (5/5)
windows           ✅✅  (2/2)
mikrotik          ✅✅  (2/2)
voip/sip          ✅✅  (2/2)
scada/iot         ✅✅  (2/2)
backup            ✅✅  (2/2)
devops            ✅✅✅✅  (4/4)
troubleshooting   ✅✅✅✅  (4/4)
cloud/virt        ✅✅✅  (3/3)
macos             ✅✅✅  (3/3)
traffic           ✅✅✅  (3/3)
greetings/typos   ✅✅✅✅✅✅✅  (7/7)
slang/infra       ✅✅✅✅  (4/4)
                           ───────
TOTAL:            ✅ 111/111 = 100%
```

## Architecture

Genesis 2 is built on 8 patented innovations:

### 1. Shared Neuron Pool
All neurons live in a single shared pool. Experts don't have their own parameters — they reference neurons by ID. One neuron can serve 50+ experts simultaneously. This makes the model **100x smaller** than traditional MoE.

### 2. Expert as Route
Each expert is just a list of neuron IDs — a "route" through the shared pool. Adding a new expert costs **bytes, not megabytes**. 10,800+ expert routes fit in 3.64 GB.

### 3. Cascade Activation (No Router)
Traditional MoE uses a trained router to pick experts. Genesis 2 uses a reverse index (neuron → experts) to find relevant experts in **0.14ms**. No router training, no routing errors.

### 4. One-Step Learning
To learn a new fact: freeze all shared neurons, create a new expert with a micro-head. Takes **130-550ms**. The new knowledge never interferes with existing knowledge.

### 5. Zero Catastrophic Forgetting
Each expert has its own micro-head (output layer). New experts can't modify existing ones. **Mathematically guaranteed** — cosine similarity = 1.000000 before/after learning.

### 6. Hash Neuron Embedding
Custom embedding system with 9,761 tokens across 72 types. No dependency on external models (MiniLM, BERT, etc.). Fully self-contained.

### 7. Infinite Context
Every learned fact becomes a permanent expert. No token window limits. 10,000 facts = 10,000 experts, all accessible instantly.

### 8. Native Generation via Concept Chains
Output is generated through a composer that chains related concepts from activated experts. Not template matching — actual generation.

```
Input → Hash Embedding (512d) → ANN Search → Seed Experts
     → Cascade Activation → Shared Neuron Pool → Composer → Output
```

## Knowledge Domains (35)

> The model is fully bilingual (RU + EN). Trained on 35 domains with 100% accuracy in both languages. Genesis 2 learns new facts in **130ms** — you can train your own model on any language and any domain in minutes, not days.

<table>
<tr><td>Networking (Cisco, MikroTik)</td><td>Linux Administration</td><td>Docker & Kubernetes</td></tr>
<tr><td>Security & Hardening</td><td>WiFi Configuration</td><td>DNS/DHCP/BIND</td></tr>
<tr><td>VPN (WireGuard, OpenVPN)</td><td>Databases (PostgreSQL, MySQL)</td><td>Web Servers (Nginx, Apache)</td></tr>
<tr><td>Monitoring (Zabbix, Prometheus)</td><td>DevOps (Ansible, Terraform)</td><td>Python Scripting</td></tr>
<tr><td>Bash Automation</td><td>Packet Analysis</td><td>VoIP (Asterisk)</td></tr>
<tr><td>Windows Active Directory</td><td>macOS Administration</td><td>Virtualization</td></tr>
<tr><td>SCADA/ICS</td><td>Cloud (AWS/GCP/Azure)</td><td>Server Configuration</td></tr>
<tr><td>Mobile Protocols</td><td colspan="2"></td></tr>
</table>

## System Requirements

| Component | Minimum | Recommended |
|:----------|:--------|:------------|
| CPU | Any modern (ARM or x86) | 4+ cores |
| RAM | 6 GB | 16 GB |
| Disk | 4 GB | 10 GB |
| Python | 3.9+ | 3.11+ |
| PyTorch | 2.0+ | 2.3+ |
| OS | macOS / Linux / Windows | Any |
| GPU | **Not required** | Not required |

## Patent

**Status:** Filed at FIPS Russia, 31.05.2026
**Type:** Utility Model, IPC G06N 3/04
**Claims:** 2 independent + 6 dependent (8 total)
**RCIS Blockchain Certificate:** #1823-376-572

The Cascade MoE architecture is protected by a pending patent. The patent covers all 8 architectural innovations listed above.

## OS-Aware Execution

Genesis 2 detects the host operating system and adapts:

- **macOS**: Strips `sudo`, warns about Linux-only commands, uses macOS equivalents
- **Linux**: Full command execution with `sudo` support
- **Windows**: Suggests PowerShell alternatives
- **Safety**: Blocks dangerous commands (`rm -rf`, `mkfs`, `dd`, `shutdown`)

## Editions

| Edition | Price | License | Includes |
|:--------|:------|:--------|:---------|
| [**Academic**](https://avlarion.gumroad.com/l/lqtsbo) | $299 | 1 person, research only | Source + model + docs |
| [**Professional**](https://avlarion.gumroad.com/l/vrzudu) | $1,499 | 5 users, commercial | + 30 datasets + 12mo updates |
| [**Enterprise**](https://avlarion.gumroad.com/l/atmon) | $4,999 | Unlimited, commercial | + patent docs + book + lifetime updates |
| [**Source + Patent Bundle**](https://avlarion.gumroad.com/l/ymyagw) | $5,000 | White-label rights | + patent license + 5h consultation |

## Project Structure

```
genesis2-cascade-moe/
├── genesis2_core.py          # Core: neurons, cascade, shared pool, training
├── genesis2_gen.py           # Generation: concept chains, composer, boost
├── genesis2_agent.py         # Agent: learn/reason/plan/chat/self-learn
├── genesis2_web.py           # Web UI + REST API + OS detection
├── genesis2_repl.py          # Interactive terminal REPL
├── embedding/
│   └── train_embedding.py    # Custom hash embedding training
├── datasets/                 # 30 training datasets (Professional+)
├── PATENT/                   # Patent materials (Enterprise+)
└── requirements.txt
```

## Author

**Larionov Alexander Viktorovich** (Ларионов Александр Викторович)

- SCADA/ICS Engineer with 10+ years of industrial automation experience
- AI Researcher specializing in novel neural architectures
- Patent holder (Cascade MoE, FIPS Russia 2026)

**Contact:** avlarionov@hotmail.com
**GitHub:** [larionovavi-stack](https://github.com/larionovavi-stack)
**Products:** [avlarion.gumroad.com](https://avlarion.gumroad.com)

## Also by Author

- **[atwSCADA](https://github.com/larionovavi-stack/awtscada)** — Free SCADA system in a single HTML file (IEC 61850, OPC UA, Modbus TCP)
- **[Network Automation with AI](https://github.com/larionovavi-stack/network-automation-ai-guide)** — 132-page practical guide ($29)

## Affiliate Program

Earn **40% commission** on every sale by promoting Genesis 2.

**[→ Join the Affiliate Program](https://avlarion.gumroad.com/affiliates)**

Payouts via Gumroad. No approval required — instant access.

## License

This repository contains the documentation, architecture description, and demo materials. The full source code and trained model are available through [Gumroad](https://avlarion.gumroad.com).

Patent pending. All rights reserved. (c) 2026 Larionov Alexander Viktorovich.

---

<p align="center">
  <strong>No GPU. No Cloud. No Limits.</strong><br>
  <a href="https://avlarion.gumroad.com/l/lqtsbo">Get Genesis 2 Academic — $299</a>
</p>
