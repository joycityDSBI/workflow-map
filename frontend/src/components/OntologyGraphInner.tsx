'use client'
import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { GraphData, ObjectCategory, OntologyStatus } from '@/types'

export interface GraphNode {
  id: string
  name: string
  category: ObjectCategory
  status: OntologyStatus
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
}

export interface GraphEdge {
  id: string
  source: string | GraphNode
  target: string | GraphNode
  label: string
}

const CATEGORY_COLORS: Record<ObjectCategory, string> = {
  actor: '#6366f1',
  domain: '#10b981',
  tx: '#f59e0b',
  cs: '#ef4444',
  record: '#8b5cf6',
}

const NODE_RADIUS = 20

interface Props {
  data: GraphData
  onNodeClick: (node: GraphNode) => void
}

export default function OntologyGraphInner({ data, onNodeClick }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current) return
    if (!data || data.nodes.length === 0) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const width = svgRef.current.clientWidth || 800
    const height = svgRef.current.clientHeight || 600

    // Arrow marker definition
    const defs = svg.append('defs')
    defs
      .append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', NODE_RADIUS + 10)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#94a3b8')

    const g = svg.append('g')

    // Zoom + pan
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)

    // Build node and edge copies (avoid mutating props)
    const nodes: GraphNode[] = data.nodes.map((n) => ({ ...n }))
    const edges: GraphEdge[] = data.edges.map((e) => ({ ...e }))

    // Force simulation
    const simulation = d3
      .forceSimulation<GraphNode>(nodes)
      .force(
        'link',
        d3
          .forceLink<GraphNode, GraphEdge>(edges)
          .id((d) => d.id)
          .distance(140)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(NODE_RADIUS + 8))

    // Edge lines
    const link = g
      .append('g')
      .attr('class', 'links')
      .selectAll<SVGLineElement, GraphEdge>('line')
      .data(edges)
      .join('line')
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', 1.5)
      .attr('marker-end', 'url(#arrowhead)')

    // Edge labels
    const edgeLabel = g
      .append('g')
      .attr('class', 'edge-labels')
      .selectAll<SVGTextElement, GraphEdge>('text')
      .data(edges)
      .join('text')
      .attr('fill', '#64748b')
      .attr('font-size', '10px')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .text((d) => d.label)

    // Node groups
    const node = g
      .append('g')
      .attr('class', 'nodes')
      .selectAll<SVGGElement, GraphNode>('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(
        d3
          .drag<SVGGElement, GraphNode>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart()
            d.fx = d.x
            d.fy = d.y
          })
          .on('drag', (event, d) => {
            d.fx = event.x
            d.fy = event.y
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0)
            d.fx = null
            d.fy = null
          })
      )
      .on('click', (_event, d) => {
        onNodeClick(d)
      })

    node
      .append('circle')
      .attr('r', NODE_RADIUS)
      .attr('fill', (d) => CATEGORY_COLORS[d.category] ?? '#94a3b8')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)

    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('fill', '#fff')
      .attr('font-size', '9px')
      .attr('font-weight', '600')
      .attr('pointer-events', 'none')
      .text((d) => (d.name.length > 8 ? d.name.slice(0, 8) + '…' : d.name))

    // Tooltip label below node
    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', NODE_RADIUS + 13)
      .attr('fill', '#334155')
      .attr('font-size', '10px')
      .attr('pointer-events', 'none')
      .text((d) => d.name)

    // Tick update
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as GraphNode).x ?? 0)
        .attr('y1', (d) => (d.source as GraphNode).y ?? 0)
        .attr('x2', (d) => (d.target as GraphNode).x ?? 0)
        .attr('y2', (d) => (d.target as GraphNode).y ?? 0)

      edgeLabel
        .attr(
          'x',
          (d) =>
            (((d.source as GraphNode).x ?? 0) + ((d.target as GraphNode).x ?? 0)) / 2
        )
        .attr(
          'y',
          (d) =>
            (((d.source as GraphNode).y ?? 0) + ((d.target as GraphNode).y ?? 0)) / 2
        )

      node.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`)
    })

    return () => {
      simulation.stop()
    }
  }, [data, onNodeClick])

  return (
    <svg
      ref={svgRef}
      style={{ width: '100%', height: '100%' }}
      className="bg-slate-50"
    />
  )
}
