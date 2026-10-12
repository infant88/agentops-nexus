import React from 'react';
import { 
  Terminal, 
  ShieldCheck, 
  BarChart3, 
  Activity, 
  Cpu, 
  Layers,
  Lock,
  FileText
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  pendingApprovalsCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, pendingApprovalsCount }) => {
  return (
    <header style={{
      borderBottom: '1px solid #1e293b',
      background: '#090d16',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      padding: '12px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }}>
      {/* Brand & Technical Subtitle */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '34px',
          height: '34px',
          borderRadius: '4px',
          background: '#0f172a',
          border: '1px solid #334155',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Cpu size={18} color="#38bdf8" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontWeight: 700, fontSize: '16px', letterSpacing: '-0.01em', color: '#f8fafc' }}>
              AgentOps Nexus
            </span>
            <span className="badge badge-info" style={{ fontSize: '10px' }}>v1.0</span>
          </div>
          <p style={{ fontSize: '11px', color: '#64748b' }}>
            LangGraph Orchestration, MCP Tools, Checkpointed Approvals, Observability
          </p>
        </div>
      </div>

      {/* Navigation Tabs (Rectangular buttons, no pill shapes, no purple) */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        <button
          onClick={() => setActiveTab('orchestrator')}
          className={`btn-secondary ${activeTab === 'orchestrator' ? 'nexus-card-active' : ''}`}
          style={{
            fontSize: '12px',
            padding: '6px 12px',
            background: activeTab === 'orchestrator' ? '#17223b' : 'transparent',
            borderColor: activeTab === 'orchestrator' ? '#0284c7' : 'transparent'
          }}
        >
          <Terminal size={14} color={activeTab === 'orchestrator' ? '#38bdf8' : '#94a3b8'} />
          <span>Orchestrator</span>
        </button>

        <button
          onClick={() => setActiveTab('approvals')}
          className={`btn-secondary ${activeTab === 'approvals' ? 'nexus-card-active' : ''}`}
          style={{
            fontSize: '12px',
            padding: '6px 12px',
            background: activeTab === 'approvals' ? '#17223b' : 'transparent',
            borderColor: activeTab === 'approvals' ? '#d97706' : 'transparent',
            position: 'relative'
          }}
        >
          <ShieldCheck size={14} color={activeTab === 'approvals' ? '#fbbf24' : '#94a3b8'} />
          <span>Approval Gate</span>
          {pendingApprovalsCount > 0 && (
            <span style={{
              background: '#e11d48',
              color: '#fff',
              fontSize: '10px',
              padding: '1px 5px',
              borderRadius: '2px',
              fontWeight: 700,
              marginLeft: '4px'
            }}>
              {pendingApprovalsCount}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('evaluation')}
          className={`btn-secondary ${activeTab === 'evaluation' ? 'nexus-card-active' : ''}`}
          style={{
            fontSize: '12px',
            padding: '6px 12px',
            background: activeTab === 'evaluation' ? '#17223b' : 'transparent',
            borderColor: activeTab === 'evaluation' ? '#10b981' : 'transparent'
          }}
        >
          <BarChart3 size={14} color={activeTab === 'evaluation' ? '#34d399' : '#94a3b8'} />
          <span>Evaluation (40 Cases)</span>
        </button>

        <button
          onClick={() => setActiveTab('observability')}
          className={`btn-secondary ${activeTab === 'observability' ? 'nexus-card-active' : ''}`}
          style={{
            fontSize: '12px',
            padding: '6px 12px',
            background: activeTab === 'observability' ? '#17223b' : 'transparent',
            borderColor: activeTab === 'observability' ? '#0ea5e9' : 'transparent'
          }}
        >
          <Activity size={14} color={activeTab === 'observability' ? '#38bdf8' : '#94a3b8'} />
          <span>Traces & Audits</span>
        </button>

        <button
          onClick={() => setActiveTab('mcp')}
          className={`btn-secondary ${activeTab === 'mcp' ? 'nexus-card-active' : ''}`}
          style={{
            fontSize: '12px',
            padding: '6px 12px',
            background: activeTab === 'mcp' ? '#17223b' : 'transparent',
            borderColor: activeTab === 'mcp' ? '#334155' : 'transparent'
          }}
        >
          <Layers size={14} color={activeTab === 'mcp' ? '#cbd5e1' : '#94a3b8'} />
          <span>MCP Tools</span>
        </button>

        <button
          onClick={() => setActiveTab('privacy')}
          className={`btn-secondary ${activeTab === 'privacy' ? 'nexus-card-active' : ''}`}
          style={{
            fontSize: '12px',
            padding: '6px 12px',
            background: activeTab === 'privacy' ? '#17223b' : 'transparent',
            borderColor: activeTab === 'privacy' ? '#334155' : 'transparent'
          }}
        >
          <FileText size={14} color={activeTab === 'privacy' ? '#cbd5e1' : '#94a3b8'} />
          <span>Privacy</span>
        </button>

        <button
          onClick={() => setActiveTab('terms')}
          className={`btn-secondary ${activeTab === 'terms' ? 'nexus-card-active' : ''}`}
          style={{
            fontSize: '12px',
            padding: '6px 12px',
            background: activeTab === 'terms' ? '#17223b' : 'transparent',
            borderColor: activeTab === 'terms' ? '#334155' : 'transparent'
          }}
        >
          <span>Terms</span>
        </button>
      </nav>

      {/* Status Badges */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#10b981' }}>
          <span style={{ width: '7px', height: '7px', borderRadius: '2px', background: '#10b981', display: 'inline-block' }}></span>
          <span style={{ fontWeight: 600 }}>LangGraph Active</span>
        </div>
        <div style={{ width: '1px', height: '16px', background: '#1e293b' }}></div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px', color: '#94a3b8' }}>
          <Lock size={12} color="#0ea5e9" />
          <span>Sandbox Boundary</span>
        </div>
      </div>
    </header>
  );
};
