import { useState } from 'react'
import api from '../api'

export default function GodTools() {
    const [file, setFile] = useState(null)
    const [analysis, setAnalysis] = useState(null)
    const [loading, setLoading] = useState(false)
    const [populating, setPopulating] = useState(false)
    const [endDate, setEndDate] = useState('')
    const [successMsg, setSuccessMsg] = useState('')

    const handleAnalize = async () => {
        if (!file) return
        setLoading(true)
        const formData = new FormData()
        formData.append('file', file)
        try {
            const res = await api.analyzeHistory(formData)
            setAnalysis(res)
        } catch (e) {
            alert(e.message)
        } finally {
            setLoading(false)
        }
    }

    const handlePopulate = async () => {
        if (!endDate || !analysis) return
        setPopulating(true)
        try {
            const res = await api.autoPopulateMarket({
                end_date: endDate,
                analysis_results: analysis,
                use_saved_model: false
            })
            setSuccessMsg(res.message)
        } catch (e) {
            alert(e.message)
        } finally {
            setPopulating(false)
        }
    }

    return (
        <div className="container">
            <div className="page-header">
                <h1>🛠️ God Mode (Dev Tools)</h1>
                <p className="text-secondary">Developer experimental ML models and market manipulation tools.</p>
            </div>

            <div className="grid">
                <div className="card">
                    <h2>Deploy ML Model: Auto-Populator</h2>
                    <p>Analyze sample CSV data to train weights, then forecast and populate the market with synthetic price history.</p>

                    <div className="form-group mt-2">
                        <label>1. Upload Training Data (.csv)</label>
                        <input type="file" accept=".csv" onChange={e => setFile(e.target.files[0])} />
                        <button className="btn btn--primary mt-1" onClick={handleAnalize} disabled={!file || loading}>
                            {loading ? 'Training Model...' : 'Train Analysis Model'}
                        </button>
                    </div>

                    {analysis && (
                        <div className="mt-2 p-1 bg-light border-radius">
                            <span className="status status--active">Model Trained</span>
                            <div className="mt-1" style={{ fontSize: '0.85rem' }}>
                                <strong>Weights Detected:</strong>
                                <ul>
                                    {Object.entries(analysis.suggested_location_weights).map(([loc, w]) => (
                                        <li key={loc}>{loc}: {w}x</li>
                                    ))}
                                </ul>
                            </div>

                            <div className="form-group mt-2">
                                <label>2. Forecast Until Date</label>
                                <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} />
                                <p className="text-secondary small">The model will generate synthetic slots and price curves based on trained probability distributions.</p>
                                <button
                                    className="btn btn--danger mt-1"
                                    style={{ width: '100%' }}
                                    onClick={handlePopulate}
                                    disabled={!endDate || populating}
                                >
                                    {populating ? 'Generating Synthetic Market...' : 'Auto-Populate Market (Apply ML Model)'}
                                </button>
                            </div>
                        </div>
                    )}

                    {successMsg && (
                        <div className="notification notification--success mt-2">
                            {successMsg}
                        </div>
                    )}
                </div>

                <div className="card">
                    <h2>Other Models (Coming Soon)</h2>
                    <div className="text-secondary" style={{ fontStyle: 'italic' }}>
                        <p>• RNN Price Predictor (In Lab)</p>
                        <p>• BERT Agent Chat Sentiment (Experimental)</p>
                        <p>• Reinforcement Learning Auctioneer (Alpha)</p>
                    </div>
                </div>
            </div>
        </div>
    )
}
