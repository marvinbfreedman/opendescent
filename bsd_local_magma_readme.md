# BSD Local Magma Batch Export

This export contains local Magma scripts for the remaining BSD primary-descent
checks.  The p=3 batch is intended to be unconditional and deliberately does
not enable `SetClassGroupBounds("GRH")`.

## Files

- `bsd_local_magma_p3_remaining.m`: all 5 remaining p=3 cases, unconditional.
- `bsd_local_magma_p5_probe.m`: all 5 p=5 cases with `FiveSelmerGroup` and generic intrinsic probes.
- `bsd_local_magma_readme.md`: this command and transcript guide.

## Run Commands

```bash
magma -b bsd_local_magma_p3_remaining.m | tee bsd_local_magma_p3_remaining.out
magma -b bsd_local_magma_p5_probe.m | tee bsd_local_magma_p5_probe.out
```

If your local Magma does not use `-b`, run:

```bash
magma bsd_local_magma_p3_remaining.m | tee bsd_local_magma_p3_remaining.out
magma bsd_local_magma_p5_probe.m | tee bsd_local_magma_p5_probe.out
```

## p=3 Expected Output

Each p=3 block should print a `ThreeSelmerGroup` section.  Expected success is
`Order(G) = 9` for every row below.

| label | conductor | a-invariants | expected `Order(G)` |
|---|---:|---|---:|
| `2429b1` | 2429 | `[1, 1, 0, -115, -528]` | 9 |
| `2534e1` | 2534 | `[1, -1, 1, -1393324, -640018129]` | 9 |
| `2534f1` | 2534 | `[1, -1, 1, -303, -1955]` | 9 |
| `2674b1` | 2674 | `[1, 1, 0, -2758, -55020]` | 9 |
| `2849a1` | 2849 | `[1, 1, 1, -53484, -4843180]` | 9 |

If a p=3 case times out, save the partial output and rerun that single block
locally with more time.  Do not mark it confirmed from a GRH-only transcript.

## p=5 Expected Output

Each p=5 block probes three possible intrinsics:

1. `FiveSelmerGroup(E)`
2. `SelmerGroup(5, E)`
3. `SelmerGroup(E, 5)`

Expected successful 5-primary evidence, if your Magma exposes it, is an order
`25` group or an explicit `Z/5 + Z/5`-type structure.  If all intrinsics report
errors, keep the transcript as an intrinsic-availability probe, not as a
certificate.

| label | conductor | a-invariants | target order |
|---|---:|---|---:|
| `1664k1` | 1664 | `[0, -1, 0, -76162, -8064798]` | 25 |
| `2366f1` | 2366 | `[1, -1, 0, -528241, -147664867]` | 25 |
| `2574d1` | 2574 | `[1, -1, 0, -51969609, -144342625779]` | 25 |
| `2834d1` | 2834 | `[1, -1, 1, -8109, -279017]` | 25 |
| `2900d1` | 2900 | `[0, 0, 0, -120775, -16155250]` | 25 |

## Split Transcripts

The scripts print headers of the form:

```text
===== LABEL p=3 unconditional =====
...
===== END LABEL =====
```

and:

```text
===== LABEL p=5 probe =====
...
===== END LABEL =====
```

Save each block to:

- `transcripts/magma_LABEL_three_selmer.txt`
- `transcripts/magma_LABEL_five_probe.txt`

## Feed p=3 Transcripts Back Into Recorders

Legacy catalog recorder commands:

```bash
python3 /Users/mbf_mini/p3/codex-2/bsd_record_magma_three_selmer.py --label 2429b1 --raw-file transcripts/magma_2429b1_three_selmer.txt
python3 /Users/mbf_mini/p3/codex-2/bsd_record_magma_three_selmer.py --label 2534e1 --raw-file transcripts/magma_2534e1_three_selmer.txt
python3 /Users/mbf_mini/p3/codex-2/bsd_record_magma_three_selmer.py --label 2534f1 --raw-file transcripts/magma_2534f1_three_selmer.txt
python3 /Users/mbf_mini/p3/codex-2/bsd_record_magma_three_selmer.py --label 2674b1 --raw-file transcripts/magma_2674b1_three_selmer.txt
python3 /Users/mbf_mini/p3/codex-2/bsd_record_magma_three_selmer.py --label 2849a1 --raw-file transcripts/magma_2849a1_three_selmer.txt
```

For OpenDescent JSON certificates, add per curve:

```json
{
  "threeSelmerTranscript": "transcripts/magma_LABEL_three_selmer.txt",
  "expectedSelmerOrder": 9,
  "prime": 3
}
```

Then run:

```bash
python3 -m opendescent.cli input.json --backend native --evidence-transcripts --summary-only
```

## Feed p=5 Probe Transcripts Back Into OpenDescent

If a p=5 transcript contains a real group/order result, add records like:

```json
{
  "curves": [
  {"label":"1664k1","weierstrass":[0, -1, 0, -76162, -8064798],"prime":5,"expectedFiveSelmerOrder":25,"fiveSelmerTranscript":"transcripts/magma_1664k1_five_probe.txt"},
  {"label":"2366f1","weierstrass":[1, -1, 0, -528241, -147664867],"prime":5,"expectedFiveSelmerOrder":25,"fiveSelmerTranscript":"transcripts/magma_2366f1_five_probe.txt"},
  {"label":"2574d1","weierstrass":[1, -1, 0, -51969609, -144342625779],"prime":5,"expectedFiveSelmerOrder":25,"fiveSelmerTranscript":"transcripts/magma_2574d1_five_probe.txt"},
  {"label":"2834d1","weierstrass":[1, -1, 1, -8109, -279017],"prime":5,"expectedFiveSelmerOrder":25,"fiveSelmerTranscript":"transcripts/magma_2834d1_five_probe.txt"},
  {"label":"2900d1","weierstrass":[0, 0, 0, -120775, -16155250],"prime":5,"expectedFiveSelmerOrder":25,"fiveSelmerTranscript":"transcripts/magma_2900d1_five_probe.txt"}
  ]
}
```

Then run:

```bash
python3 -m opendescent.cli input.json --backend native --evidence-transcripts --summary-only
```

If the p=5 transcript only contains intrinsic errors, keep it as raw probe
evidence and do not claim `fiveSelmerEvidence.status=selmer_group_match`.
