# Training plan — Track B

Track A's live chat/research milestone remains first priority. Training preparation can progress offline while credentials are unavailable. No paid GPU job or teacher collection is authorized by this document.

## Current kit and gaps

`../friday-training` contains two experimental scripts: a Qwen-derived LoRA path and random-weight tiny GPT-2-architecture path. Neither has been run. Candidate library ranges are not a verified lock. The scratch architecture is reused; its weights are not pretrained. No finished FRIDAY model exists.

The earlier 12 synthetic examples and four evaluation examples are workflow samples only. They do not satisfy permission provenance, pilot quantity, task-family independence, or the new three-way split. Their earlier `approved_for_training` boolean is insufficient. Quarantine them from any real training until reviewed under the new provenance schema. They are not 12 verified pilot records. No operational conversations are imported.

## Pilot gate

1. Select a suitably licensed base and pin its revision. Qwen2.5-0.5B-Instruct is the existing candidate; retain base attribution and license obligations. Confirm library/GPU compatibility before paying for a long session.
2. Curate about 500–1,000 verified examples targeting planning and tool selection. This count is experimental. Include permission-following, unavailable-tool, uncertainty, and multi-step planning cases.
3. Use the `pilot.py` record contract: ID, task family, input, target/output trace, source kind/reference/provider/model, generation date, permission status/evidence/reviewer/date, verification result/method/reviewer, version, split and privacy consent/exclusion metadata. Teacher permission must be established before collection; no collectors are provided.
4. Run `python pilot.py split reviewed.jsonl --out split.jsonl`, then `python pilot.py validate split.jsonl --pilot`. Assign related paraphrases/templates to the same family. Deterministic family grouping places families into train/validation/test. Human semantic leakage review is still required.
5. Export with `python pilot.py export split.jsonl --out curated-v1 --pilot`. Export preserves full provenance and source hash. Review regex redaction findings manually; `redact` invalidates prior verification and requires fresh review. Never include credentials in a dataset.
6. Evaluate the unchanged baseline on validation before training. Use validation for selection; reserve `test.jsonl` for the final comparison. Evaluate permission-following and unrelated general tasks for regressions. Do not choose checkpoints based on held-out test results.
7. Prepare a hardware/time/storage estimate and get the user's specific spending approval. First perform a two-step GPU smoke test and verify that saved weights reload. Runtime limits do not terminate a rental or guarantee costs.
8. Train, compare against the baseline, preserve artifacts, and publish a measured internal model card. Human score fields are unfilled until reviewed. Require improvement on target tasks and no material permission-following regression; record numerical thresholds before the run, not afterward.

## Promotion and rollback

No model may be promoted from code existence or a lower training loss alone. Store dataset version/hash, base ID/revision/license, environment lock, training configuration, checkpoint hash, metrics, reviewer decision and limitations. Keep the previous provider/checkpoint available. Promote by explicit server configuration change only after acceptance; rollback by restoring the previous configuration and restarting workers after accounting for in-flight jobs. The current backend has no checkpoint adapter, so production promotion is blocked.

Model card template: identity; base attribution; derivative vs from-scratch origin; intended use; excluded use; dataset/consent provenance; hardware and duration; training/evaluation split methods; baseline and trained results; uncertainty; permission tests; known regressions; model/checkpoint hashes; approval; rollback target. Fill unknown values as UNTESTED, not estimates disguised as measurements.

Removing data excludes it from future builds. It does not erase its learned influence from already trained weights. Preserve dataset exclusion history without retaining unnecessary personal content. Access-controlled export, checkpoint registry and automated rollout remain planned.
