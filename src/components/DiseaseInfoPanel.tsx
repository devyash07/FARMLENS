import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Activity, Loader2, Info } from "lucide-react";

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
  isHealthy,
}: DiseaseInfoPanelProps) => {
  const [apiResponse, setApiResponse] = useState<any>(null);
  const [loading, setLoading] = useState(true); 
  const [error, setError] = useState(false);
  
  const currentLang = localStorage.getItem("farmlens_lang") || "en";

  useEffect(() => {
    if (isHealthy || !diseaseName) {
      setApiResponse(null);
      setLoading(false);
      return;
    }

    const fetchDiseaseInfo = async () => {
      setLoading(true);
      setError(false);
      try {
        const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        const searchKey = diseaseKey || diseaseName;

        // Passing cropName so the backend can translate the full subtitle perfectly
        const response = await fetch(
          `${apiBase}/api/disease/disease/${encodeURIComponent(searchKey)}?language=${currentLang}&crop=${encodeURIComponent(cropName)}`,
          { headers: { "ngrok-skip-browser-warning": "true" } }
        );

        if (response.ok) {
          const result = await response.json();
          setApiResponse(result); // Store the entire response (including found status and ui_labels)
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
  }, [diseaseName, diseaseKey, cropName, isHealthy, currentLang]);

  if (isHealthy || !diseaseName) return null;

  if (loading) {
    return (
      <Card className="border-border">
        <CardContent className="flex items-center justify-center py-10">
          <Loader2 className="h-6 w-6 animate-spin text-primary mr-2" />
          <span className="text-sm text-muted-foreground">Translating insights...</span>
        </CardContent>
      </Card>
    );
  }

  // Extract our safe data
  const ui = apiResponse?.ui_labels;
  const info = apiResponse?.data;
  const isFound = apiResponse?.found;

  return (
    <Card className="border-border">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Info className="h-5 w-5 text-primary" />
          {ui?.title || "Detailed Disease Insights"}
        </CardTitle>
        <CardDescription>
          {ui?.subtitle || `Comprehensive analysis and management guidelines for ${diseaseName} in ${cropName}`}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error || !isFound || !info ? (
          <p className="text-xs text-muted-foreground italic">
             {ui?.not_found_msg || "Additional detailed database info currently unavailable for this specific classification."}
          </p>
        ) : (
          <div className="space-y-4">
            {info.description && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                  {ui?.description_label || "Description"}
                </h4>
                <p className="text-sm leading-relaxed text-foreground/90">{info.description}</p>
              </div>
            )}

            {info.symptoms && info.symptoms.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                  <Activity className="h-3.5 w-3.5 text-blue-500" /> 
                  {ui?.symptoms_label || "Key Symptoms"}
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
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                  {ui?.causes_label || "Causes & Pathogen"}
                </h4>
                <p className="text-xs leading-relaxed text-foreground/90">{info.causes}</p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};