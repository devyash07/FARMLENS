import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useI18n } from "@/contexts/I18nContext";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle, ArrowLeft, MessageSquare } from "lucide-react";

// Simulated diseases for demo
const diseases = [
  { name: "Leaf Blight", severity: 72, confidence: 94 },
  { name: "Powdery Mildew", severity: 45, confidence: 88 },
  { name: "Bacterial Spot", severity: 61, confidence: 91 },
  { name: "Healthy", severity: 0, confidence: 97 },
];

const Result = () => {
  const { isAuthenticated, addAnalysis } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [result, setResult] = useState<typeof diseases[0] | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    const preview = sessionStorage.getItem("farmlens_upload");
    const filename = sessionStorage.getItem("farmlens_filename") || "image.jpg";
    if (!preview) {
      navigate("/");
      return;
    }
    setImagePreview(preview);

    // Simulate analysis
    const picked = diseases[Math.floor(Math.random() * diseases.length)];
    setResult(picked);

    addAnalysis({
      imageName: filename,
      disease: picked.name,
      severity: picked.severity,
      confidence: picked.confidence,
    });
  }, []);

  if (!result) return null;

  const isHealthy = result.severity === 0;

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 pt-24 pb-16">
        <div className="container mx-auto px-4 max-w-4xl">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
            <h1 className="text-3xl font-display font-bold text-center">{t("result.disease")}</h1>

            <div className="grid md:grid-cols-2 gap-8">
              {/* Image + heatmap */}
              <div className="space-y-4">
                <div className="relative rounded-xl overflow-hidden glass">
                  {imagePreview && <img src={imagePreview} alt="Uploaded crop" className="w-full h-64 object-cover" />}
                  {!isHealthy && (
                    <div className="absolute inset-0 bg-gradient-to-br from-destructive/20 via-transparent to-primary/20 mix-blend-multiply" />
                  )}
                </div>
                <p className="text-xs text-muted-foreground text-center italic">
                  {t("result.explain")}
                </p>
              </div>

              {/* Results */}
              <div className="glass rounded-xl p-6 space-y-6">
                <div className="flex items-center gap-3">
                  {isHealthy ? (
                    <CheckCircle className="h-8 w-8 text-primary" />
                  ) : (
                    <AlertTriangle className="h-8 w-8 text-destructive" />
                  )}
                  <div>
                    <h2 className="text-2xl font-display font-bold">{result.name}</h2>
                    <p className="text-sm text-muted-foreground">
                      {isHealthy ? "Your crop appears healthy!" : "Disease detected in crop"}
                    </p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-muted-foreground">{t("result.severity")}</span>
                      <span className="font-semibold">{result.severity}%</span>
                    </div>
                    <Progress value={result.severity} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-muted-foreground">{t("result.confidence")}</span>
                      <span className="font-semibold">{result.confidence}%</span>
                    </div>
                    <Progress value={result.confidence} className="h-2" />
                  </div>
                </div>

                <div className="flex flex-col gap-3 pt-4">
                  <Button
                    onClick={() => navigate("/", { state: { scrollToUpload: true } })}
                    className="bg-primary text-primary-foreground hover:bg-primary/90"
                  >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    {t("result.another")}
                  </Button>
                  <Button variant="outline" onClick={() => navigate("/feedback")}>
                    <MessageSquare className="h-4 w-4 mr-2" />
                    {t("result.feedback")}
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Result;
