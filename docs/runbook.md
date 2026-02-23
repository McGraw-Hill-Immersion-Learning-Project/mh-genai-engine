# Runbook

How to run and deploy the Engine, and how secrets are managed. Per ADR-006: secrets live in env (local: `.env` in repo root; demo: platform env). **Never commit `.env` or real keys.** This doc must be complete before 3/23.

---

## Required env vars

*(Fill in when the app exists. Use `.env.example` in repo root as a template; copy to `.env` and set values.)*

| Variable | Purpose | Example / notes |
|----------|---------|-----------------|
| TBD      | TBD     | TBD             |

---

## Where secrets live

- **Local:** `.env` in repo root (gitignored). Create from `.env.example` if present; never commit `.env`.
- **Demo (App Runner):** Same variable names, set in AWS App Runner → Service → Environment. No file upload; configure in console or IaC.

---

## Local run

*(Steps to run the backend locally. Fill in when backend exists.)*

1. TBD (e.g. `cp .env.example .env`, set values)
2. TBD (e.g. `docker compose up` or `uvicorn app.main:app --reload`)
3. TBD (how to verify: health check, curl)

---

## Demo / App Runner deploy

*(Steps to deploy the Engine to App Runner for demo. Fill in when we have a container image and service.)*

1. TBD (build image, push to ECR or other registry)
2. TBD (create or update App Runner service, set env vars)
3. TBD (how to verify: hit service URL, smoke test)

---

## Rotation (changing secrets)

1. Generate or obtain new key/secret.
2. **Local:** Update `.env` in repo root, restart the app.
3. **Demo:** Update env vars in App Runner service config, redeploy or restart the service.
4. Revoke or expire the old key if applicable.
5. *(Optional)* Document rotation date in this section or in a changelog.

---

## Who can change secrets

- **Local:** Each developer manages their own `.env` in repo root (personal/dev keys only; no shared demo keys in personal env).
- **Demo:** TBD (e.g. Tech Lead and sponsor only; document who has access to App Runner env config).

---

*Last updated: TBD. Replace TBDs and keep this doc in sync with the backend and deploy process.*
