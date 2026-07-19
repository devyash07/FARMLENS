import { useNavigate } from "react-router-dom";
import { useAuth, supabase } from "@/contexts/AuthContext";
import { useI18n } from "@/contexts/I18nContext";
import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { User, ImageIcon, Calendar, Pencil, Check, X, Camera, Lock, Phone, Mail, Hash, AlertTriangle, CheckCircle, Loader2, FileText, ShieldAlert, Activity } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

const Profile = () => {
  const { isAuthenticated, user, updateProfile, history: localHistory } = useAuth();
  const { t, translateCrop, translateDisease } = useI18n();
  const navigate = useNavigate();
  const avatarRef = useRef<HTMLInputElement>(null);

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ name: "", phone: "", email: "", password: "", confirmPassword: "" });
  const [formError, setFormError] = useState("");
  const [saved, setSaved] = useState(false);
  
  // New state to hold our official database history
  const [dbHistory, setDbHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState<any | null>(null);

  useEffect(() => { 
    if (!isAuthenticated) navigate("/login"); 
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (user) setForm({ name: user.name, phone: user.phone || "", email: user.email, password: "", confirmPassword: "" });
  }, [user]);

  // Fetch real history from FastAPI & Supabase
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session?.access_token) return;

        const backendUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        const res = await fetch(`${backendUrl.replace(/\/$/, '')}/history`, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`
          }
        });

        if (res.ok) {
          const data = await res.json();
          setDbHistory(data.history || []);
        }
      } catch (e) {
        console.error("[FarmLens] Failed to fetch DB history:", e);
      } finally {
        setLoadingHistory(false);
      }
    };

    if (isAuthenticated) {
      fetchHistory();
    }
  }, [isAuthenticated]);

  if (!user) return null;

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => updateProfile({ avatar: ev.target?.result as string });
    reader.readAsDataURL(file);
  };

  const handleSave = () => {
    setFormError("");
    if (!form.name.trim()) return setFormError(t("error.name_required"));
    if (form.password && form.password !== form.confirmPassword) return setFormError(t("error.passwords_mismatch"));
    if (form.password && form.password.length < 6) return setFormError(t("error.password_length"));
    updateProfile({ name: form.name.trim(), phone: form.phone, email: form.email, ...(form.password ? { password: form.password } : {}) });
    setEditing(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  // Merge DB history with local history if DB is empty during transition
  const displayRecords = dbHistory.length > 0 ? dbHistory : localHistory;

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 pt-24 pb-16">
        <div className="container mx-auto px-4 max-w-4xl space-y-8">
          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-3xl font-display font-bold">
            {t("profile.title")}
          </motion.h1>

          {/* Profile card */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass rounded-xl p-6">
            <div className="flex items-start justify-between mb-6">
              {/* Avatar */}
              <div className="flex items-center gap-5">
                <div className="relative">
                  <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center overflow-hidden">
                    {user.avatar
                      ? <img src={user.avatar} alt="avatar" className="w-full h-full object-cover" />
                      : <User className="h-10 w-10 text-primary" />}
                  </div>
                  <button
                    onClick={() => avatarRef.current?.click()}
                    className="absolute bottom-0 right-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center hover:bg-primary/80 transition"
                  >
                    <Camera className="h-3 w-3" />
                  </button>
                  <input ref={avatarRef} type="file" accept="image/*" className="hidden" onChange={handleAvatarChange} />
                </div>
                <div>
                  <h2 className="font-display font-semibold text-xl capitalize">{user.name}</h2>
                  <p className="text-sm text-muted-foreground">{user.email}</p>
                  {user.userId && <p className="text-xs text-muted-foreground mt-0.5">{t("profile.user_id")}: {user.userId.slice(0, 8)}...</p>}
                </div>
              </div>

              {/* Edit toggle */}
              <div className="flex gap-2">
                {editing ? (
                  <>
                    <Button size="sm" onClick={handleSave} className="bg-primary text-primary-foreground hover:bg-primary/90">
                      <Check className="h-4 w-4 mr-1" /> Save
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => { setEditing(false); setFormError(""); }}>
                      <X className="h-4 w-4 mr-1" /> Cancel
                    </Button>
                  </>
                ) : (
                  <Button size="sm" variant="outline" onClick={() => setEditing(true)}>
                    <Pencil className="h-4 w-4 mr-1" /> {t("profile.edit")}
                  </Button>
                )}
              </div>
            </div>

            {saved && <p className="text-sm text-primary mb-4">{t("profile.updated")}</p>}

            {editing ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label className="flex items-center gap-1.5"><User className="h-3.5 w-3.5" /> {t("profile.name")}</Label>
                  <Input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
                </div>
                <div className="space-y-1.5">
                  <Label className="flex items-center gap-1.5"><Hash className="h-3.5 w-3.5" /> {t("profile.user_id")}</Label>
                  <Input value={user.userId || ""} disabled className="opacity-60" />
                </div>
                <div className="space-y-1.5">
                  <Label className="flex items-center gap-1.5"><Mail className="h-3.5 w-3.5" /> {t("profile.email")}</Label>
                  <Input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
                </div>
                <div className="space-y-1.5">
                  <Label className="flex items-center gap-1.5"><Phone className="h-3.5 w-3.5" /> {t("profile.contact")}</Label>
                  <Input type="tel" placeholder="+91 XXXXX XXXXX" value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} />
                </div>
                <div className="space-y-1.5">
                  <Label className="flex items-center gap-1.5"><Lock className="h-3.5 w-3.5" /> {t("profile.new_password")}</Label>
                  <Input type="password" placeholder={t("profile.password_placeholder")} value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
                </div>
                <div className="space-y-1.5">
                  <Label className="flex items-center gap-1.5"><Lock className="h-3.5 w-3.5" /> {t("profile.confirm_password")}</Label>
                  <Input type="password" placeholder="••••••••" value={form.confirmPassword} onChange={e => setForm(f => ({ ...f, confirmPassword: e.target.value }))} />
                </div>
                {formError && <p className="text-sm text-destructive col-span-2">{formError}</p>}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground"><User className="h-4 w-4" /> <span className="text-foreground font-medium">{user.name}</span></div>
                <div className="flex items-center gap-2 text-muted-foreground"><Hash className="h-4 w-4" /> <span className="text-foreground font-medium">{user.userId?.slice(0, 8)}...</span></div>
                <div className="flex items-center gap-2 text-muted-foreground"><Mail className="h-4 w-4" /> <span className="text-foreground font-medium">{user.email}</span></div>
                <div className="flex items-center gap-2 text-muted-foreground"><Phone className="h-4 w-4" /> <span className="text-foreground font-medium">{user.phone || "—"}</span></div>
                <div className="flex items-center gap-2 text-muted-foreground"><Lock className="h-4 w-4" /> <span className="text-foreground font-medium">••••••••</span></div>
              </div>
            )}
          </motion.div>

          {/* Analysis History */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <h2 className="text-xl font-display font-semibold mb-4">{t("profile.history")}</h2>
            
            {loadingHistory ? (
              <div className="glass rounded-xl p-12 text-center flex flex-col items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary mb-3" />
                <p className="text-muted-foreground">Loading history...</p>
              </div>
            ) : displayRecords.length === 0 ? (
              <div className="glass rounded-xl p-12 text-center">
                <ImageIcon className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
                <p className="text-muted-foreground">{t("profile.empty")}</p>
              </div>
            ) : (
              <div className="space-y-3">
                {displayRecords.map(h => (
                  <div
                    key={h.id}
                    className="glass rounded-xl p-4 flex items-center justify-between cursor-pointer hover:bg-primary/5 transition"
                    onClick={() => setSelectedRecord(h)}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center overflow-hidden shrink-0">
                        {h.image_url || h.imagePreview ? (
                          <img src={h.image_url || h.imagePreview} alt="crop" className="w-full h-full object-cover" />
                        ) : (
                          <ImageIcon className="h-5 w-5 text-primary" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium">{translateDisease(h.disease)}</p>
                        <p className="text-xs text-muted-foreground capitalize">{h.crop || "Unknown crop"}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{t("result.severity")}: {h.severity}%</p>
                      <p className="text-xs text-muted-foreground flex items-center gap-1 justify-end">
                        <Calendar className="h-3 w-3" />
                        {new Date(h.created_at || h.date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        </div>
      </main>

      {/* Full record detail modal */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" onClick={() => setSelectedRecord(null)}>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative bg-background rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden max-h-[90vh] flex flex-col md:flex-row"
            onClick={e => e.stopPropagation()}
          >
            {/* Close */}
            <button onClick={() => setSelectedRecord(null)} className="absolute top-4 right-4 z-10 p-1.5 rounded-full bg-secondary/80 hover:bg-secondary transition backdrop-blur-sm">
              <X className="h-4 w-4" />
            </button>

            {/* Images Column */}
            <div className="relative bg-muted/40 md:w-1/2 flex flex-col p-4 gap-4 overflow-y-auto border-b md:border-b-0 md:border-r border-border">
              {selectedRecord.image_url || selectedRecord.imagePreview ? (
                <div className="w-full space-y-4 my-auto">
                  <div className="relative rounded-lg overflow-hidden border border-border shadow-sm">
                    <img src={selectedRecord.image_url || selectedRecord.imagePreview} alt="Original" className="w-full h-auto object-cover" />
                    <div className="absolute top-2 left-2 bg-black/70 text-white text-[10px] px-2 py-1 rounded font-medium">
                      📷 Original
                    </div>
                  </div>
                  
                  {selectedRecord.heatmap_url && (
                    <div className="relative rounded-lg overflow-hidden border border-primary/40 shadow-sm">
                      <img src={selectedRecord.heatmap_url} alt="Heatmap" className="w-full h-auto object-cover" />
                      <div className="absolute top-2 left-2 bg-primary/90 text-primary-foreground text-[10px] px-2 py-1 rounded font-medium">
                        🔥 Heatmap
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="h-48 md:h-full flex items-center justify-center">
                  <ImageIcon className="h-16 w-16 text-muted-foreground/50" />
                </div>
              )}
            </div>

            {/* Result Details Column */}
            <div className="p-6 space-y-6 md:w-1/2 overflow-y-auto">
              <div className="flex items-start gap-3">
                {selectedRecord.severity === 0
                  ? <CheckCircle className="h-8 w-8 text-green-500 shrink-0 mt-1" />
                  : <AlertTriangle className="h-8 w-8 text-destructive shrink-0 mt-1" />
                }
                <div>
                  {selectedRecord.crop && (
                    <>
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wide font-semibold">{t("result.crop_label")}</p>
                      <p className="font-semibold text-base mb-2 capitalize">{translateCrop(selectedRecord.crop)}</p>
                    </>
                  )}
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wide font-semibold">{t("result.disease_label")}</p>
                  <h2 className="text-2xl font-display font-bold leading-tight">{translateDisease(selectedRecord.disease)}</h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    {selectedRecord.severity === 0 ? "Crop appears healthy" : t("result.disease_detected")}
                  </p>
                </div>
              </div>

              <div className="space-y-4 pt-2">
                <div>
                  <div className="flex justify-between text-sm mb-1.5">
                    <span className="text-muted-foreground font-medium">{t("result.severity")}</span>
                    <span className="font-bold">{selectedRecord.severity}%</span>
                  </div>
                  <Progress value={selectedRecord.severity} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1.5">
                    <span className="text-muted-foreground font-medium">{t("result.confidence")}</span>
                    <span className="font-bold">{selectedRecord.confidence}%</span>
                  </div>
                  <Progress value={selectedRecord.confidence} className="h-2 bg-blue-100" />
                </div>
              </div>

              {/* Treatment & Precautions (Only show if disease is present) */}
              {selectedRecord.severity > 0 && (
                <div className="space-y-4 pt-4 border-t border-border">
                  
                  {/* Treatment */}
                  {selectedRecord.treatment && selectedRecord.treatment.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="flex items-center gap-2 text-sm font-semibold text-green-700 dark:text-green-400">
                        <FileText className="h-4 w-4" /> Personalized Treatment
                      </h4>
                      <div className="bg-green-50/50 dark:bg-green-950/20 p-3 rounded-lg border border-green-200/50 dark:border-green-800/50">
                        <p className="text-xs text-foreground/90 leading-relaxed">
                          {Array.isArray(selectedRecord.treatment) ? selectedRecord.treatment.join(" ") : selectedRecord.treatment}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Precautions / Prevention */}
                  {selectedRecord.prevention && selectedRecord.prevention.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="flex items-center gap-2 text-sm font-semibold text-orange-700 dark:text-orange-400">
                        <ShieldAlert className="h-4 w-4" /> Precautions
                      </h4>
                      <div className="bg-orange-50/50 dark:bg-orange-950/20 p-3 rounded-lg border border-orange-200/50 dark:border-orange-800/50">
                        <p className="text-xs text-foreground/90 leading-relaxed">
                          {Array.isArray(selectedRecord.prevention) ? selectedRecord.prevention.join(" ") : selectedRecord.prevention}
                        </p>
                      </div>
                    </div>
                  )}
                  
                  {/* Symptoms */}
                  {selectedRecord.symptoms && selectedRecord.symptoms.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="flex items-center gap-2 text-sm font-semibold text-blue-700 dark:text-blue-400">
                        <Activity className="h-4 w-4" /> Symptoms to Watch
                      </h4>
                      <ul className="list-disc list-inside text-xs text-muted-foreground ml-1 space-y-1">
                        {(Array.isArray(selectedRecord.symptoms) ? selectedRecord.symptoms : [selectedRecord.symptoms]).map((s: string, i: number) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                </div>
              )}

              <div className="text-xs text-muted-foreground space-y-2 pt-4 border-t border-border">
                <p className="flex items-center gap-2">
                  <ImageIcon className="h-4 w-4" /> 
                  <span className="break-all">{selectedRecord.imageName || "database_record.jpg"}</span>
                </p>
                <p className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" /> 
                  {new Date(selectedRecord.created_at || selectedRecord.date).toLocaleString()}
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      <Footer />
    </div>
  );
};

export default Profile;