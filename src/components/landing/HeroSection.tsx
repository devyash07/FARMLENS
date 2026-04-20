import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useI18n } from "@/contexts/I18nContext";

const socialLinks = [
  { src: "/icon-instagram.png", alt: "Instagram", href: "https://instagram.com" },
  { src: "/icon-linkedin.png",  alt: "LinkedIn",  href: "https://linkedin.com"  }, 
  { src: "/icon-twitter.png",   alt: "X/Twitter", href: "https://twitter.com"   },
];

const HeroSection = () => {
  const { isAuthenticated } = useAuth();
  const { lang } = useI18n();
  const navigate = useNavigate();

  const heroImages: Record<string, string> = {
    en: "/englsih-hero.png",
    hi: "/hindi-hero.png",
    bn: "/bengali-hero.png",
    te: "/telugu-hero.png",
    mr: "/marathi-hero.png",
    ta: "/tamil-hero.png",
    gu: "/gujarati-hero.png",
    kn: "/kannada-hero.png",
    pa: "/punjabi-hero.png",
    or: "/odia-hero.png",
    ml: "/malayalam-hero.png",
  };
  const heroImage = heroImages[lang] ?? "/main.png";

  const handleGetStarted = () => {
    if (isAuthenticated) {
      document.getElementById("upload-section")?.scrollIntoView({ behavior: "smooth" });
    } else {
      navigate("/login");
    }
  };

  return (
    <section 
      className="relative w-full overflow-hidden bg-white" 
      style={{ 
        aspectRatio: "2528 / 1688", // Explicitly lock the container to image dimensions
      }}
    >
      {/* Background Image - Forced to absolute 100% of the aspect-ratio box */}
      <img
        src={heroImage}
        alt="FarmLens hero"
        className="absolute inset-0 w-full h-full block"
        style={{ objectFit: "fill" }} 
      />

      {/* Get started hotspot */}
      <button
        onClick={handleGetStarted}
        aria-label="Get started"
        className="absolute cursor-pointer rounded-full"
        style={{ left: "4%", top: "64%", width: "15%", height: "7%" }}
      />

      {/* Social icons — Centered on the right-side circles */}
      <div 
        className="absolute flex flex-col items-center" 
        style={{ 
          left: "48.7%", 
          top: "5.7%",   
          width: "5.5%", 
          gap: "2.1%"    
        }}
      >
        {socialLinks.map(({ src, alt, href }) => (
          <motion.a
            key={alt}
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={alt}
            className="hover:scale-110 transition-transform duration-200 block w-full"
          >
            <img src={src} alt={alt} className="w-full h-auto" />
          </motion.a>
        ))}
      </div>
    </section>
  );
};

export default HeroSection;