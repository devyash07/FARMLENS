import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useI18n, LANGUAGES } from "@/contexts/I18nContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff, ChevronDown, Globe, Loader2, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

const Login = () => {
  // 1. Added loginWithGoogle to the destructured context
  const { login, register, loginWithGoogle, isLoading, error, clearError, isAuthenticated } = useAuth();
  const { t, lang, setLang } = useI18n();
  const navigate = useNavigate();
  const location = useLocation();

  const [isSignUp, setIsSignUp] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [localError, setLocalError] = useState("");
  const [langOpen, setLangOpen] = useState(false);

  const currentLang = LANGUAGES.find(l => l.code === lang);

  // Get the return URL from location state, default to home
  const from = (location.state as any)?.from || "/";

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  // Clear errors when switching between login/signup
  useEffect(() => {
    clearError();
    setLocalError("");
  }, [isSignUp, clearError]);

  const validateForm = (): boolean => {
    setLocalError("");
    
    if (isSignUp) {
      if (!name.trim()) {
        setLocalError("Name is required");
        return false;
      }
      if (name.trim().length < 2) {
        setLocalError("Name must be at least 2 characters");
        return false;
      }
    }
    
    if (!email.trim()) {
      setLocalError("Email is required");
      return false;
    }
    
    if (!password) {
      setLocalError("Password is required");
      return false;
    }
    
    if (isSignUp) {
      if (password.length < 6) {
        setLocalError("Password must be at least 6 characters");
        return false;
      }
      
      if (!/[A-Za-z]/.test(password)) {
        setLocalError("Password must contain at least one letter");
        return false;
      }
      
      if (!/[0-9]/.test(password)) {
        setLocalError("Password must contain at least one number");
        return false;
      }
      
      if (password !== confirmPassword) {
        setLocalError("Passwords do not match");
        return false;
      }
    }
    
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      if (isSignUp) {
        await register(name.trim(), email.trim(), password);
      } else {
        await login(email.trim(), password);
      }
      
      // Navigation will happen automatically via useEffect when isAuthenticated becomes true
    } catch (err: any) {
      // Error is already set in AuthContext, but we can log it
      console.error("Auth error:", err);
    }
  };

  // 2. Updated to actually trigger the Supabase Google OAuth flow
  const handleGoogle = async () => {
    try {
      await loginWithGoogle();
    } catch (err: any) {
      console.error("Google auth error:", err);
    }
  };

  const displayError = error || localError;

  return (
    <div className="min-h-screen flex">
      {/* Left panel */}
      <div className="hidden lg:block w-1/2 relative">
        <img src="/login-left.png" alt="FarmLens" className="w-full h-full object-cover" loading="lazy" />
      </div>

      {/* Right panel */}
      <div className="w-full lg:w-1/2 flex flex-col">
        {/* Language selector */}
        <div className="flex justify-end px-8 pt-6">
          <div className="relative">
            <button
              onClick={() => setLangOpen(!langOpen)}
              className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 transition"
            >
              <Globe className="h-3.5 w-3.5" />
              {currentLang?.native}
              <ChevronDown className={`h-3 w-3 transition-transform ${langOpen ? "rotate-180" : ""}`} />
            </button>
            {langOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-background border border-border rounded-lg shadow-lg z-50 overflow-y-auto" style={{ maxHeight: "320px" }}>
                {LANGUAGES.map(l => (
                  <button
                    key={l.code}
                    onClick={() => { setLang(l.code); setLangOpen(false); }}
                    className={`w-full text-left px-4 py-2 text-sm flex items-center justify-between hover:bg-secondary transition ${lang === l.code ? "bg-primary/10 text-primary font-medium" : "text-foreground"}`}
                  >
                    <span>{l.native}</span>
                    <span className="text-xs text-muted-foreground">{l.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Form */}
        <div className="flex-1 flex items-center justify-center px-8 py-6">
          <div className="w-full max-w-md space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-display font-bold">
                {isSignUp ? t("login.create_account") : t("login.welcome")}
              </h1>
              <p className="text-muted-foreground mt-1 text-sm">
                {isSignUp ? t("login.signup_subtitle") : t("login.subtitle")}
              </p>
            </div>

            {/* Google Sign-in */}
            <button
              type="button"
              onClick={handleGoogle}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-3 border border-border rounded-lg py-2.5 text-sm font-medium hover:bg-secondary transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" className="w-5 h-5" />
              {t("login.google")}
            </button>

            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-border" />
              <span className="text-xs text-muted-foreground">{t("login.or")}</span>
              <div className="flex-1 h-px bg-border" />
            </div>

            {/* Error Alert */}
            {displayError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{displayError}</AlertDescription>
              </Alert>
            )}

            {/* Auth Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {isSignUp && (
                <div className="space-y-1.5">
                  <Label htmlFor="name">{t("login.full_name")}</Label>
                  <Input 
                    id="name" 
                    type="text" 
                    placeholder={t("login.name_placeholder")} 
                    value={name} 
                    onChange={e => setName(e.target.value)} 
                    disabled={isLoading}
                    required 
                  />
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="email">{t("login.email")}</Label>
                <Input 
                  id="email" 
                  type="email" 
                  placeholder="you@example.com" 
                  value={email} 
                  onChange={e => setEmail(e.target.value)} 
                  disabled={isLoading}
                  required 
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="password">{t("login.password")}</Label>
                <div className="relative">
                  <Input 
                    id="password" 
                    type={showPw ? "text" : "password"} 
                    placeholder="••••••••" 
                    value={password} 
                    onChange={e => setPassword(e.target.value)} 
                    disabled={isLoading}
                    required 
                  />
                  <button 
                    type="button" 
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground disabled:opacity-50" 
                    onClick={() => setShowPw(!showPw)}
                    disabled={isLoading}
                  >
                    {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {isSignUp && (
                  <p className="text-xs text-muted-foreground">
                    At least 6 characters with a letter and number
                  </p>
                )}
              </div>

              {isSignUp && (
                <div className="space-y-1.5">
                  <Label htmlFor="confirmPassword">{t("login.confirm_password")}</Label>
                  <Input 
                    id="confirmPassword" 
                    type={showPw ? "text" : "password"} 
                    placeholder="••••••••" 
                    value={confirmPassword} 
                    onChange={e => setConfirmPassword(e.target.value)} 
                    disabled={isLoading}
                    required 
                  />
                </div>
              )}

              <Button 
                type="submit" 
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90 py-5 text-base"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    {isSignUp ? "Creating account..." : "Signing in..."}
                  </>
                ) : (
                  isSignUp ? t("login.signup_btn") : t("login.submit")
                )}
              </Button>
            </form>

            <p className="text-center text-sm text-muted-foreground">
              {isSignUp ? t("login.have_account") : t("login.no_account")}{" "}
              <button 
                type="button" 
                onClick={() => { 
                  setIsSignUp(!isSignUp); 
                  setLocalError(""); 
                  clearError();
                }} 
                className="text-primary font-medium hover:underline"
                disabled={isLoading}
              >
                {isSignUp ? t("login.signin_link") : t("login.signup_link")}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;