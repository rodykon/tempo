const WIDTH = 280
const HEIGHT = 140
const CHART_HEIGHT = HEIGHT - 24

function formatDuration(seconds) {
  const totalMinutes = Math.round(seconds / 60)
  const h = Math.floor(totalMinutes / 60)
  const m = totalMinutes % 60
  if (h === 0) return `${m}m`
  return `${h}h ${m}m`
}

// Dependency-free inline SVG: 7 equally-spaced day columns, bar height
// proportional to that day's time_spent, dotted vertical lines marking the
// transition between days. A plain-text per-day summary underneath makes
// the same data assertable in tests without inspecting SVG geometry.
export default function WeeklyChart({ week }) {
  const { days } = week
  const max = Math.max(...days.map(d => d.time_spent), 1)
  const colWidth = WIDTH / days.length
  const summary = days.map(d => `${d.weekday} ${formatDuration(d.time_spent)}`).join(', ')

  return (
    <div className="weekly-chart">
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={`Time spent per day this week: ${summary}`}
      >
        {days.slice(1).map((_, i) => {
          const x = colWidth * (i + 1)
          return (
            <line
              key={`sep-${i}`}
              x1={x} y1={0} x2={x} y2={CHART_HEIGHT}
              stroke="var(--border)"
              strokeDasharray="3 3"
            />
          )
        })}
        {days.map((d, i) => {
          const barHeight = Math.max((d.time_spent / max) * (CHART_HEIGHT - 8), d.time_spent > 0 ? 2 : 0)
          const barWidth = colWidth * 0.5
          const x = colWidth * i + colWidth * 0.25
          const y = CHART_HEIGHT - barHeight
          return (
            <rect key={d.date} x={x} y={y} width={barWidth} height={barHeight} fill="var(--primary)" rx="3" />
          )
        })}
        {days.map((d, i) => (
          <text
            key={`label-${d.date}`}
            x={colWidth * i + colWidth / 2}
            y={HEIGHT - 6}
            textAnchor="middle"
            fontSize="11"
            fill="var(--muted)"
          >
            {d.weekday}
          </text>
        ))}
      </svg>
      <ul className="weekly-chart-summary">
        {days.map(d => (
          <li key={d.date}>{d.weekday} {formatDuration(d.time_spent)}</li>
        ))}
      </ul>
    </div>
  )
}
