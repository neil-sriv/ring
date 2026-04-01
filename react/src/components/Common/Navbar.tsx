import { Plus } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import AddUser from "../Admin/AddUser"
import AddGroup from "../Groups/AddGroup"

interface NavbarProps {
  type: string
}

const Navbar = ({ type }: NavbarProps) => {
  const [isAddUserOpen, setIsAddUserOpen] = useState(false)
  const [isAddGroupOpen, setIsAddGroupOpen] = useState(false)

  const onClick = (type: string): void => {
    if (type === "User") {
      setIsAddUserOpen(true)
    } else if (type === "Group") {
      setIsAddGroupOpen(true)
    }
  }
  return (
    <>
      <div className="flex items-center gap-4 py-6">
        {/* TODO: Complete search functionality */}
        <Button onClick={() => onClick(type)} className="gap-1">
          <Plus className="h-4 w-4" /> Add {type}
        </Button>
        <AddUser
          isOpen={isAddUserOpen}
          onClose={() => setIsAddUserOpen(false)}
        />
        <AddGroup
          isOpen={isAddGroupOpen}
          onClose={() => setIsAddGroupOpen(false)}
        />
      </div>
    </>
  )
}

export default Navbar
