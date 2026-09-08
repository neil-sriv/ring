import { useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"

import type { GroupLinked } from "../../client"
import { readGroupPartiesGroupGroupApiIdGetQueryKey } from "../../client/@tanstack/react-query.gen"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

function GroupInformation({ groupId }: { groupId: string }) {
  const queryClient = useQueryClient()
  const [editMode, setEditMode] = useState(false)
  const group = queryClient.getQueryData<GroupLinked>(
    readGroupPartiesGroupGroupApiIdGetQueryKey({
      path: { group_api_id: groupId },
    }),
  )

  // Hooks must run unconditionally — never after the group early-return below.
  const { register, reset } = useForm<GroupLinked>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: group?.name ?? "",
    },
  })

  useEffect(() => {
    if (!group || editMode) {
      return
    }
    reset({ name: group.name })
  }, [group, editMode, reset])

  if (group === undefined) {
    return null
  }

  const toggleEditMode = () => {
    setEditMode(!editMode)
  }

  return (
    <div className="w-full max-w-xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold">Group Information</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            The basics of this group.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={toggleEditMode}>
          Edit
        </Button>
      </div>
      <div className="mt-6 flex flex-col gap-5">
        <div className="flex flex-col gap-1.5">
          <Label>Name</Label>
          {editMode ? (
            <Input
              id="name"
              {...register("name", { maxLength: 30 })}
              type="text"
            />
          ) : (
            <p className="text-sm">{group.name || "N/A"}</p>
          )}
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Created At</Label>
          <p className="text-sm">
            {new Date(group.created_at).toLocaleDateString()}
          </p>
        </div>
      </div>
    </div>
  )
}

export default GroupInformation
