import { Button } from "@/components/ui/button"
import { useQueryClient } from "@tanstack/react-query"
import { useRouter } from "@tanstack/react-router"
import { Plus } from "lucide-react"
import { useState } from "react"
import type { GroupLinked, MinimalLetter } from "../../client"
import { listLettersLettersLettersGetQueryKey } from "../../client/@tanstack/react-query.gen"
import AddAdhocLoop from "./AddAdhocLoop"

type AdhocLoopNavProps = {
  loops: MinimalLetter[]
  group: GroupLinked
}

function AdhocLoopNav(props: AdhocLoopNavProps): JSX.Element {
  const [addAdhocLoopOpen, setAddAdhocLoopOpen] = useState(false)
  const queryClient = useQueryClient()
  const router = useRouter()

  const onClick = (): void => {
    queryClient.invalidateQueries({
      queryKey: listLettersLettersLettersGetQueryKey({
        query: {
          group_api_id: props.group.api_identifier,
        },
      }),
    })
    router.invalidate()
    setAddAdhocLoopOpen(true)
  }

  return (
    <>
      <div className="flex">
        <Button onClick={() => onClick()}>
          <Plus className="h-4 w-4" />
          Create Adhoc Loop
        </Button>
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
