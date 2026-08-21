export type OntologyStatus = 'DRAFT' | 'PENDING_REVIEW' | 'PUBLISHED' | 'REJECTED' | 'ARCHIVED'
export type ObjectCategory = 'actor' | 'domain' | 'tx' | 'cs' | 'record'
export type UserRole = 'analyst' | 'domain_expert' | 'admin'

export interface OntologyObject {
  id: string
  name: string
  category: ObjectCategory
  status: OntologyStatus
  confidence: number | null
  source_stale: boolean
  created_at: string
  updated_at: string
}

export interface OntologyLink {
  id: string
  from_id: string
  to_id: string
  label: string
  cardinality: string
  status: OntologyStatus
}

export interface GraphData {
  nodes: Array<{ id: string; name: string; category: ObjectCategory; status: OntologyStatus }>
  edges: Array<{ id: string; source: string; target: string; label: string }>
}

export interface CurrentUser {
  id: string
  username: string
  email: string
  role: UserRole
}

export interface ReviewItem {
  id: string
  entity_type: 'object' | 'link' | 'action' | 'rule'
  name: string
  status: 'PENDING_REVIEW'
  confidence: number | null
  created_at: string
}
