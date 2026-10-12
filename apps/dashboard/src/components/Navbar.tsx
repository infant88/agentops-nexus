import React from 'react';
import { 
  Terminal, 
  ShieldCheck, 
  BarChart3, 
  Activity, 
  Cpu, 
  CheckCircle2,
  Lock,
  Layers
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  pendingApprovalsCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, pendingApprovalsCount }) => {
  return (
    <header style={{
      borderBottom: '1px solid rgba(56, 96, 160, 0.25)',
      background: 'rgba(7, 13, 24, 0.85)',
      backdropFilter: 'blur(20px)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      padding: '12px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }}>
      {/* Brand & Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 18px rgba(99, 102, 241, 0.45)'
        }}>
          <Cpu size={22} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontWeight: 800, fontSize: '18px', letterSpacing: '-0.02em', color: '#f8fafc' }}>
              AgentOps <span style={{ color: '#38bdf8' }}>Nexus</span>
            </span>
            <span className="badge badge-info" style={{ fontSize: '10px' }}>v1.0 Production</span>
          </div>
          <p style={{ fontSize: '12px', color: '#94a3b8' }}>
            Evaluated AI Agent Platform · LangGraph · MCP · Guardrails
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <button
          onClick={() => setActiveTab('orchestrator')}
          className={`btn-secondary ${activeTab === 'orchestrator' ? 'nexus-card-active' : ''}`}
          style={{
            fontSize: '13px',
            padding: '7px 14px',
            background: activeTab === 'orchestrator' ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
            borderColor: activeTab === 'orchestrator' ? '#6366f1' : 'transparent'
          }}
        >
          <Terminal size={15} color={activeTab === 'orchestrator' ? '#818cf8' : '#94a3b8'} />
          <span>Orchestrator</span>
        </button>

        <button
          onClick={() => setActiveTab('approvals')}
          className={`btn-secondary ${activeTab === 'approvals' ? 'nexus-card-active' : ''}`}
          style={{
            fontSize: '13px',
            padding: '7px 14px',
            background: activeTab === 'approvals' ? 'rgba(245, 158, 11, 0.2)' : 'transparent',
            borderColor: activeTab === 'approvals' ? '#f59e0b' : 'transparent',
            position: 'relative'
          }}
        >
          <ShieldCheck size={15} color={activeTab === 'approvals' ? '#fbbf24' : '#94a3b8'} />
          <span>Approval Gate</span>
          {pendingApprovalsCount > 0 && (
            <span style={{
              background: '#f43f5e',
              color: '#fff',
              fontSize: '10px',
              padding: '1px 6px',
              borderRadius: '999px',
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
            fontSize: '13px',
            padding: '7px 14px',
            background: activeTab === 'evaluation' ? 'rgba(16, 185, 129, 0.2)' : 'transparent',
            borderColor: activeTab === 'evaluation' ? '#10b981' : 'transparent'
          }}
        >
          <BarChart3 size={15} color={activeTab === 'evaluation' ? '#34d399' : '#94a3b8'} />
          <span>Evaluation (40 Cases)</span>
        </button>

        <button
          onClick={() => setActiveTab('observability')}
          className={`btn-secondary ${activeTab === 'observability' ? 'nexus-card-active' : ''}`}
          style={{
            fontSize: '13px',
            padding: '7px 14px',
            background: activeTab === 'observability' ? 'rgba(6, 182, 212, 0.2)' : 'transparent',
            borderColor: activeTab === 'observability' ? '#06b6d4' : 'transparent'
          }}
        >
          <Activity size={15} color={activeTab === 'observability' ? '#38bdf8' : '#94a3b8'} />
          <span>Traces & Audits</span>
        </button>

        <button
          onClick={() => setActiveTab('mcp')}
          className={`btn-secondary ${activeTab === 'mcp' ? 'nexus-card-active' : ''}`}
          style={{
            fontSize: '13px',
            padding: '7px 14px',
            background: activeTab === 'mcp' ? 'rgba(139, 92, 246, 0.2)' : 'transparent',
            borderColor: activeTab === 'mcp' ? '#8b5cf6' : 'transparent'
          }}
        >
          <Layers size={15} color={activeTab === 'mcp' ? '#c084fc' : '#94a3b8'} />
          <span>MCP & Sandbox</span>
        </button>
      </nav>

      {/* Status Badges */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#10b981' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', display: 'inline-block', boxShadow: '0 0 8px #10b981' }}></span>
          <span style={{ fontWeight: 600 }}>LangGraph Active</span>
        </div>
        <div style={{ width: '1px', height: '18px', background: 'rgba(56, 96, 160, 0.3)' }}></div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px', color: '#94a3b8' }}>
          <Lock size={12} color="#06b6d4" />
          <span>MCP Sandbox Jail</span>
        </div>
      </div>
    </header>
  );
};
