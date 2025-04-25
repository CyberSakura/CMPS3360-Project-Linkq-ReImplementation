import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import { IconSettings, IconAlertTriangle } from '@tabler/icons-react';
import config from './config';
import QueryEditorUI from './components/QueryEditorUI';
import EntityRelationTable from './components/EntityRelationTable';
import ResultsPanel from './components/ResultsPanel';
import QueryGraph from './components/QueryGraph';
import SettingsModal from './components/SettingsModal';

const App = () => {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [queryResults, setQueryResults] = useState(null);
  const [queryError, setQueryError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [showWarning, setShowWarning] = useState(true);
  const DEMO_QUERY = `SELECT ?founder ?founderLabel ?birthdate
      WHERE {
        wd:Q95 wdt:P112 ?founder.
        ?founder wdt:P569 ?birthdate.
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
      }`;
  const IS_DEMO_MODE = true;
  const [queryEditorValue, setQueryEditorValue] = useState(IS_DEMO_MODE ? DEMO_QUERY : "");
  const queryEditorRef = useRef(null);

  useEffect(() => {
    const fetchChatHistory = async () => {
      try {
        const response = await fetch(`${config.API_BASE_URL}/chat-history`);
        const data = await response.json();
        // Don't set any history on initial load
        setChatHistory([]);
      } catch (error) {
        console.error("Error fetching chat history:", error);
      }
    };

    fetchChatHistory();
  }, []);

  const sendMessage = async (customMessage = null) => {
    const finalMessage = customMessage || message.trim();
    if (!finalMessage) return;

    console.log("Sending message:", finalMessage);

    try {
      const response = await fetch(`${config.API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: finalMessage }),
      });

      console.log("Response received:", response.status);
      const data = await response.json();
      console.log("Response data:", data);

      if (!data.reply) {
        console.error("Error: No reply found in API response", data);
        return;
      }

      const newMessage = {
        user: finalMessage,
        bot: data.reply,
        chatId: chatHistory.length,
        isUserMessage: true
      };

      setChatHistory((prevChat) => [...prevChat, newMessage]);
      setMessage("");

    } catch (error) {
      console.error("Error sending message:", error);
    }
  };

  const extractEntitiesFromResponse = (reply) => {
    try {
      const match = reply.match(/\[(.*?)\]/);
      if (!match) return [];
      return JSON.parse(`[${match[1]}]`);
    } catch (error) {
      console.error("Error parsing entities:", error);
      return [];
    }
  };

  function extractSparqlQuery(replyText) {
    if (!replyText || typeof replyText !== 'string') {
      return '';
    }
    const regex = /```sparql\s*([\s\S]*?)\s*```/i;
    const match = replyText.match(regex);
    return match ? match[1].trim() : '';
  }

  const runQuery = async (query) => {
    try {
      setIsLoading(true);
      setQueryResults(null); // clear old results
      // If query is undefined or null, use queryEditorValue
      const queryToRun = query || queryEditorValue;
      const cleanedQuery = queryToRun.trim();
      
      if (!cleanedQuery) {
        throw new Error('Please enter a query');
      }

      const response = await fetch(`${config.API_BASE_URL}/run_query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: cleanedQuery }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to execute query');
      }

      const data = await response.json();
      
      // Add query to history via QueryEditorUI ref
      if (queryEditorRef.current) {
        queryEditorRef.current.addToHistory(cleanedQuery);
      }

      // Set query results for the EntityRelationTable
      setQueryResults(data.result);
      setQueryError(null);

      // Update chat with results
      const newMessage = {
        type: 'system',
        user: 'system',
        bot: JSON.stringify(data.result, null, 2),
        isUserMessage: false
      };

      setChatHistory(prev => [...prev, newMessage]);
    } catch (error) {
      setQueryError(error.message);
      const errorMessage = {
        type: 'system',
        user: 'system',
        bot: `Error: ${error.message}`,
        isUserMessage: false
      };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to format query results
  const formatQueryResult = (result) => {
    if (!result || !result.results || !result.results.bindings) {
      return "No results found";
    }

    const bindings = result.results.bindings;
    if (bindings.length === 0) {
      return "No results found";
    }

    // Get the variables from the head
    const variables = result.head.vars;
    
    // Create a table-like format
    let formattedResult = "Results:\n\n";
    
    // Add headers
    formattedResult += variables.join(" | ") + "\n";
    formattedResult += "-".repeat(variables.join(" | ").length) + "\n";
    
    // Add rows
    bindings.forEach(binding => {
      const row = variables.map(varName => {
        const value = binding[varName];
        return value ? value.value : "";
      }).join(" | ");
      formattedResult += row + "\n";
    });
    
    return formattedResult;
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevent default behavior (new line)
      sendMessage();
    }
  };

  const handleQueryKeyPress = (e) => {
    if (e.key === 'Enter' && e.ctrlKey) { // Ctrl+Enter or Cmd+Enter
      e.preventDefault();
      runQuery(queryEditorValue);
    }
  };

  const handleCopyQuery = (query) => {
    setQueryEditorValue(query);
    // No need to call handleQueryPaste since we're directly setting the value
  };

  return (
    <div className="h-screen w-screen flex">
      {/* Left Chat Panel */}
      <div className="w-1/3 h-full bg-gray-900 text-white p-4 flex flex-col border-r border-white">
        <div className="flex items-center mb-4 w-full">
          <button
            className="px-3 py-2 bg-yellow-500 hover:bg-yellow-600 text-black rounded-lg text-sm font-semibold flex items-center gap-1 shadow-md transition-colors"
            onClick={() => setSettingsOpen(true)}
          >
            <IconSettings size={18} />
            Settings
          </button>

          {/* Warning icon with tooltip */}
          <div className="ml-auto relative group">
            <IconAlertTriangle size={20} className="text-yellow-300 cursor-pointer" />
            <span className="absolute left-1/2 -translate-x-1/2 mt-2 tooltip bg-gray-800 text-white text-xs rounded py-1 px-2 whitespace-nowrap shadow-lg z-10">
              This result is generated by an LLM and may contain mistakes. Please verify carefully.
            </span>
          </div>
        </div>
        <div className="flex-1 border border-gray-700 rounded p-2 overflow-auto chat-container">
          {chatHistory.length > 0 ? (
            chatHistory.map((chat, index) => {
              if ((chat.isUserMessage && chat.user) || (chat.type === "system" && chat.bot)) {
                return (
                  <div key={index} className="chat-wrapper">
                    {/* User message */}
                    {chat.isUserMessage && (
                      <div className="chat-wrapper user-message">
                        <div className="chat-meta user-meta">User, chat #{index + 1}</div>
                        <div className="chat-bubble user">{chat.user}</div>
                      </div>
                    )}

                    {/* Bot response or query result */}
                    {chat.bot && (
                      // Bot/system answer (SPARQL + explanation + copy button)
                      <div className="chat-wrapper system-message">
                        <div className="chat-meta bot-meta">
                          GPT-4-turbo-preview, chat #{index + 1}
                        </div>

                        {/* Process bot text into SPARQL block + explanation */}
                        {(() => {
                          // Robustly split bot text into SPARQL and explanation.
                          const sparqlMatch = chat.bot.match(/```sparql[\s\S]*?(?:```|$)/i);
                          const sparql = sparqlMatch ? sparqlMatch[0]
                            .replace(/```sparql/i, '')      // remove opening fence
                            .replace(/```$/i, '')           // remove closing fence if present
                            .trim() : '';

                          // Everything after the SPARQL block (or the whole text if none) is explanation
                          const explanation = chat.bot.replace(/```sparql[\s\S]*?(?:```|$)/i, '').replace(/^Explanation:\s*/i, '').trim();

                          return (
                            <div className="chat-bubble bot space-y-3">
                              {/* SPARQL code block */}
                              {sparql && (
                                <pre className="bg-gray-800 rounded p-3 overflow-x-auto text-xs whitespace-pre-wrap">
                                  <code>{sparql}</code>
                                </pre>
                              )}

                              {/* Copy button (inside bubble) */}
                              {sparql && (
                                <div className="pt-1">
                                  <button
                                    className="copy-query-button bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-1 rounded shadow"
                                    onClick={() => handleCopyQuery(sparql)}
                                  >
                                    Copy Query to Editor
                                  </button>
                                </div>
                              )}

                              {/* Explanation text */}
                              {explanation && (
                                <div className="text-sm whitespace-pre-wrap">
                                  {explanation}
                                </div>
                              )}

                              {/* Preset feedback buttons */}
                              {sparql && (
                                <div className="flex flex-col gap-1 pt-1">
                                  <button
                                    className="preset-button"
                                    onClick={() => setMessage("You identified the wrong data. I was actually looking for: ")}
                                  >
                                    You identified the wrong data
                                  </button>
                                  <button
                                    className="preset-button"
                                    onClick={() => setMessage("You misunderstood my question. I was actually asking about:  ")}
                                  >
                                    You misunderstood my question
                                  </button>
                                  <button
                                    className="preset-button"
                                    onClick={() => setMessage("I want to ask something different:  ")}
                                  >
                                    I want to ask something different
                                  </button>
                                </div>
                              )}
                            </div>
                          );
                        })()}
                      </div>
                    )}
                  </div>
                );
              }
              return null;
            })
          ) : (
            <p className="text-gray-400">No messages yet.</p>
          )}
        </div>
        <div className="mt-2 border-t border-gray-700 pt-2 flex">
          <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a message... (Press Enter to send)"
              className="flex-1 p-2 bg-gray-800 text-white rounded"
          />
          <button
              onClick={() => sendMessage()}
              className="ml-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-700"
          >
            Send
          </button>
        </div>
      </div>

      {/* Right Side - Four Panels (scrollable) */}
      <div className="w-2/3 h-full flex flex-col p-2 bg-gray-900 overflow-y-auto space-y-2">
        {/* Query Editor */}
        <div className="border border-gray-700 bg-white p-2 rounded flex-none min-h-[220px]">
          <QueryEditorUI
            value={queryEditorValue}
            onChange={setQueryEditorValue}
            onRunQuery={() => runQuery(queryEditorValue)}
            onKeyPress={handleQueryKeyPress}
            ref={queryEditorRef}
          />
        </div>
        {/* Entity-Relation Table */}
        <div className="border border-gray-700 bg-gray-900 p-2 rounded text-white flex-none">
          <h2 className="text-lg font-semibold mb-2 px-4 py-2 bg-gray-800">Entity-Relation Table from KG</h2>
          {isLoading ? (
            <div className="text-gray-400 p-4">Loading...</div>
          ) : queryError ? (
            <div className="text-red-500 p-4">{queryError}</div>
          ) : queryResults ? (
            <EntityRelationTable graphData={queryResults} />
          ) : (
            <div className="text-gray-400 p-4">Run a query to see entity information</div>
          )}
        </div>
        {/* Query Structure Graph */}
        <div className="border border-gray-700 bg-white p-2 rounded flex-none min-h-[280px] overflow-hidden">
          <h2 className="text-lg font-semibold mb-2 px-4 py-2 bg-gray-800 text-white rounded">Query Structure Graph</h2>
          {isLoading ? (
            <div className="text-gray-400 p-4">Loading...</div>
          ) : queryError ? (
            <div className="text-red-500 p-4">{queryError}</div>
          ) : queryResults ? (
            <div className="h-full">
              <QueryGraph graphData={queryResults} />
            </div>
          ) : (
            <div className="text-gray-600 p-4">Run a query to see the graph structure</div>
          )}
        </div>
        {/* Results Panel */}
        <div className="border border-gray-700 bg-gray-900 p-2 rounded text-white flex-none min-h-[220px]">
          <h2 className="text-lg font-semibold mb-2 px-4 py-2 bg-gray-800">Query Results</h2>
          {isLoading ? (
            <div className="text-gray-400 p-4">Loading...</div>
          ) : queryError ? (
            <div className="text-red-500 p-4">{queryError}</div>
          ) : queryResults ? (
            <ResultsPanel data={queryResults} />
          ) : (
            <div className="text-gray-400 p-4">Run a query to see results</div>
          )}
        </div>
      </div>

      {/* Settings Modal */}
      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />

      {/* One-time page-load warning modal */}
      {showWarning && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 max-w-sm text-center">
            <h2 className="text-lg font-semibold mb-3 text-gray-800">LLM-Generated Content</h2>
            <p className="text-gray-700 mb-4 text-sm">
              This application uses a Large Language Model to generate queries and explanations. The results may contain mistakes. Please verify carefully before relying on them.
            </p>
            <button
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
              onClick={() => setShowWarning(false)}
            >
              Got it
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;