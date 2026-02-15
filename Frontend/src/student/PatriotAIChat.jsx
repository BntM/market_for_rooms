import React, { useState, useRef, useEffect } from 'react';
import patriotAvatar from '../assets/patriot.png';
import gmuLogo from '../assets/logo.jpg';

/* ────────────────────────────────────────────────
   PatriotAIChat – styled to match the official
   Patriot AI (OneChat) interface using INLINE
   styles only (no Tailwind).
   ──────────────────────────────────────────────── */

const COLORS = {
    sidebarBg: '#006633',
    sidebarHover: '#00552a',
    gold: '#FFCC33',
    white: '#ffffff',
    lightBg: '#f5f5f5',
    border: '#e5e7eb',
    textPrimary: '#1f2937',
    textSecondary: '#6b7280',
    textMuted: '#9ca3af',
};

const PatriotAIChat = () => {
    const [messages, setMessages] = useState([
        {
            id: 1,
            sender: 'agent',
            text: "Hello! I'm your Patriot AI assistant for the Market for Rooms.\n\nHow would you like me to help? For example, I can:\n\n• 📎 Analyze your **syllabus** to find exam dates\n• 📊 Help you find the **best-priced study rooms**\n• 🕐 Predict **busy times** at the library\n• 📝 Schedule **limit orders** before your exams\n\nJust type a message or upload your syllabus PDF!",
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    /* ── API handlers ── */

    const handleSendMessage = async () => {
        if (!input.trim()) return;
        const userMsg = { id: Date.now(), sender: 'user', text: input, timestamp: new Date() };
        setMessages((prev) => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const response = await fetch('http://localhost:8000/api/student/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMsg.text }),
            });
            if (!response.ok) throw new Error('API Connection Failed');
            const data = await response.json();
            setMessages((prev) => [...prev, { id: Date.now() + 1, sender: 'agent', text: data.response, timestamp: new Date() }]);
        } catch {
            setMessages((prev) => [...prev, { id: Date.now(), sender: 'system', text: '⚠️ Connection error. Make sure the backend is running.' }]);
        } finally {
            setLoading(false);
        }
    };

    const handleFileUpload = async (e) => {
        if (!e.target.files?.[0]) return;
        const file = e.target.files[0];
        setMessages((prev) => [...prev, { id: Date.now(), sender: 'user', text: `📎 Uploaded: ${file.name}`, timestamp: new Date() }]);
        setLoading(true);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('http://localhost:8000/api/student/parse-syllabus', { method: 'POST', body: formData });
            if (response.ok) {
                const data = await response.json();
                setMessages((prev) => [...prev, { id: Date.now() + 1, sender: 'agent', text: "I've analyzed your syllabus. Please confirm your exam schedule below:", exams: data.exams, timestamp: new Date() }]);
            } else {
                const errText = await response.text();
                setMessages((prev) => [...prev, { id: Date.now() + 1, sender: 'agent', text: `Failed to parse syllabus: ${errText}` }]);
            }
        } catch (error) {
            setMessages((prev) => [...prev, { id: Date.now() + 1, sender: 'system', text: `Network error: ${error.message}` }]);
        } finally {
            setLoading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleCreateOrders = async (exams, maxPrice) => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8000/api/student/create-exam-orders', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent_id: 'User_1', exams, max_price: parseFloat(maxPrice), strategy: '3_days_before' }),
            });
            if (response.ok) {
                const data = await response.json();
                setMessages((prev) => [...prev, { id: Date.now(), sender: 'agent', text: `✅ Limit orders placed! (${data.orders_count} orders created)` }]);
            } else {
                const err = await response.text();
                setMessages((prev) => [...prev, { id: Date.now(), sender: 'agent', text: `❌ Error: ${err}` }]);
            }
        } catch (e) {
            setMessages((prev) => [...prev, { id: Date.now(), sender: 'system', text: `Error: ${e.message}` }]);
        } finally {
            setLoading(false);
        }
    };

    /* ── Render ── */

    return (
        <div style={{ display: 'flex', height: 'calc(100vh - 64px)', fontFamily: "'Inter', 'Segoe UI', sans-serif", background: COLORS.lightBg }}>
            {/* ═══════ SIDEBAR ═══════ */}
            <div style={{
                width: 280,
                minWidth: 280,
                background: COLORS.sidebarBg,
                color: COLORS.white,
                display: 'flex',
                flexDirection: 'column',
                boxShadow: '2px 0 8px rgba(0,0,0,.15)',
                zIndex: 10,
            }}>
                {/* Logo */}
                <div style={{ padding: '20px 20px 16px', display: 'flex', alignItems: 'center', gap: 12, borderBottom: `1px solid ${COLORS.sidebarHover}` }}>
                    <img src={gmuLogo} alt="GMU" style={{ width: 44, height: 44, borderRadius: '50%', border: `2px solid ${COLORS.gold}`, objectFit: 'cover' }} />
                    <div>
                        <div style={{ fontWeight: 700, fontSize: 14, color: COLORS.gold, letterSpacing: '.5px' }}>GEORGE MASON</div>
                        <div style={{ fontWeight: 600, fontSize: 11, color: COLORS.gold, letterSpacing: '1px' }}>UNIVERSITY</div>
                    </div>
                </div>

                {/* Nav Links */}
                <div style={{ padding: '12px 16px' }}>
                    <SidebarLink icon="💬" label="New Chat" active={false} />
                    <SidebarLink icon="🤖" label="Explore Agents" active={false} />
                </div>

                {/* Tabs */}
                <div style={{ display: 'flex', margin: '0 16px', borderRadius: 8, overflow: 'hidden', border: '1px solid rgba(255,255,255,.15)' }}>
                    <div style={{ flex: 1, padding: '8px 0', textAlign: 'center', fontSize: 13, fontWeight: 600, background: 'rgba(255,255,255,.15)', cursor: 'pointer' }}>💬 Chats</div>
                    <div style={{ flex: 1, padding: '8px 0', textAlign: 'center', fontSize: 13, fontWeight: 500, cursor: 'pointer', opacity: .6 }}>🤖 Agents</div>
                </div>

                {/* Chat History */}
                <div style={{ flex: 1, padding: '16px', overflowY: 'auto' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                        <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1.5px', color: 'rgba(255,255,255,.4)' }}>Today</div>
                        <span style={{ cursor: 'pointer', fontSize: 14, opacity: .5 }}>🔍</span>
                    </div>
                    <div style={{
                        padding: '10px 12px',
                        background: 'rgba(255,255,255,.08)',
                        borderRadius: 8,
                        fontSize: 13,
                        cursor: 'pointer',
                        borderLeft: `3px solid ${COLORS.gold}`,
                        color: 'rgba(255,255,255,.9)',
                    }}>
                        Market Analysis Chat
                    </div>
                </div>

                {/* Bottom Tabs */}
                <div style={{ display: 'flex', borderTop: `1px solid ${COLORS.sidebarHover}` }}>
                    <div style={{ flex: 1, padding: '10px 0', textAlign: 'center', fontSize: 12, fontWeight: 600, cursor: 'pointer', background: 'rgba(255,255,255,.05)' }}>HISTORY</div>
                    <div style={{ flex: 1, padding: '10px 0', textAlign: 'center', fontSize: 12, fontWeight: 500, cursor: 'pointer', opacity: .5 }}>ARCHIVED</div>
                </div>

                {/* User */}
                <div style={{ padding: '12px 16px', borderTop: `1px solid ${COLORS.sidebarHover}`, background: 'rgba(0,0,0,.1)', display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{
                        width: 32, height: 32, borderRadius: '50%', background: COLORS.gold,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: COLORS.sidebarBg, fontWeight: 700, fontSize: 13,
                    }}>J</div>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>Joseph Henry DeRoma</div>
                </div>
            </div>

            {/* ═══════ MAIN CHAT ═══════ */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: COLORS.white, overflow: 'hidden' }}>
                {/* Header */}
                <div style={{
                    height: 52, display: 'flex', alignItems: 'center', padding: '0 24px',
                    borderBottom: `1px solid ${COLORS.border}`, gap: 12,
                }}>
                    <span style={{ fontSize: 16 }}>🌐</span>
                    <span style={{ fontWeight: 600, fontSize: 14, color: COLORS.textPrimary }}>GPT-5.2 Auto</span>
                    <span style={{ fontSize: 12, color: COLORS.textMuted }}>▾</span>
                </div>

                {/* Messages */}
                <div style={{ flex: 1, overflowY: 'auto', padding: '32px 48px' }}>
                    {messages.map((msg) => (
                        <div key={msg.id} style={{ marginBottom: 28 }}>
                            {msg.sender === 'user' && <UserMessage text={msg.text} />}
                            {msg.sender === 'agent' && <AgentMessage text={msg.text} exams={msg.exams} onConfirm={handleCreateOrders} />}
                            {msg.sender === 'system' && <SystemMessage text={msg.text} />}
                        </div>
                    ))}
                    {loading && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
                            <img src={patriotAvatar} alt="Agent" style={{ width: 28, height: 28, borderRadius: '50%', objectFit: 'cover' }} />
                            <div style={{ display: 'flex', gap: 4 }}>
                                <Dot delay={0} /><Dot delay={150} /><Dot delay={300} />
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Bar */}
                <div style={{ padding: '12px 48px 20px' }}>
                    <div style={{
                        display: 'flex', alignItems: 'center', gap: 8,
                        border: `1px solid ${COLORS.border}`, borderRadius: 28,
                        padding: '6px 8px 6px 16px', background: COLORS.white,
                        boxShadow: '0 1px 4px rgba(0,0,0,.06)',
                    }}>
                        {/* Plus / file button */}
                        <button
                            onClick={() => fileInputRef.current?.click()}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 20, color: COLORS.textMuted, padding: 4 }}
                            title="Attach Syllabus PDF"
                        >+</button>

                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } }}
                            placeholder="Type a message..."
                            style={{
                                flex: 1, border: 'none', outline: 'none', fontSize: 14,
                                fontFamily: 'inherit', padding: '8px 0', background: 'transparent',
                            }}
                        />

                        {/* Send */}
                        <button
                            onClick={handleSendMessage}
                            disabled={!input.trim()}
                            style={{
                                width: 36, height: 36, borderRadius: '50%',
                                background: input.trim() ? COLORS.sidebarBg : '#e5e7eb',
                                color: input.trim() ? COLORS.white : COLORS.textMuted,
                                border: 'none', cursor: input.trim() ? 'pointer' : 'default',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                fontSize: 16, transition: 'background .2s',
                            }}
                        >➤</button>
                    </div>
                    <input type="file" ref={fileInputRef} style={{ display: 'none' }} accept=".pdf" onChange={handleFileUpload} />
                    <div style={{ textAlign: 'center', fontSize: 11, color: COLORS.textMuted, marginTop: 6 }}>
                        GPT-5.2 Auto can make mistakes. Consider checking important information.
                    </div>
                </div>
            </div>
        </div>
    );
};

