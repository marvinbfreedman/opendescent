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
5. Combine point-search or height-pairing lower bounds with Selmer upper bounds
   to close the rank interval.

## Certification Rule

Native OpenDescent must keep returning `rankCertified=false` until the lower and
upper rank bounds are both present and equal.
