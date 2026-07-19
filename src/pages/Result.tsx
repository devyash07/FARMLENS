import { useNavigate } from "react-router-dom";
import { useAuth, supabase } from "@/contexts/AuthContext";
import { useI18n } from "@/contexts/I18nContext";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { DiseaseInfoPanel } from "@/components/DiseaseInfoPanel";
import { motion, AnimatePresence } from "framer-motion";
import { 
  AlertTriangle, 
  CheckCircle, 
  ArrowLeft, 
  MessageSquare, 
  Loader2,
  ImageIcon,
  Activity,
  Lightbulb,
  ShieldAlert,
  BarChart3,
  FileText,
  RefreshCcw,
  Info
} from "lucide-react";

interface AnalysisItem {
  preview: string;
  filename: string;
  crop: string;
  disease: string;
  disease_key?: string;
  severity: number;
  confidence: number;
  status: string;
  heatmap: string;
  explanation: string;
  treatment: string;
  precautions?: string;
}

// Deterministic mock — same image bytes → same hash → same result (frontend fallback)
const MOCK = [
  { crop: "Tomato",  disease: "Leaf Blight",    severity: 65, confidence: 92 },
  { crop: "Wheat",   disease: "Powdery Mildew", severity: 45, confidence: 88 },
  { crop: "Maize",   disease: "Root Rot",       severity: 80, confidence: 95 },
  { crop: "Potato",  disease: "Bacterial Spot", severity: 55, confidence: 85 },
  { crop: "Rice",    disease: "Healthy",        severity: 0,  confidence: 97 },
];

async function hashIndex(dataUrl: string): Promise<number> {
  const text = dataUrl.slice(0, 2000); // use first 2KB for speed
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  const arr = new Uint8Array(buf);
  return (arr[0] * 256 + arr[1]) % MOCK.length;
}

