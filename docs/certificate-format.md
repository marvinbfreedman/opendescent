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
- `threeSelmerEvidence`: optional external 3-Selmer transcript evidence
- `higherTwoPowerEvidence`: optional external higher 2-primary evidence, such
  as `Z/4 + Z/4`

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

## Higher 2-Power Evidence

A rank/Selmer certificate is not enough to support a higher 2-primary structure
claim such as `Z/4 + Z/4`.  For that, OpenDescent expects one of:

- an explicit higher 2-descent transcript that reports the 2-primary group
  structure
- an explicit Cassels-pairing computation
- another auditable backend output that reports the same higher 2-power data

Input records can request or attach this evidence with:

```json
{
  "requiresHigherTwoPowerEvidence": true,
  "expectedTwoPrimaryStructure": "Z/4 + Z/4",
  "expectedTwoPrimaryOrder": 16,
  "higherTwoPowerTranscript": "transcripts/example_higher_2power.txt"
}
```

When `--evidence-transcripts` is enabled, OpenDescent parses lines like:

```text
Abelian Group isomorphic to Z/4 + Z/4
```

and records normalized cyclic factors, order, exponent, whether the structure is
2-primary, whether a higher 2-power factor such as `Z/4` was detected, and
whether the parsed structure/order matches the expected values.

If a curve asks for higher 2-power evidence but no transcript is supplied or
loaded, the curve certificate gets:

```json
{
  "status": "missing_higher_two_power_evidence"
}
```

That missing-evidence block is intentional.  It prevents a plain 2-Selmer rank
or ordinary second-descent trace from being mistaken for `Z/4 + Z/4` evidence.

## Optional Case Metadata

Some imported research cases include extra fields under `caseMetadata`:

- `prime`
- `expectedSelmerOrder`
- `targetPrimaryOrder`
- `predictedShaOrder`
- `predictedShaFactorization`
- `expectedTwoPrimaryStructure`
- `expectedTwoPrimaryOrder`
- `requiresHigherTwoPowerEvidence`
- `source`

These fields document the external descent target.  They do not change rank
certification rules.

## Transcript Evidence

When `--evidence-transcripts` is used, OpenDescent reads transcript paths from
curve records and attaches available `threeSelmerEvidence` and
`higherTwoPowerEvidence` blocks.  GRH-conditional transcripts are recorded with:

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
