import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import config from './config';
import QueryEditorUI from './components/QueryEditorUI';
import EntityRelationTable from './components/EntityRelationTable';

const App = () => {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [queryResults, setQueryResults] = useState(null);
  const [queryError, setQueryError] = useState(null);
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
        <div className="mb-4">Settings</div>
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
                      <div className="chat-wrapper system-message">
                        <div className="chat-meta bot-meta">
                          GPT-4-turbo-preview, chat #{index + 1}
                        </div>
                        <div className="chat-bubble bot">{chat.bot}</div>

                        {extractSparqlQuery(chat.bot) && (
                          <div style={{ marginTop: "8px" }}>
                            <button
                              className="copy-query-button"
                              onClick={() => handleCopyQuery(extractSparqlQuery(chat.bot))}
                            >
                              Copy Query to Editor
                            </button>
                          </div>
                        )}
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

      {/* Right Side - Four Panels */}
      <div className="w-2/3 h-full flex flex-col p-2 bg-gray-900">
        {/* Query Editor */}
        <div className="h-1/4 border border-gray-700 bg-white p-2 rounded">
          <QueryEditorUI
            value={queryEditorValue}
            onChange={setQueryEditorValue}
            onRunQuery={() => runQuery(queryEditorValue)}
            onKeyPress={handleQueryKeyPress}
            ref={queryEditorRef}
          />
        </div>
        {/* Entity-Relation Table */}
        <div className="h-1/4 border border-gray-700 bg-gray-900 p-2 rounded mt-2 text-white">
          {queryError ? (
            <div className="text-red-500 p-4">{queryError}</div>
          ) : queryResults ? (
            <EntityRelationTable data={queryResults} />
          ) : (
            <div className="text-gray-400 p-4">Run a query to see results here</div>
          )}
        </div>
        <div className="h-1/4 border border-gray-700 bg-gray-900 p-2 rounded mt-2 text-white">
          <h2 className="text-lg font-semibold mb-2 px-4 py-2 bg-gray-800">Query Structure Graph</h2>
          <div className="text-gray-400">Query Structure Graph (Placeholder)</div>
        </div>
        <div className="h-1/4 border border-gray-700 bg-gray-900 p-2 rounded mt-2 text-white">
          <h2 className="text-lg font-semibold mb-2 px-4 py-2 bg-gray-800">Results Panel</h2>
          <div className="text-gray-400">Results Panel (Placeholder)</div>
        </div>
      </div>
    </div>
  );
};

export default App;