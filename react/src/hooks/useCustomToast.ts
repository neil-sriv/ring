import { useCallback } from "react"
import { toast } from "sonner"

const useCustomToast = () => {
  const showToast = useCallback(
    (title: string, description: string, status: "success" | "error") => {
      if (status === "success") {
        toast.success(title, { description })
      } else {
        toast.error(title, { description })
      }
    },
    [],
  )

  return showToast
}

export default useCustomToast
