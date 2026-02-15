import google.generativeai as genai
import os

# Configure API Key (User should provide this in env or we can hardcode for hackathon demo if safe)
# For now, we'll try to read from env or expect it to be set

class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-flash-latest')
        else:
            self.model = None
            print("Warning: GEMINI_API_KEY not set. Gemini features will be mocked.")

    async def chat_with_market_analyst(self, user_message: str, market_context: dict) -> str:
        """
        Sends a message to Gemini with market context to get specialized advice.
        """
        if not self.model:
            return "I am unable to connect to the Gemini Market Brain right now (API Key missing). But based on simple logic: prices are likely to rise!"

        # Construct a rich prompt
        system_instruction = (
            "You are an expert Market Analyst for a university study room marketplace. "
            "Your goal is to help students save tokens and find the best study spots. "
            "You have access to real-time market data.\n\n"
            f"MARKET CONTEXT:\n"
            f"- Current Simulation Time: {market_context.get('sim_time')}\n"
            f"- Average Room Price: {market_context.get('avg_price')} tokens\n"
            f"- Busy Hours: {market_context.get('busy_hours')}\n"
            f"- Recent Trend: {market_context.get('trend')}\n\n"
            "Keep your responses concise, helpful, and friendly. Use emojis occasionally."
        )

        prompt = f"{system_instruction}\n\nUser: {user_message}\nAnalyst:"

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return "I'm having trouble analyzing the market signals right now. Please try again later."

    async def generate_admin_market_report(self, market_data: dict) -> str:
        """
        Generates a high-level strategic report for the Admin Dashboard.
        """
        if not self.model:
            return "## Market Analysis Unavailable\n\nPlease configure the `GEMINI_API_KEY` to enable AI insights."

        system_instruction = (
            "You are a Senior Market Consultant for a university study space exchange. "
            "Write a strategic report for the System Administrator based on the provided data. "
            "Identify anomalies, suggest pricing strategy adjustments, and highlight high-demand periods. "
            "Format the output in clear Markdown with headers and bullet points."
        )
        
        prompt = (
            f"{system_instruction}\n\n"
            f"**Current System State:**\n"
            f"- Date: {market_data.get('date')}\n"
            f"- Total Active Orders: {market_data.get('total_orders')}\n"
            f"- Average Clearing Price: {market_data.get('avg_price')} tokens\n"
            f"- Revenue (Last 24h): {market_data.get('revenue_24h')} tokens\n"
            f"- Most Popular Time: {market_data.get('popular_time')}\n"
            f"- Underutilized Time: {market_data.get('quiet_time')}\n\n"
            "**Report:**"
        )

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            return f"Error generating report: {str(e)}"

gemini_client = GeminiClient()
