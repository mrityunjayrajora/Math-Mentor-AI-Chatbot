'use client';
import { useState, useEffect } from 'react';
import { getMemoryStats, getMemoryProblems, findSimilarProblems, deleteMemoryProblem, clearAllMemory } from '@/lib/api';
import styles from './page.module.css';

const TOPICS = [
    { value: null, label: 'All Topics', icon: '📚' },
    { value: 'algebra', label: 'Algebra', icon: '📐' },
    { value: 'calculus', label: 'Calculus', icon: '📈' },
    { value: 'probability', label: 'Probability', icon: '🎲' },
    { value: 'linear_algebra', label: 'Linear Algebra', icon: '📊' },
    { value: 'geometry', label: 'Geometry', icon: '📏' },
    { value: 'number_theory', label: 'Number Theory', icon: '🔢' },
    { value: 'trigonometry', label: 'Trigonometry', icon: '📐' },
    { value: 'statistics', label: 'Statistics', icon: '📉' },
    { value: 'general', label: 'General', icon: '💡' },
];

function StatCard({ label, value, icon, color }) {
    return (
        <div className={styles.statCard}>
            <div className={styles.statIcon}>{icon}</div>
            <div className={styles.statValue} style={{ color }}>{value}</div>
            <div className={styles.statLabel}>{label}</div>
        </div>
    );
}

