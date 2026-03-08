'use client';
import { useState, useRef, useCallback } from 'react';
import styles from './InputPanel.module.css';

export default function InputPanel({ onSolve, loading }) {
    const [mode, setMode] = useState('text');
    const [text, setText] = useState('');
    const [imageBase64, setImageBase64] = useState(null);
    const [imagePreview, setImagePreview] = useState(null);
    const [audioBase64, setAudioBase64] = useState(null);
    const [audioUrl, setAudioUrl] = useState(null);
    const [recording, setRecording] = useState(false);
    const [dragover, setDragover] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const fileInputRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const timerRef = useRef(null);

    const handleImageUpload = useCallback((file) => {
        if (!file || !file.type.startsWith('image/')) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            const base64 = e.target.result.split(',')[1];
            setImageBase64(base64);
            setImagePreview(e.target.result);
        };
        reader.readAsDataURL(file);
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setDragover(false);
        const file = e.dataTransfer.files[0];
        handleImageUpload(file);
    }, [handleImageUpload]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];
            setRecordingTime(0);

            timerRef.current = setInterval(() => {
                setRecordingTime((t) => t + 1);
            }, 1000);

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) audioChunksRef.current.push(e.data);
            };

            mediaRecorder.onstop = () => {
                clearInterval(timerRef.current);
                const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                const url = URL.createObjectURL(blob);
                setAudioUrl(url);
                const reader = new FileReader();
                reader.onload = (e) => setAudioBase64(e.target.result.split(',')[1]);
                reader.readAsDataURL(blob);
                stream.getTracks().forEach((t) => t.stop());
            };

            mediaRecorder.start();
            setRecording(true);
        } catch {
            alert('Microphone access denied');
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current) {
            mediaRecorderRef.current.stop();
            setRecording(false);
        }
    };

    const handleAudioUpload = (file) => {
        if (!file) return;
        const url = URL.createObjectURL(file);
        setAudioUrl(url);
        const reader = new FileReader();
        reader.onload = (e) => setAudioBase64(e.target.result.split(',')[1]);
        reader.readAsDataURL(file);
    };

    const formatTime = (s) => {
        const m = Math.floor(s / 60);
        const sec = s % 60;
        return `${m}:${sec.toString().padStart(2, '0')}`;
    };

    const canSolve = () => {
        if (mode === 'text') return text.trim().length > 0;
        if (mode === 'image') return imageBase64 !== null;
        if (mode === 'audio') return audioBase64 !== null;
        return false;
    };

    const handleSubmit = () => {
        if (!canSolve() || loading) return;
        onSolve({
            inputMode: mode,
            text: mode === 'text' ? text : undefined,
            imageBase64: mode === 'image' ? imageBase64 : undefined,
            audioBase64: mode === 'audio' ? audioBase64 : undefined,
            audioFormat: mode === 'audio' ? 'webm' : undefined,
        });
    };

    return (
        <div className={styles.panel}>
            <div className={styles.panelHeader}>
                <span className={styles.panelIcon}>📝</span>
                <h3>What would you like to solve?</h3>
            </div>

            {/* Mode Tabs */}
            <div className="tabs">
                {['text', 'image', 'audio'].map((m) => (
                    <button
                        key={m}
                        className={`tab ${mode === m ? 'active' : ''}`}
                        onClick={() => setMode(m)}
                    >
                        {m === 'text' && '✏️'}
                        {m === 'image' && '📷'}
                        {m === 'audio' && '🎤'}
                        {m.charAt(0).toUpperCase() + m.slice(1)}
                    </button>
                ))}
            </div>

            {/* Text Input */}
            {mode === 'text' && (
                <div className={`${styles.inputArea} fade-in`}>
                    <textarea
                        className="input"
                        placeholder={"Type your math problem here...\n\nExamples:\n• Solve x² - 5x + 6 = 0\n• Find the derivative of sin(x²)\n• Explain the Pythagorean theorem\n• What is the probability of rolling a sum of 7?"}
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        rows={8}
                    />
                </div>
            )}

            {/* Image Input */}
            {mode === 'image' && (
                <div className={`${styles.inputArea} fade-in`}>
                    {!imagePreview ? (
                        <div
                            className={`upload-zone ${dragover ? 'dragover' : ''}`}
                            onClick={() => fileInputRef.current?.click()}
                            onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
                            onDragLeave={() => setDragover(false)}
                            onDrop={handleDrop}
                        >
                            <div className="icon">📸</div>
                            <p><strong>Drop an image</strong> or click to browse</p>
                            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>
                                PNG, JPG, or WEBP — photo of a math problem
                            </p>
                        </div>
                    ) : (
                        <div className={styles.previewContainer}>
                            <img src={imagePreview} alt="Uploaded math problem" className={styles.imagePreview} />
                            <button
                                className="btn btn-ghost btn-sm"
                                onClick={() => { setImageBase64(null); setImagePreview(null); }}
                            >
                                ✕ Remove
                            </button>
                        </div>
                    )}
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        style={{ display: 'none' }}
                        onChange={(e) => handleImageUpload(e.target.files[0])}
                    />
                </div>
            )}

            {/* Audio Input */}
            {mode === 'audio' && (
                <div className={`${styles.inputArea} fade-in`}>
                    <div className={styles.audioControls}>
                        {!recording ? (
                            <button
                                className={`btn ${audioUrl ? 'btn-ghost' : 'btn-primary'} btn-lg`}
                                onClick={startRecording}
                                style={{ borderRadius: 'var(--radius-full)' }}
                            >
                                🎙️ {audioUrl ? 'Re-record' : 'Start Recording'}
                            </button>
                        ) : (
                            <div className={styles.recordingState}>
                                <button
                                    className="btn btn-danger btn-lg pulse-ring"
                                    onClick={stopRecording}
                                    style={{ borderRadius: 'var(--radius-full)' }}
                                >
                                    ⏹️ Stop Recording
                                </button>
                                <div className={styles.recordingTimer}>
                                    <span className={styles.recordingDot} />
                                    {formatTime(recordingTime)}
                                </div>
                            </div>
                        )}

                        <p className="text-muted" style={{ fontSize: '0.8rem', textAlign: 'center' }}>
                            {recording ? 'Recording... Speak your math problem clearly' : 'Or upload an audio file:'}
                        </p>

                        {!recording && (
                            <label className="btn btn-ghost btn-sm" style={{ cursor: 'pointer' }}>
                                📁 Upload Audio
                                <input
                                    type="file"
                                    accept="audio/*"
                                    style={{ display: 'none' }}
                                    onChange={(e) => handleAudioUpload(e.target.files[0])}
                                />
                            </label>
                        )}
                    </div>

                    {audioUrl && (
                        <div className={styles.audioPreview}>
                            <audio controls src={audioUrl} style={{ width: '100%' }} />
                        </div>
                    )}
                </div>
            )}

            {/* Solve Button */}
            <button
                className="btn-solve mt-2"
                onClick={handleSubmit}
                disabled={!canSolve() || loading}
            >
                {loading ? (
                    <>
                        <span className="spinner" style={{ borderTopColor: 'white' }}></span>
                        Processing...
                    </>
                ) : (
                    '🚀 Submit Problem'
                )}
            </button>
        </div>
    );
}
