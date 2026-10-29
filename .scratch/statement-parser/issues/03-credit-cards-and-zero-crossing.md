# 03: Credit cards and balances crossing zero

**What to build:** Adds the second Account Type and the hard balance-sign cases from the original handoff.

Spec stories: 15, 16, 32.

**Blocked by:** 01: Tracer bullet

**Status:** done

- [x] A credit card fixture reconciles with closing = opening − Σ amounts (balance owed printed as positive)
- [x] Balance signs are read from CR/DR suffixes and minus signs
- [x] An overpaid credit card (in credit) and an overdrawn deposit account both reconcile
- [x] A Parser that reads the wrong balance field (available balance, credit limit, amount due) fails Reconciliation
