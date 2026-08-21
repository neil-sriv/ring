import { Button } from "@/components/ui/button"
import { useState } from "react"
import DeleteConfirmation from "./DeleteConfirmation"

const DeleteAccount = () => {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="w-full">
      <h3 className="text-base font-semibold">Danger zone</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Irreversible actions for your account.
      </p>
      <div className="mt-5 max-w-md rounded-lg border border-destructive/25 bg-destructive/5 p-4">
        <p className="text-sm leading-relaxed text-foreground">
          Permanently delete your data and everything associated with your
          account.
        </p>
        <Button
          variant="destructive"
          className="mt-4"
          onClick={() => setIsOpen(true)}
        >
          Delete account
        </Button>
      </div>
      <DeleteConfirmation isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </div>
  )
}

export default DeleteAccount
