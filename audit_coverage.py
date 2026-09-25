"""
Exactly how much of the benchmark the training data could possibly teach.

The benchmark's own coverage check was weak: it asked whether a strict pattern
appeared anywhere among 11,006 facts. `pg_dump` existing somewhere does not
mean any fact teaches "back up a PostgreSQL database".

Here a training fact *teaches* a benchmark query only if BOTH hold:

  1. its QUESTION matches an explicit keyword rule for that task, written out
     below as an AND of ORs — every group must be hit by at least one word;
  2. its EXEC COMMAND satisfies the same strict pattern the benchmark grades
     against.

Both halves are spelled out, so the rule can be argued with rather than
trusted. Nothing here is a similarity score or a threshold.

Run: python3 audit_coverage.py
"""
import os, re, json, glob, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))

# query -> AND-list of OR-groups that the training QUESTION must satisfy
Q_RULES = {
 "how much free space is left on the root partition": [["disk", "диск", "space", "мест", "раздел", "df", "партиц"]],
 "сколько свободного места осталось на разделе":      [["disk", "диск", "space", "мест", "раздел", "df", "партиц"]],
 "find the biggest files eating my disk":             [["big", "больш", "large", "size", "размер", "тяжел"], ["file", "файл"]],
 "какие файлы занимают больше всего места":           [["big", "больш", "large", "size", "размер", "тяжел", "занима", "мест"], ["file", "файл"]],
 "show me current memory usage":                      [["memory", "памят", "ram", "озу", "mem"]],
 "сколько оперативной памяти занято":                 [["memory", "памят", "ram", "озу", "mem"]],
 "which process is burning the CPU":                  [["cpu", "процессор", "загруз", "нагруз"], ["process", "процесс", "top", "потребл"]],
 "какой процесс грузит процессор":                    [["cpu", "процессор", "загруз", "нагруз", "грузит"], ["process", "процесс", "top", "потребл"]],
 "list all network interfaces and their addresses":   [["interface", "интерфейс", "ifconfig", "адаптер"]],
 "покажи сетевые интерфейсы и адреса":                [["interface", "интерфейс", "ifconfig", "адаптер"]],
 "what is my default gateway":                        [["gateway", "шлюз", "маршрут", "route", "default"]],
 "какой у меня шлюз по умолчанию":                    [["gateway", "шлюз", "маршрут", "route", "умолчан"]],
 "show open listening ports on this machine":         [["port", "порт", "listen", "слуша", "сокет", "socket"]],
 "какие порты сейчас слушаются":                      [["port", "порт", "listen", "слуша", "сокет", "socket"]],
 "resolve a hostname and show which DNS answered":    [["dns", "днс", "resolve", "резолв", "nslookup", "dig", "домен"]],
 "проверь работу DNS для домена":                     [["dns", "днс", "resolve", "резолв", "nslookup", "dig", "домен"]],
 "list the current firewall rules":                   [["firewall", "брандмауэр", "iptables", "ufw", "фаервол", "файрвол", "nftables", "pf"], ["rule", "правил", "list", "покаж", "вывед", "status", "статус", "текущ", "действ"]],
 "выведи действующие правила брандмауэра":            [["firewall", "брандмауэр", "iptables", "ufw", "фаервол", "файрвол", "nftables"], ["rule", "правил", "list", "покаж", "вывед", "status", "статус", "текущ", "действ"]],
 "block incoming traffic from one IP address":        [["block", "блок", "запрет", "deny", "drop", "закр"], ["ip", "адрес", "address", "port", "порт", "traffic", "трафик", "хост", "host"]],
 "set up NAT so the LAN can reach the internet":      [["nat", "masquerade", "маскарад"]],
 "настроить маскарадинг для выхода в интернет":       [["nat", "masquerade", "маскарад"]],
 "scan a subnet for live hosts":                      [["scan", "скан", "nmap", "обнаруж", "discover"], ["network", "сет", "subnet", "подсет", "host", "узл", "устройств"]],
 "просканировать подсеть на живые узлы":              [["scan", "скан", "nmap", "обнаруж", "discover"], ["network", "сет", "subnet", "подсет", "host", "узл", "устройств"]],
 "capture packets on an interface to a file":         [["packet", "пакет", "tcpdump", "трафик", "capture", "захват", "снифф", "sniff", "дамп"]],
 "is the service running and how do I check":         [["service", "служб", "сервис", "systemctl", "демон", "daemon", "процесс"], ["running", "запущ", "status", "статус", "check", "провер", "работа"]],
 "проверить, запущена ли служба":                     [["service", "служб", "сервис", "systemctl", "демон", "daemon", "процесс"], ["running", "запущ", "status", "статус", "check", "провер", "работа"]],
 "read the last log entries for a failing unit":      [["log", "лог", "journal", "журнал"], ["unit", "служб", "service", "systemd", "journalctl", "ошибк", "fail", "паден", "последн", "last"]],
 "list the containers that are currently running":    [["container", "контейнер", "docker"], ["running", "запущ", "list", "покаж", "вывед", "ps", "работа"]],
 "вывести запущенные контейнеры":                     [["container", "контейнер", "docker"], ["running", "запущ", "list", "покаж", "вывед", "ps", "работа"]],
 "why does my container have no network":             [["container", "контейнер", "docker"], ["network", "сет", "связ", "connect"]],
 "check the nginx configuration for syntax errors":   [["nginx"], ["config", "конфиг", "syntax", "синтакс", "провер", "test", "ошибк", "валид"]],
 "проверить конфигурацию nginx на ошибки":            [["nginx"], ["config", "конфиг", "syntax", "синтакс", "провер", "test", "ошибк", "валид"]],
 "put a reverse proxy in front of an app":            [["proxy", "прокси"], ["reverse", "обратн", "nginx", "apache", "traefik"]],
 "make a dump of a PostgreSQL database":              [["postgres", "постгр", "pgsql", "psql", "pg_"], ["dump", "backup", "бэкап", "бекап", "резерв", "дамп", "копи"]],
 "сделать резервную копию базы PostgreSQL":           [["postgres", "постгр", "pgsql", "psql", "pg_"], ["dump", "backup", "бэкап", "бекап", "резерв", "дамп", "копи"]],
 "bring up a WireGuard tunnel and verify it":         [["wireguard", "wg"]],
 "поднять туннель WireGuard и проверить":             [["wireguard", "wg"]],
 "when does the TLS certificate on this site expire": [["cert", "сертификат", "ssl", "tls"], ["expire", "истек", "срок", "valid", "date", "дат", "годн"]],
 "когда истекает сертификат сайта":                   [["cert", "сертификат", "ssl", "tls"], ["expire", "истек", "срок", "valid", "date", "дат", "годн"]],
 "protect SSH from brute force attempts":             [["ssh"], ["brute", "перебор", "fail2ban", "защит", "protect", "harden", "hardening", "атак", "attack", "ban"]],
 "защитить SSH от перебора паролей":                  [["ssh"], ["brute", "перебор", "fail2ban", "защит", "protect", "harden", "hardening", "атак", "attack", "ban"]],
 "poll a device over SNMP":                           [["snmp"]],
 "опросить устройство по SNMP":                       [["snmp"]],
 "deploy a monitoring server":                        [["monitor", "монитор", "zabbix", "prometheus", "grafana", "наблюден"], ["install", "установ", "deploy", "разверн", "настрой", "setup", "postav", "поднят"]],
 "join this machine to an Active Directory domain":   [["domain", "домен", "active directory", "samba", "realm", "ldap", "ad"], ["join", "ввод", "вступ", "присоедин", "provision", "завед", "подключ"]],
 "check SIP peers on the PBX":                        [["sip", "asterisk", "атс", "pbx", "freepbx"], ["peer", "пир", "транк", "trunk", "статус", "status", "check", "провер", "регистр"]],
 "show OSPF neighbours on the router":                [["ospf"], ["neighbor", "neighbour", "сосед"]],
 "посмотреть соседей OSPF на маршрутизаторе":         [["ospf"], ["neighbor", "neighbour", "сосед"]],
 "run a security audit of this host":                 [["audit", "аудит", "lynis"], ["security", "безопас", "host", "систем", "хост", "сервер"]],
}


