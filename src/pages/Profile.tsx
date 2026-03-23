import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useI18n } from "@/contexts/I18nContext";
import { useEffect } from "react";
import { motion } from "framer-motion";
import { User, ImageIcon, Calendar } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const Profile = () => {
  const { isAuthenticated, user, history } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) navigate("/login");
  }, [isAuthenticated]);

  if (!user) return null;

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 pt-24 pb-16">
        <div className="container mx-auto px-4 max-w-4xl">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
            <h1 className="text-3xl font-display font-bold">{t("profile.title")}</h1>

            {/* User info */}
            <div className="glass rounded-xl p-6 flex items-center gap-4">
              <div className="p-3 rounded-full bg-primary/10">
                <User className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h2 className="font-display font-semibold text-lg capitalize">{user.name}</h2>
                <p className="text-sm text-muted-foreground">{user.email}</p>
              </div>
            </div>

            {/* History */}
            <div>
              <h2 className="text-xl font-display font-semibold mb-4">{t("profile.history")}</h2>
              {history.length === 0 ? (
                <div className="glass rounded-xl p-12 text-center">
                  <ImageIcon className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
                  <p className="text-muted-foreground">{t("profile.empty")}</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {history.map(h => (
                    <div key={h.id} className="glass rounded-xl p-4 flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="p-2 rounded-lg bg-primary/10">
                          <ImageIcon className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium">{h.disease}</p>
                          <p className="text-xs text-muted-foreground">{h.imageName}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium">Severity: {h.severity}%</p>
                        <p className="text-xs text-muted-foreground flex items-center gap-1 justify-end">
                          <Calendar className="h-3 w-3" />
                          {new Date(h.date).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Profile;
