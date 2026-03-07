      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">Current status</h2>
          <div className="flex items-center gap-2">
            <button onClick={() => { setLoading(true); fetchStatus().then(()=>setLoading(false)) }} className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm text-gray-200">Refresh</button>
          </div>
        </div>
        {loading && <p className="text-sm text-gray-500">Loading...</p>}
        {!loading && !status && <p className="text-sm text-gray-500">No status available.</p>}
  champion?: string
  challenger?: string
  metrics?: Record<string, number>
}

export default function PromotionPage() {
  const [status, setStatus] = useState<MLStatus | null>(null)
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  async function fetchStatus(){
    try{
      const res = await fetch('/api/ml/status');
      const j = await res.json();
      setStatus(j);
    }catch(e){
      setMessage('Failed to fetch status')
    }
  }

  useEffect(()=>{ fetchStatus() }, [])

  async function runBacktest(){
    setLoading(true)
              { (status as any).last_backtest && (
                <div className="text-xs text-gray-400 mt-3">Last backtest: <span className="text-sm text-gray-200">{new Date((status as any).last_backtest).toLocaleString()}</span></div>
              )}
    setMessage('Running backtest...')
    try{
      const res = await fetch('/api/ml/backtest', {method: 'POST', headers:{'content-type':'application/json','authorization': process.env.NEXT_PUBLIC_ADMIN_TOKEN ? `Bearer ${process.env.NEXT_PUBLIC_ADMIN_TOKEN}` : ''}, body: JSON.stringify({model_name: status.challenger})})
      const j = await res.json()
      setMessage('Backtest finished: ' + JSON.stringify(j.backtest || j))
    }catch(e){ setMessage('Backtest failed') }
    setLoading(false)
          <button onClick={runBacktest} disabled={loading || !status?.challenger} className="w-full px-3 py-2 bg-indigo-600 hover:bg-indigo-500 rounded text-white font-semibold">Backtest Challenger</button>
        if (!res.ok) return
        const data = await res.json()
          <button onClick={promote} disabled={loading || !status?.challenger} className="w-full px-3 py-2 bg-green-600 hover:bg-green-500 rounded text-white font-semibold">Promote Challenger</button>
  async function promote(){
        // ignore
          <button onClick={applyCheckpoint} disabled={loading} className="w-full px-3 py-2 bg-yellow-600 hover:bg-yellow-500 rounded text-white font-semibold">Apply Checkpoint</button>
    try{
      const res = await fetch('/api/ml/promote', {method:'POST', headers:{'content-type':'application/json','authorization': process.env.NEXT_PUBLIC_ADMIN_TOKEN ? `Bearer ${process.env.NEXT_PUBLIC_ADMIN_TOKEN}` : ''}, body: JSON.stringify({require_backtest: false})})
      const j = await res.json()
        <em className="text-sm text-gray-300">{message}</em>
    }catch(e){ setMessage('Promote failed') }
    setLoading(false)
    fetchStatus()
  }

  async function applyCheckpoint(){
    const name = prompt('Checkpoint name to apply as challenger:')
    if(!name) return
    setLoading(true)
    try{
      const res = await fetch('/api/ml/apply_checkpoint', {method:'POST', headers:{'content-type':'application/json','authorization': process.env.NEXT_PUBLIC_ADMIN_TOKEN ? `Bearer ${process.env.NEXT_PUBLIC_ADMIN_TOKEN}` : ''}, body: JSON.stringify({name})})
      const j = await res.json()
      setMessage('Apply checkpoint: ' + JSON.stringify(j))
    }catch(e){ setMessage('Apply failed') }
    setLoading(false)
    fetchStatus()
  }

  return (
    <div style={{padding:20}}>
      <h1>Model Promotion</h1>
      <div>
        <strong>Champion:</strong> {status.champion || '—'}
      </div>
      <div>
        <strong>Challenger:</strong> {status.challenger || '—'}
      </div>
      <div style={{marginTop:12}}>
        <button onClick={runBacktest} disabled={loading || !status.challenger}>Backtest Challenger</button>{' '}
        <button onClick={promote} disabled={loading || !status.challenger}>Promote Challenger</button>{' '}
        <button onClick={applyCheckpoint} disabled={loading}>Apply Checkpoint</button>
      </div>
      <div style={{marginTop:12}}>
        <em>{message}</em>
      </div>
    </div>
  )
}
