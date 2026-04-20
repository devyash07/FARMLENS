import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider } from "@/contexts/AuthContext";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { I18nProvider } from "@/contexts/I18nContext";
import Chatbot from "@/components/Chatbot";
import Index from "./pages/Index";
import Login from "./pages/Login";
import Result from "./pages/Result";
import Profile from "./pages/Profile";
import Feedback from "./pages/Feedback";
import NotFound from "./pages/NotFound";
import GuideDetail from "./pages/GuideDetail";
import { useEffect, useState } from "react";

const queryClient = new QueryClient();

const AppContent = () => {
  const location = useLocation();
  const [triggerChatbot, setTriggerChatbot] = useState(false);

  // Trigger chatbot popup when navigating to GuideDetail
  useEffect(() => {
    if (location.pathname.startsWith("/guide/")) {
      setTriggerChatbot(true);
      const timer = setTimeout(() => setTriggerChatbot(false), 100);
      return () => clearTimeout(timer);
    }
  }, [location.pathname]);

  // Detect scroll to upload section on home page
  useEffect(() => {
    if (location.pathname === "/") {
      const handleScroll = () => {
        const uploadSection = document.getElementById("upload-section");
        if (uploadSection) {
          const rect = uploadSection.getBoundingClientRect();
          const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
          
          if (isVisible && !sessionStorage.getItem("chatbot_upload_shown")) {
            setTriggerChatbot(true);
            sessionStorage.setItem("chatbot_upload_shown", "true");
            setTimeout(() => setTriggerChatbot(false), 100);
          }
        }
      };

      window.addEventListener("scroll", handleScroll);
      handleScroll(); // Check on mount
      
      return () => window.removeEventListener("scroll", handleScroll);
    }
  }, [location.pathname]);

  return (
    <>
      <Routes>
        <Route path="/" element={<Index />} />
        <Route path="/login" element={<Login />} />
        <Route path="/result" element={<Result />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/feedback" element={<Feedback />} />
        <Route path="/guide/:type" element={<GuideDetail />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      <Chatbot triggerPopup={triggerChatbot} />
    </>
  );
};

const App = () => {
  // Clean up old sessionStorage data on app load to prevent quota issues
  useEffect(() => {
    try {
      // Clear all sessionStorage (temporary data) except chatbot flags
      const chatbotFlag = sessionStorage.getItem("chatbot_upload_shown");
      sessionStorage.clear();
      if (chatbotFlag) {
        sessionStorage.setItem("chatbot_upload_shown", chatbotFlag);
      }
      
      console.log("[FarmLens] Storage cleaned on app load");
    } catch (e) {
      console.warn("[FarmLens] Failed to clean storage:", e);
    }
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <I18nProvider>
          <AuthProvider>
            <TooltipProvider>
              <Toaster />
              <Sonner />
              <BrowserRouter>
                <AppContent />
              </BrowserRouter>
            </TooltipProvider>
          </AuthProvider>
        </I18nProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
