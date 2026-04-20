import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useI18n, LANGUAGES } from "@/contexts/I18nContext";
import { LogOut, Menu, X, Leaf, ChevronDown, Globe } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";

const Navbar = () => {
  const { isAuthenticated, logout } = useAuth();
  const { lang, setLang, t } = useI18n();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [langOpen, setLangOpen] = useState(false);
  const langRef = useRef<HTMLDivElement>(null);

  const handleLogout = () => { logout(); navigate("/"); setOpen(false); };

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (langRef.current && !langRef.current.contains(e.target as Node)) setLangOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const currentLang = LANGUAGES.find(l => l.code === lang);

  const navLinks = [
    { to: "/", label: t("nav.home") },
    ...(isAuthenticated ? [
      { to: "/profile",  label: t("nav.profile")  },
      { to: "/feedback", label: t("nav.feedback") },
    ] : []),
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

          {/* Language dropdown */}
          <div className="relative" ref={langRef}>
            <button
              onClick={() => setLangOpen(!langOpen)}
              className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 transition"
            >
              <Globe className="h-3.5 w-3.5" />
              {currentLang?.native}
              <ChevronDown className={`h-3 w-3 transition-transform ${langOpen ? "rotate-180" : ""}`} />
            </button>

            {langOpen && (
              <div className="absolute right-0 mt-2 w-44 bg-background border border-border rounded-lg shadow-lg overflow-hidden z-50">
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

          {/* Mobile language list */}
          <div className="pt-2">
            <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1"><Globe className="h-3 w-3" /> {t("nav.language")}</p>
            <div className="grid grid-cols-2 gap-1">
              {LANGUAGES.map(l => (
                <button
                  key={l.code}
                  onClick={() => setLang(l.code)}
                  className={`text-left px-3 py-1.5 rounded-md text-xs transition ${lang === l.code ? "bg-primary/10 text-primary font-medium" : "bg-secondary text-secondary-foreground hover:bg-secondary/80"}`}
                >
                  {l.native}
                </button>
              ))}
            </div>
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
