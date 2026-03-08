# Solution Templates

## Standard Approaches by Problem Type

### Template: Solving Quadratic Equations
1. Identify the equation in standard form: ax² + bx + c = 0
2. Calculate the discriminant: D = b² - 4ac
3. If D ≥ 0: x = (-b ± √D) / (2a)
4. If D < 0: Complex roots: x = (-b ± i√|D|) / (2a)
5. Verify by substituting roots back into the original equation
6. Check: sum of roots = -b/a, product of roots = c/a

### Template: Solving Systems of Linear Equations
1. Write the system in matrix form AX = B
2. Calculate det(A)
3. If det(A) ≠ 0: Use Cramer's rule or matrix inverse
   - X = A⁻¹B
   - Or apply Cramer's rule: xᵢ = det(Aᵢ)/det(A)
4. If det(A) = 0: Check consistency
   - Compare rank(A) with rank(A|B)
5. Verify solution by substituting back

### Template: Finding Derivatives
1. Identify the function type and applicable rules
2. Apply differentiation rules in order:
   - Power rule for polynomial terms
   - Chain rule for composite functions
   - Product/quotient rule for products/quotients
3. Simplify the result
4. Verify by checking a specific point or using alternative method

### Template: Computing Limits
1. Try direct substitution first
2. If indeterminate form (0/0, ∞/∞):
   a. Try factoring and canceling
   b. Try L'Hôpital's rule
   c. Try rationalization (for square root expressions)
   d. Try standard limits
3. If form 0 × ∞: rewrite as 0/0 or ∞/∞
4. If form 1^∞: use lim = e^(lim (f-1)×g)
5. Verify by checking left and right limits

### Template: Integration
1. Identify the integral type
2. Choose appropriate technique:
   - Direct formula if recognizable
   - Substitution: look for f(g(x))g'(x) pattern
   - By parts: use LIATE rule (Log, Inverse trig, Algebraic, Trig, Exponential)
   - Partial fractions: for rational functions
   - Trigonometric substitution: for √(a²-x²), √(a²+x²), √(x²-a²)
3. Evaluate and simplify
4. For definite integrals: apply limits
5. Verify by differentiating the result

### Template: Probability Problems
1. Identify the sample space and events
2. Determine if events are independent, mutually exclusive, or conditional
3. Choose the appropriate formula:
   - Basic: P(A) = favorable/total
   - Addition: P(A∪B) = P(A) + P(B) - P(A∩B)
   - Multiplication: P(A∩B) = P(A) × P(B|A)
   - Bayes: P(A|B) = P(B|A)×P(A) / P(B)
4. Count outcomes using permutations/combinations if needed
5. Verify that 0 ≤ P ≤ 1 and probabilities sum correctly

### Template: Matrix Operations
1. Verify dimensions are compatible for the operation
2. For determinant: use cofactor expansion or row reduction
3. For inverse: check det ≠ 0, then use adj(A)/det(A) or row reduction
4. For eigenvalues: solve det(A - λI) = 0
5. For eigenvectors: solve (A - λI)v = 0 for each eigenvalue
6. Verify: Av = λv for each eigenvalue-eigenvector pair

### Template: Optimization
1. Define the objective function f(x)
2. Find critical points: solve f'(x) = 0
3. Apply second derivative test or first derivative test
4. Check boundary values if domain is restricted
5. Compare all critical values and boundary values
6. State the maximum/minimum value and where it occurs
