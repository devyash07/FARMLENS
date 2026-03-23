import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import HeroSection from "@/components/landing/HeroSection";
import UploadSection from "@/components/landing/UploadSection";
import CropGuideSection from "@/components/landing/CropGuideSection";
import FeaturesSection from "@/components/landing/FeaturesSection";
import { useEffect } from "react";
import { useLocation } from "react-router-dom";

const Index = () => {
  const location = useLocation();

  useEffect(() => {
    if (location.state?.scrollToUpload) {
      setTimeout(() => {
        document.getElementById("upload-section")?.scrollIntoView({ behavior: "smooth" });
      }, 300);
    }
  }, [location.state]);

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="pt-16">
        <HeroSection />
        <UploadSection />
        <CropGuideSection />
        <FeaturesSection />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
