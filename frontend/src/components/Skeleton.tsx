type BlockProps = {
  w?: string
  h?: number
  r?: number
}

export function SkeletonBlock({ w = '100%', h = 12, r = 6 }: BlockProps) {
  return <span className="skel" style={{ width: w, height: h, borderRadius: r }} />
}

export function SkeletonStats({ n }: { n: number }) {
  return (
    <section className="stats" aria-hidden="true">
      {Array.from({ length: n }, (_, i) => (
        <div className="stat" key={i}>
          <SkeletonBlock w="64%" h={20} />
          <div className="skel-gap" />
          <SkeletonBlock w="44%" h={10} />
        </div>
      ))}
    </section>
  )
}

export function SkeletonPanel({ h = 320, lines = 0 }: { h?: number; lines?: number }) {
  return (
    <section className="section-body" aria-hidden="true">
      <SkeletonBlock w="100%" h={h} r={12} />
      {lines > 0 && (
        <div className="skel-stack">
          {Array.from({ length: lines }, (_, i) => (
            <SkeletonBlock key={i} w={i % 3 === 0 ? '82%' : '96%'} h={11} />
          ))}
        </div>
      )}
    </section>
  )
}

export function SkeletonRows({ rows = 8, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <section className="section-body" aria-hidden="true">
      <div className="skel-rows">
        {Array.from({ length: rows }, (_, r) => (
          <div className="skel-row" key={r}>
            {Array.from({ length: cols }, (_, c) => (
              <SkeletonBlock key={c} w={c === 0 ? '52%' : '70%'} h={11} />
            ))}
          </div>
        ))}
      </div>
    </section>
  )
}

export function SkeletonStatus({ label }: { label: string }) {
  return (
    <p className="sr-only" role="status">
      {label}
    </p>
  )
}
