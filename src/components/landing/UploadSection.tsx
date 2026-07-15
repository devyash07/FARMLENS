import { useI18n } from "@/contexts/I18nContext";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Upload, Lock, X, Loader2, Camera, FolderOpen, AlertCircle, CheckCircle2, FileWarning } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { useState, useCallback, useRef } from "react";

// Upload constraints - STRICT VALIDATION
const ALLOWED_TYPES = ['image/jpeg', 'image/png']; // Only JPG/JPEG and PNG
const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png']; // Explicit extensions
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB in bytes
const MAX_FILE_SIZE_MB = 10;

interface ImageEntry {
  file: File;
  preview: string;
  isValid: boolean;
  error?: string;
}

interface UploadError {
  message: string;
  type: 'error' | 'warning';
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
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<UploadError | null>(null);

  /**
   * Validate file type and size with STRICT requirements
   */
  const validateFile = (file: File): { isValid: boolean; error?: string } => {
    // Check if file exists
    if (!file) {
      return { isValid: false, error: '❌ No file provided. Please select an image to upload.' };
    }

    // Check for empty file FIRST
    if (file.size === 0) {
      return { isValid: false, error: '❌ File is empty (0 bytes). Please select a valid image file.' };
    }

    // Check file type - STRICT validation for JPG/JPEG/PNG only
    const fileType = file.type.toLowerCase();
    const fileName = file.name.toLowerCase();
    const fileExtension = fileName.substring(fileName.lastIndexOf('.'));

    // Reject anything that's not explicitly JPG, JPEG, or PNG
    const isValidType = ALLOWED_TYPES.includes(fileType);
    const isValidExtension = ALLOWED_EXTENSIONS.includes(fileExtension);

    if (!isValidType && !isValidExtension) {
      return { 
        isValid: false, 
        error: `❌ Invalid file type. Only JPG, JPEG, and PNG images are accepted. Your file: ${file.name} (${fileType || 'unknown type'})` 
      };
    }

    // Additional check: reject if type doesn't match extension
    if (fileExtension && !isValidExtension) {
      return {
        isValid: false,
        error: `❌ Invalid file extension "${fileExtension}". Only .jpg, .jpeg, and .png files are allowed.`
      };
    }

    // Check file size (must be under 10MB)
    if (file.size > MAX_FILE_SIZE) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
      return { 
        isValid: false, 
        error: `❌ File too large! Maximum size is ${MAX_FILE_SIZE_MB}MB. Your file: ${sizeMB}MB. Please compress or resize the image.` 
      };
    }

