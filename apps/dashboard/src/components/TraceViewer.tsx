import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Clock, 
  ShieldCheck, 
  Copy, 
  Check, 
  FileJson, 
  Lock, 
  ChevronRight, 
  ChevronDown 
} from 'lucide-react';

interface TraceViewerProps {
  taskId: string;
}

export const TraceViewer: React.FC<TraceViewerProps> = ({ taskId }) => {
  const [traceData, setTraceData] = useState<any>(null);
  const [auditEvents, setAuditEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<'waterfall' | 'audit' | 'raw'>('waterfall');

  useEffect(() => {
    if (!taskId) return;
    const fetchTelemetry = async () => {
      setLoading(true);
      try {
        const [traceRes, auditRes] = await Promise.all([
          fetch(`/api/tasks/${taskId}/trace`),
          fetch(`/api/tasks/${taskId}/audit`)
        ]);

        if (traceRes.ok) {
          const t = await traceRes.json();
          setTraceData(t);
        }
        if (auditRes.ok) {
          const a = await auditRes.json();
          setAuditEvents(a);
        }
      } catch (e) {
        console.error('Failed to load telemetry', e);
      } finally {
        setLoading(false);
      }
    };

    fetchTelemetry();
  }, [taskId]);

  const copyRaw = () => {
    if (!traceData) return;
    navigator.clipboard.writeText(JSON.stringify(traceData, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const spans = traceData?.spans || [];
  const maxDuration = Math.max(...spans.map((s: any) => s.duration_ms || 1), 1);

  return (
    <div className="nexus-card" style={{ padding: '24px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} color="#06b6d4" />
            <span>Observability & Execution Traces</span>
          </h3>
          <p style={{ fontSize: '12px', color: '#94a3b8' }}>
            OpenTelemetry & LangSmith trace tree, span latencies, and redacted audit events for task: <code>{taskId}</code>
          </p>
        </div>

        {/* View Switcher Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => setViewMode('waterfall')}
            className={`btn-secondary ${viewMode === 'waterfall' ? 'nexus-card-active' : ''}`}
            style={{ fontSize: '12px', padding: '6px 12px' }}
          >
            Span Waterfall
          </button>
          <button
            onClick={() => setViewMode('audit')}
            className={`btn-secondary ${viewMode === 'audit' ? 'nexus-card-active' : ''}`}
            style={{ fontSize: '12px', padding: '6px 12px' }}
          >
            Audit Trail ({auditEvents.length})
          </button>
          <button
            onClick={() => setViewMode('raw')}
            className={`btn-secondary ${viewMode === 'raw' ? 'nexus-card-active' : ''}`}
            style={{ fontSize: '12px', padding: '6px 12px' }}
          >
            <FileJson size={13} />
            LangSmith JSON
          </button>
        </div>
      </div>

      {/* Telemetry Summary Bar */}
      {traceData && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '10px',
          padding: '12px 16px',
          background: 'rgba(15, 23, 42, 0.5)',
          borderRadius: '10px',
          marginBottom: '20px',
          border: '1px solid rgba(56, 96, 160, 0.2)'
        }}>
          <div>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Total Latency</span>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc' }}>
              {traceData.total_latency_ms} ms
            </div>
          </div>
          <div>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Total Spans</span>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#38bdf8' }}>
              {spans.length}
            </div>
          </div>
          <div>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Input Tokens</span>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#cbd5e1' }}>
              {traceData.tokens?.input || 0}
            </div>
          </div>
          <div>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Output Tokens</span>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#cbd5e1' }}>
              {traceData.tokens?.output || 0}
            </div>
          </div>
          <div>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Estimated Cost</span>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#34d399' }}>
              ${traceData.estimated_cost_usd || 0.00015}
            </div>
          </div>
        </div>
      )}

      {/* Mode 1: Waterfall */}
      {viewMode === 'waterfall' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {spans.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '30px', color: '#94a3b8', fontSize: '13px' }}>
              No trace spans captured yet. Submit a task in the Orchestrator tab to generate traces.
            </div>
          ) : (
            spans.map((span: any, idx: number) => {
              const barPercent = Math.max(8, (span.duration_ms / maxDuration) * 100);
              return (
                <div
                  key={span.id || idx}
                  style={{
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: 'rgba(11, 19, 36, 0.6)',
                    border: '1px solid rgba(56, 96, 160, 0.2)'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 600, fontSize: '13px', color: '#f8fafc' }}>
                        {span.node_name}
                      </span>
                      <span className={`badge ${span.status === 'success' ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '9px' }}>
                        {span.status}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '11px', color: '#94a3b8' }}>
                      <span>{span.duration_ms} ms</span>
                      <span>{span.tokens_in + span.tokens_out} tok</span>
                      <span>${span.cost_usd}</span>
                    </div>
                  </div>

                  {/* Relative Timeline Bar */}
                  <div style={{ width: '100%', height: '5px', background: 'rgba(15, 23, 42, 0.8)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{
                      width: `${barPercent}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #6366f1, #06b6d4)',
                      borderRadius: '3px'
                    }}></div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Mode 2: Audit Trail */}
      {viewMode === 'audit' && (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(56, 96, 160, 0.3)', color: '#94a3b8' }}>
                <th style={{ padding: '8px 10px' }}>Timestamp</th>
                <th style={{ padding: '8px 10px' }}>Event Type</th>
                <th style={{ padding: '8px 10px' }}>Tool</th>
                <th style={{ padding: '8px 10px' }}>Outcome</th>
                <th style={{ padding: '8px 10px' }}>Parameters (Redacted)</th>
              </tr>
            </thead>
            <tbody>
              {auditEvents.map((e: any) => (
                <tr key={e.id} style={{ borderBottom: '1px solid rgba(56, 96, 160, 0.15)' }}>
                  <td style={{ padding: '8px 10px', color: '#64748b', whiteSpace: 'nowrap' }}>
                    {e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : 'now'}
                  </td>
                  <td style={{ padding: '8px 10px', fontWeight: 600, color: '#cbd5e1' }}>
                    {e.event_type}
                  </td>
                  <td style={{ padding: '8px 10px', color: '#38bdf8' }}>
                    {e.tool_name || '-'}
                  </td>
                  <td style={{ padding: '8px 10px' }}>
                    <span className={`badge ${e.outcome === 'success' ? 'badge-success' : (e.outcome === 'blocked' ? 'badge-warning' : 'badge-info')}`} style={{ fontSize: '9px' }}>
                      {e.outcome}
                    </span>
                  </td>
                  <td style={{ padding: '8px 10px', color: '#94a3b8', fontFamily: 'monospace', maxWidth: '350px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {JSON.stringify(e.parameters || {})}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Mode 3: Raw LangSmith JSON */}
      {viewMode === 'raw' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '8px' }}>
            <button
              onClick={copyRaw}
              className="btn-secondary"
              style={{ fontSize: '12px', padding: '5px 12px' }}
            >
              {copied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
              <span>{copied ? 'Copied Trace JSON' : 'Copy LangSmith JSON'}</span>
            </button>
          </div>
          <pre style={{
            background: '#040812',
            padding: '16px',
            borderRadius: '10px',
            fontSize: '12px',
            color: '#34d399',
            overflowX: 'auto',
            maxHeight: '400px',
            border: '1px solid rgba(56, 96, 160, 0.3)'
          }}>
            {JSON.stringify(traceData, null, 2)}
          </pre>
        </div>
      )}

    </div>
  );
};
