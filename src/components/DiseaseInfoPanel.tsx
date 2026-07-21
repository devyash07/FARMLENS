import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ShieldAlert, Activity, FileText, Loader2, Info } from "lucide-react";

interface DiseaseInfoPanelProps {
  diseaseKey?: string;
  diseaseName: string;
  cropName: string;
  severity: number;
  isHealthy: boolean;
}

export const DiseaseInfoPanel = ({
  diseaseKey,
  diseaseName,
  cropName,
  severity,
  isHealthy,
}: DiseaseInfoPanelProps) => {
  const [info, setInfo] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (isHealthy || !diseaseName) {
      setInfo(null);
      return;
    }

    const fetchDiseaseInfo = async () => {
      setLoading(true);
      setError(false);
      try {
        const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        const searchKey = diseaseKey || diseaseName;
        const lang = localStorage.getItem("farmlens_lang") || "en";

        const response = await fetch(
          `${apiBase}/api/disease/disease/${encodeURIComponent(searchKey)}?language=${lang}`,
          {
            headers: {
              "ngrok-skip-browser-warning": "true"
            }
          }
        );

        if (response.ok) {
          const data = await response.json();
          setInfo(data);
        } else {
          setError(true);
        }
      } catch (err) {
        console.error("[DiseaseInfo] Failed to fetch disease data:", err);
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    fetchDiseaseInfo();
  }, [diseaseName, diseaseKey, isHealthy]);

  if (isHealthy || !diseaseName) return null;

  return (
    <Card className="border-border">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Info className="h-5 w-5 text-primary" />
          Detailed Disease Insights
        </CardTitle>
        <CardDescription>
          Comprehensive analysis and management guidelines for {diseaseName} in {cropName}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading ? (
          <div className="flex items-center justify-center py-6 text-muted-foreground gap-2">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            <span className="text-sm">Fetching detailed guidelines...</span>
          </div>
        ) : error || !info ? (
          <p className="text-xs text-muted-foreground italic">
            Additional detailed database info currently unavailable for this specific classification.
          </p>
        ) : (
          <div className="space-y-4">
            {info.description && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Description</h4>
                <p className="text-sm leading-relaxed text-foreground/90">{info.description}</p>
              </div>
            )}

            {info.symptoms && info.symptoms.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                  <Activity className="h-3.5 w-3.5 text-blue-500" /> Key Symptoms
                </h4>
                <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1 ml-1">
                  {info.symptoms.map((symptom: string, idx: number) => (
                    <li key={idx}>{symptom}</li>
                  ))}
                </ul>
              </div>
            )}

            {info.causes && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Causes & Pathogen</h4>
                <p className="text-xs leading-relaxed text-foreground/90">{info.causes}</p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};