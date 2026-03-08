'use client';
import { useState } from 'react';
import styles from './ConfirmationPanel.module.css';

export default function ConfirmationPanel({ result, onConfirm, onEdit, onSelectProblems, loading }) {
    const [editMode, setEditMode] = useState(false);
    const [editedText, setEditedText] = useState(result?.extracted_text || '');
    const [selectedProblems, setSelectedProblems] = useState([]);

    const confidence = result?.extraction_confidence || 0;
    const pct = Math.round(confidence * 100);
    const isLowConfidence = confidence < 0.8;

    const detectedProblems = result?.parsed_problem?.detected_problems || [];
    const isMultiProblem = detectedProblems.length > 1;
    const needsClarification = result?.parsed_problem?.needs_clarification && !isMultiProblem;

    const handleConfirm = () => {
        onConfirm();
    };

    const handleEditSubmit = () => {
        onEdit(editedText);
    };

    const toggleProblem = (idx) => {
        setSelectedProblems((prev) =>
            prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]
        );
    };

    const selectAll = () => {
        setSelectedProblems(detectedProblems.map((_, i) => i));
    };

    const handleSolveSelected = () => {
        const chosen = selectedProblems.map((i) => detectedProblems[i]);
        if (onSelectProblems) onSelectProblems(chosen);
    };

    return (
        <div className={`${styles.panel} fade-in`}>
            <div className={styles.header}>
                <div className={styles.headerIcon}>
                    {isMultiProblem ? '📋' : needsClarification ? '❓' : '🔍'}
                </div>
                <div className={styles.headerText}>
                    <h3>
                        {isMultiProblem
                            ? 'Multiple Problems Detected'
                            : needsClarification
                                ? 'Clarification Needed'
                                : 'Review Detected Problem'}
                    </h3>
                    <p>
                        {isMultiProblem
                            ? 'Select which problems you\'d like to solve.'
                            : needsClarification
                                ? result?.parsed_problem?.clarification_reason || 'The input needs clarification.'
                                : 'Please confirm the math problem below is correct before solving.'}
                    </p>
                </div>
            </div>

            {/* Confidence indicator */}
            <div className={`${styles.confidenceBar} ${isLowConfidence ? styles.lowConfidence : styles.highConfidence}`}>
                <div className={styles.confidenceInfo}>
                    <span className={styles.confidenceLabel}>
                        {isLowConfidence ? '⚠️ Low confidence' : '✅ High confidence'} detection
                    </span>
                    <span className={styles.confidencePct}>{pct}%</span>
                </div>
                <div className={styles.confidenceTrack}>
                    <div className={styles.confidenceFill} style={{ width: `${pct}%` }} />
                </div>
            </div>

            {/* Multi-problem selection */}
            {isMultiProblem ? (
                <div className={styles.multiProblemBox}>
                    <div className={styles.multiHeader}>
                        <span className={styles.extractedLabel}>
                            {detectedProblems.length} problems found
                        </span>
                        <button
                            className="btn btn-ghost btn-sm"
                            onClick={selectAll}
                            type="button"
                        >
                            Select All
                        </button>
                    </div>
                    <div className={styles.problemList}>
                        {detectedProblems.map((prob, i) => (
                            <label
                                className={`${styles.problemItem} ${selectedProblems.includes(i) ? styles.problemSelected : ''}`}
                                key={i}
                            >
                                <input
                                    type="checkbox"
                                    checked={selectedProblems.includes(i)}
                                    onChange={() => toggleProblem(i)}
                                    className={styles.problemCheckbox}
                                />
                                <span className={styles.problemNum}>{i + 1}</span>
                                <span>{prob}</span>
                            </label>
                        ))}
                    </div>
                </div>
            ) : (
                /* Single problem view */
                <>
                    {/* Detected topic badges */}
                    {result?.parsed_problem && (
                        <div className={styles.topicBadges}>
                            <span className="badge badge-purple">{result.parsed_problem.topic}</span>
                            {result.parsed_problem.variables?.map((v) => (
                                <span className="badge badge-cyan" key={v}>var: {v}</span>
                            ))}
                        </div>
                    )}

                    {/* Extracted text or edit mode */}
                    {!editMode ? (
                        <div className={styles.extractedBox}>
                            <div className={styles.extractedLabel}>Detected Problem</div>
                            <div className={styles.extractedContent}>
                                <code>{result?.extracted_text}</code>
                            </div>
                        </div>
                    ) : (
                        <div className={styles.editBox}>
                            <div className={styles.extractedLabel}>
                                {needsClarification ? 'Clarify / Edit Problem' : 'Edit Problem Text'}
                            </div>
                            <textarea
                                className="input"
                                value={editedText}
                                onChange={(e) => setEditedText(e.target.value)}
                                rows={4}
                                autoFocus
                            />
                        </div>
                    )}
                </>
            )}

            {/* Actions */}
            <div className={styles.actions}>
                {isMultiProblem ? (
                    <>
                        <button
                            className="btn-solve"
                            onClick={handleSolveSelected}
                            disabled={loading || selectedProblems.length === 0}
                        >
                            {loading ? (
                                <>
                                    <span className="spinner" style={{ borderTopColor: 'white' }}></span>
                                    Solving...
                                </>
                            ) : (
                                `🚀 Solve ${selectedProblems.length} Problem${selectedProblems.length !== 1 ? 's' : ''}`
                            )}
                        </button>
                        <button
                            className="btn btn-ghost"
                            onClick={() => { setEditMode(true); setEditedText(result?.extracted_text || ''); }}
                            disabled={loading}
                        >
                            ✏️ Edit All
                        </button>
                    </>
                ) : !editMode ? (
                    <>
                        <button
                            className="btn-solve"
                            onClick={handleConfirm}
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <span className="spinner" style={{ borderTopColor: 'white' }}></span>
                                    Solving...
                                </>
                            ) : needsClarification ? (
                                '✏️ Clarify & Re-solve'
                            ) : (
                                '✅ Confirm & Show Solution'
                            )}
                        </button>
                        <button
                            className="btn btn-ghost"
                            onClick={() => { setEditMode(true); setEditedText(result?.extracted_text || ''); }}
                            disabled={loading}
                        >
                            ✏️ Edit Problem
                        </button>
                    </>
                ) : (
                    <>
                        <button
                            className="btn-solve"
                            onClick={handleEditSubmit}
                            disabled={loading || !editedText.trim()}
                        >
                            {loading ? (
                                <>
                                    <span className="spinner" style={{ borderTopColor: 'white' }}></span>
                                    Re-solving...
                                </>
                            ) : (
                                '🚀 Re-solve with Edited Text'
                            )}
                        </button>
                        <button
                            className="btn btn-ghost"
                            onClick={() => setEditMode(false)}
                            disabled={loading}
                        >
                            Cancel
                        </button>
                    </>
                )}
            </div>
        </div>
    );
}
