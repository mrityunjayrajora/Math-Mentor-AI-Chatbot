'use client';
import { useState, useEffect } from 'react';
import { getPendingReviews, submitReview } from '@/lib/api';
import styles from './page.module.css';

export default function ReviewPage() {
    const [pending, setPending] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedItem, setSelectedItem] = useState(null);
    const [correctedText, setCorrectedText] = useState('');
    const [correctedAnswer, setCorrectedAnswer] = useState('');
    const [feedback, setFeedback] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const fetchPending = async () => {
        setLoading(true);
        try {
            const data = await getPendingReviews();
            setPending(data);
        } catch {
            console.error('Failed to fetch pending reviews');
        }
        setLoading(false);
    };

    useEffect(() => { fetchPending(); }, []);

    const handleAction = async (action) => {
        if (!selectedItem) return;
        setSubmitting(true);
        try {
            await submitReview({
                sessionId: selectedItem.session_id,
                action,
                correctedText: action === 'correct' ? correctedText : undefined,
                correctedAnswer: action === 'correct' ? correctedAnswer : undefined,
                feedback: feedback || undefined,
            });
            setSelectedItem(null);
            setCorrectedText('');
            setCorrectedAnswer('');
            setFeedback('');
            fetchPending();
        } catch (err) {
            alert('Review failed: ' + err.message);
        }
        setSubmitting(false);
    };

    const selectItem = (item) => {
        setSelectedItem(item);
        setCorrectedText(item.extracted_text || '');
        setCorrectedAnswer(item.solution?.final_answer || '');
        setFeedback('');
    };

    return (
        <div className={styles.page}>
            <div className={styles.header}>
                <h1>
                    <span>👁️</span>
                    Human-in-the-Loop Review
                </h1>
                <p className="text-muted">Review items flagged for human verification</p>
            </div>

            {loading ? (
                <div className={styles.loadingState}>
                    <div className="spinner" style={{ width: 28, height: 28, borderTopColor: 'var(--accent-purple)' }}></div>
                    <p className="text-muted">Loading pending reviews...</p>
                </div>
            ) : pending.length === 0 ? (
                <div className={styles.emptyState}>
                    <div style={{ fontSize: '3rem', marginBottom: 12 }}>✅</div>
                    <h3>All Clear!</h3>
                    <p className="text-muted">No items pending review</p>
                </div>
            ) : (
                <div className={styles.layout}>
                    {/* Pending Items List */}
                    <div className={styles.list}>
                        <h3 className={styles.listTitle}>
                            Pending ({pending.length})
                        </h3>
                        {pending.map((item) => (
                            <button
                                key={item.session_id}
                                className={`${styles.listItem} ${selectedItem?.session_id === item.session_id ? styles.selected : ''}`}
                                onClick={() => selectItem(item)}
                            >
                                <div className="flex items-center gap-1 mb-1 flex-wrap">
                                    {item.reasons?.map((r, i) => (
                                        <span className="badge badge-amber" key={i} style={{ fontSize: '0.68rem' }}>
                                            {r.replace(/_/g, ' ')}
                                        </span>
                                    ))}
                                </div>
                                <p className={styles.listItemText}>
                                    {item.extracted_text?.substring(0, 80) || 'No text'}
                                    {item.extracted_text?.length > 80 ? '...' : ''}
                                </p>
                                <span className="text-muted" style={{ fontSize: '0.7rem' }}>
                                    {item.session_id.substring(0, 8)}...
                                </span>
                            </button>
                        ))}
                    </div>

                    {/* Review Panel */}
                    <div className={styles.reviewPanel}>
                        {!selectedItem ? (
                            <div className={styles.selectPrompt}>
                                <p className="text-muted">← Select an item to review</p>
                            </div>
                        ) : (
                            <div className="fade-in">
                                {/* Extracted Text */}
                                <div className={styles.reviewCard}>
                                    <div className={styles.reviewCardHeader}>
                                        <span>📄</span>
                                        <h3>Extracted Text</h3>
                                    </div>
                                    <div className={styles.extractedBox}>
                                        {selectedItem.extracted_text}
                                    </div>
                                </div>

                                {/* Parsed Problem */}
                                {selectedItem.parsed_problem && (
                                    <div className={styles.reviewCard}>
                                        <div className={styles.reviewCardHeader}>
                                            <span>🧩</span>
                                            <h3>Parsed Problem</h3>
                                        </div>
                                        <p style={{ fontSize: '0.875rem' }}>{selectedItem.parsed_problem.problem_text}</p>
                                        <div className="flex gap-1 flex-wrap mt-1">
                                            <span className="badge badge-purple">{selectedItem.parsed_problem.topic}</span>
                                        </div>
                                    </div>
                                )}

                                {/* Solution */}
                                {selectedItem.solution && (
                                    <div className={styles.reviewCard}>
                                        <div className={styles.reviewCardHeader}>
                                            <span>✅</span>
                                            <h3>Current Solution</h3>
                                        </div>
                                        <div className={styles.solutionBox}>
                                            {selectedItem.solution.final_answer}
                                        </div>
                                    </div>
                                )}

                                {/* Correction Form */}
                                <div className={styles.reviewCard}>
                                    <div className={styles.reviewCardHeader}>
                                        <span>✏️</span>
                                        <h3>Corrections</h3>
                                    </div>
                                    <div className={styles.formFields}>
                                        <div>
                                            <label className={styles.fieldLabel}>Corrected Text</label>
                                            <textarea
                                                className="input"
                                                value={correctedText}
                                                onChange={(e) => setCorrectedText(e.target.value)}
                                                rows={3}
                                            />
                                        </div>
                                        <div>
                                            <label className={styles.fieldLabel}>Corrected Answer</label>
                                            <input
                                                className="input"
                                                value={correctedAnswer}
                                                onChange={(e) => setCorrectedAnswer(e.target.value)}
                                            />
                                        </div>
                                        <div>
                                            <label className={styles.fieldLabel}>Feedback / Notes</label>
                                            <textarea
                                                className="input"
                                                placeholder="Optional feedback..."
                                                value={feedback}
                                                onChange={(e) => setFeedback(e.target.value)}
                                                rows={2}
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Action Buttons */}
                                <div className={styles.actionButtons}>
                                    <button className="btn btn-success" onClick={() => handleAction('approve')} disabled={submitting}>
                                        ✅ Approve
                                    </button>
                                    <button className="btn btn-danger" onClick={() => handleAction('reject')} disabled={submitting}>
                                        ❌ Reject
                                    </button>
                                    <button className="btn btn-primary" onClick={() => handleAction('correct')} disabled={submitting}>
                                        ✏️ Submit Correction
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
