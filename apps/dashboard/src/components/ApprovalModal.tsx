import React, { useState } from 'react';
import { 
  ShieldAlert, 
  Check, 
  X, 
  RotateCcw, 
  FileCode, 
  Key, 
  Info,
  CheckCircle2
} from 'lucide-react';

interface ApprovalModalProps {
  taskId: string;
  approvalPayload: any;
  onDecision: (decision: 'approved' | 'rejected' | 'revision_requested', feedback: string) => Promise<void>;
  loading: boolean;
}

export const ApprovalModal: React.FC<ApprovalModalProps> = ({
  taskId,
  approvalPayload,
  onDecision,
  loading
}) => {
  const [feedback, setFeedback] = useState('');

  if (!approvalPayload) return null;

  const patch = approvalPayload.payload || approvalPayload;
  const diffLines = (patch.diff || '').split('\n');

  return (
    <div style={{
      marginTop: '20px',
      padding: '24px',
      borderRadius: '16px',
      background: 'linear-gradient(180deg, rgba(30, 27, 75, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%)',
      border: '1px solid rgba(245, 158, 11, 0.45)',
      boxShadow: '0 12px 35px rgba(0, 0, 0, 0.4), 0 0 25px rgba(245, 158, 11, 0.15)'
    }}>
      {/* Alert Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'rgba(245, 158, 11, 0.2)',
            border: '1px solid #f59e0b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <ShieldAlert size={24} color="#fbbf24" />
          </div>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#fef3c7' }}>
              Human Authorization Required
            </h3>
            <p style={{ fontSize: '13px', color: '#cbd5e1' }}>
              Execution interrupted at persistent checkpoint. Modifying repository files requires verified sign-off.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="badge badge-warning" style={{ fontSize: '12px', padding: '4px 12px' }}>
            Checkpoint Interrupted
          </span>
        </div>
      </div>

      {/* Target details */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '12px',
        marginBottom: '18px'
      }}>
        <div style={{ padding: '10px 14px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '8px', border: '1px solid rgba(56, 96, 160, 0.2)' }}>
          <span style={{ fontSize: '11px', color: '#94a3b8', display: 'block' }}>Target File</span>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#38bdf8', fontFamily: 'monospace' }}>
            {patch.file_path || 'calculator.py'}
          </span>
        </div>

        <div style={{ padding: '10px 14px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '8px', border: '1px solid rgba(56, 96, 160, 0.2)' }}>
          <span style={{ fontSize: '11px', color: '#94a3b8', display: 'block' }}>Patch ID</span>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#a78bfa', fontFamily: 'monospace' }}>
            {patch.patch_id || 'patch-pending'}
          </span>
        </div>

        <div style={{ padding: '10px 14px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '8px', border: '1px solid rgba(56, 96, 160, 0.2)' }}>
          <span style={{ fontSize: '11px', color: '#94a3b8', display: 'block' }}>Safety Guarantee</span>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#34d399', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle2 size={13} />
            Idempotent Replay Protected
          </span>
        </div>
      </div>

      {/* Rationale */}
      {patch.explanation && (
        <div style={{
          padding: '12px 14px',
          background: 'rgba(30, 41, 59, 0.4)',
          borderRadius: '8px',
          borderLeft: '4px solid #38bdf8',
          marginBottom: '18px',
          fontSize: '13px',
          color: '#e2e8f0'
        }}>
          <strong>Agent Proposal Rationale:</strong> {patch.explanation}
        </div>
      )}

      {/* Unified Diff View */}
      <div style={{ marginBottom: '18px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1' }}>
            Unified Code Diff Preview
          </span>
          <span style={{ fontSize: '11px', color: '#64748b' }}>
            Lines starting with (-) are removed, (+) are added
          </span>
        </div>

        <div className="diff-view" style={{ maxHeight: '240px', padding: '8px 0' }}>
          {diffLines.length > 0 ? (
            diffLines.map((line: string, idx: number) => {
              let lineClass = 'diff-line-neutral';
              if (line.startsWith('+') && !line.startsWith('+++')) lineClass = 'diff-line-add';
              else if (line.startsWith('-') && !line.startsWith('---')) lineClass = 'diff-line-del';
              else if (line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++')) lineClass = 'diff-line-info';

              return (
                <div key={idx} className={lineClass}>
                  <span style={{ userSelect: 'none', width: '32px', display: 'inline-block', opacity: 0.5 }}>
                    {idx + 1}
                  </span>
                  <span>{line}</span>
                </div>
              );
            })
          ) : (
            <div style={{ padding: '16px', color: '#94a3b8', textAlign: 'center' }}>
              No diff available for preview.
            </div>
          )}
        </div>
      </div>

      {/* Feedback text */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', fontSize: '12px', color: '#cbd5e1', marginBottom: '6px', fontWeight: 500 }}>
          Optional Reviewer Comments / Revision Instructions:
        </label>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="E.g., Approved, verified the percentage denominator is correct."
          style={{
            width: '100%',
            height: '65px',
            padding: '10px',
            borderRadius: '8px',
            background: '#090d16',
            border: '1px solid rgba(56, 96, 160, 0.3)',
            color: '#f8fafc',
            fontSize: '13px',
            fontFamily: 'inherit',
            resize: 'none'
          }}
        />
      </div>

      {/* Decision Buttons */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px' }}>
        <button
          onClick={() => onDecision('rejected', feedback || 'User declined proposed changes.')}
          disabled={loading}
          className="btn-reject"
        >
          <X size={16} />
          <span>Reject & Abort</span>
        </button>

        <button
          onClick={() => onDecision('revision_requested', feedback || 'Please refine patch and re-propose.')}
          disabled={loading}
          className="btn-secondary"
          style={{ borderColor: '#f59e0b', color: '#fbbf24' }}
        >
          <RotateCcw size={16} />
          <span>Request Revision</span>
        </button>

        <button
          onClick={() => onDecision('approved', feedback || 'Approved by human reviewer.')}
          disabled={loading}
          className="btn-approve"
        >
          <Check size={16} />
          <span>Approve & Apply Patch</span>
        </button>
      </div>
    </div>
  );
};
