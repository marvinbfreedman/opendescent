# OpenDescent Compared With Magma, Sage, and PARI/GP

OpenDescent is positioned as an open-source alternative to Magma for
reproducible BSD/descent certificate workflows.

It is not a Magma clone and does not aim to reproduce Magma's proprietary
implementation.  The mathematical algorithms are public mathematics; the code,
certificate schema, and backend adapters in OpenDescent are independent.

## Magma

Magma is a broad proprietary computer algebra system with deep arithmetic,
algebra, and geometry support.  OpenDescent is narrower: it focuses first on
elliptic curves over `Q`, BSD calibration, rank intervals, Selmer data, and
machine-readable certificates.

## SageMath

SageMath is open source and currently provides the practical rank/Selmer backend
for OpenDescent's v1 certificates.  OpenDescent wraps Sage output into a stable
certificate format while native descent modules are developed.

## PARI/GP and mwrank/eclib

PARI/GP and mwrank/eclib are open-source arithmetic engines.  OpenDescent will
support direct adapters for them so users can cross-check certificates without a
single monolithic system.  The direct `mwrank` adapter is the first of these
cross-check backends.  It now records mwrank's full 2-descent and second
2-isogeny descent traces in the JSON certificate when those traces are present.

## Higher 2-Descent and Cassels Pairing

OpenDescent treats higher descent and Cassels pairing as separate certificate
claims.  A backend may record second-descent evidence, Selmer dimensions, and
Sha-size information, but that is not the same as computing a Cassels-pairing
matrix.  Certificates therefore keep `higherTwoDescent` and `casselsPairing` as
separate blocks.

Higher 2-power group-structure claims are separate again.  Evidence for a
`Z/4 + Z/4`-type structure must come from an explicit higher 2-descent,
Cassels-pairing, or transcript output that reports the 2-primary abelian group
structure.  OpenDescent records that under `higherTwoPowerEvidence`; it does not
infer it from an ordinary 2-Selmer rank alone.

For 5-primary work, OpenDescent provides a calculator primitive named
`FiveSelmerGroup(E)` that records explicit transcript/backend output such as
`Z/5 + Z/5` and runs a native 5-descent task scaffold.  The native path records
local-prime inputs and missing proof kernels, but it does not yet construct
general degree-5 coverings.

For Cassels pairings, OpenDescent can assemble and validate an `F_5` pairing
matrix when 5-covering records supply pairing entries.  It does not infer
entries from Selmer dimensions or transcript summaries.

## Design Difference

OpenDescent is certificate-first:

- every claim should have a JSON field
- every unavailable proof step should be explicit
- generated certificates should be diffable
- external backends should be replaceable
- conditional evidence, such as GRH-dependent transcript output, should be
  separated from unconditional certification
