import React, { useEffect } from 'react';
import useWikidata from '../hooks/useWikidata';

const EntityTooltip = ({ entityId, position }) => {
  const { entityData, loading, error, fetchEntityData } = useWikidata();

  useEffect(() => {
    if (entityId) {
      fetchEntityData(entityId);
    }
  }, [entityId, fetchEntityData]);

  if (!entityId || !position) return null;

  if (loading) {
    return (
      <div 
        className="absolute bg-white shadow-lg rounded-lg p-3 z-50 border border-gray-200"
        style={{
          left: position.x,
          top: position.y + 20,
          transform: 'translateX(-50%)',
          minWidth: '200px',
          maxWidth: '300px'
        }}
      >
        Loading...
      </div>
    );
  }

  if (error || !entityData[entityId]) {
    return null;
  }

  const entity = entityData[entityId];

  return (
    <div 
      className="absolute bg-white shadow-lg rounded-lg p-3 z-50 border border-gray-200"
      style={{
        left: position.x,
        top: position.y + 20,
        transform: 'translateX(-50%)',
        minWidth: '200px',
        maxWidth: '300px'
      }}
    >
      <h3 className="font-semibold text-gray-800 mb-1">{entity.label}</h3>
      {entity.description && (
        <p className="text-sm text-gray-600 mb-2">{entity.description}</p>
      )}
      <a 
        href={entity.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs text-blue-600 hover:text-blue-800"
      >
        View on Wikidata
      </a>
    </div>
  );
};

export default EntityTooltip; 