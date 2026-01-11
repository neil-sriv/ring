/**
 * Color constants for the application
 * These colors are used throughout the application to maintain consistency
 * and make it easier to update the color scheme.
 */

export const colors = {
  // Brand Colors
  primary: {
    main: "#009688", // Teal
    light: "#4DB6AC",
    dark: "#00766C",
    contrast: "#FFFFFF",
  },

  // Semantic Colors
  success: {
    main: "#48BB78", // Green
    light: "#68D391",
    dark: "#38A169",
    contrast: "#FFFFFF",
  },

  error: {
    main: "#E53E3E", // Red
    light: "#FC8181",
    dark: "#C53030",
    contrast: "#FFFFFF",
  },

  warning: {
    main: "#ECC94B", // Yellow
    light: "#F6E05E",
    dark: "#D69E2E",
    contrast: "#000000",
  },

  info: {
    main: "#4299E1", // Blue
    light: "#63B3ED",
    dark: "#3182CE",
    contrast: "#FFFFFF",
  },

  // Neutral Colors
  neutral: {
    50: "#F7FAFC",
    100: "#EDF2F7",
    200: "#E2E8F0",
    300: "#CBD5E0",
    400: "#A0AEC0",
    500: "#718096",
    600: "#4A5568",
    700: "#2D3748",
    800: "#1A202C",
    900: "#171923",
  },

  // Background Colors
  background: {
    light: "#FAFAFA",
    dark: "#1A202C",
    paper: {
      light: "#FFFFFF",
      dark: "#252D3D",
    },
  },

  // Text Colors
  text: {
    primary: {
      light: "#2D3748",
      dark: "#F7FAFC",
    },
    secondary: {
      light: "#4A5568",
      dark: "#E2E8F0",
    },
    disabled: {
      light: "#A0AEC0",
      dark: "#718096",
    },
  },

  // Border Colors
  border: {
    light: "rgba(0, 0, 0, 0.12)",
    dark: "rgba(255, 255, 255, 0.12)",
  },

  // Glassmorphism Stuff
  glass: {
    light: {
      background: "rgba(255, 255, 255, 0.8)",
      border: "rgba(255, 255, 255, 0.2)",
    },
    dark: {
      background: "rgba(26, 32, 44, 0.8)",
      border: "rgba(255, 255, 255, 0.1)",
    },
  },
} as const

export type ColorScheme = typeof colors

// Func to get color for current theme
export const getThemeColor = (
  color: keyof typeof colors,
  variant: "light" | "dark" = "light",
): string => {
  const colorObj = colors[color]
  if (typeof colorObj === "string") return colorObj
  if ("main" in colorObj) {
    return colorObj[variant as keyof typeof colorObj] || colorObj.main
  }
  return colorObj[Object.keys(colorObj)[0] as keyof typeof colorObj]
}

// Func to get color with opacity
export const withOpacity = (color: string, opacity: number): string => {
  const hex = color.replace("#", "")
  const r = Number.parseInt(hex.substring(0, 2), 16)
  const g = Number.parseInt(hex.substring(2, 4), 16)
  const b = Number.parseInt(hex.substring(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${opacity})`
}
