import { useNavigate } from "react-router-dom";
import { useAuth, AnalysisRecord } from "@/contexts/AuthContext";
import { useI18n } from "@/contexts/I18nContext";
import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { User, ImageIcon, Calendar, Pencil, Check, X, Camera, Lock, Phone, Mail, Hash, AlertTriangle, CheckCircle } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

const Profile = () => {
  const { isAuthenticated, user, history, updateProfile } = useAuth();
  const { t, translateCrop, translateDisease } = useI18n();
  const navigate = useNavigate();
  const avatarRef = useRef<HTMLInputElement>(null);

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ name: "", phone: "", email: "", password: "", confirmPassword: "" });
  const [formError, setFormError] = useState("");
  const [saved, setSaved] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<AnalysisRecord | null>(null);

  useEffect(() => { if (!isAuthenticated) navigate("/login"); }, [isAuthenticated]);

  useEffect(() => {
    if (user) setForm({ name: user.name, phone: user.phone || "", email: user.email, password: "", confirmPassword: "" });
  }, [user]);

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
            {history.length === 0 ? (
              <div className="glass rounded-xl p-12 text-center">
                <ImageIcon className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
                <p className="text-muted-foreground">{t("profile.empty")}</p>
              </div>
            ) : (
              <div className="space-y-3">
                {history.map(h => (
                  <div
                    key={h.id}
                    className="glass rounded-xl p-4 flex items-center justify-between cursor-pointer hover:bg-primary/5 transition"
                    onClick={() => setSelectedRecord(h)}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center overflow-hidden shrink-0">
                        {h.imagePreview
                          ? <img src={h.imagePreview} alt={h.imageName} className="w-full h-full object-cover" />
                          : <ImageIcon className="h-5 w-5 text-primary" />}
                      </div>
                      <div>
                        <p className="font-medium">{translateDisease(h.disease)}</p>
                        <p className="text-xs text-muted-foreground">{h.imageName}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{t("result.severity")}: {h.severity}%</p>
                      <p className="text-xs text-muted-foreground flex items-center gap-1 justify-end">
                        <Calendar className="h-3 w-3" />
                        {new Date(h.date).toLocaleDateString()}
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
            className="relative bg-background rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            {/* Close */}
            <button onClick={() => setSelectedRecord(null)} className="absolute top-4 right-4 z-10 p-1.5 rounded-full bg-secondary hover:bg-secondary/80 transition">
              <X className="h-4 w-4" />
            </button>

            <div className="grid md:grid-cols-2">
              {/* Image */}
              <div className="relative bg-muted min-h-[260px] flex items-center justify-center">
                {selectedRecord.imagePreview
                  ? <img src={selectedRecord.imagePreview} alt={selectedRecord.imageName} className="w-full h-full object-cover" />
                  : <ImageIcon className="h-16 w-16 text-muted-foreground" />
                }
                {selectedRecord.severity > 0 && (
                  <div className="absolute inset-0 bg-gradient-to-br from-destructive/20 via-transparent to-primary/20 mix-blend-multiply" />
                )}
              </div>

              {/* Result details */}
              <div className="p-6 space-y-5">
                <div className="flex items-start gap-3">
                  {selectedRecord.severity === 0
                    ? <CheckCircle className="h-7 w-7 text-primary shrink-0 mt-0.5" />
                    : <AlertTriangle className="h-7 w-7 text-destructive shrink-0 mt-0.5" />
                  }
                  <div>
                    {selectedRecord.crop && (
                      <>
                        <p className="text-[10px] text-muted-foreground uppercase tracking-wide">{t("result.crop_label")}</p>
                        <p className="font-semibold text-base">{translateCrop(selectedRecord.crop)}</p>
                      </>
                    )}
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wide mt-1">{t("result.disease_label")}</p>
                    <h2 className="text-xl font-display font-bold">{translateDisease(selectedRecord.disease)}</h2>
                    <p className="text-xs text-muted-foreground">
                      {selectedRecord.severity === 0 ? t("result.crop_healthy") : t("result.disease_detected")}
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-muted-foreground">{t("result.severity")}</span>
                      <span className="font-semibold">{selectedRecord.severity}%</span>
                    </div>
                    <Progress value={selectedRecord.severity} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-muted-foreground">{t("result.confidence")}</span>
                      <span className="font-semibold">{selectedRecord.confidence}%</span>
                    </div>
                    <Progress value={selectedRecord.confidence} className="h-2" />
                  </div>
                </div>

                <div className="text-xs text-muted-foreground space-y-1 pt-1 border-t border-border">
                  <p className="flex items-center gap-1.5"><ImageIcon className="h-3 w-3" /> {selectedRecord.imageName}</p>
                  <p className="flex items-center gap-1.5"><Calendar className="h-3 w-3" /> {new Date(selectedRecord.date).toLocaleString()}</p>
                </div>
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
