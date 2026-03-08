# Linear Algebra Formulas & Concepts

## Matrices

### Types of Matrices
- Square matrix: m × m
- Identity matrix (I): diagonal elements = 1, rest = 0
- Zero matrix (O): all elements = 0
- Diagonal matrix: non-diagonal elements = 0
- Upper triangular: elements below diagonal = 0
- Lower triangular: elements above diagonal = 0
- Symmetric: A = Aᵀ
- Skew-symmetric: Aᵀ = -A
- Orthogonal: AAᵀ = AᵀA = I

### Matrix Operations
- Addition: (A + B)ᵢⱼ = aᵢⱼ + bᵢⱼ (same dimensions required)
- Scalar multiplication: (kA)ᵢⱼ = k × aᵢⱼ
- Matrix multiplication: (AB)ᵢⱼ = Σ aᵢₖ × bₖⱼ
- Transpose: (Aᵀ)ᵢⱼ = aⱼᵢ

### Properties of Transpose
- (Aᵀ)ᵀ = A
- (A + B)ᵀ = Aᵀ + Bᵀ
- (kA)ᵀ = kAᵀ
- (AB)ᵀ = BᵀAᵀ

## Determinants

### 2×2 Determinant
det[a b; c d] = ad - bc

### 3×3 Determinant (Cofactor Expansion)
det(A) = a₁₁(a₂₂a₃₃ - a₂₃a₃₂) - a₁₂(a₂₁a₃₃ - a₂₃a₃₁) + a₁₃(a₂₁a₃₂ - a₂₂a₃₁)

### Properties of Determinants
- det(Aᵀ) = det(A)
- det(AB) = det(A) × det(B)
- det(kA) = kⁿ × det(A) for n×n matrix
- If one row/column is all zeros: det = 0
- Swapping two rows changes sign of det
- If two rows are identical: det = 0
- det(A⁻¹) = 1/det(A)

## Matrix Inverse

### Formula for 2×2
A⁻¹ = (1/det(A)) × [d -b; -c a]  for A = [a b; c d]

### Properties
- (A⁻¹)⁻¹ = A
- (AB)⁻¹ = B⁻¹A⁻¹
- (Aᵀ)⁻¹ = (A⁻¹)ᵀ
- (kA)⁻¹ = (1/k)A⁻¹
- A is invertible ⟺ det(A) ≠ 0

### Adjoint Method
A⁻¹ = adj(A) / det(A)
adj(A) = transpose of cofactor matrix

## System of Linear Equations

### Cramer's Rule
For AX = B where A is n×n:
xᵢ = det(Aᵢ) / det(A)
where Aᵢ is A with column i replaced by B.

### Conditions for Solutions
- Unique solution: det(A) ≠ 0
- No solution or infinite solutions: det(A) = 0
- For homogeneous system AX = 0:
  - det(A) ≠ 0: only trivial solution (X = 0)
  - det(A) = 0: non-trivial solutions exist

### Rank
- rank(A) = number of non-zero rows in row echelon form
- rank(A) ≤ min(m, n)
- rank(A) = rank(Aᵀ)
- For AX = B (m equations, n unknowns):
  - rank(A) = rank(A|B) = n: unique solution
  - rank(A) = rank(A|B) < n: infinite solutions
  - rank(A) ≠ rank(A|B): no solution

## Eigenvalues & Eigenvectors

### Definition
Av = λv where λ is eigenvalue, v is eigenvector

### Finding Eigenvalues
Solve det(A - λI) = 0 (characteristic equation)

### Properties
- Sum of eigenvalues = trace(A) = Σ aᵢᵢ
- Product of eigenvalues = det(A)
- Eigenvalues of Aⁿ are λⁿ
- Eigenvalues of A⁻¹ are 1/λ
- Eigenvalues of A + kI are λ + k

## Vectors

### Dot Product
a · b = |a| × |b| × cos(θ) = a₁b₁ + a₂b₂ + a₃b₃

### Cross Product
a × b = |a| × |b| × sin(θ) × n̂
|a × b| = area of parallelogram formed by a and b

### Properties
- a · b = 0 ⟹ a ⊥ b (perpendicular)
- a × b = 0 ⟹ a ∥ b (parallel)
- Scalar triple product: a · (b × c) = volume of parallelepiped