/* ── Sub-components ── */

const SidebarLink = ({ icon, label }) => (
    <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '10px 12px', borderRadius: 8, cursor: 'pointer',
        fontSize: 14, fontWeight: 500, color: 'rgba(255,255,255,.85)',
        marginBottom: 2,
    }}
        onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,.08)'}
        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
    >
        <span style={{ fontSize: 16 }}>{icon}</span>
        {label}
    </div>
);

const UserMessage = ({ text }) => (
    <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-start' }}>
        <div style={{
            width: 28, height: 28, borderRadius: '50%', background: '#FFCC33',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#006633', fontWeight: 700, fontSize: 13, flexShrink: 0,
        }}>J</div>
        <div style={{
            background: '#f0f0f0', borderRadius: '18px 18px 18px 4px',
            padding: '12px 18px', maxWidth: 600, fontSize: 14, lineHeight: 1.6,
            color: '#1f2937',
        }}>{text}</div>
    </div>
);

const AgentMessage = ({ text, exams, onConfirm }) => (
    <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
        <img src={patriotAvatar} alt="Agent" style={{ width: 28, height: 28, borderRadius: '50%', objectFit: 'cover', flexShrink: 0, marginTop: 2 }} />
        <div style={{ maxWidth: 700 }}>
            <div style={{ fontWeight: 600, fontSize: 13, color: '#006633', marginBottom: 4 }}>ONEchat</div>
            <div style={{ fontSize: 14, lineHeight: 1.7, color: '#374151', whiteSpace: 'pre-wrap' }}>{text}</div>
            {exams && <ExamConfirmationCard exams={exams} onConfirm={onConfirm} />}
        </div>
    </div>
);

