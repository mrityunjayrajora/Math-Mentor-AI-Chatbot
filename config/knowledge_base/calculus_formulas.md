# Calculus Formulas & Concepts

## Limits

### Basic Limit Laws
- lim[f(x) ± g(x)] = lim f(x) ± lim g(x)
- lim[f(x) × g(x)] = lim f(x) × lim g(x)
- lim[f(x) / g(x)] = lim f(x) / lim g(x), if lim g(x) ≠ 0
- lim[c × f(x)] = c × lim f(x)

### Important Standard Limits
- lim(x→0) sin(x)/x = 1
- lim(x→0) (1 - cos(x))/x² = 1/2
- lim(x→0) tan(x)/x = 1
- lim(x→0) (eˣ - 1)/x = 1
- lim(x→0) (aˣ - 1)/x = ln(a)
- lim(x→0) ln(1 + x)/x = 1
- lim(x→0) (1 + x)^(1/x) = e
- lim(x→∞) (1 + 1/x)^x = e
- lim(x→∞) (1 + a/x)^(bx) = e^(ab)

### L'Hôpital's Rule
If lim f(x)/g(x) gives 0/0 or ∞/∞:
lim f(x)/g(x) = lim f'(x)/g'(x)
Can be applied repeatedly if the indeterminate form persists.

### Squeeze Theorem (Sandwich Theorem)
If g(x) ≤ f(x) ≤ h(x) near a, and lim g(x) = lim h(x) = L, then lim f(x) = L.

## Derivatives

### Basic Differentiation Rules
- d/dx [c] = 0      (constant)
- d/dx [xⁿ] = nxⁿ⁻¹   (power rule)
- d/dx [eˣ] = eˣ
- d/dx [aˣ] = aˣ × ln(a)
- d/dx [ln(x)] = 1/x
- d/dx [log_a(x)] = 1/(x × ln(a))

### Trigonometric Derivatives
- d/dx [sin(x)] = cos(x)
- d/dx [cos(x)] = -sin(x)
- d/dx [tan(x)] = sec²(x)
- d/dx [cot(x)] = -csc²(x)
- d/dx [sec(x)] = sec(x)tan(x)
- d/dx [csc(x)] = -csc(x)cot(x)

### Inverse Trigonometric Derivatives
- d/dx [sin⁻¹(x)] = 1/√(1 - x²)
- d/dx [cos⁻¹(x)] = -1/√(1 - x²)
- d/dx [tan⁻¹(x)] = 1/(1 + x²)

### Differentiation Rules
- Product Rule: d/dx [f(x)g(x)] = f'(x)g(x) + f(x)g'(x)
- Quotient Rule: d/dx [f(x)/g(x)] = [f'(x)g(x) - f(x)g'(x)] / [g(x)]²
- Chain Rule: d/dx [f(g(x))] = f'(g(x)) × g'(x)

### Higher Order Derivatives
- Leibniz Rule: (fg)⁽ⁿ⁾ = Σ C(n,k) × f⁽ᵏ⁾ × g⁽ⁿ⁻ᵏ⁾

## Applications of Derivatives

### Maxima and Minima
- First Derivative Test: f'(x) changes sign at critical point
  - f'(x) changes from + to -: local maximum
  - f'(x) changes from - to +: local minimum
- Second Derivative Test:
  - f''(c) < 0: local maximum at x = c
  - f''(c) > 0: local minimum at x = c
  - f''(c) = 0: test is inconclusive

### Tangent and Normal
- Slope of tangent at (x₀, y₀): m = f'(x₀)
- Equation of tangent: y - y₀ = f'(x₀)(x - x₀)
- Slope of normal: -1/f'(x₀)
- Equation of normal: y - y₀ = -1/f'(x₀) × (x - x₀)

### Rate of Change
- Average rate of change: [f(b) - f(a)] / (b - a)
- Instantaneous rate of change: f'(a)

### Rolle's Theorem
If f is continuous on [a,b], differentiable on (a,b), and f(a) = f(b),
then there exists c ∈ (a,b) such that f'(c) = 0.

### Mean Value Theorem
If f is continuous on [a,b] and differentiable on (a,b),
then there exists c ∈ (a,b) such that f'(c) = [f(b) - f(a)] / (b - a).

## Integration

### Basic Integration Rules
- ∫ xⁿ dx = x^(n+1)/(n+1) + C, n ≠ -1
- ∫ 1/x dx = ln|x| + C
- ∫ eˣ dx = eˣ + C
- ∫ aˣ dx = aˣ/ln(a) + C

### Trigonometric Integrals
- ∫ sin(x) dx = -cos(x) + C
- ∫ cos(x) dx = sin(x) + C
- ∫ sec²(x) dx = tan(x) + C
- ∫ csc²(x) dx = -cot(x) + C
- ∫ sec(x)tan(x) dx = sec(x) + C
- ∫ csc(x)cot(x) dx = -csc(x) + C

### Integration Techniques
- Substitution: ∫ f(g(x))g'(x) dx = ∫ f(u) du
- By Parts: ∫ u dv = uv - ∫ v du (LIATE rule for choosing u)
- Partial Fractions: decompose rational functions

### Definite Integrals
- ∫ₐᵇ f(x) dx = F(b) - F(a), where F'(x) = f(x)
- Properties:
  - ∫ₐᵇ f(x) dx = -∫ᵇₐ f(x) dx
  - ∫ₐᵇ f(x) dx = ∫ₐᶜ f(x) dx + ∫ᶜᵇ f(x) dx
  - ∫₋ₐᵃ f(x) dx = 2∫₀ᵃ f(x) dx if f is even
  - ∫₋ₐᵃ f(x) dx = 0 if f is odd
