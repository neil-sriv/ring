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
    <div className="flex w-full flex-col items-center gap-4">
      <div className="w-full text-center">
        <h3 className="text-lg font-semibold">{heading}</h3>
        {subheading && <h4 className="text-sm font-medium">{subheading}</h4>}
      </div>
      <div className="flex w-full flex-wrap justify-center gap-4">
        {loops.map((loop) => (
          <div
            key={loop.api_identifier}
            className="min-w-[200px] flex-[0_1_calc(25%-1rem)]"
          >
            <LoopCard
              loop={loop}
              includeGroupName={includeGroupName}
              showLoopTypeLabel={showLoopTypeLabel}
              showResponderCount={showResponderCount}
            />
          </div>
        ))}
      </div>
    </div>
  )
}
