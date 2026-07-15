import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  AlertCircle, 
  Shield, 
  Droplets, 
  Wind, 
  Sprout,
  Bug,
  Loader2,
  AlertTriangle
} from "lucide-react";
import { motion } from "framer-motion";

interface DiseaseData {
  crop: string;
  disease: string;
  symptoms: string[];
  prevention: string[];
  treatment: string[];
}

interface DiseaseInfoPanelProps {
  diseaseKey?: string;
  diseaseName?: string;
  cropName?: string;
  severity?: number;
  isHealthy?: boolean;
}

export const DiseaseInfoPanel = ({
  diseaseKey,
  diseaseName,
  cropName,
  severity = 0,
  isHealthy = false,
}: DiseaseInfoPanelProps) => {
  const [diseaseData, setDiseaseData] = useState<DiseaseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDiseaseInfo = async () => {
      if (!diseaseKey && !diseaseName) {
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const searchKey = diseaseKey || diseaseName || "";
        const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";
        
        const response = await fetch(
          `${apiBase}/api/disease/disease/${encodeURIComponent(searchKey)}`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch disease information");
        }

        const result = await response.json();
        
        if (result.found && result.data) {
          setDiseaseData({
            crop: result.data.crop || cropName || "Unknown",
            disease: result.data.disease || diseaseName || "Unknown",
            symptoms: result.data.symptoms || [],
            prevention: result.data.prevention || [],
            treatment: result.data.treatment || [],
          });
        }
      } catch (err) {
        console.error("[DiseaseInfo] Failed to fetch disease data:", err);
        setError("Could not load disease information");
      } finally {
        setLoading(false);
      }
    };

    fetchDiseaseInfo();
  }, [diseaseKey, diseaseName, cropName]);

  if (isHealthy) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card className="bg-gradient-to-br from-green-50/50 to-emerald-50/50 dark:from-green-950/20 dark:to-emerald-950/20 border-green-200 dark:border-green-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-700 dark:text-green-400">
              <Sprout className="h-5 w-5" />
              Plant Health Status
            </CardTitle>
            <CardDescription>
              Your plant is in excellent condition
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-white/50 dark:bg-gray-900/50 rounded-lg p-4 border border-green-200/50 dark:border-green-800/50">
              <p className="text-sm font-semibold text-green-700 dark:text-green-400 mb-2">
                ✓ Healthy Plant
              </p>
              <p className="text-sm text-foreground leading-relaxed">
                No disease symptoms detected. Continue with regular plant care including:
              </p>
              <ul className="mt-3 space-y-2 text-sm text-foreground/80">
                <li className="flex items-start gap-2">
                  <Droplets className="h-4 w-4 mt-0.5 text-blue-500 flex-shrink-0" />
                  <span>Regular watering appropriate to the plant type</span>
                </li>
                <li className="flex items-start gap-2">
                  <Wind className="h-4 w-4 mt-0.5 text-blue-500 flex-shrink-0" />
                  <span>Ensure proper air circulation and sunlight</span>
                </li>
                <li className="flex items-start gap-2">
                  <Shield className="h-4 w-4 mt-0.5 text-blue-500 flex-shrink-0" />
                  <span>Monitor weekly for any signs of disease or pests</span>
                </li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card>
          <CardContent className="pt-6 flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-primary mr-2" />
            <span className="text-muted-foreground">Loading disease information...</span>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  if (error || !diseaseData) {
    return null; // Silently fail - disease info is supplementary
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="space-y-4"
    >
      {/* Symptoms Card */}
      {diseaseData.symptoms.length > 0 && (
        <Card className="border-orange-200/50 dark:border-orange-800/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-700 dark:text-orange-400">
              <AlertTriangle className="h-5 w-5" />
              Symptoms to Watch
            </CardTitle>
            <CardDescription>
              Common indicators of {diseaseData.disease}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {diseaseData.symptoms.map((symptom, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-2 rounded-lg hover:bg-orange-50/30 dark:hover:bg-orange-950/20 transition-colors"
                >
                  <AlertCircle className="h-4 w-4 mt-0.5 text-orange-600 dark:text-orange-400 flex-shrink-0" />
                  <span className="text-sm text-foreground">{symptom}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Prevention Card */}
      {diseaseData.prevention.length > 0 && (
        <Card className="border-blue-200/50 dark:border-blue-800/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-700 dark:text-blue-400">
              <Shield className="h-5 w-5" />
              Prevention Measures
            </CardTitle>
            <CardDescription>
              Steps to prevent {diseaseData.disease}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {diseaseData.prevention.map((measure, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-2 rounded-lg hover:bg-blue-50/30 dark:hover:bg-blue-950/20 transition-colors"
                >
                  <Shield className="h-4 w-4 mt-0.5 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                  <span className="text-sm text-foreground">{measure}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Treatment Options Card */}
      {diseaseData.treatment.length > 0 && (
        <Card className="border-green-200/50 dark:border-green-800/50 bg-gradient-to-br from-green-50/30 to-emerald-50/30 dark:from-green-950/10 dark:to-emerald-950/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-700 dark:text-green-400">
              <Sprout className="h-5 w-5" />
              Treatment Options
            </CardTitle>
            <CardDescription>
              Recommended treatments for {diseaseData.disease}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {diseaseData.treatment.map((treatment, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-3 p-3 rounded-lg bg-white/50 dark:bg-gray-900/50 border border-green-200/30 dark:border-green-800/30"
                >
                  <Bug className="h-4 w-4 mt-1 text-green-600 dark:text-green-400 flex-shrink-0" />
                  <span className="text-sm text-foreground">{treatment}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Disease Info Summary */}
      <Card className="bg-muted/30">
        <CardHeader>
          <CardTitle className="text-sm">Quick Reference</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Crop</p>
              <Badge variant="outline">{diseaseData.crop}</Badge>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Disease</p>
              <Badge variant="secondary">{diseaseData.disease}</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};
