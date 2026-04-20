import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useI18n } from "@/contexts/I18nContext";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, CheckCircle, ArrowLeft, MessageSquare, ChevronLeft, ChevronRight, Loader2 } from "lucide-react";

interface AnalysisItem {
  preview: string;
  filename: string;
  crop: string;
  disease: string;
  severity: number;
  confidence: number;
  status: string;
  heatmap: string;
  explanation: string;
  treatment: string;
}

// Deterministic mock — same image bytes → same hash → same result (frontend fallback)
const MOCK = [
  { crop: "Tomato",  disease: "Leaf Blight",    severity: 65, confidence: 92 },
  { crop: "Wheat",   disease: "Powdery Mildew", severity: 45, confidence: 88 },
  { crop: "Maize",   disease: "Root Rot",        severity: 80, confidence: 95 },
  { crop: "Potato",  disease: "Bacterial Spot",  severity: 55, confidence: 85 },
  { crop: "Rice",    disease: "Healthy",          severity: 0,  confidence: 97 },
];

async function hashIndex(dataUrl: string): Promise<number> {
  const text = dataUrl.slice(0, 2000); // use first 2KB for speed
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  const arr = new Uint8Array(buf);
  return (arr[0] * 256 + arr[1]) % MOCK.length;
}

async function analyzeImage(preview: string, filename: string, t: (key: string) => string, language: string): Promise<AnalysisItem> {
  // Always try real backend — token is now stored on login
  try {
    const token = localStorage.getItem("farmlens_token");
    console.log("[FarmLens] Token exists:", !!token, token ? `(${token.substring(0, 20)}...)` : "(none)");
    
    if (token) {
      const blob = await (await fetch(preview)).blob();
      const form = new FormData();
      form.append("file", blob, filename);
      form.append("language", language);  // Send user's language preference
      
      console.log("[FarmLens] Sending request to backend with language:", language);
      
      const res = await fetch("http://localhost:8001/analyze", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      
      console.log("[FarmLens] Backend response status:", res.status);
      
      if (res.ok) {
        const d = await res.json();
        console.log("[FarmLens] Backend response:", d);
        return {
          preview,
          filename,
          crop: d.crop || "Unknown",
          disease: d.disease,
          severity: d.severity,
          confidence: d.confidence,
          status: d.status,
          heatmap: d.heatmap_b64 || "",
          explanation: d.explanation || "",
          treatment: d.treatment || "",
        };
      }
      // Log backend errors for debugging
      const err = await res.json().catch(() => ({}));
      console.error("[FarmLens] Backend error:", res.status, err);
    } else {
      console.warn("[FarmLens] No token found in localStorage");
    }
  } catch (e) {
    console.error("[FarmLens] Backend request failed:", e);
  }

  // Deterministic frontend mock fallback
  console.warn("[FarmLens] Using frontend mock fallback");
  const idx = await hashIndex(preview);
  const m = MOCK[idx];
  return {
    preview,
    filename,
    crop: m.crop,
    disease: m.disease,
    severity: m.severity,
    confidence: m.confidence,
    status: m.disease === "Healthy" ? t("result.healthy") : t("result.infected"),
    heatmap: "",
    explanation: m.disease === "Healthy" ? t("result.no_disease") : t("result.infected_detected"),
    treatment: t("result.consult_treatment"),
  };
}

const Result = () => {
  const { isAuthenticated, addAnalysis } = useAuth();
  const { t, translateCrop, translateDisease, lang } = useI18n();
  const navigate = useNavigate();
  const [items, setItems] = useState<AnalysisItem[]>([]);
  const [groupedItems, setGroupedItems] = useState<{ [crop: string]: AnalysisItem[] }>({});
  const [currentCrop, setCurrentCrop] = useState<string>("");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  // Initial load - runs once
  useEffect(() => {
    if (!isAuthenticated) { 
      navigate("/login"); 
      return; 
    }

    // Load uploads
    let uploads: { preview: string; filename: string }[] = [];
    const raw = sessionStorage.getItem("farmlens_uploads");
    if (raw) { try { uploads = JSON.parse(raw); } catch { /* ignore */ } }
    if (!uploads.length) {
      const p = sessionStorage.getItem("farmlens_upload");
      const f = sessionStorage.getItem("farmlens_filename") || "image.jpg";
      if (!p) { 
        navigate("/"); 
        return; 
      }
      uploads = [{ preview: p, filename: f }];
    }

    (async () => {
      try {
        console.log(`[FarmLens] Initial analysis in language: ${lang}`);
        const analyzed = await Promise.all(uploads.map(u => analyzeImage(u.preview, u.filename, t, lang)));
        setItems(analyzed);
        
        // Group by crop type
        const grouped: { [crop: string]: AnalysisItem[] } = {};
        analyzed.forEach(item => {
          const crop = item.crop || "Unknown";
          if (!grouped[crop]) grouped[crop] = [];
          grouped[crop].push(item);
        });
        setGroupedItems(grouped);
        
        // Set initial crop to first group
        const firstCrop = Object.keys(grouped)[0] || "Unknown";
        setCurrentCrop(firstCrop);
        
        setLoading(false);
        
        // Save to history (without image previews to avoid quota issues)
        analyzed.forEach(a => addAnalysis({
          imageName: a.filename,
          crop: a.crop,
          disease: a.disease,
          severity: a.severity,
          confidence: a.confidence,
        }));
      } catch (error) {
        console.error("[FarmLens] Analysis failed:", error);
        setLoading(false);
        alert(t("error.analysis_failed"));
        navigate("/");
      }
    })();
  }, []); // Run only once on mount

  // Language change - re-analyze with new language
  useEffect(() => {
    // Skip if no items loaded yet (initial load)
    if (items.length === 0) return;

    const reAnalyze = async () => {
      setLoading(true);
      
      // Load uploads from sessionStorage
      let uploads: { preview: string; filename: string }[] = [];
      const raw = sessionStorage.getItem("farmlens_uploads");
      if (raw) { try { uploads = JSON.parse(raw); } catch { /* ignore */ } }
      if (!uploads.length) {
        const p = sessionStorage.getItem("farmlens_upload");
        const f = sessionStorage.getItem("farmlens_filename") || "image.jpg";
        if (!p) return;
        uploads = [{ preview: p, filename: f }];
      }

      try {
        console.log(`[FarmLens] Re-analyzing in language: ${lang}`);
        const analyzed = await Promise.all(uploads.map(u => analyzeImage(u.preview, u.filename, t, lang)));
        setItems(analyzed);
        
        // Group by crop type
        const grouped: { [crop: string]: AnalysisItem[] } = {};
        analyzed.forEach(item => {
          const crop = item.crop || "Unknown";
          if (!grouped[crop]) grouped[crop] = [];
          grouped[crop].push(item);
        });
        setGroupedItems(grouped);
        
        setLoading(false);
      } catch (error) {
        console.error("[FarmLens] Re-analysis failed:", error);
        setLoading(false);
      }
    };

    reAnalyze();
  }, [lang]); // Only re-run when language changes

  if (loading) return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-3">
          <Loader2 className="h-10 w-10 animate-spin text-primary mx-auto" />
          <p className="text-muted-foreground">{t("result.analyzing")}{items.length > 1 ? t("result.analyzing_plural") : ""}...</p>
        </div>
      </main>
      <Footer />
    </div>
  );

  if (!items.length) return null;
  
  // Get current crop group with safety checks
  const cropGroups = Object.keys(groupedItems);
  const currentGroup = groupedItems[currentCrop] || [];
  
  // Fallback if current group is empty (shouldn't happen but safety first)
  if (currentGroup.length === 0 && items.length > 0) {
    const fallbackCrop = cropGroups[0] || "Unknown";
    const fallbackGroup = groupedItems[fallbackCrop] || items;
    const item = fallbackGroup[0] || items[0];
    const isHealthy = item.status === "Healthy";
    const total = fallbackGroup.length;
    
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-3">
            <p className="text-muted-foreground">{t("result.loading")}</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }
  
  const item = currentGroup[currentIndex] || currentGroup[0];
  const isHealthy = item.status === "Healthy";
  const total = currentGroup.length;
  
  // Calculate aggregated stats for current crop
  const avgSeverity = currentGroup.length > 0 
    ? Math.round(currentGroup.reduce((sum, i) => sum + i.severity, 0) / currentGroup.length)
    : 0;
  const avgConfidence = currentGroup.length > 0
    ? Math.round(currentGroup.reduce((sum, i) => sum + i.confidence, 0) / currentGroup.length)
    : 0;
  const diseaseCount = currentGroup.filter(i => i.status !== "Healthy").length;
  const healthyCount = currentGroup.filter(i => i.status === "Healthy").length;

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 pt-24 pb-16">
        <div className="container mx-auto px-4 max-w-4xl">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">

            <div className="flex items-center justify-between">
              <h1 className="text-3xl font-display font-bold">{t("result.disease")}</h1>
              {total > 1 && <span className="text-sm text-muted-foreground">{currentIndex + 1} / {total}</span>}
            </div>

            {/* Crop Group Selector - only show if multiple crops detected */}
            {cropGroups.length > 1 && (
              <div className="glass rounded-lg p-4 space-y-3">
                <p className="text-sm font-semibold text-muted-foreground">{t("result.detected_crops")} ({items.length} {t("result.images")})</p>
                <div className="flex flex-wrap gap-2">
                  {cropGroups.map(crop => {
                    const count = groupedItems[crop].length;
                    const isActive = crop === currentCrop;
                    return (
                      <button
                        key={crop}
                        onClick={() => {
                          setCurrentCrop(crop);
                          setCurrentIndex(0); // Reset to first image in new crop group
                        }}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                          isActive 
                            ? "bg-primary text-primary-foreground" 
                            : "bg-muted hover:bg-muted/80"
                        }`}
                      >
                        {crop} ({count})
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Aggregated Stats for Current Crop - only show if multiple images in group */}
            {currentGroup.length > 1 && (
              <div className="glass rounded-lg p-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-primary">{currentGroup.length}</p>
                  <p className="text-xs text-muted-foreground">{t("result.total_images")}</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">{healthyCount}</p>
                  <p className="text-xs text-muted-foreground">{t("result.healthy")}</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-destructive">{diseaseCount}</p>
                  <p className="text-xs text-muted-foreground">{t("result.infected")}</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold">{avgSeverity}%</p>
                  <p className="text-xs text-muted-foreground">{t("result.avg_severity")}</p>
                </div>
              </div>
            )}

            {/* Thumbnail strip for current crop group */}
            {total > 1 && (
              <div className="flex gap-2 overflow-x-auto pb-1">
                {currentGroup.map((img, i) => (
                  <button key={i} onClick={() => setCurrentIndex(i)}
                    className={`shrink-0 w-16 h-16 rounded-lg overflow-hidden border-2 transition ${i === currentIndex ? "border-primary" : "border-transparent opacity-60 hover:opacity-100"}`}>
                    <img src={img.preview} alt={img.filename} className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            )}

            <AnimatePresence mode="wait">
              <motion.div key={`${currentCrop}-${currentIndex}`} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.2 }} className="grid md:grid-cols-2 gap-8">

                {/* Images side-by-side */}
                <div className="space-y-3">
                  {item.heatmap ? (
                    <>
                      <div className="grid grid-cols-2 gap-3">
                        {/* Original */}
                        <div className="space-y-1">
                          <div className="relative rounded-xl overflow-hidden glass">
                            <img src={item.preview} alt="Original" className="w-full h-64 object-cover" />
                            <div className="absolute bottom-2 left-2 bg-black/60 text-white text-[10px] px-2 py-0.5 rounded">
                              📷 {t("result.original")}
                            </div>
                          </div>
                          <p className="text-xs text-center text-muted-foreground">{t("result.original")}</p>
                        </div>
                        {/* Heatmap */}
                        <div className="space-y-1">
                          <div className="relative rounded-xl overflow-hidden glass">
                            <img src={item.heatmap} alt="Heatmap" className="w-full h-64 object-cover" />
                            <div className="absolute bottom-2 left-2 bg-black/60 text-white text-[10px] px-2 py-0.5 rounded">
                              🌡 {t("result.heatmap")}
                            </div>
                          </div>
                          <p className="text-xs text-center text-muted-foreground">{t("result.infected_regions")}</p>
                        </div>
                      </div>
                      
                      {/* Heatmap Legend */}
                      <div className="glass rounded-lg p-3 space-y-2">
                        <p className="text-xs font-semibold text-center mb-2">{t("result.heatmap_guide")}</p>
                        <div className="space-y-1.5">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-4 rounded" style={{ background: 'linear-gradient(to right, #0000ff, #00ffff)' }}></div>
                            <span className="text-xs text-muted-foreground flex-1">{t("result.healthy_low")}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-4 rounded" style={{ background: 'linear-gradient(to right, #00ff00, #ffff00)' }}></div>
                            <span className="text-xs text-muted-foreground flex-1">{t("result.mild_infection")}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-4 rounded" style={{ background: 'linear-gradient(to right, #ff8800, #ff0000)' }}></div>
                            <span className="text-xs text-muted-foreground flex-1">{t("result.severe_infection")}</span>
                          </div>
                        </div>
                        <div className="pt-2 border-t border-border">
                          <p className="text-[10px] text-muted-foreground text-center italic">
                            {t("result.warmer_colors")}
                          </p>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="relative rounded-xl overflow-hidden glass">
                      <img src={item.preview} alt="Original" className="w-full h-64 object-cover" />
                      {!isHealthy && (
                        <div className="absolute inset-0 bg-gradient-to-br from-destructive/20 via-transparent to-primary/20 mix-blend-multiply" />
                      )}
                    </div>
                  )}
                  <p className="text-xs text-muted-foreground text-center italic">{item.explanation}</p>
                  {total > 1 && (
                    <div className="flex justify-between">
                      <Button variant="outline" size="sm" disabled={currentIndex === 0} onClick={() => setCurrentIndex(c => c - 1)}>
                        <ChevronLeft className="h-4 w-4 mr-1" /> {t("result.prev")}
                      </Button>
                      <Button variant="outline" size="sm" disabled={currentIndex === total - 1} onClick={() => setCurrentIndex(c => c + 1)}>
                        {t("result.next")} <ChevronRight className="h-4 w-4 ml-1" />
                      </Button>
                    </div>
                  )}
                </div>

                {/* Result card */}
                <div className="glass rounded-xl p-6 space-y-5">
                  <div className="flex items-start gap-3">
                    {isHealthy ? <CheckCircle className="h-8 w-8 text-primary mt-0.5 shrink-0" /> : <AlertTriangle className="h-8 w-8 text-destructive mt-0.5 shrink-0" />}
                    <div>
                      <p className="text-xs text-muted-foreground uppercase tracking-wide mb-0.5">{t("result.crop_label")}</p>
                      <h2 className="text-xl font-display font-bold">{translateCrop(item.crop)}</h2>
                      <p className="text-xs text-muted-foreground uppercase tracking-wide mt-2 mb-0.5">{t("result.disease_label")}</p>
                      <p className="text-lg font-semibold">{translateDisease(item.disease)}</p>
                      <span className={`inline-block mt-1 text-xs font-medium px-2 py-0.5 rounded-full ${isHealthy ? "bg-primary/10 text-primary" : "bg-destructive/10 text-destructive"}`}>
                        {isHealthy ? t("result.healthy") : t("result.infected")}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted-foreground">{t("result.severity")}</span>
                        <span className="font-semibold">{item.severity}%</span>
                      </div>
                      <Progress value={item.severity} className="h-2" />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted-foreground">{t("result.confidence")}</span>
                        <span className="font-semibold">{item.confidence}%</span>
                      </div>
                      <Progress value={item.confidence} className="h-2" />
                    </div>
                  </div>

                  {item.treatment && (
                    <div className="border-t border-border pt-3">
                      <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1.5">{t("result.treatment_prevention")}</p>
                      <p className="text-sm leading-relaxed">{item.treatment}</p>
                    </div>
                  )}

                  <p className="text-xs text-muted-foreground border-t border-border pt-3">{item.filename}</p>

                  <div className="flex flex-col gap-3">
                    <Button onClick={() => { 
                      sessionStorage.clear(); // clear all cached data
                      navigate("/", { state: { scrollToUpload: true } }); 
                    }} className="bg-primary text-primary-foreground hover:bg-primary/90">
                      <ArrowLeft className="h-4 w-4 mr-2" /> {t("result.another")}
                    </Button>
                    <Button variant="outline" onClick={() => navigate("/feedback")}>
                      <MessageSquare className="h-4 w-4 mr-2" /> {t("result.feedback")}
                    </Button>
                  </div>
                </div>

              </motion.div>
            </AnimatePresence>
          </motion.div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Result;
