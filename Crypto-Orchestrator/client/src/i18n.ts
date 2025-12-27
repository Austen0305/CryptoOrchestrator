import i18n from 'i18next';
import logger from './lib/logger';
import { initReactI18next } from 'react-i18next';

// Import translation files
import en from './locales/en.json';
import es from './locales/es.json';
import ar from './locales/ar.json';
import fr from './locales/fr.json';
import de from './locales/de.json';
import ja from './locales/ja.json';
import zh from './locales/zh.json';

// Define supported languages
const resources = {
  en: { translation: en },
  es: { translation: es },
  ar: { translation: ar },
  fr: { translation: fr },
  de: { translation: de },
  ja: { translation: ja },
  zh: { translation: zh },
};

// Get initial language from localStorage or default to 'en'
const getInitialLanguage = (): string => {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('language');
    if (stored && Object.keys(resources).includes(stored)) {
      return stored;
    }
  }
  return 'en';
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: getInitialLanguage(),
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // React already escapes values
    },
    detection: {
      // Disable language detection for now, we'll handle it manually
      order: [],
    },
    react: {
      useSuspense: false,
    },
  });

// Function to change language
export const changeLanguage = async (lng: string) => {
  try {
    await i18n.changeLanguage(lng);
    if (typeof window !== 'undefined') {
      localStorage.setItem('language', lng);
    }
  } catch (error) {
    logger.error('Failed to change language:', error);
  }
};

export default i18n;