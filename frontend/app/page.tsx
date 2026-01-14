'use client'

import { useState } from 'react'

export default function Home() {
  const [task, setTask] = useState('')
  const [agentId, setAgentId] = useState('')
  const [loading, setLoading] = useState(false)

  const startAgent = async () => {
    setLoading(true)
    try {
      const res = await fetch('http://localhost:8000/api/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task })
      })
      const data = await res.json()
      setAgentId(data.id)
      // Redirect to agent page
      window.location.href = `/agents/${data.id}`
    } catch (error) {
      console.error('Failed to start agent:', error)
    }
    setLoading(false)
  }

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold mb-2">AgentOS</h1>
        <p className="text-gray-600 mb-8">
          AI agents you can trust to run unattended
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              What should the agent do?
            </label>
            <textarea
              className="w-full p-3 border rounded-lg"
              rows={4}
              placeholder="Research competitor pricing and create a comparison report..."
              value={task}
              onChange={(e) => setTask(e.target.value)}
            />
          </div>

          <button
            onClick={startAgent}
            disabled={!task || loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300"
          >
            {loading ? 'Starting...' : 'Start Agent'}
          </button>
        </div>
      </div>
    </main>
  )
}