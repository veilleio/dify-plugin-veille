# Veille for Dify

[Veille](https://www.veille.io) checks whether an email, domain, IP address, phone number, VAT number or IBAN can be trusted. This plugin gives Dify agents, workflows and chatflows those checks, with the evidence behind each verdict: DNS records, disposable providers, VPN and Tor detection, carrier and line type, the company behind a VAT number, the bank behind an IBAN, and a risk score.

**Author:** veilleio · **Source:** https://github.com/veilleio/dify-plugin-veille · **Contact:** contact@veille.io

## Tools

| Tool | What it does |
| --- | --- |
| **Check Email** | Syntax, MX, SPF and DMARC records, disposable provider, role account, alias, typo suggestion and a 0-100 risk score. 3 credits. |
| **Qualify Email** | Everything Check Email returns, plus an SMTP inbox check, catch-all detection and a verdict: valid, invalid, risky, disposable or unknown. 5 credits. |
| **Check Domain** | DNS and mail setup, mail providers, WHOIS registrar and dates, domain age, disposable or relay domain. 2 credits. |
| **Check IP** | Location, network owner, VPN, proxy, Tor, data center, crawler and abuser flags, and a threat score. 2 credits. |
| **Check Phone** | Validity, formats, country, carrier, line type, virtual or disposable number, spam reports and a risk score. 1 credit. |
| **Check VAT Number** | Validity in the EU VIES database, and the registered company name and address. 1 credit. |
| **Check IBAN** | Validity, country, bank name, BIC, bank and branch codes, SEPA zone. 1 credit. |
| **Exchange Rates** | Today's European Central Bank rates for a base currency, optionally only for some currencies. 1 credit. |

Each tool returns a text message with the API's JSON, which agents read, and a JSON message for workflow variables, for example to branch on `risk_score`, `disposable` or `valid`. Errors such as an invalid key, missing credits or a rate limit come back as a text message, and the API key never appears in it.

Use **Check Email** on sign-up forms and to clean a list; use **Qualify Email** when you need to know that the inbox really exists before an important send.

## Setup

1. Create an account and copy your API key at [app.veille.io](https://app.veille.io).
2. In Dify, install the **Veille** plugin from the Marketplace.
3. Open **Tools → Veille → Authorize** and paste the API key. Dify checks it with a request that costs no credits.
4. Add the tools to an agent, a workflow or a chatflow.

## Requirements

- Dify 1.0.0 or later.
- Outbound HTTPS access to `api.veille.io`.
- A Veille API key. Usage counts against your Veille credits; see [www.veille.io/pricing](https://www.veille.io/pricing).

## Privacy

See [PRIVACY.md](PRIVACY.md).

## Development

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt pytest pyyaml
.venv/bin/pytest
```

The `Package` workflow builds the `.difypkg` with Dify's plugin CLI and attaches it to a GitHub release when the version in `manifest.yaml` changes.
