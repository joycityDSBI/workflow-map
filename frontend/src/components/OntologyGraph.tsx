'use client'
import dynamic from 'next/dynamic'
import { GraphData, OntologyStatus, ObjectCategory } from '@/types'

export interface GraphNode {
  id: string
  name: string
  category: ObjectCategory
  status: OntologyStatus
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  label: string
}

export interface OntologyGraphProps {
  data: GraphData
  onNodeClick: (node: GraphNode) => void
}

const OntologyGraphInner = dynamic(() => import('./OntologyGraphInner'), { ssr: false })

export default function OntologyGraph(props: OntologyGraphProps) {
  return <OntologyGraphInner {...props} />
}
