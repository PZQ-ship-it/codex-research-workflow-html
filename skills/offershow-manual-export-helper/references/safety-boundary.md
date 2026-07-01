# Safety Boundary

OfferShow can be useful as a logged-in salary / offer signal source, but the safe automation boundary is narrow.

Allowed:

- Open a visible browser with a local user-controlled Chrome profile.
- Let the user manually log in, solve CAPTCHA/MFA, and apply filters.
- Save redacted JSON summaries of currently visible page candidates.
- Convert candidates to a review CSV for human selection and summarization.
- Append selected, anonymized rows to `community-salary-sample-ledger`.
- Record source metadata, uncertainty, and confidence.

Not allowed:

- Printing or saving cookies, tokens, `localStorage`, auth headers, browser profile files, or private API responses.
- Asking the user to paste credentials or cookies into chat or repo files.
- CAPTCHA bypass, paywall bypass, anti-bot evasion, or hidden API scraping.
- Bulk pagination, unattended scraping, or automatic salary database replication.
- Saving raw private screenshots, usernames, contacts, phone numbers, emails, private messages, or full private post text.
- Treating a single OfferShow row as verified compensation without cross-source validation.

If a future probe finds public JS endpoint names, use them only as UI/schema hints unless a safe public API is documented or user explicitly approves a narrow authenticated export with privacy review.
