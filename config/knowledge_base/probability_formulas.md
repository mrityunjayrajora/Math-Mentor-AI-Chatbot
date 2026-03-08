# Probability Formulas & Concepts

## Basic Probability

### Definitions
- P(A) = Number of favorable outcomes / Total number of outcomes
- 0 ≤ P(A) ≤ 1
- P(A) + P(A') = 1 (complement rule)
- P(S) = 1 (sample space)

### Addition Rule
- P(A ∪ B) = P(A) + P(B) - P(A ∩ B)
- For mutually exclusive events: P(A ∪ B) = P(A) + P(B)

### Multiplication Rule
- P(A ∩ B) = P(A) × P(B|A)
- For independent events: P(A ∩ B) = P(A) × P(B)

## Conditional Probability

### Definition
P(A|B) = P(A ∩ B) / P(B), where P(B) ≠ 0

### Bayes' Theorem
P(A|B) = [P(B|A) × P(A)] / P(B)

### Total Probability Theorem
P(B) = Σ P(B|Aᵢ) × P(Aᵢ) for partition {A₁, A₂, ..., Aₙ}

## Combinatorics

### Permutations
- nPr = n! / (n-r)!
- Permutations with repetition: n^r
- Circular permutations: (n-1)!

### Combinations
- nCr = n! / [r! × (n-r)!]
- nCr = nC(n-r)
- nC0 + nC1 + ... + nCn = 2ⁿ

### Multinomial Coefficient
n! / (n₁! × n₂! × ... × nₖ!)

## Probability Distributions

### Binomial Distribution
- X ~ B(n, p)
- P(X = k) = C(n,k) × p^k × (1-p)^(n-k)
- Mean: E(X) = np
- Variance: Var(X) = np(1-p)

### Poisson Distribution
- P(X = k) = (e^(-λ) × λ^k) / k!
- Mean = Variance = λ

### Geometric Distribution
- P(X = k) = (1-p)^(k-1) × p
- Mean: E(X) = 1/p
- Variance: Var(X) = (1-p)/p²

## Expected Value & Variance

### Expected Value
- E(X) = Σ xᵢ × P(xᵢ) (discrete)
- E(aX + b) = aE(X) + b
- E(X + Y) = E(X) + E(Y) (always)
- E(XY) = E(X) × E(Y) (if independent)

### Variance
- Var(X) = E(X²) - [E(X)]²
- Var(aX + b) = a² × Var(X)
- Var(X + Y) = Var(X) + Var(Y) (if independent)
- Standard Deviation: σ = √Var(X)

## Important Distributions for JEE

### Uniform Distribution
- P(X = xᵢ) = 1/n for each outcome
- Mean = (a + b)/2
- Variance = (b - a)²/12

### Bernoulli Trial
- Single trial with P(success) = p
- P(failure) = 1 - p = q
- Mean = p, Variance = pq

## Odds

### Definition
- Odds in favor of A = P(A) / P(A') = P(A) / (1 - P(A))
- Odds against A = P(A') / P(A)

## Independent Events

### Tests for Independence
- P(A ∩ B) = P(A) × P(B)
- P(A|B) = P(A)
- P(B|A) = P(B)

## Derangements
Number of derangements of n objects:
Dₙ = n! × Σ (-1)^k / k! for k = 0 to n
