import { useState, useEffect, useRef } from 'react'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'
import api from '../api'

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend
)

export default function PettingZooSimulator() {
    // Config state
    const [numAgents, setNumAgents] = useState(30)
    const [numRooms, setNumRooms] = useState(5)
    const [maxDays, setMaxDays] = useState(14)
    const [startPrice, setStartPrice] = useState(100)
    const [minPrice, setMinPrice] = useState(10)
    const [priceStep, setPriceStep] = useState(5)
    const [maxTicks, setMaxTicks] = useState(20)
    const [hdStart, setHdStart] = useState(10)
    const [hdEnd, setHdEnd] = useState(14)
    const [numSeeds, setNumSeeds] = useState(3)

    // Grid search ranges
    const [amountsStr, setAmountsStr] = useState('50, 75, 100, 125, 150, 200')
    const [freqsStr, setFreqsStr] = useState('3, 5, 7, 10, 14')

    // Job state
    const [jobId, setJobId] = useState(null)
    const [progress, setProgress] = useState(0)
    const [running, setRunning] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)
    const pollRef = useRef(null)

    // Single sim state
    const [singleAmount, setSingleAmount] = useState(100)
    const [singleFreq, setSingleFreq] = useState(7)
    const [singleResult, setSingleResult] = useState(null)
    const [singleLoading, setSingleLoading] = useState(false)

    // Apply state
    const [applying, setApplying] = useState(false)

    useEffect(() => {
        return () => {
            if (pollRef.current) clearInterval(pollRef.current)
        }
    }, [])

    const parseList = (str, parser) => str.split(',').map(s => parser(s.trim())).filter(v => !isNaN(v))

    const buildConfig = () => ({
        num_agents: numAgents,
        num_rooms: numRooms,
        slots_per_room_per_day: 3,
        max_days: maxDays,
        auction_start_price: startPrice,
        auction_min_price: minPrice,
        auction_price_step: priceStep,
        max_ticks: maxTicks,
        high_demand_days: [[hdStart, hdEnd]],
        token_amount: singleAmount,
        token_frequency: singleFreq,
    })

    const runGridSearch = async () => {
        setRunning(true)
        setError(null)
        setResult(null)
        setProgress(0)
        try {
            const res = await api.runPZGridSearch({
                config: buildConfig(),
                token_amounts: parseList(amountsStr, parseFloat),
                token_frequencies: parseList(freqsStr, parseInt),
                num_seeds: numSeeds,
            })
            setJobId(res.job_id)

            const startTime = Date.now()
            pollRef.current = setInterval(async () => {
                try {
                    const status = await api.getPZStatus(res.job_id)
                    setProgress(status.progress)
                    if (status.status === 'completed') {
                        clearInterval(pollRef.current)
                        pollRef.current = null
                        setResult(status.result)
                        setRunning(false)
                    } else if (status.status === 'failed') {
                        clearInterval(pollRef.current)
                        pollRef.current = null
                        setError(status.error || 'Grid search failed')
                        setRunning(false)
                    } else if (Date.now() - startTime > 300000) {
                        // 5 minute timeout
                        clearInterval(pollRef.current)
                        pollRef.current = null
                        setError('Grid search timed out after 5 minutes')
                        setRunning(false)
                    }
                } catch (e) {
                    clearInterval(pollRef.current)
                    pollRef.current = null
                    setError(e.message)
                    setRunning(false)
                }
            }, 500)
        } catch (e) {
            setError(e.message)
            setRunning(false)
        }
    }

    const runSingle = async () => {
        setSingleLoading(true)
        setSingleResult(null)
        try {
            const res = await api.runPZSingle(buildConfig())
            setSingleResult(res)
        } catch (e) {
            alert(e.message)
        } finally {
            setSingleLoading(false)
        }
    }

    const applyBest = async () => {
        if (!result?.best) return
        if (!window.confirm(`Apply token_amount=${result.best.token_amount}, frequency=${result.best.token_frequency} to live system?`)) return
        setApplying(true)
        try {
            await api.applyPZBest({
                token_amount: result.best.token_amount,
                token_frequency: result.best.token_frequency,
            })
            alert('Admin config updated!')
        } catch (e) {
            alert(e.message)
        } finally {
            setApplying(false)
        }
    }

    // Chart: heatmap as a grouped bar (stability scores by amount, grouped by frequency)
    const getHeatmapChart = () => {
        if (!result?.heatmap) return null
        const { amounts, frequencies, scores } = result.heatmap
        const colors = ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff', '#ff9f40']
        return {
            labels: amounts.map(a => `${a} tokens`),
            datasets: frequencies.map((freq, fi) => ({
                label: `Every ${freq} days`,
                data: scores[fi] || [],
                backgroundColor: colors[fi % colors.length],
            })),
        }
    }

    // Chart: daily utilization + avg price for best config
    const getDailyChart = () => {
        const daily = result?.best_daily || singleResult?.daily_detail
        if (!daily) return null
        const days = Object.keys(daily.utilization || {}).sort((a, b) => parseInt(a) - parseInt(b))
        return {
            labels: days.map(d => `Day ${d}`),
            datasets: [
                {
                    label: 'Utilization',
                    data: days.map(d => daily.utilization[d] || 0),
                    borderColor: '#4bc0c0',
                    backgroundColor: '#4bc0c0',
                    yAxisID: 'y',
                    tension: 0.3,
                },
                {
                    label: 'Avg Price',
                    data: days.map(d => daily.avg_price[d] || 0),
                    borderColor: '#ff6384',
                    backgroundColor: '#ff6384',
                    yAxisID: 'y1',
                    tension: 0.3,
                },
            ],
        }
    }

    // Chart: top 5 allocations comparison
    const getTop5Chart = () => {
        if (!result?.all_results?.length) return null
        const top5 = result.all_results.slice(0, 5)
        return {
            labels: top5.map(r => `${r.token_amount}t / ${r.token_frequency}d`),
            datasets: [
                {
                    label: 'Stability Score',
                    data: top5.map(r => r.stability_score),
                    backgroundColor: '#36a2eb',
                },
                {
                    label: 'Utilization',
                    data: top5.map(r => r.utilization_rate),
                    backgroundColor: '#4bc0c0',
                },
                {
                    label: 'Unmet Demand',
                    data: top5.map(r => r.unmet_demand),
                    backgroundColor: '#ff6384',
                },
            ],
        }
    }

    const dualAxisOpts = {
        responsive: true,
        interaction: { mode: 'index', intersect: false },
        scales: {
            y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'Utilization' } },
            y1: { type: 'linear', display: true, position: 'right', title: { display: true, text: 'Avg Price' }, grid: { drawOnChartArea: false } },
        },
    }

    return (
        <div className="container">
            <div className="page-header">
                <h1>PettingZoo Simulator</h1>
                <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>
                    Find optimal token allocation via multi-agent simulation
                </p>
            </div>

            {/* Config Panel */}
            <div className="card" style={{ marginBottom: '2rem' }}>
                <h2 style={{ marginTop: 0 }}>Configuration</h2>
                <div className="grid">
                    <div className="form-group">
                        <label>Agents</label>
                        <input type="number" value={numAgents} onChange={e => setNumAgents(parseInt(e.target.value) || 30)} />
                    </div>
                    <div className="form-group">
                        <label>Rooms</label>
                        <input type="number" value={numRooms} onChange={e => setNumRooms(parseInt(e.target.value) || 5)} />
                    </div>
                    <div className="form-group">
                        <label>Sim Days</label>
                        <input type="number" value={maxDays} onChange={e => setMaxDays(parseInt(e.target.value) || 14)} />
                    </div>
                    <div className="form-group">
                        <label>Max Ticks</label>
                        <input type="number" value={maxTicks} onChange={e => setMaxTicks(parseInt(e.target.value) || 20)} />
                    </div>
                </div>

                <div className="grid" style={{ marginTop: '1rem' }}>
                    <div className="form-group">
                        <label>Auction Start Price</label>
                        <input type="number" value={startPrice} onChange={e => setStartPrice(parseFloat(e.target.value) || 100)} />
                    </div>
                    <div className="form-group">
                        <label>Auction Min Price</label>
                        <input type="number" value={minPrice} onChange={e => setMinPrice(parseFloat(e.target.value) || 10)} />
                    </div>
                    <div className="form-group">
                        <label>Price Step</label>
                        <input type="number" value={priceStep} onChange={e => setPriceStep(parseFloat(e.target.value) || 5)} />
                    </div>
                </div>

                <div className="grid" style={{ marginTop: '1rem' }}>
                    <div className="form-group">
                        <label>High-Demand Start Day</label>
                        <input type="number" value={hdStart} onChange={e => setHdStart(parseInt(e.target.value) || 10)} />
                    </div>
                    <div className="form-group">
                        <label>High-Demand End Day</label>
                        <input type="number" value={hdEnd} onChange={e => setHdEnd(parseInt(e.target.value) || 14)} />
                    </div>
                    <div className="form-group">
                        <label>Seeds per Combo</label>
                        <input type="number" value={numSeeds} onChange={e => setNumSeeds(parseInt(e.target.value) || 3)} />
                    </div>
                </div>

                <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--color-border)', paddingTop: '1rem' }}>
                    <h3 style={{ margin: '0 0 0.75rem' }}>Grid Search Ranges</h3>
                    <div className="grid">
                        <div className="form-group">
                            <label>Token Amounts (comma-separated)</label>
                            <input type="text" value={amountsStr} onChange={e => setAmountsStr(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>Frequencies in days (comma-separated)</label>
                            <input type="text" value={freqsStr} onChange={e => setFreqsStr(e.target.value)} />
                        </div>
                    </div>
                </div>

                <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                    <button className="btn btn--primary" onClick={runGridSearch} disabled={running} style={{ minWidth: '12rem', position: 'relative', overflow: 'hidden' }}>
                        {running && (
                            <span style={{
                                position: 'absolute', left: 0, top: 0, bottom: 0,
                                width: `${Math.max(progress * 100, 2)}%`,
                                background: 'rgba(255,255,255,0.2)',
                                transition: 'width 0.3s ease',
                            }} />
                        )}
                        <span style={{ position: 'relative' }}>
                            {running
                                ? (progress > 0 ? `Searching... ${(progress * 100).toFixed(0)}%` : 'Starting...')
                                : 'Run Grid Search'}
                        </span>
                    </button>

                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <input type="number" value={singleAmount} onChange={e => setSingleAmount(parseFloat(e.target.value) || 100)} style={{ width: '5rem' }} />
                        <span>tokens /</span>
                        <input type="number" value={singleFreq} onChange={e => setSingleFreq(parseInt(e.target.value) || 7)} style={{ width: '4rem' }} />
                        <span>days</span>
                        <button className="btn btn--secondary" onClick={runSingle} disabled={singleLoading}>
                            {singleLoading ? 'Running...' : 'Run Single'}
                        </button>
                    </div>
                </div>
            </div>

            {error && (
                <div className="card notification notification--error" style={{ marginBottom: '2rem' }}>
                    <strong>Error:</strong> {error}
                </div>
            )}

            {/* Best Result Hero */}
            {result?.best && (
                <div className="card notification notification--success" style={{ marginBottom: '2rem' }}>
                    <h2 style={{ marginTop: 0 }}>Best Allocation Found</h2>
                    <div className="grid">
                        <div>
                            <div style={{ fontSize: '2rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                                {result.best.token_amount} tokens
                            </div>
                            <div style={{ color: 'var(--color-text-secondary)' }}>every {result.best.token_frequency} days</div>
                        </div>
                        <div>
                            <div style={{ fontSize: '2rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                                {result.best.stability_score.toFixed(3)}
                            </div>
                            <div style={{ color: 'var(--color-text-secondary)' }}>stability score (lower = better)</div>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.85rem' }}>
                            <div>Utilization: {(result.best.utilization_rate * 100).toFixed(1)}%</div>
                            <div>S/D Ratio: {result.best.supply_demand_ratio.toFixed(2)}</div>
                            <div>Price Vol: {result.best.price_volatility.toFixed(3)}</div>
                            <div>Unmet: {(result.best.unmet_demand * 100).toFixed(1)}%</div>
                            <div>Gini: {result.best.gini_coefficient.toFixed(3)}</div>
                        </div>
                    </div>
                    <button
                        className="btn btn--primary"
                        style={{ marginTop: '1rem' }}
                        onClick={applyBest}
                        disabled={applying}
                    >
                        {applying ? 'Applying...' : 'Apply to Live System'}
                    </button>
                </div>
            )}

            {/* Single sim metrics */}
            {singleResult && (
                <div className="card" style={{ marginBottom: '2rem' }}>
                    <h2 style={{ marginTop: 0 }}>Single Simulation Results</h2>
                    <div className="grid">
                        <div>Stability Score: <strong>{singleResult.metrics.stability_score.toFixed(3)}</strong></div>
                        <div>Utilization: <strong>{(singleResult.metrics.utilization_rate * 100).toFixed(1)}%</strong></div>
                        <div>S/D Ratio: <strong>{singleResult.metrics.supply_demand_ratio.toFixed(2)}</strong></div>
                        <div>Price Volatility: <strong>{singleResult.metrics.price_volatility.toFixed(3)}</strong></div>
                        <div>Unmet Demand: <strong>{(singleResult.metrics.unmet_demand * 100).toFixed(1)}%</strong></div>
                        <div>Gini: <strong>{singleResult.metrics.gini_coefficient.toFixed(3)}</strong></div>
                    </div>
                </div>
            )}

            {/* Charts */}
            <div className="grid">
                {getHeatmapChart() && (
                    <div className="card">
                        <h3>Stability by Allocation (Amount x Frequency)</h3>
                        <Bar data={getHeatmapChart()} options={{ responsive: true, plugins: { legend: { position: 'bottom' } } }} />
                    </div>
                )}

                {getDailyChart() && (
                    <div className="card">
                        <h3>Daily Utilization & Avg Price</h3>
                        <Line data={getDailyChart()} options={dualAxisOpts} />
                    </div>
                )}

                {getTop5Chart() && (
                    <div className="card" style={{ gridColumn: '1 / -1' }}>
                        <h3>Top 5 Allocations Comparison</h3>
                        <Bar data={getTop5Chart()} options={{ responsive: true, plugins: { legend: { position: 'bottom' } } }} />
                    </div>
                )}
            </div>
        </div>
    )
}
