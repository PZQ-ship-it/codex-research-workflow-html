# Paper Reproduction Environment Smoke Patterns

Use this reference when a paper repo has unclear installation instructions, multiple dependency managers, CUDA/GPU assumptions, or no obvious entrypoint.

## What Counts As Smoke

A smoke test is a cheap viability check, not reproduction success. Good smoke commands include:

- environment creation or dependency resolution in an isolated env;
- import of the main package or framework;
- `python main.py --help`, `python train.py --help`, or `python eval.py --help`;
- unit tests or one tiny test file;
- evaluation on a tiny bundled sample;
- one batch, dry run, or one epoch only when the repo documents it as cheap.

## Environment Priority

1. Existing documented project environment.
2. Conda from `environment.yml` or `environment.yaml`.
3. Venv plus `requirements*.txt`.
4. Project package install from `pyproject.toml`, `setup.py`, or `setup.cfg`.
5. Docker/Apptainer when the repo provides a Dockerfile or the user approves container use.
6. Manual dependency repair, recorded as a deviation.

## Inspection Checklist

- Dependency manifests and lock files.
- Python version and framework constraints.
- CUDA/cuDNN/GPU driver assumptions.
- Data/model path conventions.
- Tests, examples, demo notebooks, CLI entrypoints.
- README commands tied to result tables.
- Whether the repo needs private credentials or gated downloads.

## Blocker Classes

- `dependency`: missing or conflicting package.
- `python-version`: incompatible interpreter.
- `cuda-driver`: GPU, CUDA, cuDNN, or driver mismatch.
- `missing-data`: dataset absent or inaccessible.
- `missing-model`: checkpoint absent or inaccessible.
- `path-config`: hard-coded path or missing config.
- `api-auth`: credential or OAuth needed.
- `license`: usage/download blocked by terms.
- `code-paper-mismatch`: repo does not expose the mapped experiment.
- `resource-cost`: smoke would require unreasonable compute/time.
- `unknown`: failure requires deeper diagnosis.

## Command Safety

- Prefer commands that finish in seconds or a few minutes.
- Log command, cwd, env summary, exit code, duration, stdout/stderr paths.
- Stop after the first meaningful blocker unless the next command is an independent cheap probe.
- Do not modify official repo source unless the user explicitly asks for a repair loop.

## Source Notes

- ReproAgent smoke/runtime workflow: https://github.com/hqygtr-prog/repro-agent
- Papers with Code code completeness checklist: https://github.com/paperswithcode/releasing-research-code
- The Turing Way smoke testing overview: https://book.the-turing-way.org/reproducible-research/testing/testing-smoketest/
- EnvBench environment setup benchmark: https://arxiv.org/html/2503.14443v1
