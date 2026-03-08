/**
 * API client for the Math Mentor backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

async function request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = { ...options.headers };

    // Only set Content-Type for JSON requests (not FormData)
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    const res = await fetch(url, {
        headers,
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || 'API request failed');
    }
    return res.json();
}

export async function solveProblem({ inputMode, text, imageBase64, audioBase64, audioFormat }) {
    return request('/solve', {
        method: 'POST',
        body: JSON.stringify({
            input_mode: inputMode,
            text,
            image_base64: imageBase64,
            audio_base64: audioBase64,
            audio_format: audioFormat,
        }),
    });
}

export async function getPendingReviews() {
    return request('/hitl/pending');
}

export async function submitReview({ sessionId, action, correctedText, correctedAnswer, feedback }) {
    return request('/hitl/review', {
        method: 'POST',
        body: JSON.stringify({
            session_id: sessionId,
            action,
            corrected_text: correctedText,
            corrected_answer: correctedAnswer,
            feedback,
        }),
    });
}

export async function getReviewStatus(sessionId) {
    return request(`/hitl/${sessionId}`);
}

export async function findSimilarProblems(query, topK = 5) {
    return request(`/memory/similar?query=${encodeURIComponent(query)}&top_k=${topK}`);
}

export async function getMemoryProblems(page = 1, perPage = 20, topic = null) {
    let url = `/memory/problems?page=${page}&per_page=${perPage}`;
    if (topic) url += `&topic=${encodeURIComponent(topic)}`;
    return request(url);
}

export async function submitFeedback({ sessionId, isCorrect, comment }) {
    return request('/memory/feedback', {
        method: 'POST',
        body: JSON.stringify({
            session_id: sessionId,
            is_correct: isCorrect,
            comment,
        }),
    });
}

export async function getMemoryStats() {
    return request('/memory/stats');
}

export async function deleteMemoryProblem(sessionId) {
    return request(`/memory/problems/${sessionId}`, { method: 'DELETE' });
}

export async function clearAllMemory() {
    return request('/memory/problems', { method: 'DELETE' });
}
