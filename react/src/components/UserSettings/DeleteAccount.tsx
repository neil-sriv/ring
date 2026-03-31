import { Button } from "@/components/ui/button"
import { useState } from "react"
import DeleteConfirmation from "./DeleteConfirmation"

const DeleteAccount = () => {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="w-full">
      <div className="flex flex-col gap-6">
        <h3 className="text-sm font-semibold text-foreground">
          Delete Account
        </h3>
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <div className="flex flex-col gap-4">
            <p className="text-foreground">
              Permanently delete your data and everything associated with your
              account.
            </p>
            <Button variant="destructive" onClick={() => setIsOpen(true)}>
              Delete
            </Button>
          </div>
        </div>
        <DeleteConfirmation isOpen={isOpen} onClose={() => setIsOpen(false)} />
      </div>
    </div>
  )
}

export default DeleteAccount
