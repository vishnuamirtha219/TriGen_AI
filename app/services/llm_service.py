"""
LLM Service - Google Gemini Integration for TriGen-AI Chatbot
"""
from flask import current_app

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    genai = None
    HAS_GENAI = False
    print("[LLMService] google-generativeai not installed. Chatbot will use template responses.")

SYSTEM_PROMPT = """You are TriGen-AI, an advanced, highly versatile clinical AI assistant.
You provide holistic medical decision support by integrating genomics, haematology, and immunity data.

You specialize in three core domains:
1. **Immunity Analysis**: WBC counts, neutrophils, lymphocytes, monocytes, IgG/IgM/IgA antibodies, and inflammation markers.
2. **Sickle Cell Anemia**: HBB gene mutations (SNP GAG→GTG), hemoglobin levels (HbA, HbS, HbF), and genotype classification.
3. **Lysosomal Storage Disorders (LSD)**: Enzymatic analysis (Beta-glucosidase, alpha-galactosidase) and organomegaly patterns (Gaucher/Fabry).

**VERSATILITY FEATURE**: You must proactively link findings across domains. If a patient has both a genetic risk (Sickle Cell/LSD) and low immunity, highlight how these factors interact (e.g., increased risk of crisis or infection).

Guidelines:
- Provide clear, professional medical explanations in simple language.
- Interpret patient analysis results and provide actionable, context-aware recommendations.
- Always include the disclaimer that your responses are AI-generated and not a substitute for professional medical advice.
- Be empathetic and supportive in your tone.
- Use bullet points for clinical suggestions.
"""


