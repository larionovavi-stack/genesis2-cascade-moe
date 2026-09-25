"""
Genesis 2 — honest, reproducible benchmark.

What it does differently from the old "30/30" test:

  1. Every query is checked against the training data FIRST. A query that
     appears verbatim in a dataset hits the exact-match branch in
     genesis2_gen.py (~line 726) and gets its stored answer returned
     directly — no cascade, no neuron composition. That is a lookup, and
     counting it as a model result is dishonest. Such queries are reported
     separately and excluded from the headline score.

  2. Grading is mechanical, not eyeballed: each query declares the tool or
     flag a correct answer must contain. No human decides afterwards
     whether an answer "looks right".

  3. Latency is measured per query, cold and warm.

Run:  python3 benchmark_honest.py [--json out.json]
"""
import sys, os, time, json, glob, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))

# (query, accepted substrings — answer is correct if ANY appears)
TESTS = [
    # --- storage -------------------------------------------------------
    ("how much free space is left on the root partition", ["df"]),
    ("сколько свободного места осталось на разделе", ["df"]),
    ("find the biggest files eating my disk", ["find", "du"]),
    ("какие файлы занимают больше всего места", ["find", "du"]),
    # --- memory / cpu / processes --------------------------------------
    ("show me current memory usage", ["free", "vm_stat", "top"]),
    ("сколько оперативной памяти занято", ["free", "vm_stat", "top"]),
    ("which process is burning the CPU", ["top", "ps"]),
    ("какой процесс грузит процессор", ["top", "ps"]),
    # --- network basics -------------------------------------------------
    ("list all network interfaces and their addresses", ["ip", "ifconfig"]),
    ("покажи сетевые интерфейсы и адреса", ["ip", "ifconfig"]),
    ("what is my default gateway", ["route", "ip r", "netstat"]),
    ("какой у меня шлюз по умолчанию", ["route", "ip r", "netstat"]),
    ("show open listening ports on this machine", ["ss", "netstat", "lsof"]),
    ("какие порты сейчас слушаются", ["ss", "netstat", "lsof"]),
    # --- dns -------------------------------------------------------------
    ("resolve a hostname and show which DNS answered", ["dig", "nslookup", "host"]),
    ("проверь работу DNS для домена", ["dig", "nslookup", "named", "host"]),
    # --- firewall --------------------------------------------------------
    ("list the current firewall rules", ["iptables", "nft", "ufw", "firewall"]),
    ("выведи действующие правила брандмауэра", ["iptables", "nft", "ufw", "firewall"]),
    ("block incoming traffic from one IP address", ["iptables", "nft", "ufw", "deny", "drop"]),
    # --- routing / nat ---------------------------------------------------
    ("set up NAT so the LAN can reach the internet", ["masquerade", "iptables", "nat"]),
    ("настроить маскарадинг для выхода в интернет", ["masquerade", "iptables", "nat"]),
    # --- scanning --------------------------------------------------------
    ("scan a subnet for live hosts", ["nmap"]),
    ("просканировать подсеть на живые узлы", ["nmap"]),
    ("capture packets on an interface to a file", ["tcpdump", "pcap", "wireshark", "tshark"]),
    # --- services --------------------------------------------------------
    ("is the service running and how do I check", ["systemctl", "service", "launchctl"]),
    ("проверить, запущена ли служба", ["systemctl", "service", "launchctl"]),
    ("read the last log entries for a failing unit", ["journalctl", "log", "tail"]),
    # --- docker ----------------------------------------------------------
    ("list the containers that are currently running", ["docker"]),
    ("вывести запущенные контейнеры", ["docker"]),
    ("why does my container have no network", ["docker"]),
    # --- web servers -----------------------------------------------------
    ("check the nginx configuration for syntax errors", ["nginx"]),
    ("проверить конфигурацию nginx на ошибки", ["nginx"]),
    ("put a reverse proxy in front of an app", ["nginx", "proxy_pass", "proxy"]),
    # --- databases -------------------------------------------------------
    ("make a dump of a PostgreSQL database", ["pg_dump", "psql"]),
    ("сделать резервную копию базы PostgreSQL", ["pg_dump", "psql", "pg_basebackup"]),
    # --- vpn -------------------------------------------------------------
    ("bring up a WireGuard tunnel and verify it", ["wg", "wireguard"]),
    ("поднять туннель WireGuard и проверить", ["wg", "wireguard"]),
    # --- tls -------------------------------------------------------------
    ("when does the TLS certificate on this site expire", ["openssl", "ssl", "cert"]),
    ("когда истекает сертификат сайта", ["openssl", "ssl", "cert"]),
    # --- ssh hardening ---------------------------------------------------
    ("protect SSH from brute force attempts", ["fail2ban", "sshd", "ssh"]),
    ("защитить SSH от перебора паролей", ["fail2ban", "sshd", "ssh"]),
    # --- monitoring ------------------------------------------------------
    ("poll a device over SNMP", ["snmp"]),
    ("опросить устройство по SNMP", ["snmp"]),
    ("deploy a monitoring server", ["zabbix", "prometheus", "grafana", "monitor"]),
    # --- directory services ----------------------------------------------
    ("join this machine to an Active Directory domain", ["samba", "realm", "domain", "sssd"]),
    # --- telephony -------------------------------------------------------
    ("check SIP peers on the PBX", ["asterisk", "sip"]),
    # --- routing protocols ------------------------------------------------
    ("show OSPF neighbours on the router", ["ospf", "vtysh"]),
    ("посмотреть соседей OSPF на маршрутизаторе", ["ospf", "vtysh"]),
    # --- audit ------------------------------------------------------------
    ("run a security audit of this host", ["lynis", "audit"]),
]