def load_facts():
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, "datasets", "*.jsonl"))):
        for ln, line in enumerate(open(f, encoding="utf-8", errors="ignore"), 1):
            try:
                d = json.loads(line)
            except Exception:
                continue
            q = d.get("question") or d.get("input") or d.get("query")
            ex = d.get("exec")
            if isinstance(ex, dict):
                ex = ex.get("cmd")
            if isinstance(q, str) and q.strip():
                out.append({"file": os.path.basename(f), "line": ln, "q": q.strip(),
                            "exec": (ex or "").strip() if isinstance(ex, str) else ""})
    return out


def q_matches(question, groups):
    ql = question.lower()
    return all(any(w in ql for w in group) for group in groups)


def main():
    facts = load_facts()
    spec = importlib.util.spec_from_file_location("bh", os.path.join(HERE, "benchmark_honest.py"))
    bh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bh)

    bench = json.load(open(os.environ.get("BENCH", "/tmp/bench3.json"), encoding="utf-8"))
    got = {r["query"]: r for r in bench["results"]}

    print(f"фактов в датасетах: {len(facts)}\n")
    print(f"{'тест':<52} {'учат':>5} {'вопрос+команда':>15}  модель")
    print("-" * 92)

    teachable, taught_and_right, untaught_and_right = [], 0, 0
    rows = []
    for q, accept, strict in bh.TESTS:
        rule = Q_RULES.get(q)
        if rule is None:
            print(f"  НЕТ ПРАВИЛА для: {q}")
            continue
        # facts whose question is about this task
        on_topic = [f for f in facts if q_matches(f["q"], rule)]
        # of those, the ones whose command would actually satisfy it
        teaching = [f for f in on_topic
                    if f["exec"] and any(s.lower() in f["exec"].lower() for s in strict)]
        ok = bool(got.get(q, {}).get("ok_strict"))
        rows.append((q, len(on_topic), len(teaching), ok, teaching[:2]))
        if teaching:
            teachable.append(q)
            taught_and_right += int(ok)
        else:
            untaught_and_right += int(ok)
        mark = "верно" if ok else "промах"
        print(f"{q[:52]:<52} {len(on_topic):>5} {len(teaching):>15}  {mark}")

    n = len(rows)
    nt = len(teachable)
    print("-" * 92)
    print(f"\nтестов всего                                  : {n}")
    print(f"данные МОГУТ научить (есть факт: та же задача + верная команда) : {nt}")
    print(f"данные НЕ МОГУТ научить (такого факта нет)                      : {n - nt}")
    print()
    print(f"модель верна среди обучаемых   : {taught_and_right}/{nt} = {100*taught_and_right/max(1,nt):.0f}%")
    print(f"модель верна среди необучаемых : {untaught_and_right}/{n-nt}")
    print(f"общий результат                : {taught_and_right + untaught_and_right}/{n} "
          f"= {100*(taught_and_right+untaught_and_right)/n:.0f}%")
    print()
    print("Потолок, который ставят данные: %d/%d = %.0f%%." % (nt, n, 100*nt/n))
    print("Всё, что ниже потолка, — вина маршрутизации; разрыв до 100%% — вина разметки.")

    print("\n--- тесты, которым в данных НЕ УЧАТ (есть тема, нет верной команды) ---")
    for q, n_topic, n_teach, ok, _ in rows:
        if not n_teach:
            print(f"  • {q}")
            print(f"      фактов по теме в датасетах: {n_topic}, из них с верной командой: 0"
                  f"   | модель: {'верно (угадала)' if ok else 'промах'}")


if __name__ == "__main__":
    main()
