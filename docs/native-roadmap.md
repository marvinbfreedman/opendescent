# Native OpenDescent Roadmap

OpenDescent's native engine should eventually certify elliptic-curve rank and
2-Selmer data without relying on Sage or mwrank.

## Milestones

1. Implement the full Tate algorithm for additive and non-minimal bad-prime
   cases.
2. Construct native 2-coverings for elliptic curves over `Q`.
3. Add local solubility checks for the real place and all relevant finite
   primes.
4. Compute the native 2-Selmer group and rank upper bound.
5. Add native higher 2-descent steps for cases where the first Selmer bound
   does not close the rank interval.
6. Implement Cassels-pairing computation on 2-coverings when the pairing can
   certify the relevant Sha/Selmer obstruction.
7. Certify higher 2-primary structure claims such as `Z/4 + Z/4`, either from
   native higher 2-descent data or from a verified Cassels-pairing computation.
8. Combine point-search or height-pairing lower bounds with Selmer upper bounds
   to close the rank interval.

## Imported Timeout Cases

The `codex-2` timeout cases `2429b1`, `2534f1`, and `2674b1` are included as
OpenDescent examples so native and open-source backend work can be rerun without
depending on external Magma calculator sessions.

## Certification Rule

Native OpenDescent must keep returning `rankCertified=false` until the lower and
upper rank bounds are both present and equal.

Higher-descent evidence from external backends may be recorded in certificates,
but native OpenDescent must keep `higherTwoDescent.computed=false` and
`casselsPairing.computed=false` until those routines are implemented directly.
If a case requires higher 2-power information, native OpenDescent must also
produce or import explicit `higherTwoPowerEvidence`; ordinary 2-Selmer ranks are
not enough for a `Z/4 + Z/4`-type claim.
