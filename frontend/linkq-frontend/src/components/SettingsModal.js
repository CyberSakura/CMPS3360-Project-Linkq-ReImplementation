import React, { useState, useEffect } from 'react';

const SettingsModal = ({ open, onClose }) => {
  const [baseUrl, setBaseUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('');

  // Load saved values
  useEffect(() => {
    if (open) {
      setBaseUrl(localStorage.getItem('llmBaseUrl') || 'https://api.openai.com/v1');
      setApiKey(localStorage.getItem('llmApiKey') || '');
      setModel(localStorage.getItem('llmModel') || 'gpt-3.5-turbo');
    }
  }, [open]);

  const handleSave = () => {
    localStorage.setItem('llmBaseUrl', baseUrl);
    localStorage.setItem('llmApiKey', apiKey);
    localStorage.setItem('llmModel', model);
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-600 rounded-lg p-6 w-80 text-gray-200 relative">
        <button className="absolute top-2 right-3 text-gray-400 hover:text-white" onClick={onClose}>✕</button>
        <h2 className="text-lg font-bold mb-4">Settings</h2>

        <label className="text-sm font-semibold">LLM Base URL</label>
        <input
          type="text"
          className="w-full p-2 mb-3 bg-gray-800 rounded border border-gray-700 focus:outline-none"
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.target.value)}
        />

        <label className="text-sm font-semibold">API Key</label>
        <input
          type="password"
          className="w-full p-2 mb-3 bg-gray-800 rounded border border-gray-700 focus:outline-none"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
        />

        <label className="text-sm font-semibold">Model</label>
        <select
          className="w-full p-2 mb-5 bg-gray-800 rounded border border-gray-700 focus:outline-none"
          value={model}
          onChange={(e) => setModel(e.target.value)}
        >
          <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
          <option value="gpt-4o">gpt-4o</option>
          <option value="gpt-4-turbo-preview">gpt-4-turbo-preview</option>
        </select>

        <button
          className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded font-semibold"
          onClick={handleSave}
        >
          Save
        </button>
      </div>
    </div>
  );
};

export default SettingsModal; 