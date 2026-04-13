import React, {useEffect, useState} from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL

export default function Blockchain(){
  const [records, setRecords] = useState([])

  useEffect(()=>{ fetch(); const t = setInterval(fetch, 5000); return ()=>clearInterval(t) }, [])

  async function fetch(){
    try{
      const r = await axios.get(API + '/chain/records')
      setRecords(r.data)
    }catch(e){ setRecords([]) }
  }

  return (
    <div className="container">
      <div className="navbar">
        <div className="logo">SwarmChain AI</div>
        <div className="navlinks small">Blockchain Records</div>
      </div>

      <div className="card">
        <h3 style={{marginTop:0}}>Stored Hashes</h3>
        {records.length===0 && <div className="small">No records on-chain (or contract not configured).</div>}
        {records.slice().reverse().map((r,i)=> (
          <div key={i} style={{padding:'10px 0',borderBottom:'1px solid rgba(255,255,255,0.02)'}}>
            <div><strong>Node:</strong> {r.nodeId} <span className="small" style={{marginLeft:10}}>ts: {r.timestamp}</span></div>
            <div className="small chain-record">{r.dataHash}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