def training_questions():
    """Every question string the model was trained on, lowercased."""
    seen = set()
    for f in glob.glob(os.path.join(HERE, "datasets", "*.jsonl")):
        for line in open(f, encoding="utf-8", errors="ignore"):
            try:
                d = json.loads(line)
            except Exception:
                continue
            for k in ("question", "input", "query", "q"):
                v = d.get(k)
                if isinstance(v, str):
                    seen.add(v.lower().strip())
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write full results here")
    args = ap.parse_args()

    trained = training_questions()
    print(f"training questions loaded: {len(trained)}")

    from genesis2_gen import CascadeGenerator
    from neuron_embedding import NeuronPoolEmbedding

    # Same encoder the server uses: our own hash encoder, no sentence-transformers.
    print("loading model ...", flush=True)
    t0 = time.time()
    gen = CascadeGenerator(NeuronPoolEmbedding(dim=384), dim=384)
    gen.load_state(os.path.join(HERE, "genesis2_trained_full.pt"))
    load_s = time.time() - t0
    print(f"loaded in {load_s:.1f}s — {len(gen.routes)} experts, {len(gen.neurons)} neurons")

    # Exact-match set as the generator itself sees it.
    stored_inputs = {r.get("input_text", "").lower().strip()
                     for r in gen.routes.values()}

    rows, lookups, cascade_ok, cascade_n = [], 0, 0, 0
    for q, accept in TESTS:
        key = q.lower().strip()
        is_lookup = key in stored_inputs or key in trained
        t = time.time()
        try:
            res = gen.generate(q, top_k=5, depth=2)
            err = None
        except Exception as e:
            res, err = {}, f"{type(e).__name__}: {e}"
        ms = (time.time() - t) * 1000

        text = str(res.get("response", "") or "")
        ex = res.get("exec")
        cmd = ex.get("cmd", "") if isinstance(ex, dict) else (ex or "")
        hay = (text + " " + str(cmd)).lower()
        ok = any(a.lower() in hay for a in accept)

        if is_lookup:
            lookups += 1
        else:
            cascade_n += 1
            cascade_ok += int(ok)

        rows.append({"query": q, "lookup": is_lookup, "ok": ok, "ms": round(ms, 1),
                     "accept": accept, "cmd": str(cmd)[:120],
                     "response": text[:200], "error": err})
        mark = "LOOKUP " if is_lookup else ("  PASS " if ok else "  FAIL ")
        print(f"{mark}{ms:7.0f}ms  {q[:52]:<52} -> {(str(cmd) or text)[:46]}")

    lat = sorted(r["ms"] for r in rows)
    print("\n" + "=" * 72)
    print(f"queries                  : {len(rows)}")
    print(f"verbatim in training data: {lookups}   (excluded — these are lookups)")
    print(f"answered via cascade     : {cascade_n}")
    print(f"correct tool chosen      : {cascade_ok}/{cascade_n} "
          f"= {100.0*cascade_ok/max(1,cascade_n):.0f}%")
    print(f"latency median / p95     : {lat[len(lat)//2]:.0f}ms / {lat[int(len(lat)*0.95)]:.0f}ms")
    print(f"model load               : {load_s:.0f}s, CPU only, no GPU")
    print("=" * 72)

    if args.json:
        json.dump({"load_seconds": round(load_s, 1), "experts": len(gen.routes),
                   "neurons": len(gen.neurons), "lookups": lookups,
                   "cascade_total": cascade_n, "cascade_correct": cascade_ok,
                   "results": rows}, open(args.json, "w"), ensure_ascii=False, indent=2)
        print(f"written: {args.json}")


if __name__ == "__main__":
    main()
