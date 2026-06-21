# OpenDescent

OpenDescent is an open-source arithmetic descent engine for reproducible
elliptic-curve BSD workflows.

It is built as an open-source alternative to Magma for the part of the workflow
we need first: auditable descent/rank certificates for elliptic curves over
`Q`.  OpenDescent does not copy Magma, does not claim Magma compatibility, and
does not depend on proprietary internals.  It implements public mathematics and
emits machine-readable JSON certificates.

## What Works Now

- integral Weierstrass curves over `Q`
- standard invariants `b2,b4,b6,b8,c4,c6,Delta,j`
- point counting over finite fields
- good-prime `a_p` samples
- basic bad-prime local reduction metadata
- exact affine group law over `Q`
- naive integral point search
- JSON certificate CLI
- optional Sage/eclib backend for rank intervals and 2-Selmer ranks
- direct mwrank/eclib backend for independent rank/Selmer cross-checks
- higher 2-descent evidence capture from mwrank second-descent traces
- higher 2-power transcript parsing for structures like `Z/4 + Z/4`
- calculator primitive for `FiveSelmerGroup(E)` transcript evidence
- native 5-descent task records with local-prime selection and proof gaps
- native Cassels-pairing task records for 5-covering representatives
- explicit Cassels-pairing status fields in certificates

Native OpenDescent 2-descent is intentionally marked as a gap until the full
algorithm is implemented.  Cassels pairings are also marked as not computed
unless a backend explicitly provides pairing data.
Plain 2-Selmer output is not treated as evidence for `Z/4 + Z/4` or another
higher 2-primary structure.
`FiveSelmerGroup(E)` can parse explicit transcript/backend output such as
`Z/5 + Z/5` and can run a native task scaffold.  The native path records
local-prime inputs and rational 5-torsion candidates, but it remains partial
until degree-5 covering construction and local solubility kernels are complete.

## Quick Start

Native arithmetic scaffold:

```bash
cd /path/to/opendescent
python3 -m opendescent.cli examples/calibration_curves.json --out certificate.native.json
```

Sage-backed open-source rank/Selmer certificate:

```bash
python3 -m opendescent.cli examples/calibration_curves.json --backend sage --out certificate.sage.json
```

Direct mwrank/eclib certificate summary:

```bash
python3 -m opendescent.cli examples/calibration_curves.json --backend mwrank_direct --summary-only
```

Run the three imported `codex-2` timeout cases:

```bash
python3 -m opendescent.cli examples/codex2_timeout_cases.json --backend sage --summary-only
python3 -m opendescent.cli examples/codex2_timeout_cases.json --backend mwrank_direct --summary-only
python3 -m opendescent.cli examples/codex2_timeout_cases.json --backend native --evidence-transcripts --out timeout_evidence.json
```

Attach native 5-descent and 5-covering Cassels-pairing task output:

```bash
python3 -m opendescent.cli examples/calibration_curves.json --native-descent-tasks --summary-only
```

Expected Sage-backed calibration summary:

```text
11a1: rankInterval=[0, 0] certified=True
37a1: rankInterval=[1, 1] certified=True
389a1: rankInterval=[2, 2] certified=True
```

## Input Format

```json
{
  "curves": [
    {
      "label": "11a1",
      "conductor": 11,
      "weierstrass": [0, -1, 1, -10, -20]
    }
  ]
}
```

The Weierstrass model is:

```text
y^2 + a1*x*y + a3*y = x^3 + a2*x^2 + a4*x + a6
```

## Backends

| Backend | Status | Purpose |
| --- | --- | --- |
| `native` | partial | OpenDescent's own arithmetic and explicit descent gaps |
| `sage` | working | Open-source Sage/eclib rank bounds, Selmer rank, torsion |
| `mwrank_direct` | working | Direct eclib/mwrank rank, 2-Selmer, and second-descent trace adapter |
| `pari_gp` | planned | PARI/GP number-theory support |
| `magma` | optional detector only | Future licensed-user adapter; not required and not bundled |

Certification is true only when the backend returns equal lower and upper rank
bounds.

Committed calibration fixtures live in `examples/expected/`.
The three timeout cases from `p3/codex-2` live in
`examples/codex2_timeout_cases.json`; their GRH-conditional transcript fixtures
live in `examples/transcripts/`.

## Documentation

- [Certificate format](docs/certificate-format.md)
- [Comparison with Magma, Sage, and PARI/GP](docs/comparison.md)
- [Native roadmap](docs/native-roadmap.md)

## Roadmap

1. Full Tate algorithm for additive and non-minimal bad-prime cases.
2. Native 2-covering construction.
3. Local solubility tests for coverings.
4. Native 2-Selmer upper bounds.
5. Native higher 2-descent and Cassels-pairing routines for unresolved
   Selmer gaps.
6. Native higher 2-power structure certification, including `Z/4 + Z/4`-type
   evidence.
7. Complete native 5-covering construction and local solubility.
8. Complete native Cassels-pairing entry computation for 5-coverings.
9. Mordell-Weil rank certificate closing lower and upper bounds.
