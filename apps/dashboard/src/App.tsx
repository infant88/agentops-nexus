import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { WorkflowGraph } from './components/WorkflowGraph';
import { TaskConsole } from './components/TaskConsole';
import { ApprovalModal } from './components/ApprovalModal';
import { EvaluationSuite } from './components/EvaluationSuite';
import { TraceViewer } from './components/TraceViewer';
import { MCPExplorer } from './components/MCPExplorer';
import { PrivacyPolicy } from './components/PrivacyPolicy';
import { TermsConditions } from './components/TermsConditions';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'orchestrator' | 'approvals' | 'evaluation' | 'observability' | 'mcp' | 'privacy' | 'terms'>('orchestrator');
  const [currentTask, setCurrentTask] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [approvalLoading, setApprovalLoading] = useState(false);

  // Submit new task
  const handleTaskSubmit = async (objective: string) => {
    setLoading(true);
    try {
      const res = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ objective })
      });

      if (res.ok) {
        const data = await res.json();
        setCurrentTask(data);
      }
    } catch (err) {
      console.error('Task submission error', err);
    } finally {
      setLoading(false);
    }
  };

  // Human decision submitted on approval gate
  const handleApprovalDecision = async (
    decision: 'approved' | 'rejected' | 'revision_requested',
    feedback: string
  ) => {
    if (!currentTask?.task_id) return;
    setApprovalLoading(true);

    try {
      const res = await fetch(`/api/tasks/${currentTask.task_id}/approval`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, feedback })
      });

      if (res.ok) {
        const data = await res.json();
        setCurrentTask((prev: any) => ({
          ...prev,
          status: data.status,
          approval_status: data.approval_status,
          approval_required: false,
          execution_history: data.execution_history,
          verification_result: data.verification_result,
          final_report: data.final_report
        }));
      }
    } catch (err) {
      console.error('Approval submission error', err);
    } finally {
      setApprovalLoading(false);
    }
  };

  const isApprovalPending = currentTask?.approval_required && currentTask?.status === 'waiting_approval';

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={(tab: any) => setActiveTab(tab)}
        pendingApprovalsCount={isApprovalPending ? 1 : 0}
      />

      {/* Main Container */}
      <main style={{ flex: 1, maxWidth: '1440px', width: '100%', margin: '0 auto', padding: '24px' }}>
        
        {/* Tab 1: Orchestrator */}
        {activeTab === 'orchestrator' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Live Workflow Graph State Machine */}
            <WorkflowGraph
              currentStatus={currentTask?.status || 'idle'}
              currentStepIndex={currentTask?.current_step || 0}
              plan={currentTask?.plan || []}
              requiresApproval={isApprovalPending}
              approvalStatus={currentTask?.approval_status || 'none'}
              lastError={currentTask?.error_message}
            />

            {/* Approval Gate Alert when interrupted */}
            {isApprovalPending && (
              <ApprovalModal
                taskId={currentTask.task_id}
                approvalPayload={currentTask.approval_payload}
                onDecision={handleApprovalDecision}
                loading={approvalLoading}
              />
            )}

            {/* Task Console & Results */}
            <TaskConsole
              onSubmitTask={handleTaskSubmit}
              loading={loading}
              currentTask={currentTask}
            />
          </div>
        )}

        {/* Tab 2: Approvals Dedicated Gate */}
        {activeTab === 'approvals' && (
          <div>
            {isApprovalPending ? (
              <ApprovalModal
                taskId={currentTask.task_id}
                approvalPayload={currentTask.approval_payload}
                onDecision={handleApprovalDecision}
                loading={approvalLoading}
              />
            ) : (
              <div className="nexus-card" style={{ padding: '40px', textAlign: 'center' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#f8fafc', marginBottom: '8px' }}>
                  No Pending Human Approvals
                </h3>
                <p style={{ fontSize: '13px', color: '#94a3b8', maxWidth: '480px', margin: '0 auto 20px auto' }}>
                  The agent requires explicit human sign-off when modifying source code or applying unified patches.
                  Start a task in the Orchestrator tab to trigger an approval gate.
                </p>
                <button onClick={() => setActiveTab('orchestrator')} className="btn-primary">
                  Go to Orchestrator
                </button>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Evaluation Suite */}
        {activeTab === 'evaluation' && <EvaluationSuite />}

        {/* Tab 4: Observability & Traces */}
        {activeTab === 'observability' && (
          <TraceViewer taskId={currentTask?.task_id || 'eval-tc-01-mock'} />
        )}

        {/* Tab 5: MCP & Sandbox */}
        {activeTab === 'mcp' && <MCPExplorer />}

        {/* Tab 6: Privacy Policy */}
        {activeTab === 'privacy' && <PrivacyPolicy />}

        {/* Tab 7: Terms and Conditions */}
        {activeTab === 'terms' && <TermsConditions />}

      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid #1e293b',
        padding: '16px 24px',
        fontSize: '12px',
        color: '#64748b',
        background: '#090d16',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div>
          AgentOps Nexus: Stateful LangGraph Orchestration, Sandboxed MCP Tools, Automated Evaluation
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button
            onClick={() => setActiveTab('privacy')}
            style={{
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              fontSize: '12px',
              padding: 0
            }}
          >
            Privacy Policy
          </button>
          <span style={{ color: '#334155' }}>|</span>
          <button
            onClick={() => setActiveTab('terms')}
            style={{
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              fontSize: '12px',
              padding: 0
            }}
          >
            Terms and Conditions
          </button>
        </div>
      </footer>
    </div>
  );
};
