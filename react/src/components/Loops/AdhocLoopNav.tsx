import { Button } from "@/components/ui/button"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus } from "lucide-react"
import { useState } from "react"
import type { GroupLinked, MinimalLetter } from "../../client"
import {
  listLettersLettersLettersGetQueryKey,
  readUserMePartiesMeGetOptions,
} from "../../client/@tanstack/react-query.gen"
import AddAdhocLoop from "./AddAdhocLoop"

type AdhocLoopNavProps = {
  loops: MinimalLetter[]
  group: GroupLinked
}

function AdhocLoopNav(props: AdhocLoopNavProps): JSX.Element {
  const [addAdhocLoopOpen, setAddAdhocLoopOpen] = useState(false)
  const queryClient = useQueryClient()
  // Subscribe so admin chrome ("Create Adhoc Loop") updates when /me is
  // refetched or overwritten in cache. getQueryData alone never re-renders.
  const { data: currentUser } = useQuery({
    ...readUserMePartiesMeGetOptions(),
  })
  const isAdmin =
    props.group.admin.api_identifier === currentUser?.api_identifier

  const onClick = (): void => {
    queryClient.invalidateQueries({
      queryKey: listLettersLettersLettersGetQueryKey({
        query: { group_api_id: props.group.api_identifier },
      }),
    })
    setAddAdhocLoopOpen(true)
  }

  return (
    <>
      <div className="flex">
        {isAdmin && (
          <Button onClick={() => onClick()}>
            <Plus className="h-4 w-4" />
            Create Adhoc Loop
          </Button>
        )}
        <AddAdhocLoop
          isOpen={addAdhocLoopOpen}
          onClose={() => setAddAdhocLoopOpen(false)}
          groupApiId={props.group.api_identifier}
        />
      </div>
    </>
  )
}

export default AdhocLoopNav
