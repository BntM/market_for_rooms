import React, { useState, useRef, useEffect } from 'react';

const PatriotAIChat = () => {
    const [messages, setMessages] = useState([
        {
            id: 1,
            sender: 'agent',
            text: "Hello! I am the Patriot AI Market Assistant. I can help you schedule study rooms for your exams. Upload your syllabus PDF or just ask me for help!",
            timestamp: new Date()
        }
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);

    // Scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSendMessage = async () => {
        if (!input.trim()) return;

        const userMsg = { id: Date.now(), sender: 'user', text: input, timestamp: new Date() };
        setMessages(prev => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            const response = await fetch("http://localhost:8000/api/student/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userMsg.text })
            });

            const data = await response.json();
            const agentMsg = {
                id: Date.now() + 1,
                sender: 'agent',
                text: data.response,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, agentMsg]);
        } catch (error) {
            setMessages(prev => [...prev, { id: Date.now(), sender: 'system', text: "Error connecting to agent." }]);
        } finally {
            setLoading(false);
        }
    };

    const handleFileUpload = async (e) => {
        if (!e.target.files?.[0]) return;
        const file = e.target.files[0];

        const userMsg = { id: Date.now(), sender: 'user', text: `Uploaded: ${file.name}`, isFile: true, timestamp: new Date() };
        setMessages(prev => [...prev, userMsg]);
        setLoading(true);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("http://localhost:8000/api/student/parse-syllabus", {
                method: "POST",
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                // Render structured response
                const agentMsg = {
                    id: Date.now() + 1,
                    sender: 'agent',
                    text: "I've analyzed your syllabus. Here are the exams I found:",
                    exams: data.exams, // Special field for rendering card
                    timestamp: new Date()
                };
                setMessages(prev => [...prev, agentMsg]);
            } else {
                const errText = await response.text();
                setMessages(prev => [...prev, { id: Date.now() + 1, sender: 'agent', text: `Failed to parse syllabus: ${errText}` }]);
            }
        } catch (error) {
            setMessages(prev => [...prev, { id: Date.now() + 1, sender: 'system', text: `Network error: ${error.message}` }]);
        } finally {
            setLoading(false);
            // Reset file input
            if (fileInputRef.current) fileInputRef.current.value = "";
        }
    };

    const handleCreateOrders = async (exams, maxPrice) => {
        setLoading(true);
        try {
            const response = await fetch("http://localhost:8000/api/student/create-exam-orders", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    agent_id: "User_1",
                    exams: exams,
                    max_price: parseFloat(maxPrice),
                    strategy: "3_days_before"
                }),
            });

            if (response.ok) {
                const data = await response.json();
                setMessages(prev => [...prev, { id: Date.now(), sender: 'agent', text: `Success! ${data.message}` }]);
            } else {
                const err = await response.text();
                setMessages(prev => [...prev, { id: Date.now(), sender: 'agent', text: `Error creating orders: ${err}` }]);
            }
        } catch (e) {
            setMessages(prev => [...prev, { id: Date.now(), sender: 'system', text: `Error: ${e.message}` }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-100px)] max-w-4xl mx-auto bg-gray-50 rounded-xl shadow-lg overflow-hidden border border-gray-200">
            {/* Header */}
            <div className="bg-[#006633] text-white p-4 flex items-center shadow-sm">
                <div className="w-10 h-10 rounded-full bg-white text-[#006633] flex items-center justify-center font-bold mr-3 text-xl">P</div>
                <div>
                    <h2 className="font-bold text-lg">Patriot AI Agent</h2>
                    <p className="text-xs opacity-90">Powered by NebulaOne & GMU</p>
                </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] rounded-lg p-3 shadow-sm ${msg.sender === 'user'
                                ? 'bg-[#FFCC33] text-black rounded-tr-none'
                                : msg.sender === 'system' ? 'bg-red-100 text-red-800' : 'bg-white border border-gray-200 text-gray-800 rounded-tl-none'
                            }`}>
                            <p className="whitespace-pre-wrap">{msg.text}</p>

                            {/* Structured Exam Card */}
                            {msg.exams && (
                                <ExamConfirmationCard exams={msg.exams} onConfirm={handleCreateOrders} />
                            )}

                            <span className="text-[10px] opacity-50 block text-right mt-1">
                                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-white border border-gray-200 p-3 rounded-lg rounded-tl-none text-gray-400 italic text-sm animate-pulse">
                            Agent is thinking...
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-white border-t border-gray-200 flex items-center gap-2">
                <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    accept=".pdf"
                    onChange={handleFileUpload}
                />
                <button
                    onClick={() => fileInputRef.current?.click()}
                    className="p-2 text-gray-500 hover:bg-gray-100 rounded-full transition-colors"
                    title="Upload Syllabus"
                >
                    📎
                </button>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Type a message or upload syllabus..."
                    className="flex-1 border border-gray-300 rounded-full px-4 py-2 focus:outline-none focus:border-[#006633] focus:ring-1 focus:ring-[#006633]"
                />
                <button
                    onClick={handleSendMessage}
                    disabled={loading}
                    className="bg-[#006633] text-white rounded-full px-6 py-2 hover:bg-[#004d26] disabled:opacity-50 font-medium transition-colors"
                >
                    Send
                </button>
            </div>
        </div>
    );
};

// Sub-component for Exam Confirmation
const ExamConfirmationCard = ({ exams, onConfirm }) => {
    const [maxPrice, setMaxPrice] = useState(20);
    const [confirmed, setConfirmed] = useState(false);

    if (confirmed) {
        return <div className="mt-3 p-3 bg-green-50 text-green-700 rounded border border-green-200 text-sm">✓ Orders Confirmed</div>;
    }

    return (
        <div className="mt-3 bg-gray-50 rounded border border-gray-200 p-3 text-sm">
            <p className="font-semibold mb-2 text-[#006633]">Suggested Plan:</p>
            <ul className="space-y-1 mb-3">
                {exams.map((exam, i) => (
                    <li key={i} className="flex justify-between border-b border-gray-100 pb-1">
                        <span>{exam.name}</span>
                        <span className="font-mono text-xs">{exam.date} {exam.time}</span>
                    </li>
                ))}
            </ul>
            <div className="mb-3">
                <label className="block text-xs font-semibold text-gray-500 mb-1">Max Price (Tokens)</label>
                <input
                    type="number"
                    value={maxPrice}
                    onChange={(e) => setMaxPrice(e.target.value)}
                    className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                />
            </div>
            <button
                onClick={() => { onConfirm(exams, maxPrice); setConfirmed(true); }}
                className="w-full bg-[#006633] text-white rounded py-1.5 hover:bg-[#004d26] transition-colors shadow-sm"
            >
                Confirm & Place Orders
            </button>
        </div>
    );
};

export default PatriotAIChat;
