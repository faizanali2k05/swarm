import * as React from 'react'
import axios from 'axios'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

const API = import.meta.env.VITE_API_URL

export default function Dashboard(){
  console.debug('React hooks', { useState: typeof React.useState, useEffect: typeof React.useEffect, useMemo: typeof React.useMemo })
  const [status, setStatus] = React.useState({rounds:0, accuracies:[]})
  const [loading, setLoading] = React.useState(false)
  const [records, setRecords] = React.useState([])

  React.useEffect(()=>{ fetchAll(); const t = setInterval(fetchAll, 5000); return ()=>clearInterval(t) }, [])

  async function fetchAll(){
    try{
      const [s, c] = await Promise.all([axios.get(API + '/status'), axios.get(API + '/chain/records')])
      setStatus(s.data)
      setRecords(c.data)
    }catch(e){ console.warn('fetch failed', e) }
  }

  async function trigger(){
    setLoading(true)
    try{ await axios.post(API + '/simulate') }catch(e){ console.warn(e) }
    setTimeout(()=>{ fetchAll(); setLoading(false) }, 2000)
  }

  const contribs = React.useMemo(()=>{
    const map = {};
    (records || []).forEach(r=>{ map[r.nodeId] = (map[r.nodeId]||0)+1 })
    return Object.entries(map).map(([id,c])=>({id, count:c}))
  }, [records])

  const data = React.useMemo(()=>({
    labels: status.accuracies.map((_,i)=> 'R' + (i+1)),
    datasets: [{ label: 'Accuracy', data: status.accuracies, borderColor: '#60a5fa', backgroundColor: 'rgba(96,165,250,0.12)', tension:0.25 }]
  }), [status])

  return (
    <div className="container">
      <div className="navbar">
        <div className="logo">SwarmChain AI</div>
        <div className="navlinks small">Simulated Swarm Learning Dashboard</div>
      </div>

      <div className="grid">
        <div>
          <div className="card">
            <div className="metric">
              <div>
                <div className="small">Training Rounds</div>
                <div style={{fontSize:28,fontWeight:700}}>{status.rounds}</div>
              </div>
              <div>
                <div className="small">Latest Accuracy</div>
                <div style={{fontSize:20,fontWeight:600}}>{status.accuracies.length? (status.accuracies[status.accuracies.length-1]*100).toFixed(2)+ '%' : '—'}</div>
              </div>
              <div>
                <button className="btn" onClick={trigger} disabled={loading}>{loading? 'Starting...':'Trigger Simulation'}</button>
              </div>
            </div>
          </div>

          <div className="card">
            <h3 style={{marginTop:0}}>Accuracy Over Rounds</h3>
            <Line data={data} />
          </div>

          <div className="card">
            <h3 style={{marginTop:0}}>Notes</h3>
            <div className="small">This demo runs small local nodes that train briefly and submit flattened weights. The backend averages weights and optionally logs dataset hashes on-chain.</div>
          </div>
        </div>

        <div>
          <div className="card">
            <h4 style={{marginTop:0}}>Node Contributions</h4>
            <div className="contrib-list">
              {contribs.length===0 && <div className="small">No contributions yet.</div>}
              {contribs.map(c=> (
                <div key={c.id} style={{display:'flex',justifyContent:'space-between',padding:'6px 0'}}>
                  <div>Node {c.id}</div>
                  <div className="small">{c.count} record(s)</div>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h4 style={{marginTop:0}}>Recent Blockchain Records</h4>
            <div className="small">Hashes recorded on-chain (if contract configured)</div>
            <div style={{marginTop:8}}>
              {records.length===0 && <div className="small">No on-chain records</div>}
              {records.slice().reverse().slice(0,6).map((r,i)=> (
                <div key={i} style={{padding:'8px 0',borderBottom:'1px dashed rgba(255,255,255,0.03)'}}>
                  <div className="chain-record"><strong>Node</strong>: {r.nodeId}</div>
                  <div className="small">{r.dataHash}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
