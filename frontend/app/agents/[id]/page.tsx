'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'

interface Agent {
  id: string
  task: string
  status: 'running' | 'completed' | 'failed' | 'paused' | 'pending'
  current_step: number
  total_steps: number
  cost_usd: number
  runtime_seconds: number
  confidence_score?: number
  estimated_cost_min?: number
  estimated_cost_max?: number
  result?: {
    content?: string
    tokens?: number
    cost?: number
  } | null
  error?: string | null
}

interface TimelineEvent {
  timestamp: string
  action: string
  status: string
  step: number
  data?: Record<string, string | number | boolean | null> // NO ANY
  cost: number
}

interface TimelineResponse {
  timeline: TimelineEvent[]
}

export default function AgentPage() {
  const params = useParams()
  const agentId = params.id as string

  const [agent, setAgent] = useState<Agent | null>(null)
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    const fetchAgent = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/agents/${agentId}`)
        if (!res.ok) throw new Error('Failed to fetch agent')
        const data = await res.json() as Agent
        setAgent(data)
      } catch (err) {
        console.error('Failed to fetch agent:', err)
        setError('Failed to load agent')
      }
    }

    const fetchTimeline = async () => {
      try {
        const res = await fetch(
          `http://localhost:8000/api/agents/${agentId}/timeline`
        )
        if (!res.ok) throw new Error('Failed to fetch timeline')
        const data = await res.json() as TimelineResponse
        setTimeline(Array.isArray(data.timeline) ? data.timeline : [])
      } catch (err) {
        console.error('Failed to fetch timeline:', err)
      }
    }

    fetchAgent()
    fetchTimeline()

    const websocket = new WebSocket(`ws://localhost:8000/ws/agents/${agentId}`)
    
    websocket.onopen = () => {
      console.log('WebSocket connected')
    }
    
    websocket.onmessage = (event: MessageEvent<string>) => {
      try {
        const data = JSON.parse(event.data) as TimelineEvent
        console.log('WebSocket event:', data)
        
        setTimeline((prev) => [...prev, data])
        
        if (['agent_completed', 'agent_failed', 'agent_started'].includes(data.action)) {
          void fetchAgent()
        }
      } catch (err) {
        console.error('Invalid WebSocket message:', err)
      }
    }
    
    websocket.onerror = (err) => {
      console.error('WebSocket error:', err)
    }
    
    websocket.onclose = () => {
      console.log('WebSocket closed')
    }
    
    setWs(websocket)

    return () => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.close()
      }
    }
  }, [agentId])

  const killAgent = async () => {
    if (!confirm('Are you sure you want to kill this agent?')) return
    
    try {
      const res = await fetch(`http://localhost:8000/api/agents/${agentId}/kill`, {
        method: 'POST'
      })
      if (!res.ok) throw new Error('Failed to kill agent')
      
      const agentRes = await fetch(`http://localhost:8000/api/agents/${agentId}`)
      const data = await agentRes.json() as Agent
      setAgent(data)
    } catch (err) {
      console.error('Failed to kill agent:', err)
      alert('Failed to kill agent. Please try again.')
    }
  }

  const resumeAgent = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/agents/${agentId}/resume`, {
        method: 'POST'
      })
      if (!res.ok) throw new Error('Failed to resume agent')
      
      const agentRes = await fetch(`http://localhost:8000/api/agents/${agentId}`)
      const data = await agentRes.json() as Agent
      setAgent(data)
    } catch (err) {
      console.error('Failed to resume agent:', err)
      alert('Failed to resume agent. Please try again.')
    }
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-red-800 font-semibold mb-2">Error</h2>
            <p className="text-red-700">{error}</p>
            <Link 
              href="/" 
              className="mt-4 inline-block px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Go Back Home
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (!agent) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-2xl mx-auto text-center">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-3/4 mx-auto mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
          </div>
        </div>
      </div>
    )
  }

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'running':
        return 'bg-blue-100 text-blue-800'
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'paused':
        return 'bg-yellow-100 text-yellow-800'
      case 'pending':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatActionName = (action: string): string => {
    return action
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  const progressPercentage = agent.total_steps > 0
    ? Math.round((agent.current_step / agent.total_steps) * 100)
    : 0

  return (
    <main className="min-h-screen bg-gray-50 p-4 sm:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
            <Link href="/" className="hover:text-gray-700">
              Home
            </Link>
            <span>/</span>
            <span>Agent {agentId.slice(0, 8)}</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold mb-2 break-words">
            {agent.task}
          </h1>
          <div className="flex flex-wrap items-center gap-3">
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                agent.status
              )}`}
            >
              {agent.status}
            </span>
            <span className="text-sm text-gray-600">
              Step {agent.current_step}/{agent.total_steps}
            </span>
            {agent.status === 'running' && (
              <span className="flex items-center gap-1 text-sm text-blue-600">
                <span className="animate-pulse">●</span>
                Running
              </span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Status */}
          <div className="lg:col-span-2 space-y-6">
            {/* Confidence */}
            {agent.confidence_score && agent.confidence_score > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="font-semibold mb-4">Confidence</h2>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-2xl font-bold">
                    {agent.confidence_score}%
                  </span>
                  <span className={agent.confidence_score >= 80 ? 'text-green-600' : 'text-yellow-600'}>
                    {agent.confidence_score >= 80 ? '✓ High confidence' : '⚠ Medium confidence'}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      agent.confidence_score >= 80 ? 'bg-green-500' : 'bg-yellow-500'
                    }`}
                    style={{ width: `${agent.confidence_score}%` }}
                  />
                </div>
              </div>
            )}

            {/* Timeline */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="font-semibold mb-4">Activity Timeline</h2>
              {timeline.length === 0 ? (
                <p className="text-gray-500 text-sm">No activity yet...</p>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {timeline
                    .slice()
                    .reverse()
                    .map((event, i) => {
                      const hasData = event.data && Object.keys(event.data).length > 0
                      let displayData = ''
                      
                      if (hasData && event.data) {
                        try {
                          const dataStr = JSON.stringify(event.data, null, 2)
                          displayData = dataStr.length > 100 
                            ? dataStr.slice(0, 100) + '...' 
                            : dataStr
                        } catch (e) {
                          displayData = '[Unable to display data]'
                        }
                      }

                      return (
                        <div
                          key={`${event.timestamp}-${i}`}
                          className="flex gap-3 text-sm border-b border-gray-100 pb-3 last:border-0"
                        >
                          <div className="w-20 shrink-0 text-xs text-gray-400">
                            {new Date(event.timestamp).toLocaleTimeString()}
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="font-medium">
                              {formatActionName(event.action)}
                            </div>
                            {hasData && (
                              <div className="mt-1 overflow-x-auto text-xs font-mono text-gray-600">
                                {displayData}
                              </div>
                            )}
                          </div>
                          {event.cost > 0 && (
                            <div className="w-16 shrink-0 text-right text-xs text-gray-500">
                              ${event.cost.toFixed(4)}
                            </div>
                          )}
                        </div>
                      )
                    })}
                </div>
              )}
            </div>

            {/* Result */}
            {agent.result && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="font-semibold mb-4">Result</h2>
                <div className="overflow-x-auto rounded bg-gray-50 p-4">
                  <pre className="whitespace-pre-wrap text-sm">
                    {typeof agent.result === 'string' 
                      ? agent.result 
                      : JSON.stringify(agent.result, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Error */}
            {agent.error && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-6">
                <h2 className="mb-2 font-semibold text-red-800">Error</h2>
                <p className="mb-4 text-red-700">{agent.error}</p>
                <button
                  onClick={resumeAgent}
                  className="rounded bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700"
                >
                  Resume from Checkpoint
                </button>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Metrics */}
            <div className="space-y-4 rounded-lg bg-white p-6 shadow">
              <div>
                <div className="text-sm text-gray-600">Total Cost</div>
                <div className="text-2xl font-bold">
                  ${agent.cost_usd.toFixed(4)}
                </div>
                {agent.estimated_cost_max && agent.estimated_cost_min && (
                  <div className="mt-1 text-xs text-gray-500">
                    Est: ${agent.estimated_cost_min.toFixed(2)} - $
                    {agent.estimated_cost_max.toFixed(2)}
                  </div>
                )}
              </div>

              <div>
                <div className="text-sm text-gray-600">Runtime</div>
                <div className="text-2xl font-bold">
                  {agent.runtime_seconds}s
                </div>
              </div>

              <div>
                <div className="text-sm text-gray-600">Progress</div>
                <div className="text-2xl font-bold">{progressPercentage}%</div>
                <div className="mt-2 h-1.5 w-full rounded-full bg-gray-200">
                  <div
                    className="h-1.5 rounded-full bg-blue-500 transition-all"
                    style={{ width: `${progressPercentage}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-3 rounded-lg bg-white p-6 shadow">
              <h3 className="mb-2 font-semibold">Actions</h3>

              {agent.status === 'running' && (
                <button
                  onClick={killAgent}
                  className="w-full rounded bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700"
                >
                  🛑 Kill Agent
                </button>
              )}

              {(agent.status === 'failed' || agent.status === 'paused') && (
                <button
                  onClick={resumeAgent}
                  className="w-full rounded bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
                >
                  ▶️ Resume Agent
                </button>
              )}

              <button 
                className="w-full rounded border border-gray-300 px-4 py-2 transition-colors hover:bg-gray-50"
                onClick={() => window.location.reload()}
              >
                🔄 Refresh
              </button>
            </div>

            {/* Connection Status */}
            <div className="rounded-lg bg-white p-4 shadow">
              <div className="flex items-center gap-2 text-sm">
                <span
                  className={`h-2 w-2 rounded-full ${
                    ws?.readyState === WebSocket.OPEN
                      ? 'bg-green-500'
                      : 'bg-red-500'
                  }`}
                />
                <span className="text-gray-600">
                  {ws?.readyState === WebSocket.OPEN
                    ? 'Connected'
                    : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}