import { useEffect, useState } from "react"
import { Toaster as Sonner } from "sonner"

type ToasterProps = React.ComponentProps<typeof Sonner>

/** Tracks the `dark` class on <html> so toasts follow the app theme. */
function useHtmlTheme(): "light" | "dark" {
  const [theme, setTheme] = useState<"light" | "dark">(() =>
    document.documentElement.classList.contains("dark") ? "dark" : "light",
  )

  useEffect(() => {
    const observer = new MutationObserver(() => {
      setTheme(
        document.documentElement.classList.contains("dark") ? "dark" : "light",
      )
    })
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    })
    return () => observer.disconnect()
  }, [])

  return theme
}

export function Toaster(props: ToasterProps) {
  const theme = useHtmlTheme()

  return (
    <Sonner
      theme={theme}
      toastOptions={{
        style: {
          borderRadius: "var(--radius-lg)",
          fontFamily: "var(--font-sans)",
        },
      }}
      {...props}
    />
  )
}
