'use client';
import { useState } from 'react';
import { submitFeedback } from '@/lib/api';
import styles from './ResultsPanel.module.css';

function ConfidenceMeter({ value }) {
    const pct = Math.round(value * 100);
    const circumference = 2 * Math.PI * 34;
    const offset = circumference - (pct / 100) * circumference;
    const color = pct >= 80 ? 'var(--accent-green)' : pct >= 50 ? 'var(--accent-amber)' : 'var(--accent-red)';

    return (
        <div className="confidence-meter">
            <svg width="80" height="80" viewBox="0 0 76 76">
                <circle className="track" cx="38" cy="38" r="34" />
                <circle className="fill" cx="38" cy="38" r="34"
                    stroke={color}
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                />
            </svg>
            <div className="label" style={{ color }}>{pct}%</div>
        </div>
    );
}

function AgentTrace({ trace }) {
    const [open, setOpen] = useState(false);

    const agentInfo = {
        'Input Handler': { icon: '📥', color: '#0891b2', desc: 'Received and processed the input' },
        'Memory': { icon: '🧠', color: '#d97706', desc: 'Checked past solutions for similar problems' },
        'Parser Agent': { icon: '🔍', color: '#059669', desc: 'Identified math topic, variables, and structure' },
        'Intent Router Agent': { icon: '🧭', color: '#3b82f6', desc: 'Determined solving strategy and tools needed' },
        'Solver Agent': { icon: '🧮', color: '#7c3aed', desc: 'Computed the step-by-step solution' },
        'Verifier Agent': { icon: '✅', color: '#dc2626', desc: 'Verified the solution correctness' },
        'Explainer Agent': { icon: '🎓', color: '#8b5cf6', desc: 'Generated student-friendly explanation' },
        'RAG Retriever': { icon: '📚', color: '#0891b2', desc: 'Retrieved relevant knowledge from textbooks' },
    };

    return (
        <div className={styles.traceCard}>
            <button className={styles.collapseBtn} onClick={() => setOpen(!open)}>
                <div className={styles.collapseBtnLeft}>
                    <span>🔬</span>
                    <span>How it was solved</span>
                    <span className="badge badge-purple">{trace.length} steps</span>
                </div>
                <span style={{ transform: open ? 'rotate(180deg)' : '', transition: 'var(--transition-fast)', fontSize: '0.8rem' }}>▾</span>
            </button>
            {open && (
                <div className="timeline fade-in" style={{ marginTop: 16 }}>
                    {trace.map((step, i) => {
                        const info = agentInfo[step.agent_name] || { icon: '⚙️', color: '#7c3aed', desc: '' };
                        return (
                            <div className="timeline-item" key={i}>
                                <div className="timeline-dot" style={{ background: info.color, color: 'white', fontSize: '0.8rem' }}>
                                    {info.icon}
                                </div>
                                <div className="timeline-content">
                                    <h4>{step.agent_name}</h4>
                                    <p>{step.action}</p>
                                    {info.desc && (
                                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic', marginTop: 2 }}>
                                            {info.desc}
                                        </p>
                                    )}
                                    <div className="flex gap-1 mt-1" style={{ flexWrap: 'wrap' }}>
                                        {step.duration_ms > 0 && (
                                            <span className="badge badge-blue">{Math.round(step.duration_ms)}ms</span>
                                        )}
                                        <span className={`badge ${step.success ? 'badge-green' : 'badge-red'}`}>
                                            {step.success ? '✓ Success' : '✗ Failed'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

function RetrievedContext({ chunks }) {
    const [open, setOpen] = useState(false);
    if (!chunks || chunks.length === 0) return null;

    return (
        <div className={styles.traceCard}>
            <button className={styles.collapseBtn} onClick={() => setOpen(!open)}>
                <div className={styles.collapseBtnLeft}>
                    <span>📚</span>
                    <span>Knowledge Sources</span>
                    <span className="badge badge-cyan">{chunks.length} sources</span>
                </div>
                <span style={{ transform: open ? 'rotate(180deg)' : '', transition: 'var(--transition-fast)', fontSize: '0.8rem' }}>▾</span>
            </button>
            {open && (
                <div className="fade-in" style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {chunks.map((chunk, i) => (
                        <div className="step-card" key={i}>
                            <div className="flex items-center gap-1 mb-1">
                                <span className="badge badge-cyan">{chunk.source}</span>
                                <span className="badge badge-purple">{(chunk.score * 100).toFixed(0)}% match</span>
                            </div>
                            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                                {chunk.content}
                            </p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default function ResultsPanel({ result }) {
    const [feedbackSent, setFeedbackSent] = useState(false);
    const [feedbackComment, setFeedbackComment] = useState('');
    const [showFeedback, setShowFeedback] = useState(false);

    const handleFeedback = async (isCorrect) => {
        try {
            await submitFeedback({
                sessionId: result.session_id,
                isCorrect,
                comment: feedbackComment,
            });
            setFeedbackSent(true);
        } catch {
            alert('Failed to submit feedback');
        }
    };

    return (
        <div className={`${styles.results} fade-in`}>
            {/* HITL Banner */}
            {result.hitl_required && (
                <div className="hitl-banner">
                    <span style={{ fontSize: '1.3rem' }}>⚠️</span>
                    <div style={{ flex: 1 }}>
                        <strong style={{ color: 'var(--accent-amber)' }}>Human Review Recommended</strong>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                            {result.hitl_reasons?.map((r) => r.replace(/_/g, ' ')).join(', ')}
                        </p>
                    </div>
                    <a href="/review" className="btn btn-ghost btn-sm">Review →</a>
                </div>
            )}

            {/* Memory match banner */}
            {result.memory_similar_problems?.length > 0 && result.memory_similar_problems[0]?.similarity > 0.85 && (
                <div className={styles.memoryBanner}>
                    <span style={{ fontSize: '1.2rem' }}>🧠</span>
                    <div style={{ flex: 1 }}>
                        <strong>Answered from Memory</strong>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                            A very similar problem was solved before ({Math.round(result.memory_similar_problems[0].similarity * 100)}% match)
                        </p>
                    </div>
                </div>
            )}

            {/* ═══ QUESTION ═══ */}
            <div className={styles.questionCard}>
                <div className={styles.sectionLabel}>
                    <span>📋</span> Question
                </div>
                <div className={styles.questionText}>
                    <code>{result.extracted_text}</code>
                </div>
                {result.parsed_problem && (
                    <div className="flex gap-1 flex-wrap mt-1">
                        <span className="badge badge-purple">{result.parsed_problem.topic}</span>
                        {result.parsed_problem.sub_type && (
                            <span className="badge badge-blue">{result.parsed_problem.sub_type}</span>
                        )}
                        {result.parsed_problem.variables?.map((v) => (
                            <span className="badge badge-cyan" key={v}>{v}</span>
                        ))}
                    </div>
                )}
            </div>

            {/* ═══ ANSWER ═══ */}
            {result.solution && (
                <div className={styles.finalAnswer}>
                    <div className={styles.answerBadge}>ANSWER</div>
                    <span className={styles.answerValue}>{result.solution.final_answer}</span>
                </div>
            )}

            {/* Verification */}
            {result.verification && (
                <div className={styles.verificationCard}>
                    <div className="flex items-center gap-1">
                        <span style={{ fontSize: '1rem' }}>
                            {result.verification.is_correct ? '✅' : '⚠️'}
                        </span>
                        <strong style={{ fontSize: '0.9rem' }}>
                            Verification: {result.verification.is_correct ? 'Correct' : 'Check Needed'}
                        </strong>
                        <span className={`badge ${result.verification.is_correct ? 'badge-green' : 'badge-amber'}`} style={{ marginLeft: 'auto' }}>
                            {Math.round(result.verification.confidence * 100)}% confident
                        </span>
                    </div>
                    {result.verification.method && (
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: 6 }}>
                            Method: {result.verification.method}
                        </p>
                    )}
                </div>
            )}

            {/* ═══ EXPLANATION ═══ */}
            {result.explanation && (
                <div className={styles.explanationCard}>
                    <div className={styles.sectionLabel}>
                        <span>🎓</span> Step-by-Step Explanation
                    </div>

                    <div className={styles.explanationSummary}>
                        {result.explanation.summary}
                    </div>

                    {/* Detailed Steps — MAIN CONTENT */}
                    {result.explanation.detailed_steps?.length > 0 && (
                        <div className={styles.detailedSteps}>
                            {result.explanation.detailed_steps.map((step, i) => (
                                <div className={styles.detailedStep} key={i}>
                                    <span className={styles.detailedStepNum}>{i + 1}</span>
                                    <p>{step}</p>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Key Concepts */}
                    {result.explanation.key_concepts?.length > 0 && (
                        <div className={styles.explanationSection}>
                            <div className={styles.expSectionHeader}>
                                <span className={styles.expIcon}>💡</span>
                                <h4>Key Concepts</h4>
                            </div>
                            <div className="flex gap-1 flex-wrap">
                                {result.explanation.key_concepts.map((c) => (
                                    <span className={styles.conceptPill} key={c}>{c}</span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Common Mistakes & Tips — compact */}
                    {(result.explanation.common_mistakes?.length > 0 || result.explanation.tips?.length > 0) && (
                        <div className={styles.compactHints}>
                            {result.explanation.common_mistakes?.length > 0 && (
                                <div className={styles.hintBox}>
                                    <span>⚠️</span>
                                    <div>
                                        <strong>Watch Out</strong>
                                        <ul className={styles.expList}>
                                            {result.explanation.common_mistakes.map((m, i) => (
                                                <li key={i}>{m}</li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            )}
                            {result.explanation.tips?.length > 0 && (
                                <div className={styles.hintBox}>
                                    <span>🌟</span>
                                    <div>
                                        <strong>Pro Tips</strong>
                                        <ul className={styles.expList}>
                                            {result.explanation.tips.map((t, i) => (
                                                <li key={i}>{t}</li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Agent Trace */}
            {result.agent_trace && <AgentTrace trace={result.agent_trace} />}

            {/* Retrieved Context */}
            <RetrievedContext chunks={result.retrieved_context} />

            {/* ═══ FEEDBACK ═══ */}
            <div className={styles.feedbackCard}>
                <div className={styles.sectionLabel}>
                    <span>💬</span> Was this helpful?
                </div>
                {!feedbackSent ? (
                    <div>
                        <div className="flex gap-1">
                            <button className="btn btn-success btn-sm" onClick={() => handleFeedback(true)}>
                                👍 Correct
                            </button>
                            <button className="btn btn-danger btn-sm" onClick={() => setShowFeedback(true)}>
                                👎 Incorrect
                            </button>
                        </div>
                        {showFeedback && (
                            <div className="mt-1 fade-in">
                                <textarea
                                    className="input"
                                    placeholder="What was wrong? (optional)"
                                    value={feedbackComment}
                                    onChange={(e) => setFeedbackComment(e.target.value)}
                                    rows={2}
                                />
                                <button className="btn btn-danger btn-sm mt-1" onClick={() => handleFeedback(false)}>
                                    Submit Feedback
                                </button>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className={styles.feedbackSuccess}>
                        <span>✅</span>
                        <p>Thank you! Your feedback helps Math Mentor learn and improve.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
