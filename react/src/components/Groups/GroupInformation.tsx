import { useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"

import type { GroupLinked } from "../../client"
import { readGroupPartiesGroupGroupApiIdGetQueryKey } from "../../client/@tanstack/react-query.gen"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
  if (group === undefined) {
    return null
  }
  const { register } = useForm<GroupLinked>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: group.name,
    },
  })

  const toggleEditMode = () => {
    setEditMode(!editMode)
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Group Information</CardTitle>
        <Button variant="outline" onClick={toggleEditMode}>
          Edit
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>Name</Label>
          {editMode ? (
            <Input
              id="name"
              {...register("name", { maxLength: 30 })}
              type="text"
            />
          ) : (
            <p className="text-foreground">{group.name || "N/A"}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label>Created At</Label>
          <p className="text-foreground">
            {new Date(group.created_at).toLocaleDateString()}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

export default GroupInformation
