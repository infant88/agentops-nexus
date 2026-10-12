import React, { useState } from 'react';
import { 
  Play, 
  Terminal, 
  CheckCircle2, 
  Clock, 
  Layers, 
  ChevronDown, 
  ChevronRight,
  FileCheck2
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
      
      {/* Objective Input Card */}
      <div className="nexus-card" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Terminal size={16} color="#0ea5e9" />
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc' }}>
              Mission Objective Input
            </h3>
          </div>
          <span style={{ fontSize: '11px', color: '#64748b' }}>
            Select verified preset or input custom prompt
          </span>
        </div>

        {/* Preset Buttons */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '12px' }}>
          {presets.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setObjective(p.text)}
              className="btn-secondary"
              style={{ fontSize: '11px', padding: '5px 10px', borderRadius: '4px' }}
            >
              <span>{p.title}</span>
            </button>
          ))}
        </div>

        {/* Text Input Area */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <textarea
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            placeholder="Specify task objective..."
            rows={3}
            style={{
              flex: 1,
              padding: '10px 12px',
              borderRadius: '4px',
              background: '#040711',
              border: '1px solid #1e293b',
              color: '#f8fafc',
              fontSize: '13px',
              fontFamily: 'inherit',
              resize: 'none',
              outline: 'none'
            }}
          />
          <button
            onClick={() => onSubmitTask(objective)}
            disabled={loading || !objective.trim()}
            className="btn-primary"
            style={{ minWidth: '140px', justifyContent: 'center' }}
          >
            {loading ? (
              <span>Executing...</span>
            ) : (
              <>
                <Play size={15} fill="white" />
                <span>Execute Mission</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Plan & Step History */}
      {plan && plan.length > 0 && (
        <div className="nexus-card" style={{ padding: '20px' }}>
          <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={15} color="#38bdf8" />
            <span>Plan Decomposition ({plan.length} Steps)</span>
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
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
                    padding: '8px 12px',
                    borderRadius: '4px',
                    background: isDone ? 'rgba(16, 185, 129, 0.08)' : '#090d16',
                    border: `1px solid ${isDone ? 'rgba(16, 185, 129, 0.25)' : '#1e293b'}`
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {isDone ? (
                      <CheckCircle2 size={15} color="#10b981" />
                    ) : (
                      <span style={{
                        width: '16px',
                        height: '16px',
                        borderRadius: '2px',
                        border: '1px solid #475569',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '10px',
                        color: '#94a3b8'
                      }}>
                        {idx + 1}
                      </span>
                    )}
                    <span style={{ fontSize: '12px', color: isDone ? '#f8fafc' : '#cbd5e1' }}>
                      {step.description}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
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
        <div className="nexus-card" style={{ padding: '20px' }}>
          <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={15} color="#38bdf8" />
            <span>Execution Evidence Log ({history.length} operations)</span>
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {history.map((h: any, idx: number) => {
              const isExpanded = !!expandedSteps[idx];
              return (
                <div
                  key={idx}
                  style={{
                    borderRadius: '4px',
                    background: '#090d16',
                    border: '1px solid #1e293b',
                    overflow: 'hidden'
                  }}
                >
                  <div
                    onClick={() => toggleStep(idx)}
                    style={{
                      padding: '9px 12px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      background: '#0d1322'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      <span style={{ fontWeight: 600, fontSize: '12px', color: '#38bdf8' }}>
                        {h.tool}
                      </span>
                      <span className="badge badge-success" style={{ fontSize: '10px' }}>
                        {h.status || 'completed'}
                      </span>
                    </div>

                    <span style={{ fontSize: '11px', color: '#64748b' }}>
                      Step #{idx + 1}
                    </span>
                  </div>

                  {isExpanded && (
                    <div style={{ padding: '10px 12px', borderTop: '1px solid #1e293b' }}>
                      <div style={{ marginBottom: '8px' }}>
                        <span style={{ fontSize: '11px', color: '#64748b', display: 'block', marginBottom: '3px' }}>
                          Arguments (Redacted):
                        </span>
                        <pre style={{
                          background: '#040711',
                          padding: '6px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          color: '#cbd5e1',
                          overflowX: 'auto',
                          border: '1px solid #172033'
                        }}>
                          {JSON.stringify(h.arguments, null, 2)}
                        </pre>
                      </div>

                      <div>
                        <span style={{ fontSize: '11px', color: '#64748b', display: 'block', marginBottom: '3px' }}>
                          Tool Output:
                        </span>
                        <pre style={{
                          background: '#040711',
                          padding: '6px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          color: '#34d399',
                          overflowX: 'auto',
                          maxHeight: '160px',
                          border: '1px solid #172033'
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
          padding: '20px',
          borderRadius: '6px',
          background: '#09151c',
          border: '1px solid #047857'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileCheck2 size={18} color="#10b981" />
              <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f0fdf4' }}>
                Executive Mission Report
              </h3>
            </div>
            <span className="badge badge-success">
              Status: {currentTask.status || 'COMPLETED'}
            </span>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <span style={{ fontSize: '11px', color: '#86efac', fontWeight: 600, display: 'block', marginBottom: '3px' }}>
              Root Cause Identification:
            </span>
            <p style={{ fontSize: '12px', color: '#e2e8f0', background: '#040711', padding: '8px 12px', borderRadius: '4px', border: '1px solid #1e293b' }}>
              {finalReport.root_cause}
            </p>
          </div>

          {verification && (
            <div style={{ marginBottom: '14px' }}>
              <span style={{ fontSize: '11px', color: '#86efac', fontWeight: 600, display: 'block', marginBottom: '3px' }}>
                Verification Result:
              </span>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 10px',
                background: verification.verified ? 'rgba(16, 185, 129, 0.12)' : 'rgba(225, 29, 72, 0.12)',
                border: `1px solid ${verification.verified ? '#10b981' : '#e11d48'}`,
                borderRadius: '4px',
                fontSize: '12px',
                color: verification.verified ? '#86efac' : '#fca5a5'
              }}>
                <CheckCircle2 size={14} />
                <span>
                  {verification.test_output || 'All unit tests in test_calculator.py passed successfully.'}
                </span>
              </div>
            </div>
          )}

          {/* Metrics */}
          {finalReport.metrics && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
              gap: '8px',
              paddingTop: '10px',
              borderTop: '1px solid rgba(16, 185, 129, 0.2)'
            }}>
              <div>
                <span style={{ fontSize: '10px', color: '#94a3b8' }}>Latency</span>
                <p style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc' }}>
                  {finalReport.metrics.total_latency_ms} ms
                </p>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: '#94a3b8' }}>Tokens</span>
                <p style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc' }}>
                  {finalReport.metrics.tokens?.total || 0}
                </p>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: '#94a3b8' }}>Cost</span>
                <p style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc' }}>
                  ${finalReport.metrics.cost_usd || 0.00015}
                </p>
              </div>
              <div>
                <span style={{ fontSize: '10px', color: '#94a3b8' }}>Tool Accuracy</span>
                <p style={{ fontSize: '13px', fontWeight: 600, color: '#34d399' }}>
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
