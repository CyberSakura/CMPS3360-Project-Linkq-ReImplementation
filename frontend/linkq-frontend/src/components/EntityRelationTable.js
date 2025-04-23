import React, { useState } from 'react';
import EntityTooltip from './EntityTooltip';

const EntityRelationTable = ({ data }) => {
  console.log("[DEBUG] EntityRelationTable received data:", data);
  const [tooltipData, setTooltipData] = useState(null);

  // Handle the new response format
  const results = data?.main_results?.results;
  const bindings = results?.bindings;

  if (!data || !results || !bindings || bindings.length === 0) {
    console.log("[DEBUG] No results condition met:", {
      hasData: !!data,
      hasResults: !!results,
      hasBindings: !!bindings,
      bindingsLength: bindings?.length
    });
    return (
      <div className="h-full flex flex-col">
        <h2 className="text-lg font-semibold mb-2 px-4 py-2 bg-gray-800 text-white">Entity-Relation Table from KG</h2>
        <div className="text-gray-400 italic p-4">No results found</div>
      </div>
    );
  }

  const variables = data.main_results.head.vars;
  
  console.log("[DEBUG] Processing results:", {
    variables,
    resultsCount: bindings.length,
    firstResult: bindings[0]
  });

  const extractEntityId = (uri) => {
    if (!uri) return null;
    const match = uri.match(/\/([QP]\d+)$/);
    return match ? match[1] : null;
  };

  const handleMouseEnter = (event, uri) => {
    const entityId = extractEntityId(uri);
    if (entityId) {
      setTooltipData({
        entityId,
        position: {
          x: event.clientX,
          y: event.clientY
        }
      });
    }
  };

  const handleMouseLeave = () => {
    setTooltipData(null);
  };

  const formatValue = (value) => {
    if (!value) return '-';
    
    if (value.type === 'uri') {
      const entityId = extractEntityId(value.value);
      if (entityId) {
        // Look up entity info in the data.entity_info if available
        const entityInfo = data.entity_info?.results?.bindings?.find(
          b => extractEntityId(b.id?.value) === entityId
        );
        
        return (
          <a
            href={value.value}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800"
            onMouseEnter={(e) => handleMouseEnter(e, value.value)}
            onMouseLeave={handleMouseLeave}
            title={entityInfo?.label?.value || entityId}
          >
            {entityInfo?.label?.value || entityId}
          </a>
        );
      }
      return (
        <a
          href={value.value}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800"
        >
          {value.value}
        </a>
      );
    }
    return value.value;
  };

  return (
    <div className="h-full flex flex-col">
      <h2 className="text-lg font-semibold mb-2 px-4 py-2 bg-gray-800 text-white">Entity-Relation Table from KG</h2>
      <div className="flex-1 overflow-auto">
        <div className="relative shadow-md sm:rounded-lg">
          <table className="w-full text-sm text-left text-gray-300">
            <thead className="text-xs text-gray-300 uppercase bg-gray-800 sticky top-0">
              <tr>
                {variables.map((variable) => (
                  <th key={variable} scope="col" className="px-6 py-3">
                    {variable}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {bindings.map((result, index) => (
                <tr
                  key={index}
                  className={index % 2 === 0 ? 'bg-gray-900' : 'bg-gray-800'}
                >
                  {variables.map((variable) => (
                    <td key={variable} className="px-6 py-4">
                      {formatValue(result[variable])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {tooltipData && <EntityTooltip {...tooltipData} />}
    </div>
  );
};

export default EntityRelationTable; 