import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler)

export default function PriceChart({ data, labels, height = 200, mini = false }) {
  if (!data || data.length === 0) return <div className="text-secondary">No price data</div>

  const chartData = {
    labels: labels || data.map((_, i) => i + 1),
    datasets: [
      {
        data: data.map((d) => (typeof d === 'number' ? d : d.price)),
        borderColor: '#c23a2e',
        backgroundColor: 'rgba(194, 58, 46, 0.06)',
        borderWidth: mini ? 1.5 : 2,
        pointRadius: mini ? 0 : 2,
        pointHoverRadius: mini ? 0 : 4,
        tension: 0.3,
        fill: true,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: !mini,
        callbacks: {
          label: (ctx) => `${ctx.parsed.y.toFixed(1)} tokens`,
        },
      },
    },
    scales: {
      x: {
        display: !mini,
        grid: { display: false },
        ticks: {
          font: { family: "'JetBrains Mono', monospace", size: 10 },
          color: '#6b6b6b',
          maxRotation: labels ? 45 : 0,
          autoSkip: true,
          maxTicksLimit: 12,
        },
      },
      y: {
        display: !mini,
        grid: { color: '#e0dcd6' },
        ticks: {
          font: { family: "'JetBrains Mono', monospace", size: 10 },
          color: '#6b6b6b',
        },
      },
    },
  }

  return (
    <div style={{ height }}>
      <Line data={chartData} options={options} />
    </div>
  )
}
