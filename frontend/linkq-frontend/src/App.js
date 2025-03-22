import React, { useState, useEffect } from "react";
import "./App.css";

import CodeMirror from "@uiw/react-codemirror";
import { StreamLanguage } from "@codemirror/language";
import { sparql } from "@codemirror/legacy-modes/mode/sparql";
import { EditorView } from "@codemirror/view";

import { IconCaretRight, IconHistory } from "@tabler/icons-react";

const App = () => {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [pendingEntities, setPendingEntities] = useState(null);

  const DEMO_QUERY = `SELECT ?founder ?founderLabel ?birthdate
      WHERE {
        wd:Q95 wdt:P112 ?founder.
        ?founder wdt:P569 ?birthdate.
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
      }`;
  const IS_DEMO_MODE = true;
  const [queryEditorValue, setQueryEditorValue] = useState(IS_DEMO_MODE ? DEMO_QUERY : "");

  useEffect(() => {
    const fetchChatHistory = async () => {
      try {
        const response = await fetch("http://127.0.0.1:5000/chat-history");
        const data = await response.json();
        setChatHistory(data.history.reverse()); // Reverse order to show newest at the bottom
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
      const response = await fetch("http://127.0.0.1:5000/chat", {
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
        user: finalMessage, // Store user message
        bot: data.reply, // Store bot response
        chatId: chatHistory.length, // Assign message number
      };

      setChatHistory((prevChat) => [...prevChat, newMessage]); // Append both messages
      setMessage(""); // Clear input

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
    const regex = /```sparql\s*([\s\S]*?)\s*```/i;
    const match = replyText.match(regex);
    return match ? match[1].trim() : '';
  }

  const runQuery = async () => {
    console.log("[DEBUG] runQuery() called with queryEditorValue:\n", queryEditorValue);

    try {
      const response = await fetch("http://127.0.0.1:5000//run_query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: queryEditorValue }),
      });
      console.log("[DEBUG] /runQuery response status:", response.status);

      const data = await response.json();
      console.log("[DEBUG] /runQuery response data:", data);

      if (data.history) {
        setChatHistory(data.history.reverse());
      } else {
        console.log("[DEBUG] No 'history' field in /runQuery response");
      }
    } catch (error) {
      console.error("[ERROR] running query:", error);
    }
  };

  function QueryEditorUI({ queryValue, setQueryValue, onRunQuery }){
    const [queryHistory, setQueryHistory] = useState([]);
    const [showHistory, setShowHistory] = useState(false);

    const handleRunQuery = () => {
      if (!queryValue.trim()) return;
      console.log("[DEBUG] QueryEditorUI handleRunQuery:", queryValue);

      // Add local history entry (optional)
      const newEntry = {
        name: `Query #${queryHistory.length + 1}`,
        query: queryValue,
      };
      setQueryHistory([...queryHistory, newEntry]);

      // Actually call parent's runQuery function
      onRunQuery();
    };


    const handleHistoryClick = (item) => {
      setQueryValue(item.query);
      setShowHistory(false);
    };

    return (
      <div className="query-editor-container">
        <div className="query-editor-header">
          <h4 className="query-editor-title">Query Editor</h4>
          <button
            className="query-editor-button"
            onClick={handleRunQuery}
            aria-label="Run Query"
          >
            ►
          </button>
          <button
            className="query-editor-history-button"
            onClick={() => setShowHistory(true)}
            aria-label="History"
          >
            ⟳
          </button>
        </div>

      <div className="query-editor-body">
        <CodeMirror
          value={queryValue}
          height="100%"
          extensions={[
            StreamLanguage.define(sparql),
            // Enable line wrapping:
            EditorView.lineWrapping
          ]}
          onChange={(val) => setQueryValue(val)}
        />
      </div>

        {showHistory && (
          <div className="history-modal-overlay">
            <div className="history-modal-box">
              <h2>Query History</h2>
              <hr />
              {queryHistory.map((item, index) => (
                <button
                  key={index}
                  className="history-modal-item"
                  onClick={() => handleHistoryClick(item)}
                >
                  {item.name}
                </button>
              ))}
              <button
                className="history-modal-close"
                onClick={() => setShowHistory(false)}
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex">
      {/* Left Chat Panel */}
      <div className="w-1/3 h-full bg-gray-900 text-white p-4 flex flex-col">
        <div className="mb-4">Settings</div>
        <div className="flex-1 border border-gray-700 rounded p-2 overflow-auto chat-container">
          {chatHistory.length > 0 ? (
            chatHistory.map((chat, index) => {
              const isSystem = (chat.user === "system");
              const label = isSystem
                ? `system, chat #${index}`
                : `GPT-4-turbo-preview, chat #${index}`;

              return (
                <div key={index} className="chat-wrapper">
                  {/* User message */}
                  {/* If user is "system", you might skip showing a "user" bubble, or handle differently */}
                  {(!isSystem) && (
                    <>
                      <div className="chat-meta user-meta">User, chat #{index}</div>
                      <div className="chat-bubble user">{chat.user}</div>
                    </>
                  )}

                  {/* Bot or system message */}
                  <div className="chat-meta bot-meta">{label}</div>
                  <div className="chat-bubble bot">{chat.bot}</div>

                  {/* Conditionally render the copy button if a SPARQL query is detected */}
                  {extractSparqlQuery(chat.bot) && (
                    <div style={{ marginTop: "8px" }}>
                      <button
                        className="copy-query-button"
                        onClick={() => {
                          const query = extractSparqlQuery(chat.bot);
                          setQueryEditorValue(query);
                        }}
                      >
                        Copy Query to Editor
                      </button>
                    </div>
                  )}
                </div>
              );
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
              placeholder="Type a message..."
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
      <div className="w-2/3 h-full flex flex-col p-2 bg-gray-100">
        {/* Query Editor */}
        <div className="h-1/4 border border-gray-400 bg-white p-2 rounded">
           <QueryEditorUI
            queryValue={queryEditorValue}
            setQueryValue={setQueryEditorValue}
            onRunQuery={runQuery}
          />
        </div>
        <div className="h-1/4 border border-gray-400 bg-white p-2 rounded mt-2">
          Entity-Relation Table (Placeholder)
        </div>
        <div className="h-1/4 border border-gray-400 bg-white p-2 rounded mt-2">
          Query Structure Graph (Placeholder)
        </div>
        <div className="h-1/4 border border-gray-400 bg-white p-2 rounded mt-2">
          Results Panel (Placeholder)
        </div>
      </div>
    </div>
  );
};

export default App;