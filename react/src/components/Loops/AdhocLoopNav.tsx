import { Button } from "@/components/ui/button"
import { useQueryClient } from "@tanstack/react-query"
import { Plus } from "lucide-react"
import { useState } from "react"
import type { GroupLinked, MinimalLetter } from "../../client"
import AddAdhocLoop from "./AddAdhocLoop"

type AdhocLoopNavProps = {
  loops: MinimalLetter[]
  group: GroupLinked
}

function AdhocLoopNav(props: AdhocLoopNavProps): JSX.Element {
  const [addAdhocLoopOpen, setAddAdhocLoopOpen] = useState(false)
  const queryClient = useQueryClient()

  const onClick = (): void => {
    queryClient.invalidateQueries({
      queryKey: [{ _id: "listLettersLettersLettersGet" }],
    })
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