class LLMService:
    """Wrapper around Google Gemini for medical AI chat responses."""

    def __init__(self):
        self._model = None
        self._configured = False

    def _configure(self):
        """Lazy-configure Gemini with API key from Flask config."""
        if self._configured:
            return

        if not HAS_GENAI:
            print("[LLMService] Skipping Gemini config — library not installed")
            self._configured = False
            return

        try:
            api_key = current_app.config.get('GEMINI_API_KEY', '')
            if not api_key:
                raise ValueError("No GEMINI_API_KEY configured")

            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(
                model_name='gemini-2.0-flash',
                system_instruction=SYSTEM_PROMPT
            )
            self._configured = True
        except Exception as e:
            print(f"[LLMService] Failed to configure Gemini: {e}")
            self._model = None
            self._configured = False

    def generate_response(self, user_message, context_str=""):
        """
        Generate a response using Google Gemini.
        
        Args:
            user_message: The user's chat message
            context_str: Additional context (analysis results, page info, knowledge base)
            
        Returns:
            str: The LLM-generated response, or fallback text on failure
        """
        self._configure()

        if not self._model:
            return self._fallback_response(user_message)

        try:
            # Build the full prompt with context
            prompt_parts = []
            if context_str:
                prompt_parts.append(f"<context>\n{context_str}\n</context>\n")
            prompt_parts.append(f"User: {user_message}")

            full_prompt = "\n".join(prompt_parts)

            response = self._model.generate_content(full_prompt)
            return response.text

        except Exception as e:
            print(f"[LLMService] Gemini API error: {e}")
            return self._fallback_response(user_message)

    def _fallback_response(self, query):
        """Template-based fallback when LLM is unavailable."""
        query_lower = query.lower()

        if any(g in query_lower for g in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']):
            return ("Hello! 👋 I'm the **TriGen-AI Medical Assistant**. I specialize in:\n\n"
                    "• **Immunity Analysis** — WBC, neutrophils, lymphocytes, immunoglobulins\n"
                    "• **Sickle Cell Anemia** — HBB gene mutations, hemoglobin analysis\n"
                    "• **Lysosomal Storage Disorders** — enzyme activity, organomegaly assessment\n\n"
                    "How can I help you today?")

        if 'immunity' in query_lower or 'wbc' in query_lower or 'neutrophil' in query_lower or 'lymphocyte' in query_lower:
            return ("**Immunity Analysis** 🛡️\n\n"
                    "Normal WBC count is **4,000–11,000/mcL**. Key markers include:\n"
                    "• **Neutrophils**: 40–70% (first-line defense)\n"
                    "• **Lymphocytes**: 20–40% (adaptive immunity)\n"
                    "• **Immunoglobulins**: IgG (700–1600 mg/dL), IgM, IgA\n\n"
                    "**Recommendations for low immunity:**\n"
                    "• Vitamin C, D, and Zinc supplementation\n"
                    "• Adequate sleep (7–9 hours)\n"
                    "• Regular moderate exercise\n"
                    "• Balanced diet rich in fruits and vegetables\n\n"
                    "⚕️ *Always consult a healthcare professional for clinical interpretation.*")

        if 'sickle' in query_lower or 'hbs' in query_lower or 'hba' in query_lower or 'hemoglobin' in query_lower:
            return ("**Sickle Cell Anemia** 🧬\n\n"
                    "Caused by a mutation in the **HBB gene** (Glu6Val, GAG→GTG).\n\n"
                    "**Classification:**\n"
                    "• **Normal (AA)**: HbA >95%, HbS 0%\n"
                    "• **Carrier/Trait (AS)**: HbA ~60%, HbS ~40%\n"
                    "• **Diseased (SS)**: HbA <10%, HbS >80%\n\n"
                    "**Management:**\n"
                    "• Hydration and avoiding extreme temperatures\n"
                    "• Folic acid supplementation\n"
                    "• Hydroxyurea therapy (under medical supervision)\n"
                    "• Regular health monitoring\n\n"
                    "⚕️ *Always consult a healthcare professional for clinical interpretation.*")

        if 'lsd' in query_lower or 'gaucher' in query_lower or 'fabry' in query_lower or 'enzyme' in query_lower or 'lysosomal' in query_lower:
            return ("**Lysosomal Storage Disorders (LSD)** 🔬\n\n"
                    "Rare genetic conditions affecting enzyme activity:\n\n"
                    "• **Gaucher Disease**: Low β-Glucosidase (<2.5 nmol/hr/mg)\n"
                    "• **Fabry Disease**: Low α-Galactosidase (<4 nmol/hr/mg)\n\n"
                    "**Common symptoms:**\n"
                    "• Hepatosplenomegaly (enlarged liver/spleen)\n"
                    "• Bone pain, fatigue\n"
                    "• Neurological involvement in severe cases\n\n"
                    "**Treatment:** Enzyme Replacement Therapy (ERT) is the primary approach.\n\n"
                    "⚕️ *Always consult a healthcare professional for clinical interpretation.*")

        if any(w in query_lower for w in ['thank', 'thanks', 'bye', 'okay']):
            return ("You're welcome! 😊 If you have more questions about your analysis results or "
                    "need help with any of the modules, feel free to ask anytime.\n\n"
                    "Stay healthy! 💪")

        if any(w in query_lower for w in ['help', 'what can you do', 'features', 'how']):
            return ("I can help you with:\n\n"
                    "🛡️ **Immunity Analysis** — Interpret your blood markers and immune status\n"
                    "🧬 **Sickle Cell Prediction** — Analyze HBB gene mutations and hemoglobin levels\n"
                    "🔬 **LSD Risk Assessment** — Evaluate enzyme activity for Gaucher/Fabry disease\n\n"
                    "You can ask me questions like:\n"
                    "• *What does a low WBC count mean?*\n"
                    "• *Explain my sickle cell results*\n"
                    "• *What is Gaucher disease?*\n\n"
                    "I'm here to help! 😊")

        return ("I'm the **TriGen-AI Medical Assistant**, specializing in Immunity, Sickle Cell Anemia, "
                "and Lysosomal Storage Disorders.\n\n"
                "Feel free to ask me about:\n"
                "• Your analysis results\n"
                "• Normal ranges for blood markers\n"
                "• Disease information and recommendations\n\n"
                "How can I assist you? 😊")


# Singleton instance
llm_service = LLMService()
