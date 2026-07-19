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

  const heroImages: Record<string, { webp: string; png: string }> = {
    en: { webp: "/englsih-hero.webp", png: "/englsih-hero.png" },
    hi: { webp: "/hindi-hero.webp", png: "/hindi-hero.png" },
    bn: { webp: "/bengali-hero.webp", png: "/bengali-hero.png" },
    te: { webp: "/telugu-hero.webp", png: "/telugu-hero.png" },
    mr: { webp: "/marathi-hero.webp", png: "/marathi-hero.png" },
    ta: { webp: "/tamil-hero.webp", png: "/tamil-hero.png" },
    gu: { webp: "/gujarati-hero.webp", png: "/gujarati-hero.png" },
    kn: { webp: "/kannada-hero.webp", png: "/kannada-hero.png" },
    pa: { webp: "/punjabi-hero.webp", png: "/punjabi-hero.png" },
    or: { webp: "/odia-hero.webp", png: "/odia-hero.png" },
    ml: { webp: "/malayalam-hero.webp", png: "/malayalam-hero.png" },
  };
  const heroImage = heroImages[lang] ?? { webp: "/main.webp", png: "/main.png" };

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
      {/* Background Image - WebP with PNG fallback */}
      <picture className="absolute inset-0 w-full h-full block">
        <source srcSet={heroImage.webp} type="image/webp" />
        <img
          src={heroImage.png}
          alt="FarmLens hero"
          className="w-full h-full"
          style={{ objectFit: "fill" }}
          fetchPriority="high"
        />
      </picture>

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
            <img src={src} alt={alt} className="w-full h-auto" loading="lazy" />
          </motion.a>
        ))}
      </div>
    </section>
  );
};

export default HeroSection;