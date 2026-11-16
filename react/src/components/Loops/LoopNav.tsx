import { Plus } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { useQueryClient } from "@tanstack/react-query"
import { useRouter } from "@tanstack/react-router"
import type { GroupLinked, MinimalLetter } from "../../client"
import { listLettersLettersLettersGetQueryKey } from "../../client/@tanstack/react-query.gen"
import AddLetter from "./AddLoop"

type LoopNavProps = {
  loops: MinimalLetter[]
  group: GroupLinked
}

function LoopNav(props: LoopNavProps): JSX.Element {
  const [addLetterOpen, setAddLetterOpen] = useState(false)
  const enabled =
    props.loops.filter((loop) => loop.status === "UPCOMING").length === 0
  const queryClient = useQueryClient()
  const router = useRouter()

  const onClick = (): void => {
    queryClient.invalidateQueries({
      queryKey: listLettersLettersLettersGetQueryKey({
        query: { group_api_id: props.group.api_identifier },
      }),
    })
    router.invalidate()
    enabled ? setAddLetterOpen(true) : null
  }
  return (
    <>
      <div className="flex">
        {props.group.caller_can_admin && (
          <Button onClick={() => onClick()} disabled={!enabled}>
            <Plus className="h-4 w-4" />
            {enabled ? "Start Next Loop" : "Upcoming loop scheduled"}
          </Button>
        )}
        <AddLetter
          isOpen={addLetterOpen}
          onClose={() => setAddLetterOpen(false)}
          groupApiId={props.group.api_identifier}
        />
      </div>
    </>
  )
}

export default LoopNav
