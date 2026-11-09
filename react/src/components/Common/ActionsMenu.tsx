import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useQuery } from "@tanstack/react-query"
import { Edit, MoreVertical, Settings, User, UserPlus } from "lucide-react"
import { useState } from "react"

import { useNavigate } from "@tanstack/react-router"
import type { GroupLinked, UserLinked } from "../../client"
import { readUserMePartiesMeGetOptions } from "../../client/@tanstack/react-query.gen"
import EditUser from "../Admin/EditUser"
import ImpersonateUser from "../Admin/ImpersonateUser"
import AddMembers from "../Groups/AddMembers"
import EditGroup from "../Groups/EditGroup"

interface ActionsMenuProps {
  type: string
  value: GroupLinked | UserLinked
  disabled?: boolean
}

const ActionsMenu = ({ type, value, disabled }: ActionsMenuProps) => {
  const [isEditOpen, setIsEditOpen] = useState(false)
  const [isAddMembersOpen, setIsAddMembersOpen] = useState(false)
  const [isImpersonateOpen, setIsImpersonateOpen] = useState(false)
  const navigate = useNavigate()
  // Subscribe so admin-only items (Add Members) update when /me is
  // refetched or overwritten in cache. getQueryData alone never re-renders.
  const { data: currentUser } = useQuery({
    ...readUserMePartiesMeGetOptions(),
  })
  const isGroupAdmin =
    type === "Group" &&
    (value as GroupLinked).admin.api_identifier === currentUser?.api_identifier

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            disabled={disabled}
            className="text-muted-foreground hover:text-foreground"
          >
            <MoreVertical className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => setIsEditOpen(true)}>
            <Edit className="h-4 w-4" />
            Edit {type}
          </DropdownMenuItem>
          {type === "User" && (
            <DropdownMenuItem
              onClick={() => setIsImpersonateOpen(true)}
              className="text-destructive focus:text-destructive [&>svg]:text-destructive"
            >
              <User className="h-4 w-4" />
              Impersonate User
            </DropdownMenuItem>
          )}
          {type === "Group" && (
            <>
              {isGroupAdmin && (
                <DropdownMenuItem onClick={() => setIsAddMembersOpen(true)}>
                  <UserPlus className="h-4 w-4" />
                  Add Members
                </DropdownMenuItem>
              )}
              <DropdownMenuItem
                onClick={() =>
                  navigate({
                    to: "/groups/$groupId/settings",
                    params: { groupId: value.api_identifier },
                  })
                }
              >
                <Settings className="h-4 w-4" />
                Settings
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
      {type === "User" ? (
        <>
          <EditUser
            user={value as UserLinked}
            isOpen={isEditOpen}
            onClose={() => setIsEditOpen(false)}
          />
          <ImpersonateUser
            user={value as UserLinked}
            isOpen={isImpersonateOpen}
            onClose={() => setIsImpersonateOpen(false)}
          />
        </>
      ) : (
        <>
          <EditGroup
            group={value as GroupLinked}
            isOpen={isEditOpen}
            onClose={() => setIsEditOpen(false)}
          />
          <AddMembers
            group={value as GroupLinked}
            isOpen={isAddMembersOpen}
            onClose={() => setIsAddMembersOpen(false)}
          />
        </>
      )}
    </>
  )
}

export default ActionsMenu
