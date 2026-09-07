# src/agents/negotiation_agent.py
from typing import Dict, Any, Optional, List
from src.agents.base_agent import BaseAgent
from src.models.state import NegotiationState, Message
from src.utils.groq_client import groq
from src.utils.price_loader import price_db
from src.utils.logfire_config import logfire_trace
import json
import re
from datetime import datetime

class NegotiationAgent(BaseAgent):

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("NegotiationAgent", config)
        self.conversation_history = []

    @logfire_trace(name="NegotiationAgent - Run")
    async def run(self, state: NegotiationState) -> NegotiationState:
        self.log("Generating negotiation response with memory")

        # Get the last user message
        user_message = None
        for msg in reversed(state.messages):
            if msg.role == "user":
                user_message = msg
                break

        if not user_message:
            self.log("No user message found", "warning")
            return state

        # Initialize conversation history in state if not exists
        if "conversation_history" not in state.agent_states:
            state.agent_states["conversation_history"] = []
        
        # Add user message to history
        state.agent_states["conversation_history"].append({
            "role": "user",
            "content": user_message.content,
            "timestamp": datetime.now().isoformat()
        })

        # Build full conversation context
        conversation_context = self._build_full_context(state.messages)
        
        # Detect intent with context
        intent = self._detect_intent_with_context(
            user_message.content, 
            state.agent_states.get("conversation_history", [])
        )
        
        self.log(f"Detected intent: {intent}")
        
        # Handle different intents
        if intent == "price_inquiry":
            response = await self._handle_price_inquiry_with_context(
                user_message.content, state, conversation_context
            )
        elif intent == "negotiation":
            response = await self._handle_negotiation_with_context(
                user_message.content, state, conversation_context
            )
        elif intent == "accept_deal":
            response = await self._handle_accept_deal(state)
        elif intent == "reject_deal":
            response = await self._handle_reject_deal(state)
        else:
            response = await self._handle_general_query_with_context(
                user_message.content, state, conversation_context
            )

        # Store assistant response
        state.agent_states["conversation_history"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })

        state.messages.append(Message(
            role="assistant",
            content=response,
            language="en"
        ))

        self.log(f"Response generated. Total messages: {len(state.messages)}")
        
        return state

    def _build_full_context(self, messages: List[Message]) -> str:
        """Build full conversation context"""
        context_parts = []
        for msg in messages[-15:]:  # Last 15 messages for context
            role = "User" if msg.role == "user" else "Assistant"
            context_parts.append(f"{role}: {msg.content}")
        return "\n".join(context_parts)

    def _detect_intent_with_context(self, message: str, history: List[Dict]) -> str:
        """Detect intent with conversation context"""
        msg_lower = message.lower()
        
        # Check for follow-up questions
        if history and len(history) > 1:
            # If user is asking about something mentioned before
            followup_words = ["this", "that", "it", "these", "those", "above", "previous"]
            if any(word in msg_lower for word in followup_words):
                return "followup"
        
        if any(word in msg_lower for word in ["price", "cost", "rate", "quote", "estimate", "how much", "what is the"]):
            return "price_inquiry"
        elif any(word in msg_lower for word in ["negotiate", "discount", "offer", "deal", "best price", "reduce", "cheaper"]):
            return "negotiation"
        elif any(word in msg_lower for word in ["accept", "agree", "deal done", "book", "confirm", "yes"]):
            return "accept_deal"
        elif any(word in msg_lower for word in ["reject", "no", "not interested", "too high", "cancel"]):
            return "reject_deal"
        elif any(word in msg_lower for word in ["flat", "house", "land", "construction", "project", "option", "suggest"]):
            return "property_inquiry"
        else:
            return "general"

    async def _handle_price_inquiry_with_context(self, message: str, state: NegotiationState, context: str) -> str:
        """Handle price inquiry with full context"""
        
        # Extract previous mentions from context
        previous_mentions = self._extract_previous_mentions(state.agent_states.get("conversation_history", []))
        
        prompt = f"""
        You are Actiboost AI, a professional construction and real estate negotiation assistant.
        
        PREVIOUS CONVERSATION:
        {context}
        
        PREVIOUSLY MENTIONED:
        {previous_mentions}
        
        CURRENT USER MESSAGE:
        {message}
        
        IMPORTANT RULES:
        1. Use the previous conversation to understand what the user is asking about
        2. If they asked about a specific location (like Hinjewadi), refer to that location
        3. If they mentioned a budget, acknowledge it
        4. Don't repeat information you already shared
        5. Be conversational and helpful
        6. If the user is following up, acknowledge what you discussed before
        
        Respond naturally as a helpful AI assistant.
        """
        
        response = await groq.ask(prompt)
        return response

    async def _handle_negotiation_with_context(self, message: str, state: NegotiationState, context: str) -> str:
        """Handle negotiation with context awareness"""
        
        history = state.agent_states.get("conversation_history", [])
        previous_mentions = self._extract_previous_mentions(history)
        
        prompt = f"""
        You are Actiboost AI, a professional construction and real estate negotiation assistant.
        
        PREVIOUS CONVERSATION:
        {context}
        
        PREVIOUSLY MENTIONED:
        {previous_mentions}
        
        CURRENT USER MESSAGE:
        {message}
        
        IMPORTANT RULES:
        1. Use the previous conversation to understand the context
        2. Remember what property the user is interested in
        3. Remember any budget mentioned
        4. Handle the negotiation professionally
        5. If the user is asking for a discount, check if reasonable
        
        Negotiation Guidelines:
        - If user offers below 10% discount: Accept and move to confirmation
        - If user offers above 10% discount: Politely explain minimum price
        - If user is uncertain: Offer alternatives
        
        Be conversational and remember everything discussed before.
        """
        
        response = await groq.ask(prompt)
        return response

    async def _handle_general_query_with_context(self, message: str, state: NegotiationState, context: str) -> str:
        """Handle general queries with context"""
        
        previous_mentions = self._extract_previous_mentions(state.agent_states.get("conversation_history", []))
        
        prompt = f"""
        You are Actiboost AI, a professional construction and real estate negotiation assistant.
        
        PREVIOUS CONVERSATION:
        {context}
        
        PREVIOUSLY MENTIONED:
        {previous_mentions}
        
        CURRENT USER MESSAGE:
        {message}
        
        IMPORTANT RULES:
        1. Use the previous conversation to understand the context
        2. If the user is following up, acknowledge what was discussed
        3. If they asked about properties earlier, refer back to those options
        4. Be helpful and conversational
        5. Remember what was said before
        
        Respond naturally as a helpful AI assistant.
        """
        
        response = await groq.ask(prompt)
        return response

    async def _handle_accept_deal(self, state: NegotiationState) -> str:
        """Handle deal acceptance"""
        history = state.agent_states.get("conversation_history", [])
        
        # Extract property details from history
        property_info = self._extract_property_from_history(history)
        
        return f"""
✅ **Great! You've accepted the deal!**

📋 **Deal Details from our conversation:**
- Property: {property_info.get('type', 'Property')}
- Location: {property_info.get('location', 'Specified location')}
- Price: As discussed in our negotiation

🔄 **Next Steps:**
1. Deal will be sent for manager approval
2. You'll receive a confirmation email
3. Booking process will begin

The deal is now being processed. Thank you for choosing Actiboost! 🏗️
"""

    async def _handle_reject_deal(self, state: NegotiationState) -> str:
        """Handle deal rejection"""
        return """
I understand. Let me know if you change your mind or if you'd like to explore other options.

🏗️ **Other Options:**
- Different location
- Different size
- Other property types

Feel free to ask for more details anytime! 😊
"""

    def _extract_previous_mentions(self, history: List[Dict]) -> str:
        """Extract key information from previous conversation"""
        mentions = []
        for msg in history[-8:]:  # Last 8 messages
            content = msg.get("content", "")
            if "location" in content.lower() or "area" in content.lower():
                mentions.append(f"Location mentioned: {content}")
            if "budget" in content.lower() or "price" in content.lower():
                mentions.append(f"Budget mentioned: {content}")
            if "bhk" in content.lower() or "flat" in content.lower():
                mentions.append(f"Property mentioned: {content}")
        return "\n".join(mentions) if mentions else "No previous mentions"

    def _extract_property_from_history(self, history: List[Dict]) -> Dict[str, str]:
        """Extract property details from history"""
        property_info = {"type": "Unknown", "location": "Unknown"}
        for msg in history:
            content = msg.get("content", "")
            if "bhk" in content.lower() or "flat" in content.lower():
                property_info["type"] = content[:100]
            if "hinjewadi" in content.lower() or "pune" in content.lower():
                property_info["location"] = content[:100]
        return property_info

    def _extract_location(self, text: str) -> Optional[str]:
        locations = ["Hinjawadi", "Baner", "Koregaon Park", "Pune", "Mumbai"]
        for loc in locations:
            if loc.lower() in text.lower():
                return loc
        return None

    def _extract_property_type(self, text: str) -> Optional[str]:
        if "2bhk" in text.lower() or "2 bhk" in text.lower():
            return "2BHK"
        elif "3bhk" in text.lower() or "3 bhk" in text.lower():
            return "3BHK"
        elif "1bhk" in text.lower() or "1 bhk" in text.lower():
            return "1BHK"
        return None

    def _extract_size(self, text: str) -> Optional[float]:
        match = re.search(r'(\d+)\s*(?:sq|sqft|sq ft)', text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return None

    def _extract_price(self, text: str) -> Optional[float]:
        match = re.search(r'(\d+\.?\d*)\s*(?:lakh|lac|lakhs)', text, re.IGNORECASE)
        if match:
            return float(match.group(1)) * 100000
        match = re.search(r'(\d+\.?\d*)\s*(?:crore|crores)', text, re.IGNORECASE)
        if match:
            return float(match.group(1)) * 10000000
        match = re.search(r'(\d{5,})', text)
        if match:
            return float(match.group(1))
        return None