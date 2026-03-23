import { useI18n } from "@/contexts/I18nContext";
import { motion } from "framer-motion";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Bug, Leaf, ShieldCheck, Droplets, Sprout, AlertTriangle } from "lucide-react";

const guideData = [
  {
    id: "fungicides",
    icon: Droplets,
    title: "Fungicides",
    titleHi: "कवकनाशी",
    items: [
      { name: "Mancozeb", use: "Broad-spectrum preventive fungicide for blights, rusts, and leaf spots.", useHi: "झुलसा, जंग और पत्ती के धब्बों के लिए व्यापक-स्पेक्ट्रम निवारक कवकनाशी।" },
      { name: "Carbendazim", use: "Systemic fungicide effective against powdery mildew and root rot.", useHi: "चूर्णिल फफूंदी और जड़ सड़न के खिलाफ प्रभावी प्रणालीगत कवकनाशी।" },
      { name: "Copper Oxychloride", use: "Contact fungicide for downy mildew and bacterial diseases.", useHi: "मृदुरोमिल फफूंदी और जीवाणु रोगों के लिए संपर्क कवकनाशी।" },
    ],
  },
  {
    id: "pest-control",
    icon: Bug,
    title: "Pest Control",
    titleHi: "कीट नियंत्रण",
    items: [
      { name: "Imidacloprid", use: "Controls sucking pests like aphids, whiteflies, and jassids.", useHi: "एफिड्स, सफेद मक्खी और जैसिड जैसे रस चूसने वाले कीटों को नियंत्रित करता है।" },
      { name: "Chlorpyrifos", use: "Soil application for termites, borers, and root-feeding pests.", useHi: "दीमक, बोरर और जड़ खाने वाले कीटों के लिए मिट्टी में प्रयोग।" },
      { name: "Neem Oil", use: "Organic pest repellent effective against a wide range of insects.", useHi: "कीटों की एक विस्तृत श्रृंखला के खिलाफ प्रभावी जैविक कीट विकर्षक।" },
    ],
  },
  {
    id: "preventive",
    icon: ShieldCheck,
    title: "Preventive Measures",
    titleHi: "निवारक उपाय",
    items: [
      { name: "Crop Rotation", use: "Rotate crops seasonally to break disease and pest cycles.", useHi: "रोग और कीट चक्र को तोड़ने के लिए मौसमी रूप से फसलों को बदलें।" },
      { name: "Seed Treatment", use: "Treat seeds with fungicides before sowing to prevent soil-borne diseases.", useHi: "मिट्टी जनित रोगों को रोकने के लिए बुवाई से पहले बीजों को कवकनाशी से उपचारित करें।" },
      { name: "Field Sanitation", use: "Remove crop debris and weeds to reduce pest harboring.", useHi: "कीटों के आश्रय को कम करने के लिए फसल अवशेषों और खरपतवारों को हटाएं।" },
    ],
  },
  {
    id: "nutrient",
    icon: Sprout,
    title: "Nutrient Management",
    titleHi: "पोषक तत्व प्रबंधन",
    items: [
      { name: "Nitrogen (N)", use: "Essential for vegetative growth. Apply urea or ammonium sulfate.", useHi: "वानस्पतिक विकास के लिए आवश्यक। यूरिया या अमोनियम सल्फेट लगाएं।" },
      { name: "Phosphorus (P)", use: "Promotes root development and flowering. Use DAP or SSP.", useHi: "जड़ विकास और फूल को बढ़ावा देता है। DAP या SSP का उपयोग करें।" },
      { name: "Potassium (K)", use: "Improves disease resistance and fruit quality. Apply MOP.", useHi: "रोग प्रतिरोधक क्षमता और फल की गुणवत्ता में सुधार करता है। MOP लगाएं।" },
    ],
  },
  {
    id: "warnings",
    icon: AlertTriangle,
    title: "Safety Warnings",
    titleHi: "सुरक्षा चेतावनी",
    items: [
      { name: "PPE Required", use: "Always wear gloves, mask, and goggles when handling chemicals.", useHi: "रसायनों को संभालते समय हमेशा दस्ताने, मास्क और चश्मा पहनें।" },
      { name: "Dosage Compliance", use: "Never exceed recommended dosage to prevent crop damage and resistance.", useHi: "फसल क्षति और प्रतिरोध को रोकने के लिए अनुशंसित खुराक से अधिक न करें।" },
      { name: "Harvest Interval", use: "Maintain pre-harvest interval (PHI) for food safety compliance.", useHi: "खाद्य सुरक्षा अनुपालन के लिए पूर्व-कटाई अंतराल (PHI) बनाए रखें।" },
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
            Your smart guide to better crop care.
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
                        {lang === "hi" ? section.titleHi : section.title}
                      </span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-4 pb-2">
                      {section.items.map(item => (
                        <div key={item.name} className="p-4 rounded-lg bg-background/50 border border-border/50">
                          <h4 className="font-semibold text-foreground mb-1 flex items-center gap-2">
                            <Leaf className="h-3 w-3 text-primary" />
                            {item.name}
                          </h4>
                          <p className="text-sm text-muted-foreground">
                            {lang === "hi" ? item.useHi : item.use}
                          </p>
                        </div>
                      ))}
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