const SystemMessage = ({ text }) => (
    <div style={{
        background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8,
        padding: '10px 16px', fontSize: 13, color: '#b91c1c', maxWidth: 500,
    }}>{text}</div>
);

const Dot = ({ delay }) => (
    <div style={{
        width: 8, height: 8, borderRadius: '50%', background: '#9ca3af',
        animation: `dotBounce 1.2s infinite ease-in-out`,
        animationDelay: `${delay}ms`,
    }} />
);

const ExamConfirmationCard = ({ exams, onConfirm }) => {
    const [maxPrice, setMaxPrice] = useState(20);
    const [confirmed, setConfirmed] = useState(false);

    if (confirmed)
        return (
            <div style={{ marginTop: 12, padding: '10px 14px', background: '#ecfdf5', color: '#065f46', borderRadius: 8, border: '1px solid #a7f3d0', fontSize: 13, fontWeight: 600 }}>
                ✓ Limit Orders Scheduled!
            </div>
        );

    return (
        <div style={{ marginTop: 16, background: '#fff', borderRadius: 10, border: '1px solid #e5e7eb', padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,.06)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, color: '#006633', fontWeight: 700, fontSize: 13, textTransform: 'uppercase', letterSpacing: '.5px' }}>
                📅 Exam Schedule Detected
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 14 }}>
                {exams.map((exam, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: '#f9fafb', borderRadius: 6, border: '1px solid #f3f4f6', fontSize: 13 }}>
                        <span style={{ fontWeight: 500, color: '#1f2937' }}>{exam.name}</span>
                        <span style={{ fontFamily: 'monospace', fontSize: 12, color: '#6b7280', background: '#fff', padding: '2px 8px', borderRadius: 4, border: '1px solid #e5e7eb' }}>{exam.date}</span>
                    </div>
                ))}
            </div>
            <div style={{ marginBottom: 12 }}>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: '#6b7280', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '.5px' }}>Max Price per Slot (Tokens)</label>
                <input
                    type="number"
                    value={maxPrice}
                    onChange={(e) => setMaxPrice(e.target.value)}
                    style={{ width: '100%', border: '1px solid #d1d5db', borderRadius: 6, padding: '8px 12px', fontSize: 14, outline: 'none', boxSizing: 'border-box' }}
                />
            </div>
            <button
                type="button"
                onClick={(e) => { e.preventDefault(); onConfirm(exams, maxPrice); setConfirmed(true); }}
                style={{
                    width: '100%', padding: '10px 0', background: '#006633', color: '#fff',
                    border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 600,
                    cursor: 'pointer',
                }}
            >
                Confirm Schedule & Place Orders
            </button>
        </div>
    );
};

export default PatriotAIChat;
