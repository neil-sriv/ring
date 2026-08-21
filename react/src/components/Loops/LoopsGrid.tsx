import type { MinimalLetter, PublicLetter } from "../../client"
import { LoopCard } from "./LoopCard"

export function LoopsGrid({
  loops,
  heading,
  subheading,
  includeGroupName = false,
  showLoopTypeLabel = false,
  showResponderCount = false,
}: {
  loops: MinimalLetter[] | PublicLetter[]
  heading: string
  subheading?: string
  includeGroupName?: boolean
  showLoopTypeLabel?: boolean
  showResponderCount?: boolean
}): JSX.Element {
  return (
    <div className="flex w-full flex-col gap-4">
      <div>
        <h3 className="text-base font-semibold">{heading}</h3>
        {subheading && (
          <p className="mt-1 text-sm text-muted-foreground">{subheading}</p>
        )}
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {loops.map((loop) => (
          <LoopCard
            key={loop.api_identifier}
            loop={loop}
            includeGroupName={includeGroupName}
            showLoopTypeLabel={showLoopTypeLabel}
            showResponderCount={showResponderCount}
          />
        ))}
      </div>
    </div>
  )
}
