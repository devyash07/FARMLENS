import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useI18n } from "@/contexts/I18nContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Leaf, Eye, EyeOff } from "lucide-react";
import Navbar from "@/components/Navbar";

const Login = () => {
  const { login } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email && password) {
      login(email, password);
      navigate("/", { state: { scrollToUpload: true } });
    }
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="pt-16 min-h-screen flex">
        {/* Left panel */}
        <div className="hidden lg:flex w-1/2 bg-primary/10 relative items-center justify-center">
          <div className="text-center space-y-6 p-12">
            <Leaf className="h-16 w-16 text-primary mx-auto" />
            <h2 className="text-3xl font-display font-bold">{t("hero.title")}</h2>
            <p className="text-muted-foreground text-lg max-w-md">
              "A tool that helps you monitor, protect, and grow your crops."
            </p>
          </div>
        </div>

        {/* Right panel */}
        <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
          <div className="w-full max-w-md space-y-8">
            <div className="text-center">
              <h1 className="text-2xl font-display font-bold">{t("login.welcome")}</h1>
              <p className="text-muted-foreground mt-2">{t("login.subtitle")}</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="email">{t("login.email")}</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">{t("login.password")}</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPw ? "text" : "password"}
                    placeholder="••••••••"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    onClick={() => setShowPw(!showPw)}
                  >
                    {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <Button type="submit" className="w-full bg-primary text-primary-foreground hover:bg-primary/90 py-6 text-base">
                {t("login.submit")}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
