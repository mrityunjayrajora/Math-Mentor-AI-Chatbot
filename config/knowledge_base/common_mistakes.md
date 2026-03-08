# Common Mistakes & Pitfalls

## Algebra Mistakes

### Sign Errors
- WRONG: -(a + b) = -a + b
- CORRECT: -(a + b) = -a - b
- TIP: Distribute the negative sign to ALL terms inside the parentheses.

### Exponent Mistakes
- WRONG: (a + b)² = a² + b²
- CORRECT: (a + b)² = a² + 2ab + b²
- WRONG: (ab)ⁿ = aⁿ + bⁿ
- CORRECT: (ab)ⁿ = aⁿ × bⁿ
- WRONG: a^(m+n) = a^m + a^n
- CORRECT: a^(m+n) = a^m × a^n

### Fraction Errors
- WRONG: (a + b)/c = a/(c + b)
- CORRECT: (a + b)/c = a/c + b/c
- WRONG: a/(b + c) = a/b + a/c
- CORRECT: a/(b + c) cannot be split this way

### Logarithm Mistakes
- WRONG: log(a + b) = log(a) + log(b)
- CORRECT: log(ab) = log(a) + log(b), but log(a + b) ≠ log(a) + log(b)
- WRONG: log(a)/log(b) = log(a/b)
- CORRECT: log(a)/log(b) = log_b(a) (change of base)
- TIP: log(a + b) has NO simplification. Never split a sum inside a log.

### Quadratic Formula Errors
- Forgetting to consider both + and - in the ± sign
- Miscalculating the discriminant
- Not setting the equation to = 0 before applying the formula
- Dividing only part of the numerator by 2a

## Calculus Mistakes

### Derivative Errors
- WRONG: d/dx [f(x)g(x)] = f'(x)g'(x)
- CORRECT: d/dx [f(x)g(x)] = f'(x)g(x) + f(x)g'(x) (Product Rule)
- WRONG: d/dx [f(g(x))] = f'(g(x))
- CORRECT: d/dx [f(g(x))] = f'(g(x)) × g'(x) (Chain Rule)

### Integration Errors
- Forgetting the constant of integration (+ C)
- Wrong sign in trigonometric integrals
- Not changing limits when doing u-substitution in definite integrals
- Forgetting to apply integration by parts correctly (common: wrong choice of u and dv)

### Limit Errors
- Applying L'Hôpital's rule when the form is NOT indeterminate
- L'Hôpital's rule: differentiating the quotient instead of differentiating numerator and denominator separately
- Not checking if left-hand and right-hand limits are equal

## Probability Mistakes

### Counting Errors
- Confusing permutations (order matters) with combinations (order doesn't matter)
- Double-counting outcomes
- Not identifying if events are with or without replacement

### Conditional Probability
- Confusing P(A|B) with P(B|A)
- Incorrectly assuming independence
- Forgetting to update the sample space when computing conditional probability

### Bayes' Theorem Errors
- Incorrectly computing P(B) in the denominator
- Not using the total probability theorem for P(B)

## Linear Algebra Mistakes

### Matrix Multiplication
- WRONG: AB = BA (matrix multiplication is NOT commutative in general)
- Multiplying matrices with incompatible dimensions
- Confusing dot product with element-wise multiplication

### Determinant Errors
- Sign errors in cofactor expansion
- Forgetting that row operations affect the determinant value
- Swapping rows without changing the sign of the determinant

### Inverse Matrix Errors
- Attempting to invert a singular matrix (det = 0)
- Wrong order of multiplication: (AB)⁻¹ = B⁻¹A⁻¹, NOT A⁻¹B⁻¹
- Errors in computing the adjoint matrix

### Eigenvalue Errors
- Forgetting to include the identity matrix (λI) in the characteristic equation
- Sign errors when expanding det(A - λI)
- Not verifying eigenvalues by checking Av = λv

## General Mathematical Mistakes

### Domain Restrictions
- Forgetting that √(x) requires x ≥ 0
- Forgetting that log(x) requires x > 0
- Forgetting that 1/x requires x ≠ 0
- Not checking for division by zero in intermediate steps

### Verification Checklist
1. Does the answer satisfy the original equation/condition?
2. Are all domain restrictions met?
3. Did you consider all cases (±)?
4. Does the answer make physical/geometric sense?
5. Are units consistent throughout?
