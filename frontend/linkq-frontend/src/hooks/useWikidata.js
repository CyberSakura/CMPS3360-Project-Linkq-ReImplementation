import { useState, useEffect } from 'react';

const useWikidata = () => {
  const [entityData, setEntityData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchEntityData = async (entityId) => {
    if (!entityId || entityData[entityId]) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`https://www.wikidata.org/w/api.php?action=wbgetentities&ids=${entityId}&format=json&languages=en&origin=*`);
      const data = await response.json();

      if (data.error) {
        throw new Error(data.error.info);
      }

      const entity = data.entities[entityId];
      setEntityData(prev => ({
        ...prev,
        [entityId]: {
          id: entityId,
          label: entity.labels?.en?.value || entityId,
          description: entity.descriptions?.en?.value || '',
          url: `https://www.wikidata.org/wiki/${entityId}`,
        }
      }));
    } catch (err) {
      setError(err.message);
      console.error('Error fetching entity data:', err);
    } finally {
      setLoading(false);
    }
  };

  return {
    entityData,
    loading,
    error,
    fetchEntityData
  };
};

export default useWikidata; 