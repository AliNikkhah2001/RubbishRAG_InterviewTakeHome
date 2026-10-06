#!/usr/bin/env python3
"""Build the `candidate` branch: minimal files, sealed eval, fresh key.

What it does (run from main, clean tree required):
  1. Exports main HEAD into a temp dir (allow-list only — tools/, private
     stuff and dev traces never leave).
  2. Generates a FRESH Fernet key, patches it into server/_vault.py,
     rebuilds hidden_eval.json + hidden_eval.enc, then DELETES the plaintext.
  3. Compiles sealed server modules to sourceless .pyc (py3.11) and deletes
     their .py sources. Candidates can execute but not read them.
  4. Writes candidate .gitignore + server/.buildinfo.json, resets the README
     report section to the empty placeholder.
  5. Smoke-tests: imports every sealed .pyc, decrypts .enc, runs one retrieve.
  6. Commits the tree on the `candidate` branch (--force replaces it).

Usage:
    python3 tools/build_candidate.py [--force] [--branch candidate]

Interviewers: re-run per hiring round (fresh key + `seed` bump in
hidden_eval_builder.py), then re-validate from the private folder and push
both branches. Candidates fork the repo and work on `candidate`.
"""
import argparse
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ALLOW = [
    "README.md",
    "requirements.txt",
    ".gitignore",  # replaced by candidate version below
    "corpus/test.csv",
    "rubbish.py",
    "rubbish_rag/__init__.py",
    "rubbish_rag/art.py",
    "rubbish_rag/pipeline.py",
    "rubbish_rag/normalize_fa.py",
    "rubbish_rag/slots.py",
    "rubbish_rag/identity.py",
    "server/app.py",
    "server/visible_bench.json",
    "docs/ARCHITECTURE.md",
    "docs/API.md",
    "docs/PROOF_template.md",
    "docs/index.html",
]

SEALED = [
    "server/_hidden_retriever.py",
    "server/poison_docs.py",
    "server/_secrets.py",
    "server/build_index.py",
    "server/evaluator.py",
    "server/hidden_eval_builder.py",
    "server/_vault.py",
    "server/fa_norm.py",
]

CANDIDATE_GITIGNORE = """\
__pycache__/
*.pyc
.venv/
traces/trace.jsonl
traces/quota.json
traces/metrics.json
traces/submissions.jsonl
submissions/*.zip
server/hidden_eval.json
server/server_index.json
.candidate.json
.DS_Store
"""

REPORT_PLACEHOLDER = """<!-- RUBBISH-REPORT:START -->
## 📊 My RubbishRAG Report

_(Empty — run `python3 rubbish.py bastesh` to stamp your card, metrics and diagrams here.)_
<!-- RUBBISH-REPORT:END -->"""


