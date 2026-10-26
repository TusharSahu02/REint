export default function DataQualityBanner({
  nMissingForecast,
  nMissingActual,
}: {
  nMissingForecast: number
  nMissingActual: number
}) {
  if (nMissingForecast === 0 && nMissingActual === 0) return null
  return (
    <div className="banner" role="status">
      Data quality: {nMissingForecast} half-hour(s) with no forecast in hand at cutoff,
      {' '}{nMissingActual} with no actual. These slots are excluded from MAE/bias.
    </div>
  )
}
