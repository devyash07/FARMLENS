import React, { createContext, useContext, useState, useEffect } from "react";

type Language = "en" | "hi";

const translations: Record<string, Record<Language, string>> = {
  "nav.home": { en: "Home", hi: "होम" },
  "nav.profile": { en: "Profile", hi: "प्रोफ़ाइल" },
  "nav.feedback": { en: "Feedback", hi: "प्रतिक्रिया" },
  "nav.logout": { en: "Logout", hi: "लॉगआउट" },
  "nav.login": { en: "Login", hi: "लॉगिन" },
  "hero.title": { en: "FarmLens", hi: "FarmLens" },
  "hero.subtitle": { en: "From Image to Insight", hi: "छवि से अंतर्दृष्टि तक" },
  "hero.cta": { en: "Get Started", hi: "शुरू करें" },
  "upload.title": { en: "Upload Crop Image", hi: "फसल की छवि अपलोड करें" },
  "upload.drag": { en: "Drag & drop your image here or", hi: "अपनी छवि यहाँ खींचें और छोड़ें या" },
  "upload.choose": { en: "Choose File", hi: "फ़ाइल चुनें" },
  "upload.login_required": { en: "Login required to analyze", hi: "विश्लेषण के लिए लॉगिन आवश्यक" },
  "upload.analyze": { en: "Analyze", hi: "विश्लेषण करें" },
  "guide.title": { en: "General Crop Protection Guide", hi: "सामान्य फसल सुरक्षा गाइड" },
  "features.title": { en: "Powerful Features", hi: "शक्तिशाली विशेषताएँ" },
  "footer.tagline": { en: "From Image to Insight", hi: "छवि से अंतर्दृष्टि तक" },
  "result.disease": { en: "Disease Detected", hi: "रोग का पता चला" },
  "result.severity": { en: "Severity", hi: "गंभीरता" },
  "result.confidence": { en: "Confidence", hi: "विश्वास" },
  "result.explain": { en: "Highlighted regions show infected areas used by AI", hi: "हाइलाइट किए गए क्षेत्र AI द्वारा उपयोग किए गए संक्रमित क्षेत्रों को दिखाते हैं" },
  "result.another": { en: "Analyze Another Image", hi: "एक और छवि का विश्लेषण करें" },
  "result.feedback": { en: "Give Feedback", hi: "प्रतिक्रिया दें" },
  "profile.title": { en: "Your Profile", hi: "आपकी प्रोफ़ाइल" },
  "profile.history": { en: "Analysis History", hi: "विश्लेषण इतिहास" },
  "profile.empty": { en: "No analysis history yet", hi: "अभी तक कोई विश्लेषण इतिहास नहीं" },
  "feedback.title": { en: "Send Feedback", hi: "प्रतिक्रिया भेजें" },
  "feedback.name": { en: "Name", hi: "नाम" },
  "feedback.email": { en: "Email (optional)", hi: "ईमेल (वैकल्पिक)" },
  "feedback.message": { en: "Your feedback", hi: "आपकी प्रतिक्रिया" },
  "feedback.submit": { en: "Submit", hi: "भेजें" },
  "login.welcome": { en: "Welcome back to FarmLens", hi: "FarmLens में वापस स्वागत है" },
  "login.subtitle": { en: "Monitor and manage your crops effortlessly", hi: "अपनी फसलों की आसानी से निगरानी करें" },
  "login.email": { en: "Email", hi: "ईमेल" },
  "login.password": { en: "Password", hi: "पासवर्ड" },
  "login.submit": { en: "Log in", hi: "लॉगिन" },
  "login.signup": { en: "Don't have an account?", hi: "खाता नहीं है?" },
};

interface I18nContextType {
  lang: Language;
  setLang: (l: Language) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLang] = useState<Language>(() => (localStorage.getItem("farmlens_lang") as Language) || "en");

  useEffect(() => {
    localStorage.setItem("farmlens_lang", lang);
  }, [lang]);

  const t = (key: string) => translations[key]?.[lang] || key;

  return <I18nContext.Provider value={{ lang, setLang, t }}>{children}</I18nContext.Provider>;
};

export const useI18n = () => {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
};
