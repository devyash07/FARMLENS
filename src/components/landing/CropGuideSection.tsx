import { useI18n } from "@/contexts/I18nContext";
import { motion } from "framer-motion";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Bug, Leaf, ShieldCheck, Droplets, Sprout, AlertTriangle, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

const guideData = [
  {
    id: "fungicides",
    icon: Droplets,
    titleKey: "guide.fungicides",
    items: [
      { nameKey: "guide.name.mancozeb", useKey: "guide.mancozeb" },
      { nameKey: "guide.name.carbendazim", useKey: "guide.carbendazim" },
      { nameKey: "guide.name.copper_oxy", useKey: "guide.copper_oxy" },
    ],
  },
  {
    id: "pest-control",
    icon: Bug,
    titleKey: "guide.pest_control",
    items: [
      { nameKey: "guide.name.imidacloprid", useKey: "guide.imidacloprid" },
      { nameKey: "guide.name.chlorpyrifos", useKey: "guide.chlorpyrifos" },
      { nameKey: "guide.name.neem_oil", useKey: "guide.neem_oil" },
    ],
  },
  {
    id: "preventive",
    icon: ShieldCheck,
    titleKey: "guide.preventive",
    items: [
      { nameKey: "guide.name.crop_rotation", useKey: "guide.crop_rotation" },
      { nameKey: "guide.name.seed_treatment", useKey: "guide.seed_treatment" },
      { nameKey: "guide.name.field_sanitation", useKey: "guide.field_sanitation" },
    ],
  },
  {
    id: "nutrient",
    icon: Sprout,
    titleKey: "guide.nutrient",
    items: [
      { nameKey: "guide.name.nitrogen", useKey: "guide.nitrogen" },
      { nameKey: "guide.name.phosphorus", useKey: "guide.phosphorus" },
      { nameKey: "guide.name.potassium", useKey: "guide.potassium" },
    ],
  },
  {
    id: "warnings",
    icon: AlertTriangle,
    titleKey: "guide.warnings",
    items: [
      { nameKey: "guide.name.ppe_required", useKey: "guide.ppe_required" },
      { nameKey: "guide.name.dosage_compliance", useKey: "guide.dosage_compliance" },
      { nameKey: "guide.name.harvest_interval", useKey: "guide.harvest_interval" },
    ],
  },
];

const CropGuideSection = () => {
  const { lang, t } = useI18n();

  return (
    <section className="py-24 bg-secondary/30">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl md:text-4xl font-display font-bold text-center mb-4">
            {t("guide.title")}
          </h2>
          <p className="text-center text-muted-foreground mb-12 max-w-xl mx-auto">
            {t("guide.subtitle")}
          </p>

          <div className="max-w-3xl mx-auto">
            <Accordion type="multiple" className="space-y-3">
              {guideData.map(section => (
                <AccordionItem key={section.id} value={section.id} className="glass rounded-xl border-0 px-6 overflow-hidden">
                  <AccordionTrigger className="hover:no-underline py-5">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-primary/10">
                        <section.icon className="h-5 w-5 text-primary" />
                      </div>
                      <span className="font-display font-semibold text-lg">
                        {t(section.titleKey)}
                      </span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-4 pb-2">
                      {section.items.map(item => (
                        <div key={item.nameKey} className="p-4 rounded-lg bg-background/50 border border-border/50">
                          <h4 className="font-semibold text-foreground mb-1 flex items-center gap-2">
                            <Leaf className="h-3 w-3 text-primary" />
                            {t(item.nameKey)}
                          </h4>
                          <p className="text-sm text-muted-foreground">
                            {t(item.useKey)}
                          </p>
                        </div>
                      ))}
                      
                      {/* Read More button for all sections */}
                      {(section.id === "fungicides" || section.id === "pest-control" || section.id === "preventive" || section.id === "nutrient" || section.id === "warnings") && (
                        <div className="pt-2">
                          <Button
                            variant="outline"
                            size="sm"
                            className="w-full"
                            onClick={() => window.open(`/guide/${section.id}`, '_blank')}
                          >
                            {t("guide.read_more")}
                            <ExternalLink className="h-3 w-3 ml-2" />
                          </Button>
                        </div>
                      )}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default CropGuideSection;
