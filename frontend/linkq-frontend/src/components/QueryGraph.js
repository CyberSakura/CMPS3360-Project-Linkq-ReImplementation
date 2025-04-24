import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

const QueryGraph = ({ graphData }) => {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const nodesRef = useRef(null); // store d3 selection for later highlight updates

  // Highlight state: null | 'Variable' | 'Term'
  const [highlightType, setHighlightType] = useState(null);

  useEffect(() => {
    console.log("[DEBUG] QueryGraph received data:", graphData);

    // Transform the data into the format needed for D3
    const transformData = (data) => {
      if (!data || !data.entity_info || !data.query) {
        console.log("[DEBUG] Missing required data for graph");
        return null;
      }

      const nodes = new Map(); // Use Map to handle unique nodes
      const edges = new Set(); // Use Set to handle unique edges
      
      // Helper function to normalize entity IDs
      const normalizeId = (id) => {
        // Remove common prefixes and clean up trailing characters
        return id.replace(/^(wd:|wdt:|p:|ps:|pq:)/, '').replace(/[;.]$/, '');
      };

      const addNode = (id, type = 'Term') => {
        const normalizedId = normalizeId(id);
        if (!nodes.has(normalizedId)) {
          nodes.set(normalizedId, {
            id: normalizedId,
            type: id.startsWith('?') ? 'Variable' : type,
            label: normalizedId
          });
          console.log("[DEBUG] Added node:", normalizedId);
        }
        return normalizedId;
      };

      // Helper function to add an edge
      const addEdge = (source, target, predicate) => {
        const edgeKey = `${source}-${predicate}-${target}`;
        if (!edges.has(edgeKey)) {
          edges.add(edgeKey);
          console.log("[DEBUG] Added edge:", edgeKey);
        }
      };

      // Parse the SPARQL query: remove inline comments and extract WHERE content
      const cleanedQueryString = data.query.replace(/#.*/g, '');
      const firstBraceIdx = cleanedQueryString.indexOf('{');
      const lastBraceIdx = cleanedQueryString.lastIndexOf('}');
      if (firstBraceIdx === -1 || lastBraceIdx === -1 || lastBraceIdx <= firstBraceIdx) return null;
      const whereClause = cleanedQueryString.slice(firstBraceIdx + 1, lastBraceIdx);
      console.log("[DEBUG] WHERE clause:", whereClause);

      // Parse line by line to maintain current subject across semicolon continuations
      const lines = whereClause.split('\n')
        .map(l => l.trim())
        .filter(l => l && !l.match(/^(SERVICE|FILTER|OPTIONAL|BIND|VALUES)\b/i));

      console.log("[DEBUG] Parsed lines:", lines);

      let currentSubject = null;

      lines.forEach(rawLine => {
        // Remove trailing period
        let line = rawLine.endsWith('.') ? rawLine.slice(0, -1) : rawLine;

        // Split by semicolon segments so multiple predicate-object pairs per subject
        const segments = line.split(';').map(s => s.trim()).filter(Boolean);
        if (segments.length === 0) return;

        segments.forEach((segment, idx) => {
          const tokens = segment.split(/\s+/).filter(Boolean);
          if (tokens.length < 2) return;

          if (idx === 0 && tokens.length >= 3) {
            // New subject defined in this segment
            currentSubject = tokens[0];
            const predicate = tokens[1];
            const object = tokens[2];
            const sId = addNode(currentSubject);
            const oId = addNode(object);
            addEdge(sId, oId, normalizeId(predicate));
          } else if (currentSubject) {
            // Continuation predicate-object pairs for the current subject
            const predicate = tokens[0];
            const object = tokens[1];
            const sId = addNode(currentSubject);
            const oId = addNode(object);
            addEdge(sId, oId, normalizeId(predicate));
          }
        });
      });

      // Enrich nodes with entity information
      const entityInfo = data.entity_info.results.bindings;
      nodes.forEach((node, id) => {
        if (node.type === 'Term') {
          const entity = entityInfo.find(e => {
            const entityId = e.id.value.split('/').pop();
            return entityId === id || e.label.value.toLowerCase() === node.label.toLowerCase();
          });

          if (entity) {
            node.label = entity.label.value;
            node.description = entity.description?.value;
            console.log("[DEBUG] Enriched node:", id, "with label:", node.label);
          }
        }
      });

      // Convert to arrays for D3
      const nodeArray = Array.from(nodes.values());
      const edgeArray = Array.from(edges).map(edge => {
        const [source, predicate, target] = edge.split('-');
        return { source, target, predicate };
      });

      console.log("[DEBUG] Final graph structure:", {
        nodes: nodeArray,
        edges: edgeArray
      });

      return {
        nodes: nodeArray,
        edges: edgeArray
      };
    };

    const transformedData = transformData(graphData);
    if (!transformedData) {
      console.log("[DEBUG] No valid data for visualization");
      return;
    }

    const computeLevels = (nodes, edges) => {
      const nodeMap = new Map(nodes.map(n => [n.id, n]));

      // Build undirected adjacency list for simplicity
      const adj = new Map();
      nodes.forEach(n => adj.set(n.id, []));
      edges.forEach(e => {
        if (adj.has(e.source.id || e.source)) adj.get(e.source.id || e.source).push(e.target.id || e.target);
        if (adj.has(e.target.id || e.target)) adj.get(e.target.id || e.target).push(e.source.id || e.source);
      });

      // Identify a root: first Variable or just first node
      const root = nodes.find(n => n.type === 'Variable') || nodes[0];
      const visited = new Set();
      const queue = [];
      if (root) {
        root.level = 0;
        queue.push(root.id);
        visited.add(root.id);
      }

      while (queue.length) {
        const currentId = queue.shift();
        const currentLevel = nodeMap.get(currentId).level || 0;
        for (const neigh of adj.get(currentId) || []) {
          if (!visited.has(neigh)) {
            visited.add(neigh);
            const neighNode = nodeMap.get(neigh);
            neighNode.level = currentLevel + 1;
            queue.push(neigh);
          }
        }
      }

      // Unvisited nodes (isolated) -> level 0
      nodes.forEach(n => {
        if (n.level === undefined) n.level = 0;
      });
    };

    computeLevels(transformedData.nodes, transformedData.edges);

    // Clear previous graph
    d3.select(svgRef.current).selectAll("*").remove();

    // Set up SVG container with viewBox for responsiveness
    const container = containerRef.current;
    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;

    const svg = d3.select(svgRef.current)
      .attr("viewBox", [0, 0, containerWidth, containerHeight])
      .attr("preserveAspectRatio", "xMidYMid meet");

    // Create zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.5, 2])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom);

    // Create a group for the graph
    const g = svg.append("g");

    // Create force simulation with adjusted forces
    const simulation = d3.forceSimulation(transformedData.nodes)
      .force("link", d3.forceLink(transformedData.edges)
        .id(d => d.id)
        .distance(120)) // Increased distance for better spacing
      .force("charge", d3.forceManyBody()
        .strength(-800)  // Stronger repulsion
        .distanceMax(300)) // Limit the repulsion range
      .force("center", d3.forceCenter(containerWidth / 2, containerHeight / 2))
      .force("collide", d3.forceCollide().radius(50)); // Increased collision radius

    // Create arrow marker for edges
    g.append("defs").selectAll("marker")
      .data(["end"])
      .enter().append("marker")
      .attr("id", String)
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 22) // Adjusted for smaller node size
      .attr("refY", 0)
      .attr("markerWidth", 8)
      .attr("markerHeight", 8)
      .attr("orient", "auto")
      .append("path")
      .attr("fill", "#666")
      .attr("d", "M0,-5L10,0L0,5");

    // Draw edges with straight lines
    const edges = g.append("g")
      .selectAll("g")
      .data(transformedData.edges)
      .enter()
      .append("g");

    const lines = edges.append("line")
      .attr("stroke", "#666")
      .attr("stroke-opacity", 0.8)
      .attr("stroke-width", 1.5)
      .attr("marker-end", "url(#end)");

    // Add edge labels with background
    const edgeLabels = edges.append("g")
      .attr("class", "edge-label");

    edgeLabels.append("rect")
      .attr("fill", "white")
      .attr("rx", 4)
      .attr("ry", 4);

    edgeLabels.append("text")
      .attr("text-anchor", "middle")
      .attr("fill", "#333")
      .attr("font-size", "10px")
      .text(d => d.predicate);

    // Create node groups
    const nodes = g.append("g")
      .selectAll("g")
      .data(transformedData.nodes)
      .enter()
      .append("g")
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    // Add circles for nodes with uniform size
    nodes.append("circle")
      .attr("r", 18)
      .attr("fill", d => d.type === 'Variable' ? '#4299e1' : '#48bb78')
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);

    // Add node labels below the circles
    const nodeLabels = nodes.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "2.5em")
      .attr("fill", "#333")
      .attr("font-size", "11px")
      .each(function(d) {
        const textSel = d3.select(this);
        if (d.type === 'Variable') {
          // Single-line variable label (without leading ?)
          const content = d.id.startsWith('?') ? d.id.slice(1) : d.id;
          textSel.text(content);
        } else {
          // Term: first line ID, second line human label
          textSel.text(d.id); // first line
          const labelText = d.label && d.label !== d.id ? d.label : '';
          if (labelText) {
            textSel.append("tspan")
              .attr("x", 0)
              .attr("dy", "1.2em")
              .text(labelText);
          }
        }
      });

    // Store node selection for highlight updates
    nodesRef.current = nodes;

    // Add tooltips
    nodes.append("title")
      .text(d => `${d.label || d.id}\n${d.description || ''}`);

    // Update positions on each tick
    simulation.on("tick", () => {
      // Define column spacing for levels
      const columnSpacing = 180;

      // Constrain nodes to container boundaries
      transformedData.nodes.forEach(node => {
        // Bias x toward its column if not being dragged (fx == null)
        if (node.fx == null) {
          const targetX = 100 + (node.level || 0) * columnSpacing;
          node.x += (targetX - node.x) * 0.1; // smooth
        }
        node.x = Math.max(20, Math.min(containerWidth - 20, node.x));
        node.y = Math.max(20, Math.min(containerHeight - 20, node.y));
      });

      // Update edge line positions
      lines
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      // Update edge labels
      edgeLabels.attr("transform", d => {
        const x = (d.source.x + d.target.x) / 2;
        const y = (d.source.y + d.target.y) / 2;
        return `translate(${x},${y})`;
      });

      // Update edge label backgrounds
      edgeLabels.select("rect")
        .each(function() {
          const text = d3.select(this.parentNode).select("text");
          const bbox = text.node().getBBox();
          d3.select(this)
            .attr("x", bbox.x - 4)
            .attr("y", bbox.y - 2)
            .attr("width", bbox.width + 8)
            .attr("height", bbox.height + 4);
        });

      // Update node positions
      nodes.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [graphData]);

  // Effect to apply highlight when highlightType changes
  useEffect(() => {
    if (!nodesRef.current) return;
    // Highlight opposite: the highlightType nodes stay full opacity; others dim
    nodesRef.current.selectAll("circle")
      .style("opacity", d => !highlightType || d.type === highlightType ? 1 : 0.15);
    nodesRef.current.selectAll("text")
      .style("opacity", d => !highlightType || d.type === highlightType ? 1 : 0.15);
  }, [highlightType]);

  // Legend click handler
  const handleLegendClick = (label) => {
    // Clicking 'Term' highlights variables, clicking 'Variable' highlights terms
    const target = label === 'Term' ? 'Variable' : 'Term';
    setHighlightType(prev => prev === target ? null : target);
  };

  return (
    <div ref={containerRef} className="relative h-full w-full overflow-hidden">
      <svg
        ref={svgRef}
        className="w-full h-full"
        style={{ background: 'white' }}
      />

      {/* Legend */}
      <div className="absolute top-2 right-2 flex items-center space-x-4 text-sm select-none">
        {/* Variable legend item */}
        <div className="flex items-center cursor-pointer" onClick={() => handleLegendClick('Variable')}>
          <svg width="12" height="12" className="mr-1">
            <circle cx="6" cy="6" r="5" fill="#4299e1" stroke="#4299e1" />
          </svg>
          <span className="text-gray-700">Variable</span>
        </div>

        {/* Term legend item */}
        <div className="flex items-center cursor-pointer" onClick={() => handleLegendClick('Term')}>
          <svg width="12" height="12" className="mr-1">
            <circle cx="6" cy="6" r="5" fill="#48bb78" stroke="#48bb78" />
          </svg>
          <span className="text-gray-700">Term</span>
        </div>
      </div>
    </div>
  );
};

export default QueryGraph; 