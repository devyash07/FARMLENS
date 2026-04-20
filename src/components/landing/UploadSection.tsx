import { useI18n } from "@/contexts/I18nContext";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Upload, Lock, X, Loader2, Camera, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState, useCallback, useRef } from "react";

interface ImageEntry {
  file: File;
  preview: string;
}

const UploadSection = () => {
  const { t } = useI18n();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const [images, setImages] = useState<ImageEntry[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const addFiles = useCallback((files: FileList | File[]) => {
    Array.from(files).forEach(f => {
      if (!f.type.startsWith("image/")) return;
      const reader = new FileReader();
      reader.onload = e => {
        setImages(prev => {
          // avoid duplicates by name+size
          if (prev.some(img => img.file.name === f.name && img.file.size === f.size)) return prev;
          return [...prev, { file: f, preview: e.target?.result as string }];
        });
      };
      reader.readAsDataURL(f);
    });
  }, []);

  const handleCameraClick = () => {
    console.log("[FarmLens] Opening camera...");
    cameraInputRef.current?.click();
  };

  const handleGalleryClick = () => {
    console.log("[FarmLens] Opening file picker...");
    fileInputRef.current?.click();
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (!isAuthenticated) return;
    addFiles(e.dataTransfer.files);
  }, [isAuthenticated, addFiles]);

  const removeImage = (index: number) => {
    setImages(prev => prev.filter((_, i) => i !== index));
  };

  const compressImage = async (dataUrl: string, maxSizeKB: number = 500): Promise<string> => {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;
        
        // Scale down if too large
        const maxDim = 1024;
        if (width > maxDim || height > maxDim) {
          if (width > height) {
            height = (height / width) * maxDim;
            width = maxDim;
          } else {
            width = (width / height) * maxDim;
            height = maxDim;
          }
        }
        
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx?.drawImage(img, 0, 0, width, height);
        
        // Try different quality levels to stay under size limit
        let quality = 0.8;
        let compressed = canvas.toDataURL('image/jpeg', quality);
        
        // Reduce quality if still too large
        while (compressed.length > maxSizeKB * 1024 && quality > 0.1) {
          quality -= 0.1;
          compressed = canvas.toDataURL('image/jpeg', quality);
        }
        
        resolve(compressed);
      };
      img.src = dataUrl;
    });
  };

  const handleAnalyze = async () => {
    if (images.length === 0) return;
    
    setIsProcessing(true);
    try {
      // Clear old cached results first
      sessionStorage.removeItem("farmlens_results");
      
      // Compress images to avoid quota exceeded error
      const compressed = await Promise.all(
        images.map(async img => ({
          preview: await compressImage(img.preview, 400), // 400KB max per image
          filename: img.file.name
        }))
      );
      
      sessionStorage.setItem("farmlens_uploads", JSON.stringify(compressed));
      // keep legacy keys for single-image compat
      sessionStorage.setItem("farmlens_upload", compressed[0].preview);
      sessionStorage.setItem("farmlens_filename", compressed[0].filename);
      navigate("/result");
    } catch (error) {
      console.error("Failed to compress images:", error);
      alert(t("error.image_process_failed"));
    } finally {
      setIsProcessing(false);
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
              <div
                className="absolute inset-0 z-10 glass rounded-xl flex flex-col items-center justify-center gap-3 cursor-pointer"
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
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                isDragging ? "border-primary bg-primary/5" : "border-border"
              } ${!isAuthenticated ? "opacity-40 pointer-events-none" : ""}`}
              onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
            >
              {/* Drop / choose area always visible */}
              <div className="space-y-3 mb-6">
                <Upload className="h-10 w-10 mx-auto text-muted-foreground" />
                <p className="text-muted-foreground">{t("upload.drag")}</p>
                
                {/* Camera and Gallery buttons */}
                <div className="flex gap-3 justify-center">
                  <Button 
                    variant="outline" 
                    onClick={handleCameraClick}
                    className="flex-1 max-w-[200px]"
                  >
                    <Camera className="h-4 w-4 mr-2" />
                    {t("upload.take_photo")}
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={handleGalleryClick}
                    className="flex-1 max-w-[200px]"
                  >
                    <FolderOpen className="h-4 w-4 mr-2" />
                    {t("upload.choose_files")}
                  </Button>
                </div>
                
                {/* Hidden file inputs */}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  multiple
                  className="hidden"
                  onChange={e => { 
                    console.log("[FarmLens] Files selected from gallery:", e.target.files?.length);
                    if (e.target.files) addFiles(e.target.files); 
                    e.target.value = ""; 
                  }}
                />
                <input
                  ref={cameraInputRef}
                  type="file"
                  accept="image/*"
                  capture="environment"
                  className="hidden"
                  onChange={e => { 
                    console.log("[FarmLens] Photo captured from camera:", e.target.files?.length);
                    if (e.target.files) addFiles(e.target.files); 
                    e.target.value = ""; 
                  }}
                />
                
                <p className="text-xs text-muted-foreground">{t("upload.supported")}</p>
              </div>

              {/* Thumbnails grid */}
              {images.length > 0 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    {images.map((img, i) => (
                      <div key={i} className="relative group rounded-lg overflow-hidden aspect-square bg-muted">
                        <img src={img.preview} alt={img.file.name} className="w-full h-full object-cover" />
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition" />
                        <button
                          onClick={() => removeImage(i)}
                          className="absolute top-1 right-1 w-5 h-5 rounded-full bg-black/60 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition hover:bg-destructive"
                        >
                          <X className="h-3 w-3" />
                        </button>
                        <p className="absolute bottom-0 left-0 right-0 text-[10px] text-white bg-black/50 px-1 py-0.5 truncate">
                          {img.file.name}
                        </p>
                      </div>
                    ))}
                  </div>

                  <p className="text-sm text-muted-foreground">{images.length} {t("result.images")} {t("upload.selected")}</p>

                  <div className="flex gap-3 justify-center">
                    <Button variant="outline" onClick={() => setImages([])} disabled={isProcessing}>
                      {t("upload.clear_all")}
                    </Button>
                    <Button
                      onClick={handleAnalyze}
                      disabled={isProcessing}
                      className="bg-primary text-primary-foreground hover:bg-primary/90 glow-primary"
                    >
                      {isProcessing && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                      {isProcessing ? t("upload.processing") : `${t("upload.analyze")} ${images.length > 1 ? `(${images.length})` : ""}`}
                    </Button>
                  </div>
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
