"""Multilingual translations for Streamlit UI."""

TRANSLATIONS = {
    "en": {
        # App title
        "app_title": "Cambodia Agricultural Intelligence",
        "app_subtitle": "Semantic Search & AI Q&A for Cashew and Rubber Markets",

        # Navigation
        "nav_search": "Search Documents",
        "nav_chat": "AI Q&A",
        "nav_history": "History",
        "nav_admin": "Admin Dashboard",

        # Search page
        "search_title": "Semantic Search",
        "search_placeholder": "Search in any language (Khmer, English, Vietnamese)...",
        "search_button": "Search",
        "search_results": "Search Results",
        "search_no_results": "No results found",
        "search_similarity": "Similarity",
        "search_source": "Source",
        "search_commodity": "Commodity",

        # Filters
        "filter_commodity": "Filter by Commodity",
        "filter_source": "Filter by Source",
        "filter_all": "All",
        "filter_cashew": "Cashew",
        "filter_rubber": "Rubber",

        # Chat page
        "chat_title": "AI Q&A Assistant",
        "chat_placeholder": "Ask a question about cashew or rubber...",
        "chat_button": "Get AI Answer",
        "chat_context": "Context Retrieved",
        "chat_answer": "AI Answer",
        "chat_citations": "Citations",
        "chat_cost": "Cost",

        # History page
        "history_title": "Conversation History",
        "history_session": "Session",
        "history_query": "Query",
        "history_type": "Type",
        "history_time": "Time",
        "history_no_data": "No history yet",

        # Admin page
        "admin_title": "Admin Dashboard",
        "admin_stats": "Usage Statistics",
        "admin_budget": "Budget Tracking",
        "admin_cache": "Cache Performance",
        "admin_total_queries": "Total Queries",
        "admin_rag_queries": "RAG Queries",
        "admin_search_queries": "Search Queries",
        "admin_cost": "Total Cost",
        "admin_remaining": "Budget Remaining",
        "admin_utilization": "Budget Utilization",

        # Scenario Analysis page
        "scenario_title": "Multi-Perspective Analysis",
        "scenario_subtitle": "3 scenarios based on market prices, historical documents, and Twitter/X news",
        "scenario_pessimistic": "📉 Pessimistic Analysis",
        "scenario_realistic": "⚖️ Realistic Analysis",
        "scenario_optimistic": "📈 Optimistic Analysis",
        "scenario_based_on": "Based on",
        "scenario_market_data": "Market data",
        "scenario_historical_docs": "Historical documents",
        "scenario_twitter_news": "Twitter/X news",
        "scenario_key_tweet": "Key Tweet",
        "scenario_analysis": "Analysis",
        "scenario_price_outlook": "Price Outlook",
        "scenario_risk_factors": "Risk Factors",
        "scenario_opportunities": "Opportunities",
        "scenario_generating": "Generating analysis...",
        "scenario_refresh": "Refresh Analysis",
        "scenario_data_sources": "Data Sources",
        "scenario_price_trend": "Price Trend",
        "scenario_doc_count": "documents analyzed",
        "scenario_tweet_count": "recent tweets",
        "scenario_confidence": "Confidence Level",
        "scenario_timeframe": "Time Horizon",
        "scenario_short_term": "Short term (1-3 months)",
        "scenario_medium_term": "Medium term (3-6 months)",
        "scenario_long_term": "Long term (6-12 months)",
        "macro_indicators": "Macro Indicators",
        "macro_exchange_rate": "USD/KHR Exchange Rate",
        "macro_csx_summary": "CSX Summary",
        "macro_csx_index": "CSX Index",
        "macro_up": "Up",
        "macro_down": "Down",
        "macro_flat": "Flat",
        "macro_volume": "Volume",
        "macro_value": "Value",

        # Market Trends
        "trends_overall_trend": "Overall Trend",
        "trends_twitter_sentiment": "Twitter Sentiment",
        "trends_tweet_volume": "Tweet Volume (30d)",
        "trends_sentiment_not_enough": "Not enough data",
        "trends_sentiment_score": "Score",
        "trend_strong_bullish": "Strong Bullish",
        "trend_bullish": "Bullish",
        "trend_slightly_bullish": "Slightly Bullish",
        "trend_neutral": "Neutral",
        "trend_slightly_bearish": "Slightly Bearish",
        "trend_bearish": "Bearish",
        "trend_strong_bearish": "Strong Bearish",

        # Common
        "loading": "Loading...",
        "error": "Error",
        "success": "Success",
        "export": "Export",
        "clear": "Clear",
        "settings": "Settings",
    },

    "km": {  # Khmer
        # App title
        "app_title": "វេទិកាព័ត៌មានកសិកម្មកម្ពុជា",
        "app_subtitle": "ស្វែងរកឯកសារនិងសួរចម្លើយជាមួយ AI សម្រាប់ទីផ្សារស្វាយចន្ទី និងកៅស៊ូ",

        # Navigation
        "nav_search": "ស្វែងរកឯកសារ",
        "nav_chat": "សួរចម្លើយ AI",
        "nav_history": "ប្រវត្តិ",
        "nav_admin": "ផ្ទាំងគ្រប់គ្រង",

        # Search page
        "search_title": "ស្វែងរកឯកសារ",
        "search_placeholder": "ស្វែងរកជាភាសាណាមួយ (ខ្មែរ, អង់គ្លេស, វៀតណាម)...",
        "search_button": "ស្វែងរក",
        "search_results": "លទ្ធផលស្វែងរក",
        "search_no_results": "រកមិនឃើញ",
        "search_similarity": "ភាពស្រដៀងគ្នា",
        "search_source": "ប្រភព",
        "search_commodity": "ទំនិញ",

        # Filters
        "filter_commodity": "ច្រោះតាមទំនិញ",
        "filter_source": "ច្រោះតាមប្រភព",
        "filter_all": "ទាំងអស់",
        "filter_cashew": "ស្វាយចន្ទី",
        "filter_rubber": "កៅស៊ូ",

        # Chat page
        "chat_title": "ជំនួយការសួរចម្លើយ AI",
        "chat_placeholder": "សួរសំណួរអំពីស្វាយចន្ទី ឬ កៅស៊ូ...",
        "chat_button": "សួរ AI",
        "chat_context": "បរិបទដែលបានស្វែងរក",
        "chat_answer": "ចម្លើយ AI",
        "chat_citations": "ឯកសារយោង",
        "chat_cost": "តម្លៃ",

        # History page
        "history_title": "ប្រវត្តិសន្ទនា",
        "history_session": "វគ្គ",
        "history_query": "សំណួរ",
        "history_type": "ប្រភេទ",
        "history_time": "ពេលវេលា",
        "history_no_data": "មិនទាន់មានប្រវត្តិ",

        # Admin page
        "admin_title": "ផ្ទាំងគ្រប់គ្រង",
        "admin_stats": "ស្ថិតិការប្រើប្រាស់",
        "admin_budget": "តាមដានថវិកា",
        "admin_cache": "ការអនុវត្ត Cache",
        "admin_total_queries": "សំណួរសរុប",
        "admin_rag_queries": "សំណួរ RAG",
        "admin_search_queries": "សំណួរស្វែងរក",
        "admin_cost": "តម្លៃសរុប",
        "admin_remaining": "ថវិកានៅសល់",
        "admin_utilization": "ការប្រើប្រាស់ថវិកា",

        # Common
        "loading": "កំពុងផ្ទុក...",
        "error": "កំហុស",
        "success": "ជោគជ័យ",
        "export": "នាំចេញ",
        "clear": "សម្អាត",
        "settings": "ការកំណត់",
    },

    "vi": {  # Vietnamese
        # App title
        "app_title": "Nền tảng Thông tin Nông nghiệp Campuchia",
        "app_subtitle": "Tìm kiếm ngữ nghĩa & Hỏi đáp AI cho thị trường điều và cao su",

        # Navigation
        "nav_search": "Tìm kiếm Tài liệu",
        "nav_chat": "Hỏi đáp AI",
        "nav_history": "Lịch sử",
        "nav_admin": "Bảng điều khiển",

        # Search page
        "search_title": "Tìm kiếm Ngữ nghĩa",
        "search_placeholder": "Tìm kiếm bằng bất kỳ ngôn ngữ nào (Khmer, Tiếng Anh, Tiếng Việt)...",
        "search_button": "Tìm kiếm",
        "search_results": "Kết quả Tìm kiếm",
        "search_no_results": "Không tìm thấy kết quả",
        "search_similarity": "Độ tương đồng",
        "search_source": "Nguồn",
        "search_commodity": "Hàng hóa",

        # Filters
        "filter_commodity": "Lọc theo Hàng hóa",
        "filter_source": "Lọc theo Nguồn",
        "filter_all": "Tất cả",
        "filter_cashew": "Điều",
        "filter_rubber": "Cao su",

        # Chat page
        "chat_title": "Trợ lý Hỏi đáp AI",
        "chat_placeholder": "Đặt câu hỏi về điều hoặc cao su...",
        "chat_button": "Hỏi AI",
        "chat_context": "Ngữ cảnh đã tìm kiếm",
        "chat_answer": "Câu trả lời AI",
        "chat_citations": "Trích dẫn",
        "chat_cost": "Chi phí",

        # History page
        "history_title": "Lịch sử Hội thoại",
        "history_session": "Phiên",
        "history_query": "Truy vấn",
        "history_type": "Loại",
        "history_time": "Thời gian",
        "history_no_data": "Chưa có lịch sử",

        # Admin page
        "admin_title": "Bảng điều khiển Quản trị",
        "admin_stats": "Thống kê Sử dụng",
        "admin_budget": "Theo dõi Ngân sách",
        "admin_cache": "Hiệu suất Cache",
        "admin_total_queries": "Tổng số Truy vấn",
        "admin_rag_queries": "Truy vấn RAG",
        "admin_search_queries": "Truy vấn Tìm kiếm",
        "admin_cost": "Tổng Chi phí",
        "admin_remaining": "Ngân sách Còn lại",
        "admin_utilization": "Sử dụng Ngân sách",

        # Common
        "loading": "Đang tải...",
        "error": "Lỗi",
        "success": "Thành công",
        "export": "Xuất",
        "clear": "Xóa",
        "settings": "Cài đặt",
    },

    "fr": {  # French
        # App title
        "app_title": "Intelligence Agricole du Cambodge",
        "app_subtitle": "Recherche sémantique & Q&R IA pour les marchés de cajou et caoutchouc",

        # Navigation
        "nav_search": "Rechercher Documents",
        "nav_chat": "Q&R IA",
        "nav_history": "Historique",
        "nav_admin": "Tableau de bord",

        # Search page
        "search_title": "Recherche Sémantique",
        "search_placeholder": "Rechercher en toute langue (Khmer, Anglais, Français, Vietnamien)...",
        "search_button": "Rechercher",
        "search_results": "Résultats de Recherche",
        "search_no_results": "Aucun résultat trouvé",
        "search_similarity": "Similarité",
        "search_source": "Source",
        "search_commodity": "Matière première",

        # Filters
        "filter_commodity": "Sélectionner matière première",
        "filter_source": "Filtrer par source",
        "filter_all": "Toutes",
        "filter_cashew": "Cajou",
        "filter_rubber": "Caoutchouc",

        # Chat page
        "chat_title": "Assistant Q&R IA",
        "chat_placeholder": "Posez une question sur le cajou ou le caoutchouc...",
        "chat_button": "Obtenir une réponse IA",
        "chat_context": "Contexte récupéré",
        "chat_answer": "Réponse IA",
        "chat_citations": "Citations",
        "chat_cost": "Coût",

        # History page
        "history_title": "Historique des Conversations",
        "history_session": "Session",
        "history_query": "Requête",
        "history_type": "Type",
        "history_time": "Heure",
        "history_no_data": "Aucun historique pour le moment",
        "history_days": "Historique (jours)",

        # Admin page
        "admin_title": "Tableau de bord Administration",
        "admin_stats": "Statistiques d'utilisation",
        "admin_budget": "Suivi du budget",
        "admin_cache": "Performance du cache",
        "admin_total_queries": "Total des requêtes",
        "admin_rag_queries": "Requêtes RAG",
        "admin_search_queries": "Requêtes de recherche",
        "admin_cost": "Coût total",
        "admin_remaining": "Budget restant",
        "admin_utilization": "Utilisation du budget",

        # Market Trends page
        "trends_title": "Analyse des Tendances du Marché",
        "trends_subtitle": "Sentiment Twitter/X + Données boursières • Mise à jour quotidienne",
        "trends_latest_analysis": "Dernière Analyse",
        "trends_updated": "Mise à jour",
        "trends_overall_trend": "Tendance Globale",
        "trends_twitter_sentiment": "Sentiment Twitter",
        "trends_price_change": "Variation Prix",
        "trends_confidence": "Confiance",
        "trends_twitter_analysis": "Analyse Twitter/X",
        "trends_stock_market": "Marché Boursier",
        "trends_tweet_volume": "Volume Tweets (30j)",
        "trends_sentiment_not_enough": "Données insuffisantes",
        "trends_summary": "Résumé",
        "trends_top_tweets": "Top Tweets",
        "trends_price": "Prix",
        "trends_24h_change": "Variation 24h",
        "trends_volume": "Volume",
        "trends_key_factors": "Facteurs Clés",
        "trends_ai_analysis": "Analyse IA Complète",
        "trends_sources": "Sources & Citations",
        "trends_no_data": "Aucune donnée de tendance trouvée pour",
        "trends_historical": "Tendances Historiques",
        "trends_sentiment_chart": "Tendance du Sentiment",
        "trends_price_chart": "Tendance Variation Prix",
        "trends_actual_price_chart": "Tendance Prix Réel (USD/tonne)",
        "trends_confidence_chart": "Score de Confiance",
        "trends_raw_data": "Données Brutes",
        "trends_alerts": "Alertes Actives",
        "trends_no_alerts": "Aucune alerte active",
        "trends_no_price_data": "Aucune donnée de prix disponible pour la période sélectionnée",
        "trends_current_price": "Prix Actuel",
        "trends_avg_price": "Prix Moyen",
        "trends_highest": "Plus Haut",
        "trends_lowest": "Plus Bas",
        "trends_public_data": "Données Publiques de Prix",
        "trends_source": "Source",

        # Trend values
        "trend_strong_bullish": "Très Haussier",
        "trend_bullish": "Haussier",
        "trend_slightly_bullish": "Légèrement Haussier",
        "trend_neutral": "Neutre",
        "trend_slightly_bearish": "Légèrement Baissier",
        "trend_bearish": "Baissier",
        "trend_strong_bearish": "Très Baissier",

        # Scenario Analysis page
        "scenario_title": "Analyses Multi-Perspectives",
        "scenario_subtitle": "3 scénarios basés sur les prix du marché, documents historiques et actualités Twitter/X",
        "scenario_pessimistic": "📉 Analyse Dépréciative",
        "scenario_realistic": "⚖️ Analyse Réaliste",
        "scenario_optimistic": "📈 Analyse Positive",
        "scenario_based_on": "Basée sur",
        "scenario_market_data": "Données du marché",
        "scenario_historical_docs": "Documents historiques",
        "scenario_twitter_news": "Actualités Twitter/X",
        "scenario_key_tweet": "Tweet Clé",
        "scenario_analysis": "Analyse",
        "scenario_price_outlook": "Perspective Prix",
        "scenario_risk_factors": "Facteurs de Risque",
        "scenario_opportunities": "Opportunités",
        "scenario_generating": "Génération de l'analyse...",
        "scenario_refresh": "Rafraîchir l'analyse",
        "scenario_data_sources": "Sources de Données",
        "scenario_price_trend": "Tendance Prix",
        "scenario_doc_count": "documents analysés",
        "scenario_tweet_count": "tweets récents",
        "scenario_confidence": "Niveau de Confiance",
        "scenario_timeframe": "Horizon Temporel",
        "scenario_short_term": "Court terme (1-3 mois)",
        "scenario_medium_term": "Moyen terme (3-6 mois)",
        "scenario_long_term": "Long terme (6-12 mois)",
        "macro_indicators": "Indicateurs macro",
        "macro_exchange_rate": "Taux USD/KHR",
        "macro_csx_summary": "Resume CSX",
        "macro_csx_index": "Indice CSX",
        "macro_up": "Hausse",
        "macro_down": "Baisse",
        "macro_flat": "Stable",
        "macro_volume": "Volume",
        "macro_value": "Valeur",

        # Common
        "loading": "Chargement...",
        "error": "Erreur",
        "success": "Succès",
        "export": "Exporter",
        "clear": "Effacer",
        "settings": "Paramètres",
        "date": "Date",
        "tweets": "tweets",
    }
}


def get_translation(key: str, language: str = "en") -> str:
    """
    Get translation for a key in a specific language.

    Args:
        key: Translation key
        language: Language code (en, km, vi, fr)

    Returns:
        Translated string, or key if not found
    """
    if language not in TRANSLATIONS:
        language = "en"

    return TRANSLATIONS[language].get(key, key)


def get_all_translations(language: str = "en") -> dict:
    """
    Get all translations for a language.

    Args:
        language: Language code (en, km, vi, fr)

    Returns:
        Dictionary of all translations
    """
    if language not in TRANSLATIONS:
        language = "en"

    return TRANSLATIONS[language]
