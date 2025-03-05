import React from "react";

const App = () => {
  return (
    <div className="h-screen w-screen flex">
      {/* Left Chat Panel */}
      <div className="w-1/3 h-full bg-gray-900 text-white p-4 flex flex-col">
        <div className="mb-4">Settings</div>
        <div className="flex-1 border border-gray-700 rounded p-2 overflow-auto">
          Chat Panel (Placeholder)
        </div>
        <div className="mt-2 border-t border-gray-700 pt-2">
          <input
            type="text"
            placeholder="Type a message..."
            className="w-full p-2 bg-gray-800 text-white rounded"
          />
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
