import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Edit,
  MoreVertical,
  Settings,
  Trash2,
  User,
  UserPlus,
} from "lucide-react"
import { useState } from "react"

import { useNavigate } from "@tanstack/react-router"
import type { GroupLinked, UserLinked } from "../../client"
import EditUser from "../Admin/EditUser"
import ImpersonateUser from "../Admin/ImpersonateUser"
import AddMembers from "../Groups/AddMembers"
import EditGroup from "../Groups/EditGroup"
import Delete from "./DeleteAlert"

interface ActionsMenuProps {
  type: string
  value: GroupLinked | UserLinked
  disabled?: boolean
}

const ActionsMenu = ({ type, value, disabled }: ActionsMenuProps) => {
  const [isEditOpen, setIsEditOpen] = useState(false)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [isAddMembersOpen, setIsAddMembersOpen] = useState(false)
  const [isImpersonateOpen, setIsImpersonateOpen] = useState(false)
  const navigate = useNavigate()

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" disabled={disabled}>
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
              className="text-destructive"
            >
              <User className="h-4 w-4" />
              Impersonate User
            </DropdownMenuItem>
          )}
          <DropdownMenuItem
            onClick={() => setIsDeleteOpen(true)}
            className="text-destructive"
          >
            <Trash2 className="h-4 w-4" />
            Delete {type}
          </DropdownMenuItem>
          {type === "Group" && (
            <>
              <DropdownMenuItem onClick={() => setIsAddMembersOpen(true)}>
                <UserPlus className="h-4 w-4" />
                Add Members
              </DropdownMenuItem>
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
      <Delete
        type={type}
        id={value.api_identifier}
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
      />
    </>
  )
}

export default ActionsMenu
