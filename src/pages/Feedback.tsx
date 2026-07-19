import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth, supabase } from "@/contexts/AuthContext";
import { useI18n } from "@/contexts/I18nContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const Feedback = () => {
  const { isAuthenticated, user } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) navigate("/login");
    // Pre-fill the user's name and email if they are logged in
    if (user) {
      if (!name) setName(user.name || "");
      if (!email) setEmail(user.email || "");
    }
  }, [isAuthenticated, user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // --- 1. VALIDATION CHECKS ---
    
    // Name: Must contain at least one actual letter (prevents "123456")
    if (!/[a-zA-Z]/.test(name)) {
      toast.error("Please enter a valid name (cannot be only numbers).");
      return;
    }

    // Email: Must match a standard email format (e.g., something@something.com)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (email && !emailRegex.test(email)) {
      toast.error("Please enter a valid email address (e.g., name@gmail.com).");
      return;
    }

    // Message: Must be at least 10 characters long
    if (message.trim().length < 10) {
      toast.error("Please provide a bit more detail in your feedback.");
      return;
    }

    // --- 2. SEND TO DATABASE ---
    setIsSubmitting(true);

    try {
      const { error } = await supabase.from('feedback').insert([{
        user_id: user?.userId || null,
        name: name.trim(),
        email: email.trim(),
        message: message.trim(),
        feedback_type: 'General'
      }]);

      if (error) throw error;

      toast.success(t("feedback.success") || "Feedback sent successfully!");
      setMessage(""); // Clear message, keep name/email
      
    } catch (error) {
      console.error("[FarmLens] Failed to submit feedback:", error);
      toast.error("Failed to send feedback. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 pt-24 pb-16">
        <div className="container mx-auto px-4 max-w-xl">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
            <h1 className="text-3xl font-display font-bold text-center">{t("feedback.title")}</h1>

            <form onSubmit={handleSubmit} className="glass rounded-xl p-6 space-y-5">
              <div className="space-y-2">
                <Label htmlFor="fb-name">{t("feedback.name")}</Label>
                <Input 
                  id="fb-name" 
                  value={name} 
                  onChange={e => setName(e.target.value)} 
                  placeholder="e.g. John Doe"
                  required 
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="fb-email">{t("feedback.email")}</Label>
                <Input 
                  id="fb-email" 
                  type="email" 
                  value={email} 
                  onChange={e => setEmail(e.target.value)} 
                  placeholder="e.g. john@gmail.com"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="fb-msg">{t("feedback.message")}</Label>
                <Textarea 
                  id="fb-msg" 
                  rows={5} 
                  value={message} 
                  onChange={e => setMessage(e.target.value)} 
                  placeholder="Tell us what you think..."
                  required 
                  spellCheck={true}        // Explicitly turns on red squiggly lines for typos
                  autoCorrect="on"         // Tells mobile keyboards to auto-correct typos
                  autoCapitalize="sentences" // Ensures first letter of sentences are capitalized
                />
              </div>
              <Button 
                type="submit" 
                disabled={isSubmitting}
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Sending...
                  </>
                ) : (
                  t("feedback.submit")
                )}
              </Button>
            </form>
          </motion.div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Feedback;