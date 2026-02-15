import React, { useState } from 'react';

const StudentSyllabusUpload = () => {
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [exams, setExams] = useState([]);
    const [maxPrice, setMaxPrice] = useState(20);
    const [parsedText, setParsedText] = useState("");
    const [message, setMessage] = useState("");
    const [agentId, setAgentId] = useState("User_1"); // hardcoded for demo, or fetch from context

    const handleFileChange = (e) => {
        if (e.target.files) {
            setFile(e.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setMessage("Please select a file first.");
            return;
        }

        setUploading(true);
        setMessage("");
        const formData = new FormData();
        formData.append("file", file);

        try {
            // In production, use environment variable for API URL
            const response = await fetch("http://localhost:8000/api/student/parse-syllabus", {
                method: "POST",
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                setExams(data.exams || []);
                setParsedText(data.raw_text_preview || "");
                setMessage("Syllabus parsed successfully! Please review exams below.");
            } else {
                const err = await response.text();
                setMessage(`Error parsing syllabus: ${err}`);
            }
        } catch (error) {
            setMessage(`Network error: ${error.message}`);
        } finally {
            setUploading(false);
        }
    };

    const handleConfirmOrders = async () => {
        if (exams.length === 0) {
            setMessage("No exams to schedule.");
            return;
        }

        setUploading(true);
        try {
            const response = await fetch("http://localhost:8000/api/student/create-exam-orders", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    agent_id: agentId,
                    exams: exams,
                    max_price: parseFloat(maxPrice),
                    strategy: "3_days_before"
                }),
            });

            if (response.ok) {
                const data = await response.json();
                setMessage(`Success! Created ${data.orders_count} limit orders.`);
                setExams([]); // Clear after success
            } else {
                const err = await response.text();
                setMessage(`Error creating orders: ${err}`);
            }
        } catch (error) {
            setMessage(`Network error: ${error.message}`);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="p-6 max-w-4xl mx-auto bg-white rounded-xl shadow-md space-y-4">
            <h2 className="text-2xl font-bold text-gray-800">Student Syllabus Upload</h2>
            <p className="text-gray-600">Upload your course syllabus (PDF) to automatically schedule study room limit orders.</p>

            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileChange}
                    className="block w-full text-sm text-slate-500
            file:mr-4 file:py-2 file:px-4
            file:rounded-full file:border-0
            file:text-sm file:font-semibold
            file:bg-violet-50 file:text-violet-700
            hover:file:bg-violet-100"
                />
                <button
                    onClick={handleUpload}
                    disabled={uploading || !file}
                    className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
                >
                    {uploading ? "Processing..." : "Upload & Parse"}
                </button>
            </div>

            {message && (
                <div className={`p-4 rounded-md ${message.includes("Error") ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"}`}>
                    {message}
                </div>
            )}

            {exams.length > 0 && (
                <div className="space-y-4">
                    <h3 className="text-xl font-semibold">Detected Exams</h3>
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Exam Name</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {exams.map((exam, idx) => (
                                <tr key={idx}>
                                    <td className="px-6 py-4 whitespace-nowrap">{exam.name}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">{exam.date}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">{exam.time || "N/A"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    <div className="bg-gray-50 p-4 rounded-md space-y-2">
                        <label className="block text-sm font-medium text-gray-700">Max Price Willing to Pay (Tokens)</label>
                        <input
                            type="number"
                            value={maxPrice}
                            onChange={(e) => setMaxPrice(e.target.value)}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                        />
                        <p className="text-xs text-gray-500">We will place Limit Buy Orders for 3 days before each exam date.</p>
                    </div>

                    <button
                        onClick={handleConfirmOrders}
                        disabled={uploading}
                        className="w-full px-6 py-3 bg-green-600 text-white font-bold rounded-md hover:bg-green-700 disabled:bg-gray-400"
                    >
                        {uploading ? "Creating Orders..." : "Place Limit Orders"}
                    </button>
                </div>
            )}

            {parsedText && (
                <details className="mt-4">
                    <summary className="cursor-pointer text-sm text-gray-500">Show Extracted Text Preview</summary>
                    <pre className="mt-2 p-2 bg-gray-100 text-xs overflow-auto max-h-40">{parsedText}</pre>
                </details>
            )}
        </div>
    );
};

export default StudentSyllabusUpload;
