import { Leaf } from "lucide-react";
import { useI18n } from "@/contexts/I18nContext";

const Footer = () => {
  const { t } = useI18n();
  return (
    <footer className="border-t border-border bg-card">
      <div className="container mx-auto px-4 py-10 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Leaf className="h-5 w-5 text-primary" />
          <span className="font-display font-bold">FarmLens AI</span>
        </div>
        <p className="text-sm text-muted-foreground">{t("footer.tagline")}</p>
        <p className="text-xs text-muted-foreground">© {new Date().getFullYear()} FarmLens. All rights reserved.</p>
      </div>
    </footer>
  );
};

export default Footer;
