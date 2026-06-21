# OpenDescent

OpenDescent is a small open-source BSD/descent certificate engine scaffold.

The goal is not to clone Magma.  The goal is to implement public mathematics in
a reproducible, auditable way and emit machine-readable certificates for
elliptic curves over `Q`.

Current scope:

- short/local arithmetic for integral Weierstrass models
- standard invariants `b2,b4,b6,b8,c4,c6,Delta,j`
- point counting over finite fields
- good-prime `a_p`
- basic bad-prime reduction metadata
- exact affine group law over `Q`
- naive small integral point search
- certificate JSON CLI

Not yet implemented:

- full Tate algorithm for all additive cases
- genuine 2-descent
- certified Selmer upper bounds
- rigorous Mordell-Weil basis certification

Until the 2-descent module lands, certificates explicitly mark Selmer/rank upper
bounds as unavailable.

## Quick Start

```bash
cd /path/to/opendescent
python3 -m opendescent.cli examples/calibration_curves.json --out certificate.json
python3 -m json.tool certificate.json | head -120
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

