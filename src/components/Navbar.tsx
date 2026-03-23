import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { useI18n } from "@/contexts/I18nContext";
import { Sun, Moon, LogOut, Menu, X, Leaf } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";

const Navbar = () => {
  const { isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { lang, setLang, t } = useI18n();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/");
    setOpen(false);
  };

  const navLinks = [
    { to: "/", label: t("nav.home") },
    ...(isAuthenticated
      ? [
          { to: "/profile", label: t("nav.profile") },
          { to: "/feedback", label: t("nav.feedback") },
        ]
      : []),
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-border/50">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-display font-bold text-xl">
          <Leaf className="h-6 w-6 text-primary" />
          <span>FarmLens</span>
        </Link>

        {/* Desktop */}
        <div className="hidden md:flex items-center gap-6">
          {navLinks.map(l => (
            <Link key={l.to} to={l.to} className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
              {l.label}
            </Link>
          ))}

          <button
            onClick={() => setLang(lang === "en" ? "hi" : "en")}
            className="text-xs font-medium px-2 py-1 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 transition"
          >
            {lang === "en" ? "हिंदी" : "EN"}
          </button>

          <button onClick={toggleTheme} className="p-2 rounded-md hover:bg-secondary transition">
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>

          {isAuthenticated ? (
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4 mr-1" />
              {t("nav.logout")}
            </Button>
          ) : (
            <Link to="/login">
              <Button size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90">
                {t("nav.login")}
              </Button>
            </Link>
          )}
        </div>

        {/* Mobile toggle */}
        <button className="md:hidden p-2" onClick={() => setOpen(!open)}>
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden glass border-t border-border/50 p-4 space-y-3">
          {navLinks.map(l => (
            <Link key={l.to} to={l.to} onClick={() => setOpen(false)} className="block text-sm font-medium text-muted-foreground hover:text-foreground">
              {l.label}
            </Link>
          ))}
          <div className="flex items-center gap-3 pt-2">
            <button onClick={() => setLang(lang === "en" ? "hi" : "en")} className="text-xs px-2 py-1 rounded-md bg-secondary text-secondary-foreground">
              {lang === "en" ? "हिंदी" : "EN"}
            </button>
            <button onClick={toggleTheme} className="p-2 rounded-md hover:bg-secondary">
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
          </div>
          {isAuthenticated ? (
            <button onClick={handleLogout} className="text-sm text-destructive">{t("nav.logout")}</button>
          ) : (
            <Link to="/login" onClick={() => setOpen(false)} className="text-sm text-primary font-medium">{t("nav.login")}</Link>
          )}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
