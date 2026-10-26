import { Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { DecisionRow } from '../api/types'

const timeFmt = new Intl.DateTimeFormat('en-GB', {
  timeZone: 'Europe/London',
  hour: '2-digit',
  minute: '2-digit',
})

interface ChartPoint {
  time: string
  forecast: number | null
  actual: number | null
  conservative: number | null
  publish: string | null
}

const fmt = (v: number | null | undefined): string =>
  v == null ? '–' : v.toLocaleString('en-GB', { maximumFractionDigits: 1 })

export default function ForecastChart({
  rows,
  bufferMw,
}: {
  rows: DecisionRow[]
  bufferMw: number | null
}) {
  const data: ChartPoint[] = rows.map((r) => ({
    time: timeFmt.format(new Date(r.start_time)),
    forecast: r.forecast_mw,
    actual: r.actual_mw,
    conservative:
      r.forecast_mw != null && bufferMw != null ? r.forecast_mw - bufferMw : null,
    publish: r.publish_time,
  }))
  const ticks = data.filter((_, i) => i % 6 === 0).map((d) => d.time)

  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
        <XAxis dataKey="time" ticks={ticks} tick={{ fontSize: 12 }} />
        <YAxis
          width={64}
          tick={{ fontSize: 12 }}
          tickFormatter={(v: number) => v.toLocaleString('en-GB')}
        />
        <Tooltip
          content={(raw: unknown) => {
            const props = raw as { active?: boolean; payload?: ReadonlyArray<{ payload: ChartPoint }> }
            const point = props.payload?.[0]?.payload
            if (!props.active || !point) return null
            return (
              <div className="chart-tip">
                <b>{point.time}</b>
                <div>Forecast: {fmt(point.forecast)} MW</div>
                <div>Actual: {fmt(point.actual)} MW</div>
                <div>Conservative: {fmt(point.conservative)} MW</div>
                <div>Publish: {point.publish ?? 'no forecast'}</div>
              </div>
            )
          }}
        />
        <Legend />
        <Line
          type="stepAfter"
          dataKey="forecast"
          name="Decision forecast (MW)"
          stroke="#2563eb"
          strokeWidth={2}
          dot={false}
          connectNulls={false}
        />
        <Line
          type="monotone"
          dataKey="actual"
          name="Actual (MW)"
          stroke="#b45309"
          strokeWidth={2}
          dot={false}
          connectNulls={false}
        />
        <Line
          type="stepAfter"
          dataKey="conservative"
          name="Conservative wind (MW)"
          stroke="#6b7280"
          strokeWidth={2}
          strokeDasharray="6 4"
          dot={false}
          connectNulls={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
