"""
What is actually in the training data, and is it good enough to answer the
benchmark at all?

Two questions the benchmark could not answer on its own:

  1. Corpus health — how many facts carry a real command, how many carry a
     placeholder (an `echo` that prints advice and runs nothing), how many
     questions are duplicated, how many commands are pasted across unrelated
     questions.

  2. Per-test coverage — for each benchmark query, is there a training fact
     that genuinely teaches it? Not "does this token appear somewhere in
     10,653 facts", which is what the benchmark checked, but: does the
     nearest-matching question carry a command that would satisfy the task?

Run: python3 audit_datasets.py
"""
import os, re, json, glob
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

STOP = set("""a an the how do i to for on in of and or is are my me you your what
which when where with without from at by it its this that if then else can could
should would make show list find get set up as not no using use run""".split())


def tok(s):
    return {w for w in re.findall(r"[a-zа-яё0-9_.\-]+", (s or "").lower()) if w not in STOP and len(w) > 1}


def load():
    facts = []
    for f in sorted(glob.glob(os.path.join(HERE, "datasets", "*.jsonl"))):
        for ln, line in enumerate(open(f, encoding="utf-8", errors="ignore"), 1):
            try:
                d = json.loads(line)
            except Exception:
                continue
            q = d.get("question") or d.get("input") or d.get("query")
            a = d.get("answer") or d.get("response")
            ex = d.get("exec")
            if isinstance(ex, dict):
                ex = ex.get("cmd")
            if isinstance(q, str) and q.strip():
                facts.append({"file": os.path.basename(f), "line": ln, "q": q.strip(),
                              "a": (a or "").strip(), "exec": (ex or "").strip()})
    return facts


def is_placeholder(cmd):
    """A command that prints advice instead of doing anything."""
    if not cmd:
        return True
    c = cmd.strip()
    # strip the common `which X >/dev/null && ... || echo 'install X'` guard
    body = re.sub(r"2>\s*/dev/null|>\s*/dev/null", "", c)
    # everything the line does is echo
    parts = re.split(r"&&|\|\||;", body)
    real = [p.strip() for p in parts if p.strip() and not p.strip().startswith(("echo", "printf"))]
    return not real


def main():
    facts = load()
    print(f"фактов всего: {len(facts)}   файлов: {len({f['file'] for f in facts})}\n")

    # ---------- 1. corpus health ----------
    no_exec = [f for f in facts if not f["exec"]]
    ph = [f for f in facts if f["exec"] and is_placeholder(f["exec"])]
    real = [f for f in facts if f["exec"] and not is_placeholder(f["exec"])]

    qs = Counter(f["q"].lower() for f in facts)
    dup_q = {q: n for q, n in qs.items() if n > 1}

    cmds = Counter(f["exec"] for f in facts if f["exec"])
    reused = [(c, n) for c, n in cmds.most_common(12) if n > 1]

    # answer text reused across different questions
    answers = Counter(f["a"].lower() for f in facts if f["a"])
    dup_a = sum(n - 1 for a, n in answers.items() if n > 1 and len(a) > 20)

    print("=== ЗДОРОВЬЕ КОРПУСА ===")
    print(f"  без exec-команды вовсе : {len(no_exec):>6}  ({100*len(no_exec)/len(facts):.0f}%)")
    print(f"  exec — только echo     : {len(ph):>6}  ({100*len(ph)/len(facts):.0f}%)  «команда», которая ничего не делает")
    print(f"  exec — настоящая       : {len(real):>6}  ({100*len(real)/len(facts):.0f}%)")
    print(f"  вопросы-дубликаты      : {len(dup_q):>6} разных текстов повторяются")
    print(f"  повторы текста ответа  : {dup_a:>6} лишних копий")

    print("\n  одна и та же команда на многих вопросах:")
    for c, n in reused[:8]:
        print(f"    {n:>4}×  {c[:96]}")

    # how often does the command have nothing to do with the question
    mismatch = []
    for f in real:
        qt, ct = tok(f["q"]), tok(f["exec"])
        if qt and not (qt & ct):
            mismatch.append(f)
    print(f"\n  команда не делит НИ ОДНОГО слова с вопросом: {len(mismatch)} "
          f"({100*len(mismatch)/max(1,len(real)):.0f}% от настоящих)")
    for f in mismatch[:6]:
        print(f"    {f['file']}:{f['line']}  «{f['q'][:52]}»")
        print(f"        → {f['exec'][:86]}")

    # ---------- 2. per-benchmark-query coverage ----------
    import importlib.util
    spec = importlib.util.spec_from_file_location("bh", os.path.join(HERE, "benchmark_honest.py"))
    bh = importlib.util.module_from_spec(spec)
    # TESTS is a module-level constant; executing main() is avoided by the __main__ guard
    spec.loader.exec_module(bh)

    print("\n\n=== ЕСТЬ ЛИ В ДАННЫХ ОТВЕТ НА КАЖДЫЙ ТЕСТ ===")
    print("(ищем факт, чей вопрос ближе всего по словам И чья команда проходит строгий шаблон)\n")

    taught, near_only, absent = [], [], []
    for q, accept, strict in bh.TESTS:
        qt = tok(q)
        # any fact whose command satisfies the strict pattern
        satisfying = [f for f in facts
                      if f["exec"] and any(s.lower() in f["exec"].lower() for s in strict)]
        if not satisfying:
            absent.append((q, None, 0.0))
            continue
        # of those, the one whose question is closest to ours
        best = max(satisfying, key=lambda f: len(qt & tok(f["q"])) / max(1, len(qt | tok(f["q"]))))
        sim = len(qt & tok(best["q"])) / max(1, len(qt | tok(best["q"])))
        (taught if sim >= 0.20 else near_only).append((q, best, sim))

    print(f"  ЕСТЬ прямой обучающий факт (похожий вопрос + верная команда): {len(taught)}/{len(bh.TESTS)}")
    print(f"  команда в корпусе есть, но привязана к ДРУГОЙ теме:          {len(near_only)}/{len(bh.TESTS)}")
    print(f"  верной команды в корпусе НЕТ вообще:                         {len(absent)}/{len(bh.TESTS)}")

    if absent:
        print("\n  --- нет в данных совсем (модель не могла ответить): ---")
        for q, _, _ in absent:
            print(f"    • {q}")

    if near_only:
        print("\n  --- команда есть, но у чужого вопроса (ближайший факт): ---")
        for q, f, sim in sorted(near_only, key=lambda x: x[2]):
            print(f"    • {q}")
            print(f"        ближайший обучающий вопрос ({sim:.2f}): «{f['q'][:60]}»")
            print(f"        его команда: {f['exec'][:80]}")


if __name__ == "__main__":
    main()
