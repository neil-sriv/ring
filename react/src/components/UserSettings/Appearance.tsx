import { Badge } from "@/components/ui/badge"
import { useEffect, useState } from "react"

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
      <div className="flex flex-col gap-6">
        <h3 className="text-sm font-semibold text-foreground">Appearance</h3>
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <div className="flex flex-col gap-4">
            <label className="flex items-center gap-2 cursor-pointer transition-transform hover:translate-x-1">
              <input
                type="radio"
                name="theme"
                value="light"
                checked={theme === "light"}
                onChange={() => handleThemeChange("light")}
                className="accent-primary h-4 w-4"
              />
              <span className="text-sm text-foreground">Light Mode</span>
              <Badge variant="secondary" className="ml-2">
                Default
              </Badge>
            </label>
            <label className="flex items-center gap-2 cursor-pointer transition-transform hover:translate-x-1">
              <input
                type="radio"
                name="theme"
                value="dark"
                checked={theme === "dark"}
                onChange={() => handleThemeChange("dark")}
                className="accent-primary h-4 w-4"
              />
              <span className="text-sm text-foreground">Dark Mode</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Appearance
