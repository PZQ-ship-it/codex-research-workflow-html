# Wave Protocol

Use this when planning or running a wide scout.

## Setup

Create a small control table before dispatch:

```text
wave | lane_id | hypothesis | probe | mode | isolation | budget
```

Default wave shape:

- wave 1: maximize diversity;
- wave 2: refine families that showed promise or surprise;
- wave 3 or later: only when the problem is still broad and the user wants more breadth.

## Lane Scoring

Score each lane with 0-5 integers:

- `novelty`: opens a new view or surprising path;
- `promise`: likely to produce useful next work;
- `evidence`: supported by observed facts or sources;
- `coverage`: fills a distinct part of the problem map;
- `cost`: time, complexity, money, or dependency burden;
- `risk`: chance of damage, overclaiming, privacy issues, or wasted work.

Use this rough total for sorting, not as a false precision claim:

```text
total = 0.25 * promise
      + 0.20 * novelty
      + 0.20 * evidence
      + 0.20 * coverage
      - 0.075 * cost
      - 0.075 * risk
```

## Between Waves

After collecting all lanes in a wave:

1. Group lanes into families.
2. Mark each family as `promising`, `uncertain`, `dead`, or `wildcard`.
3. Decide the next wave:
   - deepen only if the user asked for a full exploration loop;
   - otherwise split one or two broad families into new lanes;
   - keep at most one wildcard lane.
4. Preserve dead zones in the final output so future agents do not repeat them.

## Stop Rules

Stop when:

- wave budget is used;
- the top families are clear enough to hand off;
- all lanes are blocked by auth, data, or cost;
- a lead is already implementation-shaped;
- the user redirects.

Do not continue breadth just because parallelism is available.

## Final Scout Map

Include:

- top lane families and why they matter;
- surprising leads;
- dead zones and evidence against them;
- key artifacts or URLs;
- recommended next skill or human decision;
- residual uncertainty.
