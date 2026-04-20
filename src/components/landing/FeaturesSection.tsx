import { useI18n } from "@/contexts/I18nContext";
import { motion } from "framer-motion";
import { Scan, BarChart3, Brain, Zap } from "lucide-react";

const features = [
  { icon: Scan, titleKey: "features.detection", descKey: "features.detection_desc" },
  { icon: BarChart3, titleKey: "features.estimation", descKey: "features.estimation_desc" },
  { icon: Brain, titleKey: "features.explainable", descKey: "features.explainable_desc" },
  { icon: Zap, titleKey: "features.realtime", descKey: "features.realtime_desc" },
];

const FeaturesSection = () => {
  const { t } = useI18n();

  return (
    <section className="py-24">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl md:text-4xl font-display font-bold text-center mb-12">
          {t("features.title")}
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
          {features.map((f, i) => (
            <motion.div
              key={f.titleKey}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="glass rounded-xl p-6 hover:glow-primary transition-shadow duration-300 group"
            >
              <div className="p-3 rounded-lg bg-primary/10 w-fit mb-4 group-hover:bg-primary/20 transition">
                <f.icon className="h-6 w-6 text-primary" />
              </div>
              <h3 className="font-display font-semibold text-lg mb-2">{t(f.titleKey)}</h3>
              <p className="text-sm text-muted-foreground">{t(f.descKey)}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
