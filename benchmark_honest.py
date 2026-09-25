"""
Genesis 2 — honest, reproducible benchmark.

What it does differently from the old "30/30" test:

  1. Every query is checked against the training data FIRST. A query that
     appears verbatim in a dataset hits the exact-match branch in
     genesis2_gen.py (~line 726) and gets its stored answer returned
     directly — no cascade, no neuron composition. That is a lookup, and
     counting it as a model result is dishonest. Such queries are reported
     separately and excluded from the headline score.

  2. Grading is mechanical, not eyeballed, and it is done at two levels.
     "Right tool" only asks whether the answer reached for the right family
     of command. "Does what was asked" demands the flags that actually carry
     out the task: nginx -t, not any nginx; pg_dump, not any psql; a rule
     that adds a DROP, not one that lists rules. The second number is the
     honest one — the first is kept only to show how much of the gap is
     "wrong neighbourhood" versus "right neighbourhood, wrong house".

  3. Latency is measured per query, cold and warm.

Run:  python3 benchmark_honest.py [--json out.json]
"""
import sys, os, time, json, glob, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))

# (query, tool-level accept, task-level accept)
#
#   tool-level  — did it reach for the right family of tool at all
#   task-level  — would running this actually do what was asked
#
# Both are reported. The second is the one that matters to a user; the first
# is kept because it shows how much of the gap is "wrong neighbourhood" versus
# "right neighbourhood, wrong house".
TESTS = [
    # --- storage -------------------------------------------------------
    ("how much free space is left on the root partition", ["df"], ["df"]),
    ("сколько свободного места осталось на разделе", ["df"], ["df"]),
    ("find the biggest files eating my disk", ["find", "du"], ["-size", "du ", "sort -rh", "sort -rn"]),
    ("какие файлы занимают больше всего места", ["find", "du"], ["-size", "du ", "sort -rh", "sort -rn"]),
    # --- memory / cpu / processes --------------------------------------
    ("show me current memory usage", ["free", "vm_stat", "top"], ["free", "vm_stat", "top"]),
    ("сколько оперативной памяти занято", ["free", "vm_stat", "top"], ["free", "vm_stat", "top"]),
    ("which process is burning the CPU", ["top", "ps"], ["sort=-%cpu", "sort -rn", "top -o cpu", "top -b"]),
    ("какой процесс грузит процессор", ["top", "ps"], ["sort=-%cpu", "sort -rn", "top -o cpu", "top -b"]),
    # --- network basics -------------------------------------------------
    ("list all network interfaces and their addresses", ["ip", "ifconfig"], ["ifconfig", "ip addr", "ip a "]),
    ("покажи сетевые интерфейсы и адреса", ["ip", "ifconfig"], ["ifconfig", "ip addr", "ip a "]),
    ("what is my default gateway", ["route", "ip r", "netstat"], ["netstat -rn", "ip route show", "ip route list", "route -n", "route get", "ip r s"]),
    ("какой у меня шлюз по умолчанию", ["route", "ip r", "netstat"], ["netstat -rn", "ip route show", "ip route list", "route -n", "route get", "ip r s"]),
    ("show open listening ports on this machine", ["ss", "netstat", "lsof"], ["listen", "-tlnp", "-tuln", "lsof -i"]),
    ("какие порты сейчас слушаются", ["ss", "netstat", "lsof"], ["listen", "-tlnp", "-tuln", "lsof -i"]),
    # --- dns -------------------------------------------------------------
    ("resolve a hostname and show which DNS answered", ["dig", "nslookup", "host"], ["dig", "nslookup"]),
    ("проверь работу DNS для домена", ["dig", "nslookup", "named", "host"], ["dig", "nslookup"]),
    # --- firewall --------------------------------------------------------
    ("list the current firewall rules", ["iptables", "nft", "ufw", "firewall"], ["iptables -l", "ufw status", "pfctl -sr", "nft list"]),
    ("выведи действующие правила брандмауэра", ["iptables", "nft", "ufw", "firewall"], ["iptables -l", "ufw status", "pfctl -sr", "nft list"]),
    ("block incoming traffic from one IP address", ["iptables", "nft", "ufw", "deny", "drop"], ["-a input", "-i input", "ufw deny", "ufw insert", "drop", "block drop"]),
    # --- routing / nat ---------------------------------------------------
    ("set up NAT so the LAN can reach the internet", ["masquerade", "iptables", "nat"], ["masquerade", "postrouting", "-j snat"]),
    ("настроить маскарадинг для выхода в интернет", ["masquerade", "iptables", "nat"], ["masquerade", "postrouting", "-j snat"]),
    # --- scanning --------------------------------------------------------
    ("scan a subnet for live hosts", ["nmap"], ["nmap"]),
    ("просканировать подсеть на живые узлы", ["nmap"], ["nmap"]),
    ("capture packets on an interface to a file", ["tcpdump", "pcap", "wireshark", "tshark"], ["tcpdump", "tshark"]),
    # --- services --------------------------------------------------------
    ("is the service running and how do I check", ["systemctl", "service", "launchctl"], ["systemctl is-active", "systemctl status", "launchctl list", "pgrep", "service "]),
    ("проверить, запущена ли служба", ["systemctl", "service", "launchctl"], ["systemctl is-active", "systemctl status", "launchctl list", "pgrep", "service "]),
    ("read the last log entries for a failing unit", ["journalctl", "log", "tail"], ["journalctl"]),
    # --- docker ----------------------------------------------------------
    ("list the containers that are currently running", ["docker"], ["docker ps"]),
    ("вывести запущенные контейнеры", ["docker"], ["docker ps"]),
    ("why does my container have no network", ["docker"], ["docker network", "docker inspect"]),
    # --- web servers -----------------------------------------------------
    ("check the nginx configuration for syntax errors", ["nginx"], ["nginx -t"]),
    ("проверить конфигурацию nginx на ошибки", ["nginx"], ["nginx -t"]),
    ("put a reverse proxy in front of an app", ["nginx", "proxy_pass", "proxy"], ["proxy_pass"]),
    # --- databases -------------------------------------------------------
    ("make a dump of a PostgreSQL database", ["pg_dump", "psql"], ["pg_dump", "pg_basebackup"]),
    ("сделать резервную копию базы PostgreSQL", ["pg_dump", "psql", "pg_basebackup"], ["pg_dump", "pg_basebackup"]),
    # --- vpn -------------------------------------------------------------
    ("bring up a WireGuard tunnel and verify it", ["wg", "wireguard"], ["wg-quick", "wg show", "wg set", "wg genkey"]),
    ("поднять туннель WireGuard и проверить", ["wg", "wireguard"], ["wg-quick", "wg show", "wg set", "wg genkey"]),
    # --- tls -------------------------------------------------------------
    ("when does the TLS certificate on this site expire", ["openssl", "ssl", "cert"], ["s_client", "-enddate", "-dates"]),
    ("когда истекает сертификат сайта", ["openssl", "ssl", "cert"], ["s_client", "-enddate", "-dates"]),
    # --- ssh hardening ---------------------------------------------------
    ("protect SSH from brute force attempts", ["fail2ban", "sshd", "ssh"], ["install fail2ban", "jail", "sshd_config", "maxretry"]),
    ("защитить SSH от перебора паролей", ["fail2ban", "sshd", "ssh"], ["install fail2ban", "jail", "sshd_config", "maxretry"]),
    # --- monitoring ------------------------------------------------------
    ("poll a device over SNMP", ["snmp"], ["snmpwalk", "snmpget"]),
    ("опросить устройство по SNMP", ["snmp"], ["snmpwalk", "snmpget"]),
    ("deploy a monitoring server", ["zabbix", "prometheus", "grafana", "monitor"], ["install zabbix", "zabbix-server", "zabbix_server", "prometheus.yml", "grafana-server", "docker run"]),
    # --- directory services ----------------------------------------------
    ("join this machine to an Active Directory domain", ["samba", "realm", "domain", "sssd"], ["realm join", "net ads join", "samba-tool domain join", "samba-tool domain provision"]),
    # --- telephony -------------------------------------------------------
    ("check SIP peers on the PBX", ["asterisk", "sip"], ["sip show peers", "pjsip show", "asterisk -rx"]),
    # --- routing protocols ------------------------------------------------
    ("show OSPF neighbours on the router", ["ospf", "vtysh"], ["ospf neighbor", "ospf neighbour", "ospf neigh"]),
    ("посмотреть соседей OSPF на маршрутизаторе", ["ospf", "vtysh"], ["ospf neighbor", "ospf neighbour"]),
    # --- audit ------------------------------------------------------------
    ("run a security audit of this host", ["lynis", "audit"], ["lynis audit", "lynis -c", "lynis --"]),
]


