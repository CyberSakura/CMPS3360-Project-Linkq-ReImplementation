import React, { useState, useEffect } from 'react';
import EntityTooltip from './EntityTooltip';
import config from '../config';

const ResultsPanel = ({ data }) => {
  const [tooltipData, setTooltipData] = useState(null);
  const [summary, setSummary] = useState('');
  const [loadingSummary, setLoadingSummary] = useState(false);

  // Fetch summary whenever new data arrives
  useEffect(() => {
    const fetchSummary = async () => {
      if (!data) return;
      try {
        setLoadingSummary(true);
        const resp = await fetch(`${config.API_BASE_URL}/summarize-results`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ result: data.main_results, query: data.query }),
        });
        const json = await resp.json();
        if (json.summary) setSummary(json.summary);
      } catch (e) {
        console.error('Summary fetch error', e);
      } finally {
        setLoadingSummary(false);
      }
    };
    fetchSummary();
  }, [data]);

  // Handle the new response format
  const results = data?.main_results?.results;
  const bindings = results?.bindings;

  if (!data || !results || !bindings || bindings.length === 0) {
    return (
      <div className="text-gray-400 p-4">No results found</div>
    );
  }

  const variables = data.main_results.head.vars;

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
    <div className="h-[calc(100%-2rem)] overflow-hidden">
      {/* Summary */}
      <div className="text-base text-gray-200 mb-2">
        <h3 className="font-bold mb-1">Results Summary from LLM</h3>
        {loadingSummary ? (
          <span className="text-gray-400">Generating summary...</span>
        ) : summary ? (
          <p>{summary}</p>
        ) : (
          <span className="text-gray-400">No summary available</span>
        )}
      </div>

      {/* Divider */}
      <hr className="border-gray-500 my-2" />

      {/* Results Table Title */}
      <div className="text-base text-gray-200 mb-1">
        <h3 className="font-bold">Results Table from KG</h3>
      </div>

      {/* Results table */}
      <div className="h-full overflow-y-auto">
        <div className="min-w-full inline-block align-middle">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="sticky top-0 bg-gray-800">
                <tr>
                  {variables.map((variable) => (
                    <th key={variable} scope="col" className="px-4 py-2 text-left text-xs font-semibold text-gray-300 uppercase">
                      {variable}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {bindings.map((result, index) => (
                  <tr key={index} className={index % 2 === 0 ? 'bg-gray-900' : 'bg-gray-800'}>
                    {variables.map((variable) => (
                      <td key={variable} className="px-4 py-2 text-sm text-gray-300 whitespace-nowrap">
                        {formatValue(result[variable])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      {tooltipData && <EntityTooltip {...tooltipData} />}
    </div>
  );
};

export default ResultsPanel; 