import { useState } from 'react'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'
import api from '../api'

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
)

export default function HistoricalAnalysis() {
    const [file, setFile] = useState(null)
    const [analysis, setAnalysis] = useState(null)
    const [loading, setLoading] = useState(false)

    const handleUpload = async () => {
        if (!file) return
        setLoading(true)
        const formData = new FormData()
        formData.append('file', file)

        try {
            // Note: We need to bypass the default JSON header in api.js
            // The modified api.js `request` function handles this if we pass empty headers
            const res = await api.analyzeHistory(formData)
            setAnalysis(res)
        } catch (e) {
            alert('Analysis failed: ' + e.message)
        } finally {
            setLoading(false)
        }
    }

    const locationData = analysis ? {
        labels: Object.keys(analysis.suggested_location_weights),
        datasets: [
            {
                label: 'Suggested Multiplier',
                data: Object.values(analysis.suggested_location_weights),
                backgroundColor: 'rgba(53, 162, 235, 0.5)',
            },
        ],
    } : null

    const timeData = analysis ? {
        labels: Object.keys(analysis.suggested_time_weights).sort(),
        datasets: [
            {
                label: 'Hourly Multiplier',
                data: Object.keys(analysis.suggested_time_weights).sort().map(k => analysis.suggested_time_weights[k]),
                backgroundColor: 'rgba(255, 99, 132, 0.5)',
            },
        ],
    } : null

    return (
        <div className="container">
            <h1>Historical Data Analysis</h1>
            <p className="description">
                Upload a CSV file containing <code>location</code>, <code>time_slot</code>, and <code>day</code> columns to detect demand patterns.
            </p>

            <div className="card" style={{ maxWidth: '600px', margin: '2rem 0' }}>
                <div className="form-group">
                    <label>Upload CSV</label>
                    <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files[0])} />
                </div>
                <button
                    className="btn btn-primary"
                    onClick={handleUpload}
                    disabled={!file || loading}
                >
                    {loading ? 'Analyzing...' : 'Analyze Data'}
                </button>
            </div>

            {analysis && (
                <div className="grid">
                    <div className="card">
                        <h3>Location Weights</h3>
                        <Bar data={locationData} options={{ responsive: true }} />
                    </div>
                    <div className="card">
                        <h3>Time of Day Weights</h3>
                        <Bar data={timeData} options={{ responsive: true }} />
                    </div>
                </div>
            )}

            {analysis?.detected_events?.length > 0 && (
                <div className="card" style={{ marginTop: '2rem' }}>
                    <h3>⚠️ Detected Seasonality Events</h3>
                    <p>The following days showed abnormally high booking volume:</p>
                    <ul>
                        {analysis.detected_events.map((ev, i) => (
                            <li key={i}>
                                <strong>Day {ev.day}</strong>: {ev.volume} bookings (Suggested Multiplier: {ev.multiplier_suggestion}x)
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    )
}