def sh(*cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd or REPO, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd)}\n{r.stderr}")
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="replace existing candidate branch")
    ap.add_argument("--branch", default="candidate")
    args = ap.parse_args()

    if sh("git", "status", "--porcelain"):
        sys.exit("error: working tree not clean — commit first.")
    if sh("git", "rev-parse", "--abbrev-ref", "HEAD") != "main":
        sys.exit("error: run from the main branch.")
    existing = sh("git", "branch", "--list", args.branch)
    if existing and not args.force:
        sys.exit(f"error: branch {args.branch} exists — pass --force to replace.")
    if f"{sys.version_info.major}.{sys.version_info.minor}" != "3.11":
        sys.exit(f"error: sealed .pyc must be built with Python 3.11 "
                 f"(you have {sys.version_info.major}.{sys.version_info.minor}).")

    tmp = tempfile.mkdtemp(prefix="rubbish_candidate_")
    try:
        # 1) allow-list export from main HEAD
        for rel in ALLOW:
            src = os.path.join(REPO, rel)
            if not os.path.exists(src):
                sys.exit(f"error: missing {rel} on main")
            dst = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        for rel in SEALED:
            src = os.path.join(REPO, rel)
            dst = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        for pkg in ("rubbish_rag", "server"):
            open(os.path.join(tmp, pkg, "__init__.py"), "a").close()

        # 2) fresh vault key; build hidden eval + index in a subprocess
        #    (modules resolve paths from __file__, so the build must run
        #    from the REPO tree; tmp gets the patched copy + artifacts)
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        key_line = f'KEY = b"{key.decode()}"'
        vmain = os.path.join(REPO, "server", "_vault.py")
        orig_vault = open(vmain, encoding="utf-8").read()
        patched_vault = re.sub(r'KEY = b".*?"', key_line, orig_vault)
        assert patched_vault != orig_vault, "vault KEY placeholder not found"
        vtmp = os.path.join(tmp, "server", "_vault.py")
        vtmp_text = open(vtmp, encoding="utf-8").read()
        assert re.sub(r'KEY = b".*?"', key_line, vtmp_text) != vtmp_text
        open(vtmp, "w", encoding="utf-8").write(
            re.sub(r'KEY = b".*?"', key_line, vtmp_text))
        open(vmain, "w", encoding="utf-8").write(patched_vault)
        try:
            build_cmd = ("from server.build_index import build as bi; bi(); "
                         "from server.hidden_eval_builder import build as be; be()")
            r = subprocess.run([sys.executable, "-c", build_cmd], cwd=REPO,
                               capture_output=True, text=True)
            if r.returncode != 0:
                sys.exit(f"eval build FAILED:\n{r.stderr}")
            print(r.stdout.strip())
        finally:
            open(vmain, "w", encoding="utf-8").write(orig_vault)
        shutil.copy2(os.path.join(REPO, "server", "hidden_eval.enc"),
                     os.path.join(tmp, "server", "hidden_eval.enc"))
        hid = json.load(open(os.path.join(REPO, "server", "hidden_eval.json"),
                             encoding="utf-8"))
        print(f"candidate hidden set: n={len(hid)} "
              f"(visible stays 20 → hidden/visible ≈ {len(hid) / 20:.0f}x)")

        # 3) seal: .pyc + delete sources + delete plaintext eval
        for rel in SEALED:
            src = os.path.join(tmp, rel)
            pyc = os.path.splitext(src)[0] + ".pyc"
            py_compile.compile(src, cfile=pyc, doraise=True)
            os.remove(src)
        for d in ("__pycache__",):
            for root, dirs, _ in os.walk(tmp):
                if d in dirs:
                    shutil.rmtree(os.path.join(root, d))
        # plaintext eval must never reach the candidate tree (build wrote to
        # REPO; tmp only ever received hidden_eval.enc)
        assert not os.path.exists(os.path.join(tmp, "server", "hidden_eval.json"))
        open(os.path.join(tmp, "server", "__init__.py"), "a").close()

        # 4) candidate gitignore + buildinfo + pristine report markers
        open(os.path.join(tmp, ".gitignore"), "w",
             encoding="utf-8").write(CANDIDATE_GITIGNORE)
        pyver = f"{sys.version_info.major}.{sys.version_info.minor}"
        json.dump({"python": pyver, "sealed": True},
                  open(os.path.join(tmp, "server", ".buildinfo.json"), "w"))
        rp = os.path.join(tmp, "README.md")
        rtext = open(rp, encoding="utf-8").read()
        pat = re.compile(r"<!-- RUBBISH-REPORT:START -->.*?"
                         r"<!-- RUBBISH-REPORT:END -->", re.S)
        assert pat.search(rtext), "report markers missing in README"
        open(rp, "w", encoding="utf-8").write(pat.sub(REPORT_PLACEHOLDER, rtext))
        assert ".candidate.json" not in os.listdir(tmp), "identity leaked!"

        # 5) smoke test inside temp tree (fresh interpreter, no .py fallbacks)
        smoke = (
            "import sys; sys.path.insert(0, '.'); "
            "import server._hidden_retriever as hr, "
            "server.evaluator as ev, server.hidden_eval_builder as hb, "
            "server._vault as v; "
            "hid = v.load_hidden(); "
            "assert len(hid) > 100, len(hid); "
            "hits = hr.remote_retrieve('رتبه C1 یعنی چی؟', topk=3, api_key='smoke'); "
            "assert len(hits) == 3 and 'fused' in hits[0]; "
            "print('smoke OK:', len(hid), 'hidden items, retrieve works')"
        )
        r = subprocess.run([sys.executable, "-c", smoke], cwd=tmp,
                           capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"smoke test FAILED:\n{r.stderr}")
        print(r.stdout.strip())
        leak_probe = "بدهی دارم چرا امتیازم بالاست؟".encode("utf-8")
        enc = open(os.path.join(tmp, "server", "hidden_eval.enc"), "rb").read()
        assert leak_probe not in enc, "plaintext leak in .enc!"
        print("enc OK: no plaintext leak")
        # smoke test imports create __pycache__ again — purge before commit
        for root, dirs, _ in os.walk(tmp):
            if "__pycache__" in dirs:
                shutil.rmtree(os.path.join(root, "__pycache__"))

        # purge runtime junk from tmp BEFORE merging into the working tree
        # (shutil.move nests src inside an existing dst dir — traces/traces!)
        for junk in ("traces", "plots", "submissions", ".candidate.json",
                     "__pycache__"):
            jp = os.path.join(tmp, junk)
            if os.path.isdir(jp) and not os.path.islink(jp):
                shutil.rmtree(jp)
            elif os.path.exists(jp):
                os.remove(jp)
        plots_dir = os.path.join(tmp, "plots")
        os.makedirs(plots_dir, exist_ok=True)
        open(os.path.join(plots_dir, ".gitkeep"), "w").close()
        # fail fast on stray committable artifacts in the working tree
        # (candidate .gitignore tracks plots/ — local test PNGs must not ship)
        import glob as _glob
        strays = _glob.glob(os.path.join(REPO, "plots", "*.png"))
        if strays:
            sys.exit("error: local test plots would ship to candidates: "
                     f"{strays}\ndelete them and re-run.")

        # 6) commit onto candidate branch
        sh("git", "checkout", "-B", args.branch)
        sh("git", "rm", "-r", "--cached", "--quiet", ".")
        # clear working tree except .git (+ untracked dev dirs we keep)
        keep = {".git", "traces", "plots", "submissions", ".venv",
                ".candidate.json", ".DS_Store"}
        for entry in os.listdir(REPO):
            if entry in keep:
                continue
            p = os.path.join(REPO, entry)
            if os.path.isdir(p) and not os.path.islink(p):
                shutil.rmtree(p)
            else:
                os.remove(p)
        for entry in os.listdir(tmp):
            shutil.move(os.path.join(tmp, entry), os.path.join(REPO, entry))
        assert not os.path.exists(os.path.join(REPO, "traces", "traces")), \
            "nested traces/ slipped through!"
        sh("git", "add", "-A")
        sh("git", "add", "-f", "server/hidden_eval.enc", "server/*.pyc")
        # sealed bytecode must be tracked (candidate .gitignore skips *.pyc)
        sealed_tracked = sh("git", "ls-files", "server/").splitlines()
        missing = [f"server/{m}.pyc" for m in
                   ("_hidden_retriever", "_vault", "evaluator",
                    "hidden_eval_builder", "build_index", "poison_docs",
                    "_secrets", "fa_norm")
                   if f"server/{m}.pyc" not in sealed_tracked]
        if missing:
            sys.exit(f"error: sealed modules missing from index: {missing}")
        n_hidden = len(hid)
        sh("git", "commit", "-m",
           f"Candidate take-home: sealed eval ({n_hidden} hidden vs 20 visible), "
           f"minimal files, fork-based workflow")
        print(f"branch '{args.branch}' ready — review, then: git checkout main")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        # always return to main (best effort)
        subprocess.run(["git", "checkout", "--quiet", "main"], cwd=REPO)


if __name__ == "__main__":
    main()
