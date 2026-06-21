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
- `higherTwoDescent`: backend evidence for second 2-descent or related
  higher-descent steps
- `casselsPairing`: Cassels-pairing status; `computed` must be `false` unless
  a backend provides actual pairing data
- `status`: human-readable certificate state

OpenDescent must not mark `rankCertified=true` unless the rank interval is
closed by a successful backend.

### Higher 2-Descent and Cassels Pairing

The `higherTwoDescent` block records what the selected backend actually did.
For `mwrank_direct`, OpenDescent parses public mwrank output such as:

- full 2-descent via multiplication-by-2
- descent via a 2-isogeny
- the second local descent step
- reported `S^2`, `S^phi`, `S^phi'`, and `III[2]` dimensions

This is evidence capture, not a native implementation claim.  Native
OpenDescent currently returns:

```json
{
  "computed": false,
  "status": "gap: native higher 2-descent is not implemented yet"
}
```

The `casselsPairing` block is deliberately separate.  Selmer dimensions and
Sha-size traces are not a Cassels pairing matrix.  OpenDescent therefore marks
`casselsPairing.computed=false` unless an explicit Cassels-pairing backend is
added.

## Optional Case Metadata

Some imported research cases include extra fields under `caseMetadata`:

- `prime`
- `expectedSelmerOrder`
- `targetPrimaryOrder`
- `predictedShaOrder`
- `predictedShaFactorization`
- `source`

These fields document the external descent target.  They do not change rank
certification rules.

## Transcript Evidence

When `--evidence-transcripts` is used, OpenDescent reads transcript paths from
curve records and attaches a `threeSelmerEvidence` block.  GRH-conditional
transcripts are recorded with:

```json
{
  "conditional": true,
  "condition": "GRH",
  "matchesExpected": true
}
```

Conditional transcript evidence is not an unconditional closure.

## Summary Output

The CLI supports:

```bash
python3 -m opendescent.cli examples/calibration_curves.json --backend sage --summary-only
```

Summary mode prints only the run status, selected backend, curve label, rank
interval, certification flag, 2-Selmer rank, torsion order, engine, and
transcript evidence fields when present.  JSON output remains the canonical
certificate format.

## Calibration Fixtures

The repository keeps expected calibration certificates in `examples/expected/`:

- `native_calibration.json`
- `sage_calibration.json`
- `mwrank_calibration.json`
- `codex2_timeout_sage.json`
- `codex2_timeout_mwrank.json`
- `codex2_timeout_grh_evidence.json`
