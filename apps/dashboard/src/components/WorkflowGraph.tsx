import React from 'react';
import { 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  ShieldAlert, 
  RotateCcw, 
  Check, 
  X, 
  ArrowRight, 
  ArrowDown, 
  Sparkles,
  FileCode,
  Search,
  Database,
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
  // Determine highlight states
  const isPlanning = currentStatus === 'planning';
  const isExecuting = currentStatus === 'executing';
  const isWaitingApproval = currentStatus === 'waiting_approval' || requiresApproval;
  const isApproved = approvalStatus === 'approved';
  const isRejected = approvalStatus === 'rejected' || currentStatus === 'cancelled';
  const isVerified = currentStatus === 'verified' || currentStatus === 'completed';
  const isFailed = currentStatus === 'failed';

  return (
    <div className="nexus-card" style={{ padding: '24px', overflowX: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={18} color="#06b6d4" />
            LangGraph Orchestration State Machine
          </h3>
          <p style={{ fontSize: '12px', color: '#94a3b8' }}>
            State transitions, bounded retries, checkpoint interrupts, and verification gates
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '11px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#06b6d4' }}></span>
            Active Node
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }}></span>
            Completed
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b' }}></span>
            Approval Gate
          </span>
        </div>
      </div>

      {/* Visual Flowchart Representation */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', minWidth: '820px' }}>
        
        {/* Row 1: Pipeline Initiation */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '18px' }}>
          <div style={{
            padding: '10px 18px',
            borderRadius: '10px',
            background: isPlanning || currentStatus !== 'pending' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(30, 52, 92, 0.4)',
            border: `1px solid ${isPlanning ? '#06b6d4' : '#10b981'}`,
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            fontWeight: 600
          }}>
            <CheckCircle2 size={15} color="#10b981" />
            <span>1. Receive Task</span>
          </div>

          <ArrowRight size={18} color="#64748b" />

          <div style={{
            padding: '10px 18px',
            borderRadius: '10px',
            background: isPlanning ? 'rgba(6, 182, 212, 0.2)' : (plan && plan.length > 0 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(30, 52, 92, 0.4)'),
            border: `1px solid ${isPlanning ? '#06b6d4' : (plan && plan.length > 0 ? '#10b981' : 'rgba(56, 96, 160, 0.3)')}`,
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            fontWeight: 600
          }} className={isPlanning ? 'node-active' : ''}>
            <TerminalSquare size={15} color="#38bdf8" />
            <span>2. Classify & Plan ({plan ? plan.length : 0} steps)</span>
          </div>

          <ArrowRight size={18} color="#64748b" />

          <div style={{
            padding: '10px 18px',
            borderRadius: '10px',
            background: isExecuting ? 'rgba(6, 182, 212, 0.2)' : 'rgba(30, 52, 92, 0.4)',
            border: `1px solid ${isExecuting ? '#06b6d4' : 'rgba(56, 96, 160, 0.3)'}`,
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            fontWeight: 600
          }} className={isExecuting ? 'node-active' : ''}>
            <Search size={15} color="#a78bfa" />
            <span>3. Select Tool (Step {currentStepIndex + 1})</span>
          </div>
        </div>

        {/* Row 2: Validation & Execution Loop */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '18px' }}>
          <div style={{
            padding: '10px 18px',
            borderRadius: '10px',
            background: 'rgba(30, 52, 92, 0.4)',
            border: '1px solid rgba(56, 96, 160, 0.3)',
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            fontWeight: 600
          }}>
            <ShieldAlert size={15} color="#06b6d4" />
            <span>4. Validate Permissions & Inputs</span>
          </div>

          <ArrowRight size={18} color="#64748b" />

          <div style={{
            padding: '10px 18px',
            borderRadius: '10px',
            background: 'rgba(30, 52, 92, 0.4)',
            border: '1px solid rgba(56, 96, 160, 0.3)',
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            fontWeight: 600
          }}>
            <Cpu size={15} color="#60a5fa" />
            <span>5. Execute MCP Tool</span>
          </div>
        </div>

        {/* Row 3: Decision Gate (Approval Interrupt vs Safe Path) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '6px' }}>
          
          {/* Sensitive Action Branch */}
          <div style={{
            padding: '16px',
            borderRadius: '12px',
            background: isWaitingApproval ? 'rgba(245, 158, 11, 0.12)' : 'rgba(15, 27, 48, 0.5)',
            border: `1px solid ${isWaitingApproval ? '#f59e0b' : 'rgba(56, 96, 160, 0.25)'}`,
            position: 'relative'
          }} className={isWaitingApproval ? 'approval-gate-pulse' : ''}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: 700, color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <AlertTriangle size={16} />
                Human Approval Gate (Interrupt Checkpoint)
              </span>
              <span className={`badge ${isWaitingApproval ? 'badge-warning' : (isApproved ? 'badge-success' : 'badge-info')}`}>
                {isWaitingApproval ? 'PAUSED / WAITING' : (isApproved ? 'APPROVED' : (isRejected ? 'REJECTED' : 'READY'))}
              </span>
            </div>
            <p style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '12px' }}>
              LangGraph persistent checkpoint holds state on disk before allowing destructive source code patches or write mutations.
            </p>
            <div style={{ display: 'flex', gap: '10px' }}>
              <div style={{
                flex: 1,
                padding: '8px',
                borderRadius: '6px',
                background: isApproved ? 'rgba(16, 185, 129, 0.2)' : 'rgba(30, 52, 92, 0.3)',
                border: `1px solid ${isApproved ? '#10b981' : 'transparent'}`,
                fontSize: '11px',
                textAlign: 'center'
              }}>
                Approved: Apply Patch
              </div>
              <div style={{
                flex: 1,
                padding: '8px',
                borderRadius: '6px',
                background: isRejected ? 'rgba(244, 63, 94, 0.2)' : 'rgba(30, 52, 92, 0.3)',
                border: `1px solid ${isRejected ? '#f43f5e' : 'transparent'}`,
                fontSize: '11px',
                textAlign: 'center'
              }}>
                Rejected: Abort / Revise
              </div>
            </div>
          </div>

          {/* Failure Recovery & Retry Branch */}
          <div style={{
            padding: '16px',
            borderRadius: '12px',
            background: isFailed ? 'rgba(244, 63, 94, 0.12)' : 'rgba(15, 27, 48, 0.5)',
            border: `1px solid ${isFailed ? '#f43f5e' : 'rgba(56, 96, 160, 0.25)'}`
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <RotateCcw size={16} color="#60a5fa" />
                Transient Retry & Bounded Recovery
              </span>
              <span className="badge badge-info">3 Tries Max</span>
            </div>
            <p style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '12px' }}>
              Bounded exponential backoff retries transient timeouts. Fail-fast triggers on security violations or malformed queries.
            </p>
            {lastError && (
              <div style={{
                padding: '8px 10px',
                borderRadius: '6px',
                background: 'rgba(244, 63, 94, 0.15)',
                border: '1px solid rgba(244, 63, 94, 0.3)',
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
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '18px', marginTop: '10px' }}>
          <div style={{
            padding: '10px 18px',
            borderRadius: '10px',
            background: isVerified ? 'rgba(16, 185, 129, 0.2)' : 'rgba(30, 52, 92, 0.4)',
            border: `1px solid ${isVerified ? '#10b981' : 'rgba(56, 96, 160, 0.3)'}`,
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            fontWeight: 600
          }}>
            <CheckCircle2 size={15} color="#10b981" />
            <span>Verify Result (Unit Tests)</span>
          </div>

          <ArrowRight size={18} color="#64748b" />

          <div style={{
            padding: '10px 18px',
            borderRadius: '10px',
            background: isVerified ? 'rgba(16, 185, 129, 0.2)' : 'rgba(30, 52, 92, 0.4)',
            border: `1px solid ${isVerified ? '#10b981' : 'rgba(56, 96, 160, 0.3)'}`,
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            fontWeight: 600
          }}>
            <Clock size={15} color="#06b6d4" />
            <span>Evaluate & Trace Telemetry</span>
          </div>

          <ArrowRight size={18} color="#64748b" />

          <div style={{
            padding: '10px 18px',
            borderRadius: '10px',
            background: isVerified ? 'rgba(16, 185, 129, 0.2)' : (isFailed ? 'rgba(244, 63, 94, 0.2)' : 'rgba(30, 52, 92, 0.4)'),
            border: `1px solid ${isVerified ? '#10b981' : (isFailed ? '#f43f5e' : 'rgba(56, 96, 160, 0.3)')}`,
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            fontWeight: 600
          }}>
            <FileCode size={15} color="#a78bfa" />
            <span>Return Executive Report</span>
          </div>
        </div>

      </div>
    </div>
  );
};
