import { useState } from 'react'
import { Bot, Plus, Search } from 'lucide-react'
import { StatusBadge } from '@/components/ui/StatusBadge'
import type { Agent } from '@/types/api'

// Placeholder — replaced by real API in Phase 2
const MOCK_AGENTS: Agent[] = [
  { id: '1', org_id: 'org-1', name: 'Customer Support Agent', slug: 'customer-support', description: 'Handles tier-1 support tickets', agent_type: 'customer_support', framework: 'langgraph', status: 'active', tags: ['production', 'tier-1'], created_by: 'user-1', created_at: '2026-06-01T00:00:00Z', updated_at: '2026-06-10T00:00:00Z' },
  { id: '2', org_id: 'org-1', name: 'SQL Agent', slug: 'sql-agent', description: 'Converts natural language to SQL queries', agent_type: 'sql', framework: 'langchain', status: 'active', tags: ['analytics'], created_by: 'user-1', created_at: '2026-06-02T00:00:00Z', updated_at: '2026-06-09T00:00:00Z' },
  { id: '3', org_id: 'org-1', name: 'Research Agent', slug: 'research-agent', description: 'Deep research and summarization', agent_type: 'research', framework: 'langgraph', status: 'inactive', tags: ['experimental'], created_by: 'user-2', created_at: '2026-06-05T00:00:00Z', updated_at: '2026-06-08T00:00:00Z' },
]

export function AgentsPage() {
  const [search, setSearch] = useState('')
  const filtered = MOCK_AGENTS.filter(a => a.name.toLowerCase().includes(search.toLowerCase()))

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Agents</h1>
          <p className="text-gray-400 mt-1">Manage and monitor your AI agent registry</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Register Agent
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          type="text"
          placeholder="Search agents..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-gray-900 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500"
        />
      </div>

      {/* Agent grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>
    </div>
  )
}

function AgentCard({ agent }: { agent: Agent }) {
  return (
    <div className="card hover:border-gray-700 transition-colors cursor-pointer group">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gray-800 rounded-lg flex items-center justify-center group-hover:bg-brand-600/20 transition-colors">
            <Bot className="w-5 h-5 text-gray-400 group-hover:text-brand-400 transition-colors" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">{agent.name}</h3>
            <p className="text-xs text-gray-500">{agent.framework}</p>
          </div>
        </div>
        <StatusBadge status={agent.status} />
      </div>
      <p className="text-xs text-gray-400 mb-4 line-clamp-2">{agent.description}</p>
      <div className="flex items-center gap-2 flex-wrap">
        {agent.tags.map(tag => (
          <span key={tag} className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">{tag}</span>
        ))}
      </div>
    </div>
  )
}
