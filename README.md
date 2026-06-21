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

Native OpenDescent 2-descent is intentionally marked as a gap until the full
algorithm is implemented.

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
| `pari_gp` | planned | PARI/GP number-theory support |
| `mwrank_direct` | planned | Direct eclib/mwrank adapter |
| `magma` | optional detector only | Future licensed-user adapter; not required and not bundled |

Certification is true only when the backend returns equal lower and upper rank
bounds.

## Documentation

- [Certificate format](docs/certificate-format.md)
- [Comparison with Magma, Sage, and PARI/GP](docs/comparison.md)

## Roadmap

1. Full Tate algorithm for additive and non-minimal bad-prime cases.
2. Native 2-covering construction.
3. Local solubility tests for coverings.
4. Native 2-Selmer upper bounds.
5. Mordell-Weil rank certificate closing lower and upper bounds.