function ProblemCard({ problem, expanded, onToggle, onDelete, deleting }) {
    const [confirmDelete, setConfirmDelete] = useState(false);

    const handleDeleteClick = (e) => {
        e.stopPropagation();
        setConfirmDelete(true);
    };

    const handleConfirmDelete = (e) => {
        e.stopPropagation();
        onDelete(problem.session_id);
    };

    const handleCancelDelete = (e) => {
        e.stopPropagation();
        setConfirmDelete(false);
    };

    return (
        <div className={`${styles.problemCard} ${expanded ? styles.problemExpanded : ''}`}>
            <button className={styles.problemHeader} onClick={onToggle}>
                <div className={styles.problemMeta}>
                    <span className={`badge badge-purple`}>{problem.topic}</span>
                    <span className={`badge ${problem.is_correct ? 'badge-green' : 'badge-red'}`}>
                        {problem.is_correct ? '✅ Correct' : '❌ Incorrect'}
                    </span>
                    <span className="badge badge-blue">
                        {Math.round((problem.verification_confidence || 0) * 100)}% confidence
                    </span>
                </div>
                <p className={styles.problemText}>
                    {problem.problem_text}
                </p>
                <div className={styles.problemFooter}>
                    <span className={styles.problemDate}>
                        {problem.created_at?.substring(0, 10)}
                    </span>
                    <span className={styles.expandIcon} style={{ transform: expanded ? 'rotate(180deg)' : '' }}>▾</span>
                </div>
            </button>

            {expanded && (
                <div className={`${styles.problemDetails} fade-in`}>
                    {/* Answer */}
                    <div className={styles.answerBox}>
                        <div className={styles.answerLabel}>ANSWER</div>
                        <div className={styles.answerValue}>{problem.final_answer}</div>
                    </div>

                    {/* Explanation */}
                    {problem.explanation && (
                        <div className={styles.stepsSection}>
                            <h4 className={styles.detailTitle}>🎓 Explanation</h4>
                            <p className={styles.explanationText}>{problem.explanation}</p>
                        </div>
                    )}

                    {/* Feedback */}
                    {problem.user_feedback && (
                        <div className={styles.feedbackNote}>
                            <span>💬</span>
                            <span>{problem.user_feedback}</span>
                        </div>
                    )}

                    {/* Delete — inline confirmation */}
                    {!confirmDelete ? (
                        <button
                            className={styles.deleteBtn}
                            onClick={handleDeleteClick}
                        >
                            🗑️ Remove from Memory
                        </button>
                    ) : (
                        <div className={`${styles.confirmDeleteBox} fade-in`}>
                            <span className={styles.confirmText}>Remove this problem?</span>
                            <div className={styles.confirmActions}>
                                <button
                                    className={styles.confirmYes}
                                    onClick={handleConfirmDelete}
                                    disabled={deleting}
                                >
                                    {deleting ? '...' : 'Yes, remove'}
                                </button>
                                <button
                                    className={styles.confirmNo}
                                    onClick={handleCancelDelete}
                                    disabled={deleting}
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default function MemoryPage() {
    const [stats, setStats] = useState(null);
    const [problems, setProblems] = useState([]);
    const [totalProblems, setTotalProblems] = useState(0);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(0);
    const [selectedTopic, setSelectedTopic] = useState(null);
    const [expandedId, setExpandedId] = useState(null);
    const [loadingStats, setLoadingStats] = useState(true);
    const [loadingProblems, setLoadingProblems] = useState(true);
    const [query, setQuery] = useState('');
    const [searchResults, setSearchResults] = useState(null);
    const [searching, setSearching] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [showClearConfirm, setShowClearConfirm] = useState(false);
    const [clearing, setClearing] = useState(false);

    useEffect(() => {
        getMemoryStats()
            .then(setStats)
            .catch(() => { })
            .finally(() => setLoadingStats(false));
    }, []);

    useEffect(() => {
        setLoadingProblems(true);
        getMemoryProblems(page, 12, selectedTopic)
            .then((data) => {
                setProblems(data.problems || []);
                setTotalProblems(data.total || 0);
                setTotalPages(data.total_pages || 0);
            })
            .catch(() => { })
            .finally(() => setLoadingProblems(false));
    }, [page, selectedTopic]);

    const handleSearch = async () => {
        if (!query.trim()) return;
        setSearching(true);
        try {
            const data = await findSimilarProblems(query);
            setSearchResults(data);
        } catch {
            // silently fail
        }
        setSearching(false);
    };

    const handleTopicChange = (topic) => {
        setSelectedTopic(topic);
        setPage(1);
        setSearchResults(null);
    };

    const refreshData = () => {
        setLoadingStats(true);
        setLoadingProblems(true);
        getMemoryStats().then(setStats).catch(() => { }).finally(() => setLoadingStats(false));
        getMemoryProblems(page, 12, selectedTopic)
            .then((data) => {
                setProblems(data.problems || []);
                setTotalProblems(data.total || 0);
                setTotalPages(data.total_pages || 0);
            })
            .catch(() => { })
            .finally(() => setLoadingProblems(false));
    };

    const handleDelete = async (sessionId) => {
        setDeleting(true);
        try {
            await deleteMemoryProblem(sessionId);
            setExpandedId(null);
            refreshData();
        } catch (err) {
            console.error('Delete failed:', err);
        }
        setDeleting(false);
    };

    const handleClearAll = async () => {
        setClearing(true);
        try {
            await clearAllMemory();
            setShowClearConfirm(false);
            refreshData();
        } catch (err) {
            console.error('Clear failed:', err);
        }
        setClearing(false);
    };

    return (
        <div className={styles.page}>
            <div className={styles.header}>
                <div className={styles.headerRow}>
                    <h1>
                        <span>🧠</span>
                        Memory Store
                    </h1>
                    {stats && stats.total_problems > 0 && !showClearConfirm && (
                        <button
                            className={`btn btn-ghost btn-sm ${styles.clearAllBtn}`}
                            onClick={() => setShowClearConfirm(true)}
                        >
                            🗑️ Clear All
                        </button>
                    )}
                </div>
                <p className="text-muted">All previously solved problems and learning data</p>

                {/* Clear All inline confirmation */}
                {showClearConfirm && (
                    <div className={`${styles.clearConfirmBar} fade-in`}>
                        <span>⚠️ Delete <strong>all {stats?.total_problems || 0}</strong> problems from memory? This cannot be undone.</span>
                        <div className={styles.confirmActions}>
                            <button
                                className={styles.confirmYes}
                                onClick={handleClearAll}
                                disabled={clearing}
                            >
                                {clearing ? 'Clearing...' : 'Yes, clear all'}
                            </button>
                            <button
                                className={styles.confirmNo}
                                onClick={() => setShowClearConfirm(false)}
                                disabled={clearing}
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Stats Dashboard */}
            <div className={styles.statsGrid}>
                {loadingStats ? (
                    <>
                        {[1, 2, 3, 4].map((i) => (
                            <div className={styles.statCard} key={i}>
                                <div className="skeleton" style={{ width: 40, height: 40, borderRadius: '50%' }}></div>
                                <div className="skeleton" style={{ width: 50, height: 24 }}></div>
                                <div className="skeleton" style={{ width: 70, height: 14 }}></div>
                            </div>
                        ))}
                    </>
                ) : stats ? (
                    <>
                        <StatCard label="Problems Solved" value={stats.total_problems || 0} icon="📊" color="var(--text-primary)" />
                        <StatCard label="Correct" value={stats.correct_problems || 0} icon="✅" color="var(--accent-green)" />
                        <StatCard label="Accuracy" value={`${((stats.accuracy || 0) * 100).toFixed(0)}%`} icon="🎯" color="var(--accent-purple)" />
                        <StatCard label="Feedback" value={stats.feedback_count || 0} icon="💬" color="var(--accent-blue)" />
                    </>
                ) : (
                    <div className={styles.emptyStats}>
                        <p className="text-muted">No memory data yet. Solve some problems first!</p>
                    </div>
                )}
            </div>

            {/* Search */}
            <div className={styles.searchCard}>
                <div className={styles.searchHeader}>
                    <span>🔍</span>
                    <h3>Find Similar Problems</h3>
                </div>
                <div className={styles.searchRow}>
                    <input
                        className="input flex-1"
                        placeholder="Search for a problem, e.g. 'quadratic equation'..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    />
                    <button className="btn btn-primary" onClick={handleSearch} disabled={searching}>
                        {searching ? <span className="spinner" style={{ borderTopColor: 'white' }}></span> : 'Search'}
                    </button>
                </div>
            </div>

            {/* Search Results */}
            {searchResults && (
                <div className={`${styles.searchResults} fade-in`}>
                    <h3 className={styles.sectionTitle}>
                        {searchResults.count} result{searchResults.count !== 1 ? 's' : ''} found
                    </h3>
                    {searchResults.results?.length === 0 ? (
                        <div className={styles.emptyState}>
                            <p className="text-muted">No similar problems found in memory</p>
                        </div>
                    ) : (
                        <div className={styles.resultsList}>
                            {searchResults.results?.map((item, i) => (
                                <div className={styles.searchResultCard} key={i}>
                                    <div className="flex items-center gap-1 mb-1 flex-wrap">
                                        <span className="badge badge-purple">{item.topic}</span>
                                        <span className={`badge ${item.is_correct ? 'badge-green' : 'badge-red'}`}>
                                            {item.is_correct ? '✅ Correct' : '❌ Incorrect'}
                                        </span>
                                        <span className="badge badge-blue" style={{ marginLeft: 'auto' }}>
                                            {(item.similarity * 100).toFixed(0)}% similar
                                        </span>
                                    </div>
                                    <p className={styles.resultProblem}>{item.problem_text}</p>
                                    <div className={styles.resultAnswer}>
                                        Answer: {item.final_answer}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Topic Filter */}
            <div className={styles.topicFilter}>
                <h3 className={styles.sectionTitle}>Solved Problems</h3>
                <div className={styles.topicTabs}>
                    {TOPICS.map((t) => (
                        <button
                            key={t.label}
                            className={`${styles.topicTab} ${selectedTopic === t.value ? styles.topicTabActive : ''}`}
                            onClick={() => handleTopicChange(t.value)}
                        >
                            <span>{t.icon}</span>
                            <span>{t.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Problems list */}
            {loadingProblems ? (
                <div className={styles.loadingProblems}>
                    {[1, 2, 3].map((i) => (
                        <div className={styles.problemCard} key={i} style={{ padding: 24 }}>
                            <div className="skeleton" style={{ width: '60%', height: 16, marginBottom: 8 }}></div>
                            <div className="skeleton" style={{ width: '100%', height: 14 }}></div>
                        </div>
                    ))}
                </div>
            ) : problems.length === 0 ? (
                <div className={styles.emptyState}>
                    <div className={styles.emptyIcon}>📭</div>
                    <h3>No problems found</h3>
                    <p className="text-muted">
                        {selectedTopic ? `No ${selectedTopic} problems solved yet.` : 'Solve some problems and they\'ll appear here!'}
                    </p>
                </div>
            ) : (
                <>
                    <div className={styles.problemsList}>
                        {problems.map((p) => (
                            <ProblemCard
                                key={p.session_id}
                                problem={p}
                                expanded={expandedId === p.session_id}
                                onToggle={() => setExpandedId(expandedId === p.session_id ? null : p.session_id)}
                                onDelete={handleDelete}
                                deleting={deleting}
                            />
                        ))}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className={styles.pagination}>
                            <button
                                className="btn btn-ghost btn-sm"
                                disabled={page <= 1}
                                onClick={() => setPage(page - 1)}
                            >
                                ← Previous
                            </button>
                            <span className={styles.pageInfo}>
                                Page {page} of {totalPages} ({totalProblems} total)
                            </span>
                            <button
                                className="btn btn-ghost btn-sm"
                                disabled={page >= totalPages}
                                onClick={() => setPage(page + 1)}
                            >
                                Next →
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
