import React from 'react';

const QueryHistoryModal = ({ history, onClose, onSelect }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-3/4 max-w-4xl max-h-[80vh] flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Query History</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {history.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No queries in history</p>
          ) : (
            <div className="space-y-4">
              {history.map((item, index) => (
                <div
                  key={index}
                  className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
                  onClick={() => onSelect(item.query)}
                >
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="font-medium">{item.name}</h3>
                    <button
                      className="text-blue-500 hover:text-blue-700 text-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelect(item.query);
                      }}
                    >
                      Use Query
                    </button>
                  </div>
                  <pre className="text-sm text-gray-600 whitespace-pre-wrap">
                    {item.query.length > 200 
                      ? item.query.substring(0, 200) + '...' 
                      : item.query}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default QueryHistoryModal; 