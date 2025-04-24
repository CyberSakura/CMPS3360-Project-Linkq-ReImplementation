import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import { IconCaretRight, IconHistory, IconTrash } from '@tabler/icons-react';
import CodeMirror from "@uiw/react-codemirror";
import { StreamLanguage } from "@codemirror/language";
import { sparql } from "@codemirror/legacy-modes/mode/sparql";
import { EditorView } from "@codemirror/view";
import QueryHistoryModal from './QueryHistoryModal';
import config from '../config';

const QueryEditorUI = forwardRef(({ value, onChange, onRunQuery, onKeyPress }, ref) => {
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    // Load history from localStorage on mount
    const savedHistory = localStorage.getItem('queryHistory');
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory));
      } catch (error) {
        console.error('Error loading query history:', error);
        localStorage.removeItem('queryHistory');
      }
    }
  }, []);

  useEffect(() => {
    // Sync history to localStorage whenever it changes
    if (history.length > 0) {
      localStorage.setItem('queryHistory', JSON.stringify(history));
    } else {
      localStorage.removeItem('queryHistory');
    }
  }, [history]);

  useImperativeHandle(ref, () => ({
    addToHistory: async (query) => {
      try {
        console.log('Attempting to generate query name...');
        // Try to get a generated name for the query
        const response = await fetch(`${config.API_BASE_URL}/generate-query-name`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query })
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          console.error('Failed to generate query name:', errorData);
          throw new Error(`Failed to generate query name: ${errorData.error || 'Unknown error'}`);
        }
        
        const data = await response.json();
        console.log('Generated query name:', data);
        
        const timestamp = new Date().toISOString();
        const newHistory = [{ name: data.name, query, timestamp }, ...history].slice(0, 50);
        setHistory(newHistory);
      } catch (error) {
        console.error('Error in addToHistory:', error);
        // If name generation fails, use a default name
        const timestamp = new Date().toISOString();
        const newHistory = [{ 
          name: `Untitled Query ${history.length + 1}`, 
          query,
          timestamp
        }, ...history].slice(0, 50);
        setHistory(newHistory);
      }
    },
    handleQueryPaste: (query) => {
      onChange(query);
    }
  }));

  const handleQueryPaste = (e) => {
    const pastedText = e.clipboardData.getData('text');
    onChange(pastedText);
  };

  const handleQuerySelect = (query) => {
    onChange(query);
    setShowHistory(false);
  };

  // Clear query history handler
  const handleClearHistory = () => {
    if (history.length === 0) return;
    if (window.confirm('Are you sure you want to delete all query history?')) {
      setHistory([]);
      localStorage.removeItem('queryHistory');
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between items-center mb-2 p-2 bg-gray-100 rounded-t-lg">
        <h2 className="text-lg font-semibold">SPARQL Query Editor</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setShowHistory(true)}
            className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded-lg flex items-center gap-2 transition-colors"
            title="View Query History"
          >
            <IconHistory size={20} />
            History ({history.length})
          </button>
          <button
            onClick={handleClearHistory}
            className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-lg flex items-center gap-2 transition-colors"
            title="Clear Query History"
          >
            <IconTrash size={20} />
            Clear
          </button>
          <button
            onClick={() => onRunQuery(value)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            title="Run Query (Ctrl/Cmd + Enter)"
          >
            <IconCaretRight size={20} />
            Run Query
          </button>
        </div>
      </div>

      <div className="flex-1 border rounded-lg overflow-hidden">
        <CodeMirror
          value={value}
          height="100%"
          extensions={[
            StreamLanguage.define(sparql),
            EditorView.lineWrapping
          ]}
          onChange={onChange}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
              onRunQuery(value);
            }
            if (onKeyPress) {
              onKeyPress(e);
            }
          }}
          onPaste={handleQueryPaste}
        />
      </div>

      {showHistory && (
        <QueryHistoryModal
          history={history}
          onClose={() => setShowHistory(false)}
          onSelect={handleQuerySelect}
        />
      )}
    </div>
  );
});

export default QueryEditorUI; 