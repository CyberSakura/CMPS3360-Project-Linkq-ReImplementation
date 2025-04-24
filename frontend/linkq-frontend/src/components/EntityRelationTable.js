import React from 'react';

const EntityRelationTable = ({ graphData }) => {
  console.log("[DEBUG] EntityRelationTable received graphData:", graphData);
  
  // Extract entity information from the response
  const entityInfo = graphData?.entity_info?.results?.bindings || [];
  console.log("[DEBUG] Entity info bindings:", entityInfo);
  
  if (!entityInfo.length) {
    console.log("[DEBUG] No entity information found in response");
    return <div className="text-gray-400 p-4">No entity information available</div>;
  }

  return (
    <div className="h-full flex flex-col">
      <div className="overflow-y-auto flex-1">
        <table className="min-w-full table-auto">
          <thead className="sticky top-0 bg-gray-800">
            <tr>
              <th className="px-4 py-2 text-left text-sm font-semibold text-gray-200">ID</th>
              <th className="px-4 py-2 text-left text-sm font-semibold text-gray-200">Label</th>
              <th className="px-4 py-2 text-left text-sm font-semibold text-gray-200">Description</th>
            </tr>
          </thead>
          <tbody>
            {entityInfo.map((entity, index) => {
              console.log("[DEBUG] Rendering entity:", entity);
              const id = entity.id.value.split('/').pop(); // Extract Q/P number from URI
              return (
                <tr key={id} className={index % 2 === 0 ? 'bg-gray-900' : 'bg-gray-800'}>
                  <td className="px-4 py-2 text-sm text-gray-300">{id}</td>
                  <td className="px-4 py-2 text-sm text-gray-300">{entity.label.value}</td>
                  <td className="px-4 py-2 text-sm text-gray-300">{entity.description?.value || 'No description available'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default EntityRelationTable; 