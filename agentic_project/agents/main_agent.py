import os
import logging
import hashlib
import chromadb
from datetime import datetime
from typing import List, Dict, Any, Optional

from langchain_google_vertexai import ChatVertexAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tools.tool_manager import get_tools
from error_handling.handler import retry_with_exponential_backoff
from guardrails.safety import validate_input, validate_output

logger = logging.getLogger(__name__)

class ApigeeProxyTestingAgent:
    def __init__(self):
        self.llm = ChatVertexAI(
            model_name="gemini-2.5-flash",
            project=os.environ.get("GOOGLE_CLOUD_PROJECT", "gen-ai-poc-onboarding"),
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        )
        self.tools_map = {t.name: t for t in self._get_tools()}
        self.llm_with_tools = self.llm.bind_tools(list(self.tools_map.values()))
        
        # The system prompt for the Apigee Proxy Testing Agent
        self.system_prompt = """You are the Apigee Proxy Testing Agent, an expert AI designed to automate the comprehensive testing and validation of Apigee API proxies. Your core responsibilities include intelligently generating and executing test cases, covering functional correctness, performance benchmarks, and security vulnerabilities across various proxy configurations and policies. You must be capable of simulating diverse traffic patterns, analyzing response payloads, and identifying deviations from expected behavior or specified service level agreements (SLAs). Proactively identify issues, enhance API reliability, accelerate the development lifecycle, and ensure consistent quality and security of APIs managed within the Apigee platform. Always aim for thoroughness and accuracy in your testing and reporting.

Your primary inputs will include Apigee Proxy Bundles, Apigee Management APIs for direct interaction, API Specifications (like OpenAPI/Swagger) for defining expected behavior, specific test data (or you can generate synthetic data), and target environment details.

You will integrate with CI/CD pipelines for automated triggering, reporting dashboards for visualization, security scanning tools for vulnerability detection, and load testing tools for performance benchmarking.

When processing user messages, you will interpret the request, validate its scope, gather and validate necessary inputs, and then orchestrate the appropriate testing tools to achieve the user's objective. You will then generate comprehensive reports detailing test results, performance metrics, security findings, and recommendations.
"""
        self.chroma_client = self._init_chroma_client()
        self.rag_collection = self.chroma_client.get_or_create_collection('knowledge_base', metadata={'hnsw:space': 'cosine'})

    def _init_chroma_client(self):
        """Initializes ChromaDB client."""
        chroma_path = os.path.join(os.path.dirname(__file__), '..', 'chroma_db')
        os.makedirs(chroma_path, exist_ok=True)
        return chromadb.PersistentClient(path=os.path.abspath(chroma_path))

    def _get_tools(self):
        """Retrieves the list of tools available to the agent."""
        return get_tools()

    def _ingest_to_rag(self, query: str, mcp_result: str, tool_name: str = 'mcp_tool') -> None:
        """Ingest MCP-fetched data into ChromaDB for future RAG retrieval."""
        try:
            doc_id = 'mcp_' + hashlib.md5(f'{tool_name}:{query}'.encode()).hexdigest()[:16]
            chunk_id = f'{doc_id}_chunk_0'
            self.rag_collection.upsert(
                ids=[chunk_id],
                documents=[f'Tool: {tool_name}\nQuery: {query}\nResult: {mcp_result}'],
                metadatas=[{'doc_id': doc_id, 'title': f'MCP: {tool_name}', 'source': 'mcp_tool',
                             'chunk_index': 0, 'ingested_at': datetime.utcnow().isoformat()}],
            )
            logger.info(f"Ingested data from tool '{tool_name}' into RAG with doc_id: {doc_id}")
        except Exception as e:
            logger.warning(f'RAG ingestion failed: {e}')

    def _retrieve_from_rag(self, query: str, n_results: int = 3) -> List[str]:
        """Retrieves relevant context from ChromaDB based on the query."""
        try:
            # Note: ChromaDB's query method requires embeddings or a query_text.
            # For simplicity, we're using query_texts directly. In a real scenario,
            # you'd embed the query using an embedding model.
            results = self.rag_collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents']
            )
            if results and results['documents']:
                return [doc for sublist in results['documents'] for doc in sublist]
            return []
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return []

    @retry_with_exponential_backoff(max_retries=3, timeout=30, fallback_response="An error occurred. Please try again.")
    async def chat(self, message: str) -> str:
        """
        Processes a chat message, potentially using tools and RAG for context.
        """
        validated_message = validate_input(message)
        if validated_message.startswith("Error:"):
            return validated_message

        # Retrieve relevant context from RAG
        rag_context = self._retrieve_from_rag(validated_message)
        context_message = ""
        if rag_context:
            context_message = "\n\nRelevant context from knowledge base:\n" + "\n".join(rag_context)
            logger.info(f"Retrieved RAG context for query: {validated_message}")

        messages = [
            SystemMessage(content=self.system_prompt + context_message),
            HumanMessage(content=validated_message),
        ]

        final_response_content = "No response generated."

        # Agentic loop: keep calling LLM until no more tool calls or max iterations reached
        for _ in range(10):  # max iterations to prevent infinite loops
            try:
                response = self.llm_with_tools.invoke(messages)
            except Exception as e:
                logger.error(f"LLM invocation failed: {e}")
                return "I encountered an issue while processing your request. Please try again."

            messages.append(response)

            if not response.tool_calls:
                final_response_content = response.content if hasattr(response, "content") else str(response)
                break

            # Execute each tool call and feed results back
            for tc in response.tool_calls:
                fn = self.tools_map.get(tc["name"])
                if fn:
                    try:
                        logger.info(f"Calling tool: {tc['name']} with args: {tc['args']}")
                        tool_result = fn.invoke(tc["args"])
                        messages.append(ToolMessage(content=str(tool_result), tool_call_id=tc["id"]))
                        self._ingest_to_rag(validated_message, str(tool_result), tc["name"]) # Ingest tool results
                    except Exception as tool_e:
                        error_msg = f"Error executing tool {tc['name']}: {tool_e}"
                        logger.error(error_msg)
                        messages.append(ToolMessage(content=f"Error: {error_msg}", tool_call_id=tc["id"]))
                else:
                    error_msg = f"Unknown tool: {tc['name']}"
                    logger.warning(error_msg)
                    messages.append(ToolMessage(content=error_msg, tool_call_id=tc["id"]))
            
            # If the loop finishes without a break, it means the last response was a tool call
            # and we need to get the final LLM response after tool execution.
            # This is handled by the next iteration of the loop or the final assignment.
            if not response.tool_calls and hasattr(response, "content"):
                final_response_content = response.content
                break
            elif response.tool_calls and _ == 9: # If max iterations reached and still tool calls
                final_response_content = "I've reached my maximum processing steps and still have pending tasks. Please refine your request or try again."
                break

        return validate_output(final_response_content)

    async def run_task(self, input_data: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Runs a specific task for the agent, similar to chat but focused on task execution.
        """
        # For this agent, run_task can leverage the chat method for simplicity,
        # as the chat method is designed to handle complex requests involving tools.
        # In a more complex scenario, run_task might have a dedicated workflow.
        logger.info(f"Running task with input: {input_data}, context: {context}")
        # You might want to format the input_data and context into a more specific
        # message for the chat method if the task requires it.
        task_message = f"Execute the following task: {input_data}"
        if context:
            task_message += f"\nContext: {context}"
        return await self.chat(task_message)