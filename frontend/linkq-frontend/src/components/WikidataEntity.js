import React, { useEffect, useState } from 'react';

const WikidataEntity = ({ entityId }) => {
  const [entityInfo, setEntityInfo] = useState({ label: 'Loading...', description: 'Loading...' });

  useEffect(() => {
    const fetchEntityInfo = async () => {
      try {
        const response = await fetch(
          `https://www.wikidata.org/w/api.php?action=wbgetentities&ids=${entityId}&format=json&languages=en&props=labels|descriptions&origin=*`
        );
        const data = await response.json();
        
        if (data.entities && data.entities[entityId]) {
          const entity = data.entities[entityId];
          setEntityInfo({
            label: entity.labels?.en?.value || entityId,
            description: entity.descriptions?.en?.value || 'No description available'
          });
        }
      } catch (error) {
        console.error('Error fetching entity info:', error);
        setEntityInfo({
          label: entityId,
          description: 'Error loading entity information'
        });
      }
    };

    fetchEntityInfo();
  }, [entityId]);

  return {
    label: entityInfo.label,
    description: entityInfo.description
  };
};

export default WikidataEntity; 