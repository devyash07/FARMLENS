import { useI18n } from "@/contexts/I18nContext";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Upload, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState, useCallback, useRef } from "react";

const UploadSection = () => {
  const { t } = useI18n();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = useCallback((f: File) => {
    if (f.type.startsWith("image/")) {
      setFile(f);
      const reader = new FileReader();
      reader.onload = e => setPreview(e.target?.result as string);
      reader.readAsDataURL(f);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (!isAuthenticated) return;
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [isAuthenticated, handleFile]);

  const handleAnalyze = () => {
    if (file) {
      // Store preview for result page
      sessionStorage.setItem("farmlens_upload", preview || "");
      sessionStorage.setItem("farmlens_filename", file.name);
      navigate("/result");
    }
  };

  return (
    <section id="upload-section" className="py-24">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-2xl mx-auto"
        >
          <h2 className="text-3xl md:text-4xl font-display font-bold text-center mb-10">
            {t("upload.title")}
          </h2>

          <div className="relative">
            {!isAuthenticated && (
              <div className="absolute inset-0 z-10 glass rounded-xl flex flex-col items-center justify-center gap-3 cursor-pointer"
                onClick={() => navigate("/login")}
              >
                <Lock className="h-8 w-8 text-primary" />
                <p className="font-medium text-foreground">{t("upload.login_required")}</p>
                <Button size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90">
                  {t("nav.login")}
                </Button>
              </div>
            )}

            <div
              className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors ${
                isDragging ? "border-primary bg-primary/5" : "border-border"
              } ${!isAuthenticated ? "opacity-40 pointer-events-none" : ""}`}
              onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
            >
              {preview ? (
                <div className="space-y-4">
                  <img src={preview} alt="Preview" className="max-h-64 mx-auto rounded-lg" />
                  <p className="text-sm text-muted-foreground">{file?.name}</p>
                  <div className="flex gap-3 justify-center">
                    <Button variant="outline" onClick={() => { setFile(null); setPreview(null); }}>
                      Clear
                    </Button>
                    <Button onClick={handleAnalyze} className="bg-primary text-primary-foreground hover:bg-primary/90 glow-primary">
                      {t("upload.analyze")}
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
                  <p className="text-muted-foreground">{t("upload.drag")}</p>
                  <Button
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    {t("upload.choose")}
                  </Button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={e => {
                      const f = e.target.files?.[0];
                      if (f) handleFile(f);
                    }}
                  />
                  <p className="text-xs text-muted-foreground">Supported: JPG, PNG, WEBP • Max 20MB</p>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default UploadSection;