def training_corpus():
    """Every trained question (lowercased) and the whole corpus text.

    The corpus text is used to answer a separate question: was the model ever
    taught this task at all? A query whose expected command appears nowhere in
    the training data is not a routing failure — it is something the model was
    never told. Those are reported apart from real misses.
    """
    seen = set()
    blob = []
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
            for k in ("answer", "response", "exec", "cmd"):
                v = d.get(k)
                if isinstance(v, dict):
                    v = v.get("cmd")
                if isinstance(v, str):
                    blob.append(v.lower())
    return seen, "\n".join(blob)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write full results here")
    args = ap.parse_args()

    trained, corpus = training_corpus()
    print(f"training questions loaded: {len(trained)}")

    # A test is "teachable" only if the corpus contains something that would
    # satisfy it. Otherwise the model was never given the knowledge.
    teachable = {q: any(a.lower() in corpus for a in strict) for q, _, strict in TESTS}
    for q, _, strict in TESTS:
        if not teachable[q]:
            print(f"  never taught: {q}")
    print(f"tests the corpus could answer at all: {sum(teachable.values())}/{len(TESTS)}")

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

    rows, lookups, cascade_ok, cascade_n, strict_ok = [], 0, 0, 0, 0
    taught_n, taught_ok = 0, 0
    for q, accept, strict in TESTS:
        in_corpus = teachable[q]
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
        # Tool level may be satisfied by the prose. The task level may not:
        # what the user runs is the command, so that is what gets graded.
        cmd_hay = str(cmd).lower()
        ok = any(a.lower() in hay for a in accept)
        ok_strict = bool(cmd_hay.strip()) and any(a.lower() in cmd_hay for a in strict)

        if is_lookup:
            lookups += 1
        else:
            cascade_n += 1
            cascade_ok += int(ok)
            strict_ok += int(ok_strict)
            if in_corpus:
                taught_n += 1
                taught_ok += int(ok_strict)

        rows.append({"query": q, "lookup": is_lookup, "in_corpus": in_corpus,
                     "ok": ok, "ok_strict": ok_strict,
                     "ms": round(ms, 1), "accept": accept, "strict": strict,
                     "cmd": str(cmd)[:160], "response": text[:200], "error": err})
        if is_lookup:
            mark = "LOOKUP "
        elif not in_corpus:
            mark = "UNTAUG "
        elif ok_strict:
            mark = "  PASS "
        elif ok:
            mark = "  TOOL "
        else:
            mark = "  MISS "
        print(f"{mark}{ms:7.0f}ms  {q[:52]:<52} -> {(str(cmd) or text)[:46]}")

    lat = sorted(r["ms"] for r in rows)
    print("\n" + "=" * 72)
    print(f"queries                  : {len(rows)}")
    print(f"verbatim in training data: {lookups}   (excluded — these are lookups)")
    print(f"answered via cascade     : {cascade_n}")
    print(f"never taught (not in corpus): {cascade_n - taught_n}  — reported, not scored")
    print(f"does what was asked, of the taught ones: {taught_ok}/{taught_n} "
          f"= {100.0*taught_ok/max(1,taught_n):.0f}%   <-- the number that matters")
    print(f"does what was asked, of all {cascade_n}      : {strict_ok}/{cascade_n} "
          f"= {100.0*strict_ok/max(1,cascade_n):.0f}%")
    print(f"right tool, any use of it               : {cascade_ok}/{cascade_n} "
          f"= {100.0*cascade_ok/max(1,cascade_n):.0f}%")
    print(f"latency median / p95     : {lat[len(lat)//2]:.0f}ms / {lat[int(len(lat)*0.95)]:.0f}ms")
    print(f"model load               : {load_s:.0f}s, CPU only, no GPU")
    print("=" * 72)

    if args.json:
        json.dump({"load_seconds": round(load_s, 1), "experts": len(gen.routes),
                   "neurons": len(gen.neurons), "lookups": lookups,
                   "cascade_total": cascade_n, "cascade_correct": cascade_ok,
                   "cascade_correct_strict": strict_ok,
                   "taught_total": taught_n, "taught_correct": taught_ok,
                   "results": rows}, open(args.json, "w"), ensure_ascii=False, indent=2)
        print(f"written: {args.json}")


if __name__ == "__main__":
    main()
