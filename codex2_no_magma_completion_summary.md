# codex-2 Magma-Free Completion Summary

This report uses Sage/eclib evidence only.  Exact primary-order
certification is recorded only when Sage proves the primary order.

## Summary

- total cases: `14`
- certified cases: `7`
- unresolved cases: `7`
- status counts: `{"higher_two_power_unresolved": 4, "sage_primary_bound_matches_expected": 2, "sage_primary_order_confirmed": 7, "sage_primary_unavailable": 1}`

## Cases

| label | p | expected primary order | state | status | Sage value |
|---|---:|---:|---|---|---:|
| `2045b1` | 2 | 16 | `requires_higher_two_power_evidence` | `higher_two_power_unresolved` | 2 |
| `2678a1` | 2 | 16 | `requires_higher_two_power_evidence` | `higher_two_power_unresolved` | 2 |
| `2738c1` | 2 | 16 | `requires_higher_two_power_evidence` | `higher_two_power_unresolved` | 2 |
| `2742b1` | 2 | 16 | `requires_higher_two_power_evidence` | `higher_two_power_unresolved` | 2 |
| `2429b1` | 3 | 9 | `certified` | `sage_primary_order_confirmed` | 9 |
| `2534e1` | 3 | 9 | `bounded_not_certified` | `sage_primary_bound_matches_expected` | 9 |
| `2534f1` | 3 | 9 | `bounded_not_certified` | `sage_primary_bound_matches_expected` | 9 |
| `2674b1` | 3 | 9 | `certified` | `sage_primary_order_confirmed` | 9 |
| `2849a1` | 3 | 9 | `certified` | `sage_primary_order_confirmed` | 9 |
| `1664k1` | 5 | 25 | `certified` | `sage_primary_order_confirmed` | 25 |
| `2366f1` | 5 | 25 | `certified` | `sage_primary_order_confirmed` | 25 |
| `2574d1` | 5 | 25 | `certified` | `sage_primary_order_confirmed` | 25 |
| `2834d1` | 5 | 25 | `certified` | `sage_primary_order_confirmed` | 25 |
| `2900d1` | 5 | 25 | `unavailable` | `sage_primary_unavailable` |  |

## Unresolved

- `2045b1` p=2: ordinary 2-Selmer/Sha[2] data does not certify the required higher 2-primary structure
- `2678a1` p=2: ordinary 2-Selmer/Sha[2] data does not certify the required higher 2-primary structure
- `2738c1` p=2: ordinary 2-Selmer/Sha[2] data does not certify the required higher 2-primary structure
- `2742b1` p=2: ordinary 2-Selmer/Sha[2] data does not certify the required higher 2-primary structure
- `2534e1` p=3: Sage proves the 3-primary Sha order is at most 9, matching the expected exponent, but exact-order certification failed.
- `2534f1` p=3: Sage proves the 3-primary Sha order is at most 9, matching the expected exponent, but exact-order certification failed.
- `2900d1` p=5: pPrimaryOrderExponent: The order is not provably known using Skinner-Urban.
Try running p_primary_bound to get a bound.; pPrimaryBoundExponent: The curve has to have semi-stable reduction at p.

## Re-run

```bash
python3 codex2_no_magma_completion.py --codex2-dir /Users/mbf_mini/p3/codex-2
```
