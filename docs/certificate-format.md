# OpenDescent Certificate Format

OpenDescent certificates are JSON records intended to be reproducible, auditable,
and easy to compare across backends.

## Top-Level Fields

- `artifact`: always `opendescent_certificate`
- `version`: OpenDescent certificate version
- `status`: human-readable run status
- `backend`: selected backend, usually `native` or `sage`
- `availableBackends`: backend detector results from the local machine
- `backendResult`: raw backend execution record when an external backend is used
- `curves`: list of per-curve certificates
- `remainingWork`: explicit native implementation gaps

## Per-Curve Fields

- `label`: curve label from input
- `conductor`: conductor from input when supplied
- `weierstrass`: `[a1,a2,a3,a4,a6]`
- `invariants`: standard integral invariants
- `badPrimes`: primes dividing the discriminant
- `localRecords`: bad-prime local metadata
- `goodPrimeSamples`: sampled good-prime `a_p` values
- `integralPointSearch`: bounded integral point search result
- `descent`: rank/Selmer certificate block

## Descent Block

The `descent` block is the certification boundary.

- `engine`: backend used for rank/Selmer data
- `rankLowerBound`: lower rank bound, or `null`
- `rankUpperBound`: upper rank bound, or `null`
- `rankInterval`: `[lower, upper]` when both bounds are known
- `rankCertified`: `true` only when `lower == upper`
- `twoSelmerRank`: 2-Selmer rank when available
- `selmerUpperBound`: Selmer-derived upper bound when available
- `torsionOrder`: torsion subgroup order when available
- `regulator`: regulator when reported by a backend
- `generators`: generators reported by a backend when available
- `status`: human-readable certificate state

OpenDescent must not mark `rankCertified=true` unless the rank interval is
closed by a successful backend.

## Summary Output

The CLI supports:

```bash
python3 -m opendescent.cli examples/calibration_curves.json --backend sage --summary-only
```

Summary mode prints only the run status, selected backend, curve label, rank
interval, certification flag, 2-Selmer rank, torsion order, and engine.  JSON
output remains the canonical certificate format.

## Calibration Fixtures

The repository keeps expected calibration certificates in `examples/expected/`:

- `native_calibration.json`
- `sage_calibration.json`
- `mwrank_calibration.json`
