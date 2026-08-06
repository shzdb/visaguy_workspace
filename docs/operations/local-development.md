# Local Development

**Safety disclaimer:** every command below is documented from checked-in scripts, `Procfile`, `package.json`, and accepted reconnaissance reports. No commands were executed as part of this audit. Run each against a staging bench or with a verified backup first.

## Prerequisite: clone the frontends

As of 2026-08-06 **none of the frontend repositories is cloned on the active workstation**. Clone them before any frontend work:

```bash
git clone git@tridz:tvgglobal/visa_eligibility_checker.git
```

```bash
git clone git@tridz:tridz-dev/visaguy_business_client.git
```

```bash
git clone git@tridz:tvgglobal/visaguy-website-client.git
```

`visaguy-website-client` is read-only design reference for FEAT-001 TASK-008 — never commit tracker changes into it.

The fourth frontend, `visa_tracker`, does not exist yet; TASK-008 creates it locally with Vite and requires no remote.

## `visa_eligibility_checker`

```bash
# Frontend
cd /path/to/visa_eligibility_checker
bun install
cp .env.example .env   # set VITE_PUBLIC_ZONE, VITE_PUBLIC_API_URL,
                       # VITE_PUBLIC_FRAPPE_BASE_URL, VITE_PUBLIC_WHATSAPP_NUMBER
bun run lint
bun run build          # tsc -b && vite build → dist/
bun run preview        # serve dist/ locally
bun dev                # http://localhost:5173

# Companion backend
cd server
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set OPENAI_API_KEY
uvicorn main:app --reload --port 8000
```

## `visaguy_business_client`

```bash
cd /path/to/visaguy_business_client
pnpm install          # or bun install; pick one and align lockfile

cp env.example .env.local
# NEXT_PUBLIC_API_BASE_URL
# NEXT_PUBLIC_CLIENT_ID, NEXT_PUBLIC_CLIENT_SECRET
# NEXT_PUBLIC_ZONE, NEXT_PUBLIC_CURRENCY
# NEXT_PUBLIC_CONTACT_URL
# NEXT_PUBLIC_INVOICE_PRINT_FORMAT, NEXT_PUBLIC_INVOICE_LETTERHEAD

pnpm dev              # http://localhost:3000
pnpm lint
pnpm build
pnpm start
```

Optional Docker:

```bash
docker build -f Dockerfile .
docker compose -f compose.yaml up -d --build
```

## `visaguy-website-client`

```bash
cd /path/to/visaguy-website-client
bun install
cp env.example .env.local   # set NEXT_PUBLIC_FRAPPE_BASE_URL
bun dev                     # Turbopack, http://localhost:3000
bun run lint
bun run build
bun run start
```

## Notes

- No test scripts exist in any of the three repositories.
- The business client has both `bun.lock` and `pnpm-lock.yaml`; the `Dockerfile` uses `pnpm`.
- Verify `next.config.ts` image hostnames match the chosen Frappe domain for the consumer site.
- Verify the hard-coded fallback URL at `app/orders/[id]/page.tsx:32` does not override the intended backend for the business client.
