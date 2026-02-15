import { useState } from 'react';
import api from '../api';

export default function AdminMarketAnalysis() {
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleGenerateReport = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.post('/admin/market-analysis');
            setReport(response.report);
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card mb-2">
            <div className="flex-between" style={{ alignItems: 'flex-start' }}>
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <h3 style={{ margin: 0 }}>Market Strategy Analysis</h3>
                        <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2 py-0.5 rounded border border-blue-200">Gemini 1.5 Flash</span>
                    </div>
                    <p className="text-sm text-gray-500 mb-0">AI-powered insights on pricing, demand anomalies, and revenue optimization.</p>
                </div>
                <button
                    className="btn btn--primary"
                    onClick={handleGenerateReport}
                    disabled={loading}
                >
                    {loading ? (
                        <span className="flex items-center gap-2">
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            Generating...
                        </span>
                    ) : 'Generate Report'}
                </button>
            </div>

            {error && (
                <div className="mt-4 p-3 bg-red-50 text-red-700 rounded border border-red-200 text-sm">
                    Error generating report: {error}
                </div>
            )}

            {report && (
                <div className="mt-4 p-5 bg-gray-50 rounded-lg border border-gray-100" style={{ marginTop: '1rem', padding: '1.5rem', background: '#f9fafb', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
                    <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: '0.9rem', lineHeight: 1.7, margin: 0 }}>{report}</pre>
                </div>
            )}
        </div>
    );
}
