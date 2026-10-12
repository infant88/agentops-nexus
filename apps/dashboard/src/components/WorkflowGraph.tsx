import React from 'react';
import { 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  ShieldAlert, 
  RotateCcw, 
  ArrowRight, 
  FileCode, 
  Search, 
  TerminalSquare,
  Cpu
} from 'lucide-react';

interface WorkflowGraphProps {
  currentStatus: string;
  currentStepIndex: number;
  plan: any[];
  requiresApproval: boolean;
  approvalStatus: string;
  lastError?: string | null;
}

export const WorkflowGraph: React.FC<WorkflowGraphProps> = ({
  currentStatus,
  currentStepIndex,
  plan,
  requiresApproval,
  approvalStatus,
  lastError
}) => {
  const isPlanning = currentStatus === 'planning';
  const isExecuting = currentStatus === 'executing';
  const isWaitingApproval = currentStatus === 'waiting_approval' || requiresApproval;
  const isApproved = approvalStatus === 'approved';
  const isRejected = approvalStatus === 'rejected' || currentStatus === 'cancelled';
  const isVerified = currentStatus === 'verified' || currentStatus === 'completed';
  const isFailed = currentStatus === 'failed';

  return (
    <div className="nexus-card" style={{ padding: '20px', overflowX: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div>
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Cpu size={17} color="#0ea5e9" />
            <span>LangGraph Orchestration State Machine</span>
          </h3>
          <p style={{ fontSize: '12px', color: '#64748b' }}>
            Deterministic state transitions, bounded retries, checkpoint interrupts, and test verification
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '11px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '7px', height: '7px', borderRadius: '2px', background: '#0ea5e9' }}></span>
            Active Node
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '7px', height: '7px', borderRadius: '2px', background: '#10b981' }}></span>
            Completed
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '7px', height: '7px', borderRadius: '2px', background: '#d97706' }}></span>
            Approval Checkpoint
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', minWidth: '820px' }}>
        
        {/* Row 1: Pipeline Initiation */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '14px' }}>
          <div style={{
            padding: '9px 16px',
            borderRadius: '4px',
            background: isPlanning || currentStatus !== 'pending' ? 'rgba(16, 185, 129, 0.12)' : '#0d1322',
            border: `1px solid ${isPlanning ? '#0ea5e9' : '#10b981'}`,
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            fontWeight: 600
          }}>
            <CheckCircle2 size={14} color="#10b981" />
            <span>1. Receive Task</span>
          </div>

          <ArrowRight size={16} color="#475569" />

          <div style={{
            padding: '9px 16px',
            borderRadius: '4px',
            background: isPlanning ? 'rgba(14, 165, 233, 0.12)' : (plan && plan.length > 0 ? 'rgba(16, 185, 129, 0.12)' : '#0d1322'),
            border: `1px solid ${isPlanning ? '#0ea5e9' : (plan && plan.length > 0 ? '#10b981' : '#1e293b')}`,
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            fontWeight: 600
          }} className={isPlanning ? 'node-active' : ''}>
            <TerminalSquare size={14} color="#38bdf8" />
            <span>2. Classify & Plan ({plan ? plan.length : 0} steps)</span>
          </div>

          <ArrowRight size={16} color="#475569" />

          <div style={{
            padding: '9px 16px',
            borderRadius: '4px',
            background: isExecuting ? 'rgba(14, 165, 233, 0.12)' : '#0d1322',
            border: `1px solid ${isExecuting ? '#0ea5e9' : '#1e293b'}`,
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            fontWeight: 600
          }} className={isExecuting ? 'node-active' : ''}>
            <Search size={14} color="#38bdf8" />
            <span>3. Select Tool (Step {currentStepIndex + 1})</span>
          </div>
        </div>

        {/* Row 2: Validation & Execution Loop */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '14px' }}>
          <div style={{
            padding: '9px 16px',
            borderRadius: '4px',
            background: '#0d1322',
            border: '1px solid #1e293b',
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            fontWeight: 600
          }}>
            <ShieldAlert size={14} color="#0ea5e9" />
            <span>4. Validate Permissions & Inputs</span>
          </div>

          <ArrowRight size={16} color="#475569" />

          <div style={{
            padding: '9px 16px',
            borderRadius: '4px',
            background: '#0d1322',
            border: '1px solid #1e293b',
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            fontWeight: 600
          }}>
            <Cpu size={14} color="#38bdf8" />
            <span>5. Execute MCP Tool</span>
          </div>
        </div>

        {/* Row 3: Decision Gate (Approval Interrupt vs Safe Path) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '4px' }}>
          
          {/* Sensitive Action Branch */}
          <div style={{
            padding: '14px',
            borderRadius: '4px',
            background: isWaitingApproval ? 'rgba(217, 119, 6, 0.08)' : '#0d1322',
            border: `1px solid ${isWaitingApproval ? '#d97706' : '#1e293b'}`
          }} className={isWaitingApproval ? 'approval-gate-active' : ''}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <AlertTriangle size={15} />
                Human Approval Gate (Interrupt Checkpoint)
              </span>
              <span className={`badge ${isWaitingApproval ? 'badge-warning' : (isApproved ? 'badge-success' : 'badge-neutral')}`}>
                {isWaitingApproval ? 'PAUSED / WAITING' : (isApproved ? 'APPROVED' : (isRejected ? 'REJECTED' : 'IDLE'))}
              </span>
            </div>
            <p style={{ fontSize: '11px', color: '#64748b', marginBottom: '10px' }}>
              LangGraph checkpointer serializes execution state to disk before applying file patch mutations.
            </p>
            <div style={{ display: 'flex', gap: '8px' }}>
              <div style={{
                flex: 1,
                padding: '6px',
                borderRadius: '4px',
                background: isApproved ? 'rgba(16, 185, 129, 0.15)' : '#090d16',
                border: `1px solid ${isApproved ? '#10b981' : '#1e293b'}`,
                fontSize: '11px',
                textAlign: 'center',
                color: isApproved ? '#34d399' : '#94a3b8'
              }}>
                Approved: Apply Patch
              </div>
              <div style={{
                flex: 1,
                padding: '6px',
                borderRadius: '4px',
                background: isRejected ? 'rgba(225, 29, 72, 0.15)' : '#090d16',
                border: `1px solid ${isRejected ? '#e11d48' : '#1e293b'}`,
                fontSize: '11px',
                textAlign: 'center',
                color: isRejected ? '#fb7185' : '#94a3b8'
              }}>
                Rejected: Abort / Revise
              </div>
            </div>
          </div>

          {/* Failure Recovery & Retry Branch */}
          <div style={{
            padding: '14px',
            borderRadius: '4px',
            background: isFailed ? 'rgba(225, 29, 72, 0.08)' : '#0d1322',
            border: `1px solid ${isFailed ? '#e11d48' : '#1e293b'}`
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <RotateCcw size={15} color="#38bdf8" />
                Transient Retry & Bounded Recovery
              </span>
              <span className="badge badge-neutral">Max 3 Retries</span>
            </div>
            <p style={{ fontSize: '11px', color: '#64748b', marginBottom: '10px' }}>
              Bounded exponential backoff handles transient network errors. Zero retries on permission or security violations.
            </p>
            {lastError && (
              <div style={{
                padding: '6px 8px',
                borderRadius: '4px',
                background: 'rgba(225, 29, 72, 0.1)',
                border: '1px solid rgba(225, 29, 72, 0.25)',
                fontSize: '11px',
                color: '#fca5a5',
                fontFamily: 'monospace'
              }}>
                {lastError}
              </div>
            )}
          </div>
        </div>

        {/* Row 4: Terminal Pipeline Stages */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '14px', marginTop: '6px' }}>
          <div style={{
            padding: '9px 16px',
            borderRadius: '4px',
            background: isVerified ? 'rgba(16, 185, 129, 0.12)' : '#0d1322',
            border: `1px solid ${isVerified ? '#10b981' : '#1e293b'}`,
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            fontWeight: 600
          }}>
            <CheckCircle2 size={14} color="#10b981" />
            <span>Verify Result (Unit Tests)</span>
          </div>

          <ArrowRight size={16} color="#475569" />

          <div style={{
            padding: '9px 16px',
            borderRadius: '4px',
            background: isVerified ? 'rgba(16, 185, 129, 0.12)' : '#0d1322',
            border: `1px solid ${isVerified ? '#10b981' : '#1e293b'}`,
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            fontWeight: 600
          }}>
            <Clock size={14} color="#0ea5e9" />
            <span>Evaluate & Trace Telemetry</span>
          </div>

          <ArrowRight size={16} color="#475569" />

          <div style={{
            padding: '9px 16px',
            borderRadius: '4px',
            background: isVerified ? 'rgba(16, 185, 129, 0.12)' : (isFailed ? 'rgba(225, 29, 72, 0.12)' : '#0d1322'),
            border: `1px solid ${isVerified ? '#10b981' : (isFailed ? '#e11d48' : '#1e293b')}`,
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            fontWeight: 600
          }}>
            <FileCode size={14} color="#cbd5e1" />
            <span>Return Executive Report</span>
          </div>
        </div>

      </div>
    </div>
  );
};
