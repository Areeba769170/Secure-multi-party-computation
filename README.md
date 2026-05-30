# Secure Multi-Party Computation - Project Overview

## What I built

For this project I implemented a small **secure multi-party computation (SMC)**
system in Python. The idea is that several people each hold a private number,
and together they want to compute some arithmetic over those numbers : a sum, a
product, and so on ,*without anyone revealing their own value to the others*.
At the end, everyone learns only the final result.

The trick that makes this possible is **additive secret sharing**: a secret
value is split into random pieces ("shares") that add up to the original. Each
party holds one piece, and a single piece on its own tells you nothing. Only by
combining all the shares can the secret be recovered.

The system works on **arithmetic circuits** made up of additions, subtractions,
multiplication by a constant, addition of a constant, and multiplication of two
secrets.

## The parts I implemented

The project came with a skeleton where the communication layer, the server, and
the tests were already provided. I implemented four files:

- **`expression.py`** - lets me describe a computation like `a * b + c` as a
  tree (an abstract syntax tree). Writing the expression doesn't compute
  anything; it just records the structure so the client can walk it later.
- **`secret_sharing.py`** - splits a number into shares and reconstructs it. All
  the math happens modulo a large prime so the numbers stay in a fixed range,
  and because the prime is far bigger than any real value, the final answer is
  always exact.
- **`ttp.py`** - the trusted parameter generator. It creates **Beaver triplets**
  `(a, b, c)` with `a * b = c`, which are the helper values needed to multiply
  two secrets. A fresh triplet is generated for every multiplication.
- **`smc_party.py`** - the brain of each participant. It shares out its own
  secrets, walks the expression tree computing its own share of every result,
  and finally reconstructs the answer with the other parties.

### How each operation is handled

- **Addition / subtraction** of two secrets is done locally — each party just
  adds or subtracts its own shares, no communication needed.
- **Multiplication by a constant** is also local - each party multiplies its
  share by the public number.
- **Adding a constant** is done by only one designated party, so the constant is
  counted exactly once instead of once per participant.
- **Multiplication of two secrets** is the hard case. It uses the Beaver triplet
  protocol: each party masks its secrets, publishes the masked differences,
  everyone reconstructs those public values, and then each party computes its
  share of the product from them.

## Testing

The implementation passes **all 10 integration tests** in `test_integration.py`,
which cover every type of circuit (additions, subtractions, scalar operations,
constants, and multiplications combined in different ways). The grading uses a
`python:3.11-alpine` container, so I kept the code compatible with Python 3.11.

## Custom application: Private Interest Matching

For the application part, I built a simple version of **Private Set Intersection
(PSI)** in `custom_app.py`.

**The scenario:** two people, Alice and Bob, want to find out *how many*
interests they have in common, without revealing *which* interests each of them
actually has.

**How it works:** they agree on a public list of interests (e.g. sports, music,
cooking, travel, gaming). Each person gives a secret `1`/`0` answer per interest.
An interest counts as shared only if both said `1`, which is exactly what
multiplying the two secret answers does (`1 * 1 = 1`, otherwise `0`). Summing
those products gives the overlap, and multiplying by a public points constant
turns it into a compatibility score:

```
overlap = a0*b0 + a1*b1 + a2*b2 + a3*b3 + a4*b4
score   = overlap * POINTS_PER_MATCH
```

This circuit uses **all** the operations I implemented: secret × secret
multiplication (Beaver triplets), addition, and multiplication by a public
constant.

**Threat model:** I assume the *honest-but-curious* model — both parties follow
the protocol correctly but would peek at each other's secrets if they could.
Because the inputs are secret-shared, neither party ever sees the other's
individual answers; they only learn the final score. I also documented the
honest limitations: the scheme doesn't protect against an actively cheating
party (e.g. submitting values that aren't `0`/`1`), and revealing the score on a
very small interest list could leak information - which is why I use several
interests.

**A design decision I had to make:** I deliberately did *not* subtract the match
threshold inside the circuit. Since the field math wraps negative numbers around
to huge values, a "below threshold" score would look wrong. Instead I keep the
score non-negative and do the threshold comparison in normal Python after the
result is revealed.

I also wrote `test_custom_app.py`, which checks the application across many edge
cases (no overlap, full overlap, single overlap, one party with all zeros, both
with all zeros, and so on), comparing the secure result against a value computed
by hand.

## Files

| File | What it is |
| --- | --- |
| `expression.py` | Arithmetic expression / circuit definitions (mine) |
| `secret_sharing.py` | Additive secret sharing scheme (mine) |
| `ttp.py` | Trusted Beaver triplet generator (mine) |
| `smc_party.py` | SMC participant logic (mine) |
| `custom_app.py` | Private Interest Matching application (mine) |
| `test_custom_app.py` | Tests for the custom application (mine) |
| `communication.py`, `server.py`, `protocol.py` | Provided by the skeleton |
| `test_integration.py` | Provided integration tests (all passing) |
