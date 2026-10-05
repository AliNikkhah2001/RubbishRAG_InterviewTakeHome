"""Encrypted store for the hidden evaluation set.

DO NOT OPEN during the interview (honor system). In the candidate branch this
module ships as compiled bytecode only; hidden_eval.json never leaves the
interviewers' machine — only hidden_eval.enc (unreadable without this key).

- build side: hidden_eval_builder.build() writes hidden_eval.json (gitignored)
  AND hidden_eval.enc (via save_hidden).
- runtime: load_hidden() decrypts hidden_eval.enc in memory. Gold answers are
  never printed, only aggregates.
"""
import json
import os

KEY = b"bRIW77yr6Yu7Hc3KeF1A5uN4Hmr_mnRK91m2AV3_wQs="
ENC_NAME = "hidden_eval.enc"


def _enc_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), ENC_NAME)


def save_hidden(items) -> str:
    from cryptography.fernet import Fernet, InvalidToken  # noqa
    data = json.dumps(items, ensure_ascii=False).encode("utf-8")
    token = Fernet(KEY).encrypt(data)
    with open(_enc_path(), "wb") as f:
        f.write(token)
    return _enc_path()


def load_hidden():
    from cryptography.fernet import Fernet
    with open(_enc_path(), "rb") as f:
        token = f.read()
    data = Fernet(KEY).decrypt(token)
    return json.loads(data.decode("utf-8"))
