import os
from tavily import TavilyClient
from dotenv import load_dotenv
from parsing_agent import ParsingAgent

load_dotenv()

class FlightAgent:
    def __init__(self):
        self.tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
        self.parsing_agent = ParsingAgent()

    def search_flights(self, user_message):
        """
        Complete flight search workflow:
        1. Parse user message using parsing agent
        2. Search for flights using Tavily
        3. Return formatted results
        """
        try:
            # Step 1: Parse user message to extract flight details
            origin, destination, date, is_valid = self.parsing_agent.parse_flight_request(user_message)
            
            if not is_valid:
                return self._format_error_response(origin, destination, date)
            
            # Step 2: Search for flights using Tavily
            flight_results = self._search_flight_data(origin, destination, date)
            
            # Step 3: Format and return results
            return self._format_flight_results(origin, destination, date, flight_results)
            
        except Exception as e:
            return f"Error processing flight search: {str(e)}. Please try again."

    def _search_flight_data(self, origin, destination, date):
        """
        Search for flight data using Tavily with multiple queries
        """
        queries = [
            f"cheapest flights from {origin} to {destination} on {date}",
            f"best deals flights {origin} to {destination} {date}",
            f"flight prices {origin} {destination} {date} airlines",
            f"flight booking {origin} to {destination} {date} comparison"
        ]
        
        all_results = []
        
        for query in queries:
            try:
                response = self.tavily_client.search(
                    query=query,
                    search_depth="basic",
                    max_results=3
                )
                all_results.extend(response.get('results', []))
            except Exception as e:
                print(f"Error searching with query '{query}': {e}")
                continue
        
        return all_results

    def _format_flight_results(self, origin, destination, date, results):
        """
        Format flight search results for display
        """
        if not results:
            return f"No flight information found for {origin} to {destination} on {date}."
        
        formatted_response = f"Flight Search Results\n"
        formatted_response += f"{'='*50}\n"
        formatted_response += f"Route: {origin} → {destination}\n"
        formatted_response += f"Date: {date}\n"
        formatted_response += f"{'='*50}\n\n"
        
        # Process and format results
        seen_urls = set()
        for i, result in enumerate(results[:5], 1):  # Limit to top 5 results
            title = result.get('title', 'No title')
            content = result.get('content', 'No content')
            url = result.get('url', '')
            
            # Avoid duplicate results
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            formatted_response += f"{i}. {title}\n"
            formatted_response += f"   {content[:200]}{'...' if len(content) > 200 else ''}\n"
            if url:
                formatted_response += f"   Source: {url}\n"
            formatted_response += "\n"
        
        return formatted_response

    def _format_error_response(self, origin, destination, date):
        """
        Format error response based on missing information
        """
        if not origin and not destination:
            return "Please provide both origin and destination cities. Example: 'I want to fly from New York to Los Angeles on 2024-01-15'"
        elif not origin:
            return "Please provide the origin city. Example: 'I want to fly from New York to Los Angeles on 2024-01-15'"
        elif not destination:
            return "Please provide the destination city. Example: 'I want to fly from New York to Los Angeles on 2024-01-15'"
        elif not date:
            return "Please provide a date in YYYY-MM-DD format. Example: 'I want to fly from New York to Los Angeles on 2024-01-15'"
        else:
            return "Please provide complete flight information including origin, destination, and date."

    def get_flight_info(self, origin, destination, date):
        """
        Legacy method for backward compatibility
        """
        user_message = f"I want to fly from {origin} to {destination} on {date}"
        return self.search_flights(user_message)