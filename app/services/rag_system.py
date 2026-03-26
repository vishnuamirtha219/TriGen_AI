from app.services.llm_service import llm_service
class RAGSystem:
    def __init__(self):
        # Medical Knowledge Base (used as supplementary context for LLM)
        self.knowledge_base = {
            "immunity": "Normal WBC count is 4000-11000/mcL. Neutrophils should be 40-70%, Lymphocytes 20-40%. Low immunity can be improved with diet (Vitamin C, D, Zinc), sleep, and exercise. High WBC might indicate infection.",
            "sickle": "Sickle Cell Anemia is caused by a mutation in the HBB gene (Glu6Val). HbS > 40% usually indicates disease or trait. Hydration and avoiding stress are key for management. Hydroxyurea is a common treatment.",
            "lsd": "Lysosomal Storage Disorders (LSD) like Gaucher or Fabry disease are rare genetic conditions. Low Beta-Glucosidase activity (<2.5) suggests Gaucher disease. Enlarged liver/spleen (hepatosplenomegaly) is a common symptom.",
            "general": "TriGen-AI is a specialized medical assistant for analyzing immunity, sickle cell anemia risks, and LSD risks. Always consult a doctor for a clinical diagnosis."
        }
    def retrieve_context(self, query):
        """Keyword-based retrieval from local knowledge base for LLM context enrichment."""
        query_lower = query.lower()
        context = []

        if "immunity" in query_lower or "wbc" in query_lower or "neutrophil" in query_lower:
            context.append(self.knowledge_base["immunity"])
        if "sickle" in query_lower or "hba" in query_lower or "hbs" in query_lower:
            context.append(self.knowledge_base["sickle"])
        if "lsd" in query_lower or "gaucher" in query_lower or "enzyme" in query_lower:
            context.append(self.knowledge_base["lsd"])

        if not context:
            context.append(self.knowledge_base["general"])

        return "\n".join(context)
    def generate_response(self, query, context_data=None):
        """
        Generate response using LLM with rich medical context.
        Falls back to template response if LLM is unavailable.
        """
        # 1. Retrieve relevant medical knowledge
        knowledge_context = self.retrieve_context(query)

        # 2. Build context string from patient analysis results
        context_parts = [f"Medical Knowledge Reference:\n{knowledge_context}"]

        if context_data:
            analysis = context_data.get('analysis')
            page = context_data.get('page', '')

            if page:
                page_name = page.split('/')[-1].replace('_', ' ').title()
                context_parts.append(f"Current Page: {page_name}")

            if analysis:
                context_parts.append(f"Patient Analysis Results: {analysis}")

        context_str = "\n\n".join(context_parts)

        # 3. Call LLM for intelligent response
        response = llm_service.generate_response(query, context_str)

        return response


# Singleton
rag_bot = RAGSystem()
