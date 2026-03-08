'use client';
import { useState } from 'react';
import InputPanel from '@/components/solve/InputPanel';
import ConfirmationPanel from '@/components/solve/ConfirmationPanel';
import ResultsPanel from '@/components/solve/ResultsPanel';
import { solveProblem } from '@/lib/api';
import styles from './page.module.css';

/**
 * Solve Page — Main flow:
 * 1. idle        → user enters input
 * 2. extracting  → backend processing
 * 3. confirming  → show extracted text for HITL confirmation
 * 4. solving     → user confirmed, showing solution
 * 5. done        → results displayed
 */
export default function SolvePage() {
  const [phase, setPhase] = useState('idle'); // idle | extracting | confirming | done
  const [result, setResult] = useState(null);
  const [multiResults, setMultiResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastInput, setLastInput] = useState(null);

  const handleSolve = async (inputData) => {
    setLoading(true);
    setError(null);
    setPhase('extracting');
    setLastInput(inputData);
    setMultiResults([]);

    try {
      const response = await solveProblem(inputData);
      setResult(response);

      // If from memory, skip confirmation — show answer instantly
      if (response.memory_similar_problems?.length > 0 &&
        response.memory_similar_problems[0]?.similarity > 0.85) {
        setPhase('done');
      } else {
        // Always show HITL confirmation step
        setPhase('confirming');
      }
    } catch (err) {
      setError(err.message);
      setPhase('idle');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = () => {
    // User confirmed the extracted text - show the solution
    setPhase('done');
  };

  const handleEdit = async (editedText) => {
    // Re-solve with the corrected text
    setLoading(true);
    setError(null);

    try {
      const response = await solveProblem({
        inputMode: 'text',
        text: editedText,
      });
      setResult(response);
      setPhase('done');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectProblems = async (selectedProblems) => {
    // Solve selected problems sequentially
    setLoading(true);
    setError(null);
    const results = [];
    for (const problemText of selectedProblems) {
      try {
        const res = await solveProblem({ inputMode: 'text', text: problemText });
        results.push(res);
      } catch (err) {
        results.push({ error: err.message, extracted_text: problemText });
      }
    }
    setMultiResults(results);
    if (results.length === 1) setResult(results[0]);
    setPhase('done');
    setLoading(false);
  };

  const handleNewProblem = () => {
    setPhase('idle');
    setResult(null);
    setMultiResults([]);
    setError(null);
    setLastInput(null);
  };

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerTop}>
          <div>
            <h1 className={styles.title}>
              <span className={styles.titleIcon}>✨</span>
              Solve a Problem
            </h1>
            <p className={styles.subtitle}>
              Enter a math problem via text, image, or voice — I&apos;ll solve it step by step.
            </p>
          </div>
          {phase !== 'idle' && (
            <button className="btn btn-ghost" onClick={handleNewProblem}>
              ✕ New Problem
            </button>
          )}
        </div>

        {/* Progress steps */}
        <div className={styles.progressBar}>
          <div className={`${styles.progressStep} ${phase !== 'idle' ? styles.progressActive : ''}`}>
            <div className={styles.progressDot}>1</div>
            <span>Input</span>
          </div>
          <div className={styles.progressLine} />
          <div className={`${styles.progressStep} ${phase === 'confirming' || phase === 'done' ? styles.progressActive : ''}`}>
            <div className={styles.progressDot}>2</div>
            <span>Confirm</span>
          </div>
          <div className={styles.progressLine} />
          <div className={`${styles.progressStep} ${phase === 'done' ? styles.progressActive : ''}`}>
            <div className={styles.progressDot}>3</div>
            <span>Solution</span>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className={`card fade-in ${styles.errorCard}`}>
          <p>⚠️ {error}</p>
        </div>
      )}

      {/* Phase: Input */}
      {phase === 'idle' && (
        <div className={styles.contentArea}>
          <InputPanel onSolve={handleSolve} loading={loading} />
        </div>
      )}

      {/* Phase: Extracting */}
      {phase === 'extracting' && (
        <div className={styles.loadingState}>
          <div className={styles.loadingCard}>
            <div className={styles.loadingSpinner}>
              <div className="spinner" style={{ width: 36, height: 36, borderTopColor: 'var(--accent-purple)' }}></div>
            </div>
            <h3>Analyzing your problem...</h3>
            <p className="text-muted" style={{ fontSize: '0.85rem' }}>
              Extracting and parsing the math problem
            </p>
            <div className={styles.loadingSteps}>
              <span className={styles.loadingStepActive}>📝 Extracting text</span>
              <span>🔍 Parsing problem</span>
              <span>🧠 Checking memory</span>
              <span>📐 Solving</span>
            </div>
          </div>
        </div>
      )}

      {/* Phase: Confirming */}
      {phase === 'confirming' && result && (
        <div className={styles.contentArea}>
          <ConfirmationPanel
            result={result}
            onConfirm={handleConfirm}
            onEdit={handleEdit}
            onSelectProblems={handleSelectProblems}
            loading={loading}
          />
        </div>
      )}

      {/* Phase: Done — show results */}
      {phase === 'done' && (
        <div className={styles.contentArea}>
          {multiResults.length > 1 ? (
            multiResults.map((res, i) => (
              <div key={i} style={{ marginBottom: 24 }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: 8 }}>
                  Problem {i + 1} of {multiResults.length}
                </div>
                {res.error ? (
                  <div className="card"><p>⚠️ {res.error}</p></div>
                ) : (
                  <ResultsPanel result={res} />
                )}
              </div>
            ))
          ) : result ? (
            <ResultsPanel result={result} />
          ) : null}
        </div>
      )}

      {/* Empty state hint */}
      {phase === 'idle' && !error && (
        <div className={styles.hints}>
          <h4>Try these examples:</h4>
          <div className={styles.hintGrid}>
            <div className={styles.hintCard}>
              <span className={styles.hintIcon}>📐</span>
              <span>Solve x² - 5x + 6 = 0</span>
            </div>
            <div className={styles.hintCard}>
              <span className={styles.hintIcon}>📊</span>
              <span>Find the derivative of sin(x²)</span>
            </div>
            <div className={styles.hintCard}>
              <span className={styles.hintIcon}>🎲</span>
              <span>Probability of rolling a sum of 7 with two dice</span>
            </div>
            <div className={styles.hintCard}>
              <span className={styles.hintIcon}>📏</span>
              <span>Explain the Pythagorean theorem</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
