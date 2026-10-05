# Data provenance and permission gate

Operational memory, chat history, temporary execution state, and training records are separate. No automated chat-to-training pipeline exists. Personal information requires explicit, traceable opt-in. A general desire for a trained model is not permission to ingest every team member's information.

| Proposed teacher | Permission status | Collection |
|---|---|---|
| OpenAI / requested Astra | Unresolved: exact available product/model and applicable agreement not established | BLOCKED |
| Anthropic Claude | Current agreement and training-use rights not reviewed | BLOCKED |
| Google Gemini | Current agreement and training-use rights not reviewed | BLOCKED |
| xAI Grok | Current agreement and training-use rights not reviewed | BLOCKED |
| Open-model teachers | Model-specific license and dataset rights must be reviewed | BLOCKED until established |

This is not a legal conclusion that any provider permits or prohibits this use. Before collection, retain the official applicable terms/contract URL or document, version/date, account/product scope, relevant restriction/permission, review identity/date and conclusion. Uncertainty blocks collection. API availability, payment, model agreement and silence do not establish training permission. No teacher calls were made.

Prefer properly licensed datasets and human-authored examples when permission is clear. Model-generated examples are not automatically human-authored just because they were generated for this project. The old kit's synthetic examples are quarantined from the verified pilot pending review.

`pilot.py` enforces declared permission/verification/consent, exact normalized deduplication, family split separation, and simple email/credential red flags. It cannot establish legal validity, catch all private information, judge factual correctness, verify source pages, execute candidate code, or validate arbitrary tool action schemas. These remain separate review gates; do not mislabel them as implemented.

For excluded records: set privacy.excluded=true, remove them from the next curated export, and create a new dataset version. Retain a minimal exclusion ID ledger separately. Existing trained weights may retain influence; rollback or retraining is a separate decision. No fine-tuned weights currently exist.

## Licensed dataset candidate reviewed 2026-10-03

Databricks Dolly-15k: the official dataset card explicitly lists LLM training and academic/commercial use under CC BY-SA 3.0. Human authorship is described by the publisher. Revision bdd27f4d94b9c1f951818a7da7fd7aeea5dbff1a was downloaded with network permission. Attribution, ShareAlike, change notices and record-level privacy/accuracy review are retained. Twelve candidates remain excluded/pending; none is approved for training. See ../../friday-training/dolly-review. Teacher API collection remains blocked. No GPU run or paid API occurred.
