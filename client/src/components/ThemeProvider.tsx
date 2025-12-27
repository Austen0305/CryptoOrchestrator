import { createContext, useContext, useEffect, useState } from "react";
import logger from "@/lib/logger";
import { usePreferences } from "../hooks/usePreferences";

type Theme = "light" | "dark" | "system";

type ThemeProviderProps = {
  children: React.ReactNode;
  defaultTheme?: Theme;
};

type ThemeProviderState = {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: "light" | "dark";
};

const ThemeProviderContext = createContext<ThemeProviderState | undefined>(
  undefined
);

export function ThemeProvider({
  children,
  defaultTheme = "dark",
}: ThemeProviderProps) {
  const { preferences, updateTheme } = usePreferences();

  // Use preferences theme if available, otherwise fall back to localStorage or default
  const [theme, setThemeState] = useState<Theme>(() => {
    return preferences?.theme || (localStorage.getItem("theme") as Theme) || defaultTheme;
  });

  // Update theme when preferences change
  useEffect(() => {
    if (preferences?.theme) {
      setThemeState(preferences.theme);
    }
  }, [preferences?.theme]);

  // Resolve system theme to actual light/dark
  const resolvedTheme = theme === "system"
    ? (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
    : theme;

  const setTheme = async (newTheme: Theme) => {
    setThemeState(newTheme);
    try {
      await updateTheme(newTheme);
    } catch (error) {
      logger.error("Failed to save theme preference:", error);
    }
  };

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.add(resolvedTheme);
    localStorage.setItem("theme", theme);
  }, [theme, resolvedTheme]);

  return (
    <ThemeProviderContext.Provider value={{ theme, setTheme, resolvedTheme }}>
      {children}
    </ThemeProviderContext.Provider>
  );
}

export const useTheme = () => {
  const context = useContext(ThemeProviderContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
};
