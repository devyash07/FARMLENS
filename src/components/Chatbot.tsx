import React, { useState, useRef, useEffect } from "react";
import { X, Send, Loader2, Sprout } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useI18n } from "@/contexts/I18nContext";
import { useAuth } from "@/contexts/AuthContext";
import { motion, AnimatePresence } from "framer-motion";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  language: string; // Track language for each message
}

interface ChatbotProps {
  triggerPopup?: boolean;
}

const Chatbot: React.FC<ChatbotProps> = ({ triggerPopup = false }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [shouldBounce, setShouldBounce] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { t, lang } = useI18n();
  const { user } = useAuth();

  // Get storage key for current user and language
  const getStorageKey = () => {
    const userId = user?.userId || user?.email || "guest";
    return `chatbot_history_${userId}_${lang}`;
  };

  // Load chat history from localStorage when component mounts or language changes
  useEffect(() => {
    const storageKey = getStorageKey();
    try {
      const savedHistory = localStorage.getItem(storageKey);
      if (savedHistory) {
        const parsed = JSON.parse(savedHistory);
        // Convert timestamp strings back to Date objects
        const messagesWithDates = parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
        }));
        setMessages(messagesWithDates);
        console.log(`[Chatbot] Loaded ${messagesWithDates.length} messages for ${lang}`);
      } else {
        // No history for this language, start with welcome message
        const welcomeMsg: Message = {
          role: "assistant",
          content: t("chatbot.welcome"),
          timestamp: new Date(),
          language: lang,
        };
        setMessages([welcomeMsg]);
      }
    } catch (error) {
      console.error("[Chatbot] Failed to load history:", error);
      // Fallback to welcome message
      const welcomeMsg: Message = {
        role: "assistant",
        content: t("chatbot.welcome"),
        timestamp: new Date(),
        language: lang,
      };
      setMessages([welcomeMsg]);
    }
  }, [lang, user?.userId, user?.email, t]);

  // Save chat history to localStorage whenever messages change
  useEffect(() => {
    if (messages.length > 0) {
      const storageKey = getStorageKey();
      try {
        // Keep only last 50 messages to avoid storage issues
        const messagesToSave = messages.slice(-50);
        localStorage.setItem(storageKey, JSON.stringify(messagesToSave));
        console.log(`[Chatbot] Saved ${messagesToSave.length} messages for ${lang}`);
      } catch (error) {
        console.error("[Chatbot] Failed to save history:", error);
        // If storage is full, clear old messages
        try {
          const messagesToSave = messages.slice(-20);
          localStorage.setItem(storageKey, JSON.stringify(messagesToSave));
        } catch (e) {
          console.error("[Chatbot] Storage quota exceeded, clearing history");
        }
      }
    }
  }, [messages, lang, user?.userId, user?.email]);

  // Show popup hint when triggered from parent
  useEffect(() => {
    if (triggerPopup && !isOpen) {
      // First, make button bounce to get attention
      setShouldBounce(true);
      
      // Then auto-open after 1 second
      const openTimer = setTimeout(() => {
        setIsOpen(true);
        setShouldBounce(false);
        
        // Add a welcome message explaining the feature
        const welcomeMsg: Message = {
          role: "assistant",
          content: t("chatbot.auto_open_message"),
          timestamp: new Date(),
          language: lang,
        };
        
        // Add welcome message after a short delay
        setTimeout(() => {
          setMessages(prev => [...prev, welcomeMsg]);
        }, 500);
      }, 1000);
      
      return () => clearTimeout(openTimer);
    }
  }, [triggerPopup, isOpen, t, lang]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date(),
      language: lang,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8001/api/chatbot/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: input,
          history: messages
            .filter(msg => msg.language === lang) // Only send messages in current language
            .map((msg) => ({
              role: msg.role,
              content: msg.content,
            })),
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const data = await response.json();

      const assistantMessage: Message = {
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
        language: lang,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Chatbot error:", error);
      const errorMessage: Message = {
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
        timestamp: new Date(),
        language: lang,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* Floating Chat Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ 
              scale: 1, 
              opacity: 1,
              y: shouldBounce ? [0, -20, 0, -10, 0] : 0,
            }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{
              y: {
                duration: 0.6,
                repeat: shouldBounce ? 2 : 0,
                ease: "easeOut"
              }
            }}
            className="fixed bottom-6 right-6 z-50"
          >
            <Button
              onClick={() => {
                setIsOpen(true);
                setShouldBounce(false);
              }}
              size="lg"
              className={`h-16 w-16 rounded-full shadow-lg bg-primary hover:bg-primary/90 relative group overflow-visible ${
                shouldBounce ? 'ring-4 ring-primary/50 ring-offset-2' : ''
              }`}
            >
              {/* Animated Farmer */}
              <motion.div
                animate={{
                  rotate: shouldBounce ? [0, -15, 15, -15, 15, 0] : [0, -10, 10, -10, 0],
                  scale: shouldBounce ? [1, 1.2, 1, 1.2, 1] : [1, 1.1, 1, 1.1, 1],
                }}
                transition={{
                  duration: shouldBounce ? 0.6 : 2,
                  repeat: shouldBounce ? 2 : Infinity,
                  repeatDelay: shouldBounce ? 0 : 1,
                }}
                className="text-4xl"
              >
                👨‍🌾
              </motion.div>
              <span className="absolute -top-1 -right-1 h-3 w-3 bg-green-500 rounded-full animate-pulse" />
              
              {/* Popup hint tooltip */}
              <AnimatePresence>
                {shouldBounce && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8, y: 10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.8, y: 10 }}
                    className="absolute bottom-full right-0 mb-3 px-4 py-3 bg-primary text-primary-foreground text-sm rounded-lg shadow-xl whitespace-nowrap max-w-xs font-semibold"
                  >
                    <div className="flex items-center gap-2">
                      <Sprout className="h-4 w-4" />
                      <span>👋 {t("chatbot.ask_question")}</span>
                    </div>
                    <div className="absolute -bottom-2 right-4 w-0 h-0 border-l-8 border-r-8 border-t-8 border-transparent border-t-primary" />
                  </motion.div>
                )}
              </AnimatePresence>
              
              {/* Hover tooltip */}
              <div className="absolute bottom-full right-0 mb-2 px-3 py-1 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                {t("chatbot.ask_question")}
              </div>
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="fixed bottom-6 right-6 z-50 w-96 h-[600px] bg-background border border-border rounded-2xl shadow-2xl flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="bg-primary text-primary-foreground p-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <motion.div 
                  className="h-10 w-10 rounded-full bg-white/20 flex items-center justify-center text-2xl"
                  animate={{
                    rotate: [0, -5, 5, -5, 0],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    repeatDelay: 3,
                  }}
                >
                  👨‍🌾
                </motion.div>
                <div>
                  <h3 className="font-semibold">{t("chatbot.title")}</h3>
                  <p className="text-xs opacity-90">{t("chatbot.subtitle")}</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsOpen(false)}
                className="text-primary-foreground hover:bg-white/20"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4" ref={scrollRef}>
              <div className="space-y-4">
                {messages.map((message, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                        message.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-secondary text-secondary-foreground"
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      <p className="text-xs opacity-60 mt-1">
                        {message.timestamp.toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                  </motion.div>
                ))}
                {isLoading && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex justify-start"
                  >
                    <div className="bg-secondary text-secondary-foreground rounded-2xl px-4 py-2">
                      <Loader2 className="h-5 w-5 animate-spin" />
                    </div>
                  </motion.div>
                )}
              </div>
            </ScrollArea>

            {/* Input */}
            <div className="p-4 border-t border-border bg-background">
              <div className="flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={t("chatbot.placeholder")}
                  className="flex-1"
                  disabled={isLoading}
                />
                <Button
                  onClick={sendMessage}
                  disabled={!input.trim() || isLoading}
                  size="icon"
                  className="shrink-0"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-2 text-center">
                {t("chatbot.powered_by")}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default Chatbot;
