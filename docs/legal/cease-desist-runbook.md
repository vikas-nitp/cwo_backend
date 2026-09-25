# Cease & Desist Runbook

This document describes how to respond if Harvest receives a cease-and-desist letter,
takedown request, or legal notice from a travel platform, bank, or rights-holder.

---

## 1. Receive and triage (within 24 hours)

- Forward the notice to `support@cardsage.in` and the project owner immediately.
- Record the date received, sender name, and the specific demand.
- Do **not** respond, acknowledge, or dismiss the notice until Step 2 is complete.

---

## 2. Stop the relevant scraping immediately

Use the kill switches in `cardsage/constants/phases.py` to halt the specific source
without touching anything else:

```python
# Disable a single source web scraper
MMT_WEB_ENABLED       = False   # MakeMyTrip
CLEARTRIP_WEB_ENABLED = False   # Cleartrip
IXIGO_WEB_ENABLED     = False   # Ixigo (once added)
```

- Set the flag to `False`, commit with message `"kill-switch: disable <source> per legal notice"`.
- Verify the next scheduled CI run does not hit the source.
- Do **not** delete any existing output files — they may be required as evidence.

---

## 3. Preserve evidence

Before making any other changes:

- Archive the current `cardsage/output/` directory (zip or `git stash`).
- Save a copy of the C&D letter (PDF or email export) to `cardsage/docs/legal/` (create if absent).
- Note the last run ID and timestamp that scraped the platform in question.

---

## 4. Assess the demand

Common demands and responses:

| Demand | Action |
|--------|--------|
| Stop scraping their website | Kill switch already done (Step 2); confirm in writing |
| Remove specific offer data | Remove the offer IDs from `offers.json` / `output/` and redeploy |
| Remove all data from their platform | Purge all outputs with that `platform_id`; remove adapter |
| Cease using their brand name / logo | Remove brand assets; replace with generic description |

---

## 5. Draft a response (within 72 hours)

Standard response points:
- Harvest scrapes only publicly available offer pages (no login required, no credentials).
- We do not resell, redistribute, or commercially exploit the data.
- We provide attribution links back to the original source on every offer card.
- We comply with `robots.txt` directives and do not use CAPTCHA-bypass or anti-bot evasion.
- We are happy to discuss a formal data-sharing agreement if the platform prefers.

Send the response from `support@cardsage.in` and keep a copy in `cardsage/docs/legal/`.

---

## 6. Platform removal (if demanded)

```bash
# In cardsage/output/: remove all runs for the platform
rm -rf cardsage/output/*/cleartrip/
rm -rf cardsage/output/latest/cleartrip_*.json
rm -rf cardsage/output/exports/cleartrip*.csv

# In frontend frontend: filter the offer from generated/offers.json
# (mark is_active: false or remove the entries with platform_id matching)
```

After removal: redeploy the frontend so the stale data is no longer served.

---

## 7. Escalation

If the demand is unclear, involves financial claims, or threatens litigation:

1. Do not respond further without legal advice.
2. Contact a technology / IP lawyer in India.
3. Document all communications.
4. The Data Protection Board of India handles DPDP-related complaints; for copyright,
   the relevant body is Delhi High Court (IP Division) or Bombay High Court.

---

## Notes

- This runbook does **not** constitute legal advice.
- Keep this document updated when new sources are added (Ixigo, Yatra, etc.).
- Review annually or after any significant product change.

Last updated: 2026-09-19
