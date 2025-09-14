import gradio as gr
from flight_agent import FlightAgent

class FlightChatInterface:
    def __init__(self):
        self.flight_agent = FlightAgent()
    
    def chat_response(self, message, history):
        """Handle chat messages and return flight information"""
        try:
            # Use the flight agent's complete search workflow
            # This handles parsing, searching, and formatting internally
            return self.flight_agent.search_flights(message)
            
        except Exception as e:
            return f"Error searching for flights: {str(e)}. Please try again."

def create_interface():
    """Create and return the Gradio interface"""
    chat_interface = FlightChatInterface()
    
    # Create the Gradio interface
    demo = gr.ChatInterface(
        fn=chat_interface.chat_response,
        title="Flight Search Assistant",
        description="Search for flights by providing origin, destination, and date.",
        examples=[
            "I want to fly from New York to Los Angeles on 2024-01-15",
            "Search flights from London to Paris for 2024-02-20",
            "Find flights from Tokyo to Seoul on 2024-03-10"
        ],
        cache_examples=False
    )
    
    return demo
