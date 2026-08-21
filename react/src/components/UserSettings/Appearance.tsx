import { Moon, Sun } from "lucide-react"
import { useEffect, useState } from "react"

import { cn } from "@/lib/utils"

const themeOptions = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
]

const Appearance = () => {
  const [theme, setTheme] = useState<string>(() => {
    if (typeof window !== "undefined") {
      return (
        localStorage.getItem("theme") ||
        (document.documentElement.classList.contains("dark") ? "dark" : "light")
      )
    }
    return "light"
  })

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark")
    } else {
      document.documentElement.classList.remove("dark")
    }
    localStorage.setItem("theme", theme)
  }, [theme])

  const handleThemeChange = (value: string) => {
    setTheme(value)
  }

  return (
    <div className="w-full">
      <h3 className="text-base font-semibold">Appearance</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Choose how Ring looks in this browser.
      </p>
      <div className="mt-5 grid max-w-md grid-cols-2 gap-3">
        {themeOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            aria-pressed={theme === option.value}
            onClick={() => handleThemeChange(option.value)}
            className={cn(
              "cursor-pointer rounded-lg border p-4 text-left transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/30",
              theme === option.value
                ? "border-primary bg-accent/50 ring-[3px] ring-ring/20"
                : "hover:bg-accent/50",
            )}
          >
            <option.icon className="h-4 w-4 text-muted-foreground" />
            <span className="mt-2 block text-sm font-medium text-foreground">
              {option.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

export default Appearance
