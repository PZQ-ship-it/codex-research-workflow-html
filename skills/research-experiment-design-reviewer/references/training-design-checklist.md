# Training Design Checklist

Use this reference when reviewing ML training, fine-tuning, pretraining, distillation, RL, retrieval-augmented tuning, or optimizer/schedule design.

## Minimum Design Brief

- Objective: supervised, self-supervised, RL, preference tuning, distillation, retrieval, calibration, compression, or domain adaptation.
- Claim: what training change is expected to improve and why.
- Data: source, license, split, filtering, deduplication, contamination checks, labels, class/task balance, and domain shift.
- Model: architecture, pretrained checkpoint, frozen/trainable components, tokenizer/feature pipeline, initialization, adapters, retrieval, or tool-use boundary.
- Optimization: loss, optimizer, learning rate, scheduler, batch size, gradient accumulation, clipping, precision, regularization, early stopping, and checkpoint policy.
- Evaluation: validation split, test split, primary metric, guardrail metrics, evaluator model/human evaluator boundaries, and failure categories.
- Compute: hardware, memory budget, expected run time, cost, number of seeds, and rerun budget.
- Reproducibility: config files, commit hash, environment, data version, seed policy, logging, artifact paths, and result completeness rules.

## High-Risk Review Questions

- Is the target claim actually about training, or could it be explained by data, prompt, evaluator, preprocessing, or selection effects?
- Could train/validation/test leakage occur through duplicates, near-duplicates, user/session overlap, temporal leakage, benchmark contamination, or preprocessing fitted on all data?
- Are baselines trained and tuned with comparable data, compute, hyperparameter budget, and stopping criteria?
- Are failed runs, cherry-picked checkpoints, or exploratory trials included in the accounting?
- Are random seeds and variance handled with repeated runs or confidence intervals when the metric is noisy?
- Does early stopping use only validation data and avoid peeking at test metrics?
- Are any evaluator models also used in training data generation, reward modeling, or filtering?
- Is the training change isolated from unrelated changes in data, architecture, inference, decoding, or postprocessing?
- Are safety, privacy, license, or consent constraints affected by the training data or model outputs?
- Is the compute budget realistic enough to complete sanity, baseline, main, and ablation stages?

## Recommended Training Run Order

1. Sanity run: tiny data or few steps to verify loss decreases, metrics compute, and artifacts write correctly.
2. Baseline reproduction: reproduce known baseline or current production/model result under the same evaluation.
3. Main method: run the proposed training change with frozen protocol.
4. Ablations: remove or vary one factor at a time.
5. Robustness: seeds, alternate split, harder subset, stress cases, or domain shift.
6. Final locked run: rerun only after the protocol and analysis plan are fixed.

## Failure Modes To Surface

- Loss improves while target metric worsens.
- Validation improves but test or out-of-domain performance collapses.
- A data filter silently removes hard examples and inflates metrics.
- Hyperparameter search budget favors the proposed method.
- Metric script differs between baseline and main method.
- Results depend on a single seed, checkpoint, prompt, evaluator, or split.
- The design lacks a stop rule for divergence, mode collapse, memory errors, or evaluator failure.
- The design cannot distinguish method benefit from extra compute or extra data.

## Useful Output Additions

When reviewing a training design, include:

- a minimal run matrix with rows for sanity, baseline, main, ablation, and robustness;
- a leakage/control table;
- a compute and rerun budget;
- a list of locked variables that must not change across comparisons;
- a result trust gate before paper/product claims are allowed.
