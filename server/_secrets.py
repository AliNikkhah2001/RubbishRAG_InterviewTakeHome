"""Per-candidate secrets (production: one file per API key on server).

Jitter prevents solution sharing: same fault TYPES, slightly different params.
Demo key below is used for local development.
"""
SECRETS_BY_KEY = {
    "demo-key": {"k1": 1.2, "b": 0.9, "rrf_k": 60, "poison_salt": 0},
    # production example:
    # "cand-xxx": {"k1": 1.05, "b": 0.82, "rrf_k": 47, "poison_salt": 3},
}

QUOTA = {"max_retrieve": 1000}