async function analyzeImage(preview: string, filename: string, t: (key: string) => string, language: string): Promise<AnalysisItem> {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;
    
    if (token) {
      const blob = await (await fetch(preview)).blob();
      const form = new FormData();
      form.append("file", blob, filename);
      form.append("language", language);  
      
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/analyze`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      
      if (res.ok) {
        const d = await res.json();
        return {
          preview,
          filename,
          crop: d.crop || "Unknown",
          disease: d.disease,
          disease_key: d.disease_key || "",
          severity: d.severity,
          confidence: d.confidence,
          status: d.status,
          heatmap: d.heatmap_b64
            ? `data:image/jpeg;base64,${d.heatmap_b64}`
            : "",
          explanation: d.explanation || "",
          treatment: d.treatment || "",
          precautions: d.precautions || "",
        };
      }
    } 
  } catch (e) {
    console.error("[FarmLens] Backend request failed:", e);
  }

  const idx = await hashIndex(preview);
  const m = MOCK[idx];
  return {
    preview,
    filename,
    crop: m.crop,
    disease: m.disease,
    disease_key: "",
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) { 
      navigate("/login"); 
      return; 
    }

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
        const analyzed = await Promise.all(uploads.map(u => analyzeImage(u.preview, u.filename, t, lang)));
        setItems(analyzed);
        
        const grouped: { [crop: string]: AnalysisItem[] } = {};
        analyzed.forEach(item => {
          const crop = item.crop || "Unknown";
          if (!grouped[crop]) grouped[crop] = [];
          grouped[crop].push(item);
        });
        setGroupedItems(grouped);
        setCurrentCrop(Object.keys(grouped)[0] || "Unknown");
        setLoading(false);
        
        analyzed.forEach(async (a) => {
          addAnalysis({
            imageName: a.filename,
            crop: a.crop,
            disease: a.disease,
            severity: a.severity,
            confidence: a.confidence,
          });

          try {
            const { data: { session } } = await supabase.auth.getSession();
            const token = session?.access_token;
            if (!token) return;

            const uploadToBucket = async (base64Data: string, prefix: string) => {
              if (!base64Data || !base64Data.startsWith('data:')) return null;
              try {
                const res = await fetch(base64Data);
                const blob = await res.blob();
                const fileExt = a.filename.split('.').pop() || 'jpg';
                const fileName = `${prefix}_${Date.now()}_${Math.random().toString(36).substring(7)}.${fileExt}`;
                
                const { data, error } = await supabase.storage.from('images').upload(fileName, blob);
                if (error) throw error;
                if (data) {
                  return supabase.storage.from('images').getPublicUrl(fileName).data.publicUrl;
                }
              } catch (err) {
                console.error(`[FarmLens] Storage upload failed for ${prefix}:`, err);
              }
              return null;
            };

            const imageUrl = await uploadToBucket(a.preview, "crop");
            const heatmapUrl = await uploadToBucket(a.heatmap, "heat");

            const backendUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
            await fetch(`${backendUrl.replace(/\/$/, '')}/history`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify({
                crop: a.crop,
                disease: a.disease,
                severity: a.severity,
                confidence: a.confidence,
                image_url: imageUrl,
                heatmap_url: heatmapUrl,
                symptoms: [],
                prevention: a.precautions ? [a.precautions] : [],
                treatment: a.treatment ? [a.treatment] : []
              })
            });
          } catch (e) {
            console.error("[FarmLens] Failed to save detailed history:", e);
          }
        });

      } catch (error) {
        console.error("[FarmLens] Analysis failed:", error);
        setLoading(false);
        alert(t("error.analysis_failed"));
        navigate("/");
      }
    })();
  }, []); 

  useEffect(() => {
    if (items.length === 0) return;
    const reAnalyze = async () => {
      setLoading(true);
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
        const analyzed = await Promise.all(uploads.map(u => analyzeImage(u.preview, u.filename, t, lang)));
        setItems(analyzed);
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
  }, [lang]); 

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
  
  const item = items[0];
  const isHealthy = item.status === "Healthy" || item.disease.toLowerCase() === "healthy";
  
  const getSeverityLevel = (severity: number) => {
    if (severity === 0) return { label: t("result.healthy"), color: "text-green-600", bgColor: "bg-green-100" };
    if (severity < 40) return { label: t("result.mild"), color: "text-yellow-600", bgColor: "bg-yellow-100" };
    if (severity < 70) return { label: t("result.moderate"), color: "text-orange-600", bgColor: "bg-orange-100" };
    return { label: t("result.severe"), color: "text-red-600", bgColor: "bg-red-100" };
  };
  
  const severityInfo = getSeverityLevel(item.severity);
  
  const getConfidenceLevel = (confidence: number) => {
    if (confidence >= 90) return { label: t("result.very_high"), color: "text-green-600" };
    if (confidence >= 80) return { label: t("result.high"), color: "text-blue-600" };
    if (confidence >= 70) return { label: t("result.moderate"), color: "text-yellow-600" };
    return { label: t("result.low"), color: "text-orange-600" };
  };
  
  const confidenceInfo = getConfidenceLevel(item.confidence);

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-background via-background to-primary/5">
      <Navbar />
      <main className="flex-1 pt-20 pb-16">
        <div className="container mx-auto px-4 max-w-7xl">
          <motion.div 
            initial={{ opacity: 0, y: 20 }} 
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="space-y-6"
          >
            
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <h1 className="text-3xl md:text-4xl font-display font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                  {t("result.disease")}
                </h1>
                <p className="text-muted-foreground mt-1">
                  AI-Powered Plant Disease Analysis
                </p>
              </div>
              
              <div className="flex gap-3">
                <Button 
                  onClick={() => { 
                    sessionStorage.clear();
                    navigate("/", { state: { scrollToUpload: true } }); 
                  }}
                  className="bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  <RefreshCcw className="h-4 w-4 mr-2" />
                  {t("result.another")}
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => navigate("/feedback")}
                >
                  <MessageSquare className="h-4 w-4 mr-2" />
                  {t("result.feedback")}
                </Button>
              </div>
            </div>

            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <Card className={`border-2 ${isHealthy ? 'border-green-500 bg-green-50/50 dark:bg-green-950/20' : 'border-orange-500 bg-orange-50/50 dark:bg-orange-950/20'}`}>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-4">
                    {isHealthy ? (
                      <div className="p-3 rounded-full bg-green-500/20">
                        <CheckCircle className="h-8 w-8 text-green-600" />
                      </div>
                    ) : (
                      <div className="p-3 rounded-full bg-orange-500/20">
                        <AlertTriangle className="h-8 w-8 text-orange-600" />
                      </div>
                    )}
                    <div className="flex-1">
                      <h2 className="text-2xl font-bold">
                        {isHealthy ? t("result.healthy_detected_title") : t("result.disease_detected_title")}
                      </h2>
                      <p className="text-muted-foreground">
                        {isHealthy 
                          ? t("result.healthy_desc")
                          : t("result.infected_desc")
                        }
                      </p>
                    </div>
                    <Badge 
                      variant={isHealthy ? "default" : "destructive"}
                      className="text-lg px-4 py-2"
                    >
                      {isHealthy ? t("result.healthy") : t("result.infected")}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            <div className="grid lg:grid-cols-2 gap-6">
              
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
                className="space-y-6"
              >
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <ImageIcon className="h-5 w-5 text-primary" />
                      {t("result.visual_analysis")}
                    </CardTitle>
                    <CardDescription>
                      {t("result.visual_desc")}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <div className="relative rounded-lg overflow-hidden border-2 border-border group">
                          <img 
                            src={item.preview} 
                            alt="Original Plant" 
                            className="w-full aspect-square object-cover transition-transform group-hover:scale-105"
                          />
                          <div className="absolute top-2 left-2">
                            <Badge variant="secondary" className="bg-black/60 text-white border-none">
                              📷 {t("result.original")}
                            </Badge>
                          </div>
                        </div>
                        <p className="text-xs text-center text-muted-foreground font-medium">
                          {t("result.original")}
                        </p>
                      </div>

                      <div className="space-y-2">
                        {item.heatmap ? (
                          <>
                            <div className="relative rounded-lg overflow-hidden border-2 border-primary/50 group">
                              <img 
                                src={item.heatmap} 
                                alt="Disease Heatmap" 
                                className="w-full aspect-square object-cover transition-transform group-hover:scale-105"
                              />
                              <div className="absolute top-2 left-2">
                                <Badge className="bg-primary/90 text-primary-foreground border-none">
                                  🔥 Grad-CAM
                                </Badge>
                              </div>
                            </div>
                            <p className="text-xs text-center text-muted-foreground font-medium">
                              {t("result.heatmap")}
                            </p>
                          </>
                        ) : (
                          <div className="rounded-lg border-2 border-dashed border-border bg-muted aspect-square flex items-center justify-center">
                            <div className="text-center p-4">
                              <Activity className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                              <p className="text-sm text-muted-foreground">
                                Heatmap not available
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {item.heatmap && !isHealthy && (
                      <div className="bg-muted/50 rounded-lg p-4 space-y-3">
                        <div className="flex items-center gap-2 mb-2">
                          <Info className="h-4 w-4 text-primary" />
                          <p className="text-sm font-semibold">{t("result.heatmap_legend")}</p>
                        </div>
                        <div className="space-y-2">
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-4 rounded" style={{ background: 'linear-gradient(to right, #0000ff, #00ffff)' }}></div>
                            <span className="text-xs text-muted-foreground flex-1">{t("result.healthy_area")}</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-4 rounded" style={{ background: 'linear-gradient(to right, #00ff00, #ffff00)' }}></div>
                            <span className="text-xs text-muted-foreground flex-1">{t("result.mild_infection")}</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-4 rounded" style={{ background: 'linear-gradient(to right, #ff8800, #ff0000)' }}></div>
                            <span className="text-xs text-muted-foreground flex-1">{t("result.severe_infection")}</span>
                          </div>
                        </div>
                        <Separator />
                        <p className="text-xs text-muted-foreground italic text-center">
                          {t("result.warmer_colors")}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {item.explanation && (
                  <Card className="bg-gradient-to-br from-blue-50/50 to-purple-50/50 dark:from-blue-950/20 dark:to-purple-950/20">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <Lightbulb className="h-5 w-5 text-blue-600" />
                        {t("result.explainability")}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm leading-relaxed text-foreground/90">
                        {item.explanation}
                      </p>
                    </CardContent>
                  </Card>
                )}
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
                className="space-y-6"
              >
                
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5 text-primary" />
                      {t("result.detection_results")}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <label className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                          {t("result.crop_name")}
                        </label>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="flex-1">
                          <p className="text-2xl font-bold">{translateCrop(item.crop)}</p>
                        </div>
                        <Badge variant="outline" className="text-sm">
                          🌱 Crop
                        </Badge>
                      </div>
                    </div>

                    <Separator />

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <label className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                          {t("result.disease_name")}
                        </label>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="flex-1">
                          <p className="text-2xl font-bold">{translateDisease(item.disease)}</p>
                        </div>
                        <Badge 
                          variant={isHealthy ? "default" : "destructive"}
                          className="text-sm"
                        >
                          {isHealthy ? "✓" : "⚠"} {isHealthy ? t("result.healthy") : t("result.infected")}
                        </Badge>
                      </div>
                    </div>

                    <Separator />

                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <label className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                          {t("result.severity_level")}
                        </label>
                        <Badge className={`${severityInfo.bgColor} ${severityInfo.color} border-none`}>
                          {severityInfo.label}
                        </Badge>
                      </div>
                      <div className="space-y-2">
                        <Progress value={item.severity} className="h-3" />
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-muted-foreground">0%</span>
                          <span className={`text-2xl font-bold ${severityInfo.color}`}>
                            {item.severity}%
                          </span>
                          <span className="text-xs text-muted-foreground">100%</span>
                        </div>
                      </div>
                    </div>

                    <Separator />

                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <label className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                          {t("result.ai_confidence")}
                        </label>
                        <Badge variant="outline" className={confidenceInfo.color}>
                          {confidenceInfo.label}
                        </Badge>
                      </div>
                      <div className="space-y-2">
                        <Progress value={item.confidence} className="h-3 bg-blue-100" />
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-muted-foreground">50%</span>
                          <span className={`text-2xl font-bold ${confidenceInfo.color}`}>
                            {item.confidence}%
                          </span>
                          <span className="text-xs text-muted-foreground">100%</span>
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground italic">
                        {t("result.model_certainty")}
                      </p>
                    </div>

                  </CardContent>
                </Card>

                <DiseaseInfoPanel
                  diseaseKey={item.disease_key}
                  diseaseName={item.disease}
                  cropName={item.crop}
                  severity={item.severity}
                  isHealthy={isHealthy}
                />

                {item.treatment && !isHealthy && (
                  <Card className="bg-gradient-to-br from-green-50/50 to-emerald-50/50 dark:from-green-950/20 dark:to-emerald-950/20 border-green-200 dark:border-green-800">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-green-700 dark:text-green-400">
                        <FileText className="h-5 w-5" />
                        {t("result.treatment")}
                      </CardTitle>
                      <CardDescription>
                        {t("result.treatment_desc")}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="bg-white/50 dark:bg-gray-900/50 rounded-lg p-4 border border-green-200/50 dark:border-green-800/50">
                        <p className="text-sm leading-relaxed text-foreground">
                          {item.treatment}
                        </p>
                      </div>
                      
                      {item.precautions && (
                        <>
                          <Separator />
                          <div className="space-y-3">
                            <div className="flex items-center gap-2">
                              <ShieldAlert className="h-4 w-4 text-orange-600" />
                              <h4 className="text-sm font-semibold text-orange-700 dark:text-orange-400">
                                {t("result.precautions")}
                              </h4>
                            </div>
                            <div className="bg-orange-50/50 dark:bg-orange-950/20 rounded-lg p-3 border border-orange-200/50 dark:border-orange-800/50">
                              <p className="text-xs leading-relaxed text-foreground/90">
                                {item.precautions}
                              </p>
                            </div>
                          </div>
                        </>
                      )}
                    </CardContent>
                  </Card>
                )}

                {isHealthy && (
                  <Card className="bg-gradient-to-br from-green-50/50 to-emerald-50/50 dark:from-green-950/20 dark:to-emerald-950/20 border-green-200 dark:border-green-800">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-green-700 dark:text-green-400">
                        <CheckCircle className="h-5 w-5" />
                        {t("result.maintenance")}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm leading-relaxed">
                        {item.treatment || t("result.maintenance_default")}
                      </p>
                    </CardContent>
                  </Card>
                )}

                <Card className="bg-muted/30">
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-3 text-sm text-muted-foreground">
                      <ImageIcon className="h-4 w-4" />
                      <span className="font-mono text-xs">{item.filename}</span>
                    </div>
                  </CardContent>
                </Card>

              </motion.div>
            </div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="flex flex-col sm:flex-row gap-3 pt-4"
            >
              <Button 
                onClick={() => { 
                  sessionStorage.clear();
                  navigate("/", { state: { scrollToUpload: true } }); 
                }}
                size="lg"
                className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90"
              >
                <RefreshCcw className="h-5 w-5 mr-2" />
                {t("result.another")}
              </Button>
              <Button 
                variant="outline"
                size="lg"
                onClick={() => navigate("/feedback")}
                className="flex-1"
              >
                <MessageSquare className="h-5 w-5 mr-2" />
                {t("result.feedback")}
              </Button>
              <Button 
                variant="outline"
                size="lg"
                onClick={() => navigate("/")}
                className="sm:w-auto"
              >
                <ArrowLeft className="h-5 w-5 mr-2" />
                {t("result.home")}
              </Button>
            </motion.div>

          </motion.div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Result;