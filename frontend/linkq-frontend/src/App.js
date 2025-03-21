import React, { useState, useEffect } from "react";
import "./App.css";

const App = () => {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [pendingEntities, setPendingEntities] = useState(null);

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

  return (
    <div className="h-screen w-screen flex">
      {/* Left Chat Panel */}
      <div className="w-1/3 h-full bg-gray-900 text-white p-4 flex flex-col">
        <div className="mb-4">Settings</div>
        <div className="flex-1 border border-gray-700 rounded p-2 overflow-auto chat-container">
          {chatHistory.length > 0 ? (
              chatHistory.map((chat, index) => (
                  <div key={index} className="chat-wrapper">
                    {/* User message */}
                    <div className="chat-meta user-meta">User, chat #{index}</div>
                    <div className="chat-bubble user">{chat.user}</div>

                    {/* Bot message */}
                    <div className="chat-meta bot-meta">GPT-4-turbo-preview, chat #{index}</div>
                    <div className="chat-bubble bot">{chat.bot}</div>
                  </div>
              ))
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
        <div className="h-1/4 border border-gray-400 bg-white p-2 rounded">
          Query Editor (Placeholder)
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