    // All checks passed
    return { isValid: true };
  };

  /**
   * Add files with comprehensive validation and user feedback
   */
  const addFiles = useCallback((files: FileList | File[]) => {
    // Prevent upload during processing
    if (isProcessing) {
      setError({ 
        message: '⏳ Please wait. An analysis is currently in progress.', 
        type: 'warning' 
      });
      return;
    }

    if (!files || files.length === 0) {
      setError({ 
        message: '⚠️ No files selected. Please choose at least one image to upload.', 
        type: 'warning' 
      });
      return;
    }

    setError(null); // Clear previous errors
    setUploadProgress(0); // Reset progress
    
    let validCount = 0;
    let invalidCount = 0;
    const errors: string[] = [];
    const totalFiles = files.length;

    Array.from(files).forEach((file, index) => {
      // Validate file
      const validation = validateFile(file);

      if (!validation.isValid) {
        invalidCount++;
        errors.push(validation.error || 'Unknown error');
        console.warn(`[Upload] ❌ Rejected file "${file.name}":`, validation.error);
        return;
      }

      // Check for duplicates
      setImages(prev => {
        if (prev.some(img => img.file.name === file.name && img.file.size === file.size)) {
          console.log(`[Upload] ⚠️ Skipping duplicate: ${file.name}`);
          return prev;
        }

        validCount++;

        // Read file and create preview with progress tracking
        const reader = new FileReader();
        
        reader.onprogress = (e) => {
          if (e.lengthComputable) {
            const progress = ((index + (e.loaded / e.total)) / totalFiles) * 100;
            setUploadProgress(Math.round(progress));
          }
        };

        reader.onload = e => {
          setImages(current => [...current, { 
            file, 
            preview: e.target?.result as string,
            isValid: true
          }]);
          
          // Update progress
          const progress = ((index + 1) / totalFiles) * 100;
          setUploadProgress(Math.round(progress));
          
          console.log(`[Upload] ✅ Successfully loaded: ${file.name}`);
        };

        reader.onerror = () => {
          console.error(`[Upload] ❌ Failed to read file: ${file.name}`);
          errors.push(`Failed to read "${file.name}". The file may be corrupted.`);
          invalidCount++;
        };

        reader.readAsDataURL(file);
        return prev;
      });
    });

    // Show comprehensive error/success feedback
    setTimeout(() => {
      if (invalidCount > 0 && validCount === 0) {
        // All files rejected
        const errorMessage = `❌ All ${invalidCount} file(s) were rejected:\n${errors.slice(0, 3).join('\n')}${errors.length > 3 ? `\n... and ${errors.length - 3} more` : ''}`;
        setError({ message: errorMessage, type: 'error' });
      } else if (invalidCount > 0) {
        // Some files rejected
        const errorMessage = `⚠️ ${invalidCount} of ${totalFiles} file(s) rejected. ${validCount} file(s) added successfully.\n${errors[0]}${errors.length > 1 ? ` (and ${errors.length - 1} more...)` : ''}`;
        setError({ message: errorMessage, type: 'warning' });
      } else if (validCount > 0) {
        // All files accepted
        console.log(`[Upload] ✅ ${validCount} file(s) added successfully`);
        setError({ 
          message: `✅ ${validCount} valid image(s) uploaded successfully!`, 
          type: 'warning' // Using 'warning' for success messages (green)
        });
        
        // Clear success message after 3 seconds
        setTimeout(() => setError(null), 3000);
      }
      
      // Reset progress after a delay
      setTimeout(() => setUploadProgress(0), 1000);
    }, 100);
  }, [isProcessing]);

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
    // Prevent multiple uploads while processing
    if (isProcessing) {
      setError({ 
        message: '⏳ Analysis already in progress. Please wait...', 
        type: 'warning' 
      });
      return;
    }

    // Require at least one valid image
    if (images.length === 0) {
      setError({ 
        message: '❌ No images selected. Please upload at least one image to analyze.', 
        type: 'error' 
      });
      return;
    }
    
    setIsProcessing(true);
    setUploadProgress(0);
    setError(null);

    try {
      // Clear old cached results first
      sessionStorage.removeItem("farmlens_results");
      
      setUploadProgress(20);
      
      // Compress images to avoid quota exceeded error
      const compressed = await Promise.all(
        images.map(async (img, index) => {
          const result = {
            preview: await compressImage(img.preview, 400), // 400KB max per image
            filename: img.file.name
          };
          
          // Update progress during compression
          setUploadProgress(20 + ((index + 1) / images.length) * 60);
          
          return result;
        })
      );
      
      setUploadProgress(85);
      
      sessionStorage.setItem("farmlens_uploads", JSON.stringify(compressed));
      // keep legacy keys for single-image compat
      sessionStorage.setItem("farmlens_upload", compressed[0].preview);
      sessionStorage.setItem("farmlens_filename", compressed[0].filename);
      
      setUploadProgress(100);
      
      console.log(`[Upload] ✅ Navigating to results page with ${compressed.length} image(s)`);
      navigate("/result");
    } catch (error) {
      console.error("[Upload] ❌ Failed to process images:", error);
      setError({ 
        message: '❌ Failed to process images. Please try again with different images.', 
        type: 'error' 
      });
      setIsProcessing(false);
      setUploadProgress(0);
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
              } ${!isAuthenticated ? "opacity-40 pointer-events-none" : ""} ${isProcessing ? "opacity-60 pointer-events-none" : ""}`}
              onDragOver={e => { e.preventDefault(); if (!isProcessing) setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
            >
              {/* Error/Success Alert */}
              {error && (
                <Alert className={`mb-4 ${error.type === 'error' ? 'border-destructive bg-destructive/10' : 'border-green-500 bg-green-500/10'}`}>
                  {error.type === 'error' ? (
                    <AlertCircle className="h-4 w-4 text-destructive" />
                  ) : (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  )}
                  <AlertDescription className={`whitespace-pre-line ${error.type === 'error' ? 'text-destructive' : 'text-green-700 dark:text-green-400'}`}>
                    {error.message}
                  </AlertDescription>
                </Alert>
              )}

              {/* Upload Progress */}
              {uploadProgress > 0 && uploadProgress < 100 && (
                <div className="mb-4">
                  <Progress value={uploadProgress} className="h-2" />
                  <p className="text-xs text-muted-foreground mt-1">
                    {isProcessing ? `Processing... ${uploadProgress}%` : `Loading... ${uploadProgress}%`}
                  </p>
                </div>
              )}

              {/* Drop / choose area always visible */}
              <div className="space-y-3 mb-6">
                <Upload className={`h-10 w-10 mx-auto ${isProcessing ? 'text-muted-foreground/50' : 'text-muted-foreground'}`} />
                <p className="text-muted-foreground">
                  {isProcessing ? "Processing images..." : t("upload.drag")}
                </p>
                
                {/* Camera and Gallery buttons */}
                <div className="flex gap-3 justify-center">
                  <Button 
                    variant="outline" 
                    onClick={handleCameraClick}
                    className="flex-1 max-w-[200px]"
                    disabled={isProcessing}
                  >
                    <Camera className="h-4 w-4 mr-2" />
                    {t("upload.take_photo")}
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={handleGalleryClick}
                    className="flex-1 max-w-[200px]"
                    disabled={isProcessing}
                  >
                    <FolderOpen className="h-4 w-4 mr-2" />
                    {t("upload.choose_files")}
                  </Button>
                </div>
                
                {/* Hidden file inputs - STRICT file type acceptance */}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                  multiple
                  className="hidden"
                  disabled={isProcessing}
                  onChange={e => { 
                    console.log("[FarmLens] Files selected from gallery:", e.target.files?.length);
                    if (e.target.files) addFiles(e.target.files); 
                    e.target.value = ""; 
                  }}
                />
                <input
                  ref={cameraInputRef}
                  type="file"
                  accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                  capture="environment"
                  className="hidden"
                  disabled={isProcessing}
                  onChange={e => { 
                    console.log("[FarmLens] Photo captured from camera:", e.target.files?.length);
                    if (e.target.files) addFiles(e.target.files); 
                    e.target.value = ""; 
                  }}
                />
                
                <p className="text-xs text-muted-foreground font-medium">
                  📋 Accepted: JPG, JPEG, PNG only • Max size: 10MB
                </p>
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
                          disabled={isProcessing}
                          className="absolute top-1 right-1 w-5 h-5 rounded-full bg-black/60 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition hover:bg-destructive disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <X className="h-3 w-3" />
                        </button>
                        <p className="absolute bottom-0 left-0 right-0 text-[10px] text-white bg-black/50 px-1 py-0.5 truncate">
                          {img.file.name}
                        </p>
                        {/* Valid indicator */}
                        <div className="absolute top-1 left-1 w-5 h-5 rounded-full bg-green-500/80 flex items-center justify-center">
                          <CheckCircle2 className="h-3 w-3 text-white" />
                        </div>
                      </div>
                    ))}
                  </div>

                  <p className="text-sm text-muted-foreground">
                    {images.length} {t("result.images")} {t("upload.selected")}
                  </p>

                  <div className="flex gap-3 justify-center">
                    <Button 
                      variant="outline" 
                      onClick={() => {
                        setImages([]);
                        setError(null);
                        setUploadProgress(0);
                      }} 
                      disabled={isProcessing}
                    >
                      {t("upload.clear_all")}
                    </Button>
                    <Button
                      onClick={handleAnalyze}
                      disabled={isProcessing || images.length === 0}
                      className="bg-primary text-primary-foreground hover:bg-primary/90 glow-primary disabled:opacity-50 disabled:cursor-not-allowed"
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
