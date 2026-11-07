# Breach Notification Response Playbook
**DPDP Act 2023 §8(6) + DPDP Rules 2025 Rule 7**
Version 1.0 — Sep 20 2026

---

## Overview

A personal data breach requires two parallel actions:

1. **Immediate user notification** — as soon as the breach is discovered
2. **DPB report** — comprehensive written report to the Data Protection Board of India
   within **72 hours** of discovery

The 72-hour clock starts from the moment any team member has reason to believe a breach
has occurred — not from when it is confirmed.

---

## Step 1 — Classify the incident

A notifiable breach is any accidental or unlawful destruction, loss, alteration,
unauthorised disclosure of, or access to personal data we process. This includes:

- Unauthorised access to the database containing hashed mobile numbers
- Exposure of OTP logs or session identifiers
- Data exfiltration from the FastAPI backend
- Accidental public exposure of backup files containing user data
- Third-party SMS provider breach affecting our users' numbers

**Not notifiable (internal only, no DPB report required):**
- Failed login attempt with no data accessed
- Scraping of publicly visible offer data (no user personal data involved)
- Server downtime with no data exposure

If unsure: **treat it as notifiable** and escalate immediately.

---

## Step 2 — Immediate containment (Hour 0–2)

- [ ] Isolate the affected system or revoke the compromised credential
- [ ] Preserve logs — do **not** delete or overwrite any system logs
- [ ] Identify: what data, how many users, how long was it exposed
- [ ] Document the exact discovery timestamp (this starts the 72-hour clock)
- [ ] Notify the Grievance Officer: grievance@cardsage.in

---

## Step 3 — User notification (as soon as possible, before DPB report)

Send the following email / SMS to affected users. Replace bracketed fields.

### User notification template

**Subject:** Important notice about your CardSage account security

> Dear CardSage user,
>
> We are writing to inform you that we recently discovered a security incident that may
> have affected your account.
>
> **What happened:** [One sentence description, e.g. "An unauthorised party briefly
> accessed our user database on [DATE]."]
>
> **What data was involved:** [e.g. "Your mobile number stored in hashed form."]
>
> **What we have done:** We have [contained the incident / revoked the affected
> credentials / patched the vulnerability] and are conducting a full investigation.
>
> **What you should do:** [e.g. "No action is required from your side. Your OTP sign-in
> flow was not affected." OR "We recommend you be alert for any unusual SMS activity."]
>
> **Your rights:** Under India's DPDP Act 2023, you have the right to seek clarification
> or lodge a complaint. Contact us at grievance@cardsage.in or escalate to the Data
> Protection Board of India at dpboard.gov.in.
>
> We sincerely apologise for this incident. The security of your data is our first
> priority.
>
> — The CardSage Team

---

## Step 4 — DPB report (within 72 hours of discovery)

Submit via the Data Protection Board portal at **dpboard.gov.in**.

Use the following template. All fields are mandatory.

### DPB report template

```
PERSONAL DATA BREACH NOTIFICATION
Submitted under DPDP Act 2023 §8(6) and DPDP Rules 2025 Rule 7

DATA FIDUCIARY DETAILS
  Organisation:     CardSage (CardwiseOffer)
  Website:          https://cardsage.in
  Grievance Officer: grievance@cardsage.in
  Contact person:   [Name, phone number]

INCIDENT DETAILS
  Discovery date/time:      [DD MMM YYYY HH:MM IST]
  Breach start (estimated): [DD MMM YYYY or "unknown"]
  Breach end:               [DD MMM YYYY HH:MM IST or "ongoing"]
  Report submission time:   [DD MMM YYYY HH:MM IST]
  Time since discovery:     [X hours Y minutes]

NATURE OF THE BREACH
  Type: [ ] Unauthorised access  [ ] Accidental disclosure
        [ ] Data loss/destruction  [ ] Alteration
  Description: [2–3 sentences describing what happened]

DATA INVOLVED
  Categories of personal data: [e.g. Mobile numbers (hashed)]
  Approximate number of data principals affected: [number or "under investigation"]
  Sensitivity: [ ] Standard  [ ] Sensitive (financial / health / children's data)

LIKELY CONSEQUENCES
  [Describe the likely consequences for data principals, e.g.
  "Hashed mobile numbers were exposed. Risk of targeted phishing if combined with
  other data sources. No financial data was involved."]

MEASURES TAKEN
  Containment: [What was done to stop the breach]
  Remediation: [What was done to fix the vulnerability]
  User notification: [When and how users were notified]
  Ongoing: [Any ongoing investigation or monitoring]

DECLARATION
  I confirm this report is accurate to the best of my knowledge as of the
  submission time above.
  Signed: [Name, Role]
```

---

## Step 5 — Post-incident (72 hours to 30 days)

- [ ] Complete full forensic investigation
- [ ] Identify root cause and document it
- [ ] Implement permanent fix and verify with VAPT team
- [ ] Update the DPB with a final incident report if new material facts emerge
- [ ] Schedule a post-mortem and update this playbook if any step was unclear
- [ ] Review whether affected users need additional follow-up

---

## Escalation contacts

| Role | Contact |
|------|---------|
| Grievance Officer | grievance@cardsage.in |
| DPB portal | dpboard.gov.in |
| CERT-In (if applicable) | incident@cert-in.org.in |

---

## Penalties reference

| Violation | Max penalty |
|-----------|-------------|
| Breach without adequate safeguards (§8(5) + Rule 6) | ₹250 Crore |
| Failure to notify DPB within 72 hours (§8(6) + Rule 7) | ₹200 Crore |
| Failure to notify affected users promptly | ₹200 Crore (same provision) |
