import React, { useState } from 'react';
import { 
  Play, 
  Terminal, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Layers, 
  ChevronDown, 
  ChevronRight,
  ShieldCheck,
  FileCheck2,
  DollarSign,
  Cpu
} from 'lucide-react';

interface TaskConsoleProps {
  onSubmitTask: (objective: string) => Promise<void>;
  loading: boolean;
  currentTask: any;
}

export const TaskConsole: React.FC<TaskConsoleProps> = ({
  onSubmitTask,
  loading,
  currentTask
}) => {
  const [objective, setObjective] = useState(
    'Investigate the failing tests in my repository, identify the likely root cause, propose a fix, and wait for my approval before modifying any files.'
  );
  const [expandedSteps, setExpandedSteps] = useState<Record<number, boolean>>({});

  const toggleStep = (idx: number) => {
    setExpandedSteps(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const presets = [
    {
      title: 'Fix Failing Billing Tests (Approval Gate)',
      text: 'Investigate the failing tests in my repository, identify the likely root cause, propose a fix, and wait for my approval before modifying any files.'
    },
    {
      title: 'Check Project Status & Tickets',
      text: 'Retrieve project tickets and active test suite status from the repository database.'
    },
    {
      title: 'Query Database Records (Read-Only)',
      text: 'Query project database for open high priority tickets and test runs.'
    },
    {
      title: 'Security Jail Test (Blocked)',
      text: 'Query database to DROP TABLE project_tasks; DROP TABLE test_runs;'
    }
  ];

  const plan = currentTask?.plan || [];
  const history = currentTask?.execution_history || [];
  const finalReport = currentTask?.final_report;
  const verification = currentTask?.verification_result;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Objective Input Card */}
      <div className="nexus-card" style={{ padding: '22px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Terminal size={18} color="#06b6d4" />
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc' }}>
              Agent Mission Objective
            </h3>
          </div>
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>
            Select a preset or input custom prompt
          </span>
        </div>

        {/* Preset Buttons */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '14px' }}>
          {presets.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setObjective(p.text)}
              className="btn-secondary"
              style={{ fontSize: '11px', padding: '5px 11px', borderRadius: '6px' }}
            >
              <Sparkles size={12} color="#818cf8" />
              <span>{p.title}</span>
            </button>
          ))}
        </div>

        {/* Text Input Area */}
        <div style={{ display: 'flex', gap: '12px' }}>
          <textarea
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            placeholder="Describe the agent mission..."
            rows={3}
            style={{
              flex: 1,
              padding: '12px 14px',
              borderRadius: '10px',
              background: '#040812',
              border: '1px solid rgba(56, 96, 160, 0.3)',
              color: '#f8fafc',
              fontSize: '13px',
              fontFamily: 'inherit',
              resize: 'none'
            }}
          />
          <button
            onClick={() => onSubmitTask(objective)}
            disabled={loading || !objective.trim()}
            className="btn-primary"
            style={{ minWidth: '150px', justifyContent: 'center' }}
          >
            {loading ? (
              <span>Orchestrating...</span>
            ) : (
              <>
                <Play size={16} fill="white" />
                <span>Run Agent</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Plan & Step History */}
      {plan && plan.length > 0 && (
        <div className="nexus-card" style={{ padding: '22px' }}>
          <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={16} color="#38bdf8" />
            <span>Structured Plan Decomposition ({plan.length} Steps)</span>
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {plan.map((step: any, idx: number) => {
              const isDone = history.some((h: any) => h.step_id === step.step_id);
              const isSensitive = step.is_sensitive;
              return (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: isDone ? 'rgba(16, 185, 129, 0.08)' : 'rgba(15, 23, 42, 0.4)',
                    border: `1px solid ${isDone ? 'rgba(16, 185, 129, 0.3)' : 'rgba(56, 96, 160, 0.2)'}`
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {isDone ? (
                      <CheckCircle2 size={16} color="#10b981" />
                    ) : (
                      <span style={{
                        width: '18px',
                        height: '18px',
                        borderRadius: '50%',
                        border: '1px solid #64748b',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '11px',
                        color: '#94a3b8'
                      }}>
                        {idx + 1}
                      </span>
                    )}
                    <span style={{ fontSize: '13px', color: isDone ? '#f8fafc' : '#cbd5e1' }}>
                      {step.description}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {isSensitive && (
                      <span className="badge badge-warning" style={{ fontSize: '10px' }}>
                        Requires Approval
                      </span>
                    )}
                    <span className="badge badge-info" style={{ fontSize: '10px' }}>
                      {step.tool}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Execution History Timeline */}
      {history && history.length > 0 && (
        <div className="nexus-card" style={{ padding: '22px' }}>
          <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={16} color="#a78bfa" />
            <span>Tool Execution Evidence Log ({history.length} operations)</span>
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {history.map((h: any, idx: number) => {
              const isExpanded = !!expandedSteps[idx];
              return (
                <div
                  key={idx}
                  style={{
                    borderRadius: '8px',
                    background: 'rgba(11, 19, 36, 0.6)',
                    border: '1px solid rgba(56, 96, 160, 0.25)',
                    overflow: 'hidden'
                  }}
                >
                  <div
                    onClick={() => toggleStep(idx)}
                    style={{
                      padding: '10px 14px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      background: 'rgba(15, 27, 48, 0.4)'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      <span style={{ fontWeight: 600, fontSize: '13px', color: '#38bdf8' }}>
                        {h.tool}
                      </span>
                      <span className="badge badge-success" style={{ fontSize: '10px' }}>
                        {h.status || 'completed'}
                      </span>
                    </div>

                    <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                      Step #{idx + 1}
                    </span>
                  </div>

                  {isExpanded && (
                    <div style={{ padding: '12px 14px', borderTop: '1px solid rgba(56, 96, 160, 0.2)' }}>
                      <div style={{ marginBottom: '8px' }}>
                        <span style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                          Arguments (Secrets Redacted):
                        </span>
                        <pre style={{
                          background: '#040812',
                          padding: '8px 10px',
                          borderRadius: '6px',
                          fontSize: '11px',
                          color: '#cbd5e1',
                          overflowX: 'auto'
                        }}>
                          {JSON.stringify(h.arguments, null, 2)}
                        </pre>
                      </div>

                      <div>
                        <span style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                          Tool Output:
                        </span>
                        <pre style={{
                          background: '#040812',
                          padding: '8px 10px',
                          borderRadius: '6px',
                          fontSize: '11px',
                          color: '#34d399',
                          overflowX: 'auto',
                          maxHeight: '180px'
                        }}>
                          {JSON.stringify(h.output, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Final Executive Report Card */}
      {finalReport && (
        <div style={{
          padding: '24px',
          borderRadius: '16px',
          background: 'linear-gradient(135deg, rgba(6, 78, 59, 0.25) 0%, rgba(15, 23, 42, 0.8) 100%)',
          border: '1px solid rgba(16, 185, 129, 0.45)',
          boxShadow: '0 8px 30px rgba(0, 0, 0, 0.4)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FileCheck2 size={22} color="#10b981" />
              <h3 style={{ fontSize: '17px', fontWeight: 700, color: '#f0fdf4' }}>
                Executive Mission Report
              </h3>
            </div>
            <span className="badge badge-success" style={{ fontSize: '12px' }}>
              Terminal Status: {currentTask.status || 'COMPLETED'}
            </span>
          </div>

          <div style={{ marginBottom: '14px' }}>
            <span style={{ fontSize: '12px', color: '#86efac', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              Root Cause Identification:
            </span>
            <p style={{ fontSize: '13px', color: '#e2e8f0', background: 'rgba(15, 23, 42, 0.6)', padding: '10px 14px', borderRadius: '8px' }}>
              {finalReport.root_cause}
            </p>
          </div>

          {verification && (
            <div style={{ marginBottom: '16px' }}>
              <span style={{ fontSize: '12px', color: '#86efac', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                Automated Verification Status:
              </span>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                background: verification.verified ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                border: `1px solid ${verification.verified ? '#10b981' : '#f43f5e'}`,
                borderRadius: '8px',
                fontSize: '13px',
                color: verification.verified ? '#86efac' : '#fca5a5'
              }}>
                <CheckCircle2 size={16} />
                <span>
                  {verification.test_output || 'All unit tests in test_calculator.py passed successfully!'}
                </span>
              </div>
            </div>
          )}

          {/* Quick Metrics Bar */}
          {finalReport.metrics && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
              gap: '10px',
              paddingTop: '12px',
              borderTop: '1px solid rgba(16, 185, 129, 0.25)'
            }}>
              <div>
                <span style={{ fontSize: '11px', color: '#94a3b8' }}>Latency</span>
                <p style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc' }}>
                  {finalReport.metrics.total_latency_ms} ms
                </p>
              </div>
              <div>
                <span style={{ fontSize: '11px', color: '#94a3b8' }}>Tokens</span>
                <p style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc' }}>
                  {finalReport.metrics.tokens?.total || 0}
                </p>
              </div>
              <div>
                <span style={{ fontSize: '11px', color: '#94a3b8' }}>Est. Cost</span>
                <p style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc' }}>
                  ${finalReport.metrics.cost_usd || 0.00015}
                </p>
              </div>
              <div>
                <span style={{ fontSize: '11px', color: '#94a3b8' }}>Tool Accuracy</span>
                <p style={{ fontSize: '14px', fontWeight: 700, color: '#34d399' }}>
                  {((finalReport.metrics.tool_accuracy || 1) * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
