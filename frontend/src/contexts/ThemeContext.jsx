import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  getTheme,
  setTheme,
  applyThemeColors,
  themes,
} from '../utils/themeManager';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [currentTheme, setCurrentTheme] = useState(() => getTheme());

  useEffect(() => {
    // Apply theme colors on mount
    applyThemeColors(currentTheme);
  }, [currentTheme]);

  const changeTheme = (themeId) => {
    const theme = themes[themeId];
    if (!theme) {
      console.error(`Theme ${themeId} not found`);
      return;
    }

    // Update localStorage and apply colors
    setTheme(themeId);
    setCurrentTheme(theme);
  };

  const value = {
    currentTheme,
    changeTheme,
    themes,
  };

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
