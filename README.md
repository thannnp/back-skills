# back-skills

Agent skills for horoacademy, installable via [`npx skills`](https://github.com/vercel-labs/skills).

## Install

```bash
npx skills add thannnp/back-skills
```

This scans the repo for all skills and shows an interactive menu to pick which ones to install.

List available skills without installing:

```bash
npx skills add thannnp/back-skills --list
```

Install a specific skill only:

```bash
npx skills add thannnp/back-skills --skill horo-db
```

## Available skills

| Skill | Purpose |
|---|---|
| `horo-db` | Assistant for answering questions about the structure and relationships of the two horoacademy databases (`horoacademy-backoffice` and `horoacademy-wpe-service`) — which tables exist, what columns they have, how they relate, cross-DB references, and polymorphic relations. |
| `horo-summon-money` | Local-only testing helper that forces the payment status of a payment link or payment transaction (`successful` / `pending` / `failed` / `expired` / `reversed`). Accepts either a payment-link id or a transaction id; supports a direct (tinker) mode and a real Omise webhook mode. Only touches payment state — does not notify wpe-service. |

## Repo structure

```
back-skills/
└── skills/
    ├── horo-db/
    │   ├── SKILL.md                              # instructions (English; replies to the user in Thai)
    │   ├── HORO_BACKOFFICE_DATABASE_DIAGRAM.md   # Mermaid ER diagram — backoffice
    │   └── WPE_SERVICE_DATABASE_DIAGRAM.md       # Mermaid ER diagram — wpe-service
    └── horo-summon-money/
        └── SKILL.md                              # instructions (English; asks the user in Thai)
```

To add a new skill, create `skills/<name>/SKILL.md` and `npx skills` will discover it automatically.
