'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'

interface Agent {
  id: string
  task: string
  status: string
  confidence_score?: number
  estimated_cost_min?: number
  estimated_cost_max?: number
}

export default function AgentPage() {
  const params = useParams()
  const agentId = params.id as string
  
  const [agent, setAgent] = useState<Agent | null>(null)

  useEffect(() => {
    const fetchAgent = async () => {
      const res = await fetch(`http://localhost:8000/api/agents/${agentId}`)
      const data: Agent = await res.json()
      setAgent(data)
    }

    fetchAgent()

    const interval = setInterval(fetchAgent, 2000)
    return () => clearInterval(interval)
  }, [agentId])

  if (!agent) return <div className="p-8">Loading...</div>

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold mb-2">Agent {agentId.slice(0, 8)}</h1>
          <p className="text-gray-600">{agent.task}</p>
        </div>

        <div className="bg-white border rounded-lg p-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Status</span>
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              {agent.status}
            </span>
          </div>

          {agent.confidence_score !== undefined && (
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Confidence</span>
                <span className="font-medium">{agent.confidence_score}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full"
                  style={{ width: `${agent.confidence_score}%` }}
                />
              </div>
            </div>
          )}

          {agent.estimated_cost_min !== undefined && (
            <div className="text-sm">
              <span className="text-gray-600">Estimated cost:</span>
              <span className="ml-2 font-medium">
                ${agent.estimated_cost_min} - ${agent.estimated_cost_max}
              </span>
            </div>
          )}

          <div className="pt-4 border-t space-x-2">
            <button className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
              Kill Agent
            </button>
            <button className="px-4 py-2 border rounded hover:bg-gray-50">
              View Logs
            </button>
          </div>
        </div>
      </div>
    </main>
  )
}
