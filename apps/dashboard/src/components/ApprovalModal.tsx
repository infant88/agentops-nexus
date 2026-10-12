import React, { useState } from 'react';
import { 
  ShieldAlert, 
  Check, 
  X, 
  RotateCcw, 
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
      marginTop: '16px',
      padding: '20px',
      borderRadius: '6px',
      background: '#0d1322',
      border: '1px solid #d97706'
    }}>
      {/* Alert Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '4px',
            background: 'rgba(217, 119, 6, 0.15)',
            border: '1px solid #d97706',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <ShieldAlert size={20} color="#fbbf24" />
          </div>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#fef3c7' }}>
              Human Authorization Required
            </h3>
            <p style={{ fontSize: '12px', color: '#94a3b8' }}>
              Execution interrupted at persistent checkpoint. Review proposed patch before disk mutation.
            </p>
          </div>
        </div>

        <span className="badge badge-warning">
          Checkpoint Interrupted
        </span>
      </div>

      {/* Target details */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '10px',
        marginBottom: '14px'
      }}>
        <div style={{ padding: '8px 12px', background: '#040711', borderRadius: '4px', border: '1px solid #1e293b' }}>
          <span style={{ fontSize: '11px', color: '#64748b', display: 'block' }}>Target File</span>
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#38bdf8', fontFamily: 'monospace' }}>
            {patch.file_path || 'calculator.py'}
          </span>
        </div>

        <div style={{ padding: '8px 12px', background: '#040711', borderRadius: '4px', border: '1px solid #1e293b' }}>
          <span style={{ fontSize: '11px', color: '#64748b', display: 'block' }}>Patch Identifier</span>
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1', fontFamily: 'monospace' }}>
            {patch.patch_id || 'patch-pending'}
          </span>
        </div>

        <div style={{ padding: '8px 12px', background: '#040711', borderRadius: '4px', border: '1px solid #1e293b' }}>
          <span style={{ fontSize: '11px', color: '#64748b', display: 'block' }}>Safety Guarantee</span>
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#34d399', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle2 size={12} />
            Idempotent Replay Protected
          </span>
        </div>
      </div>

      {/* Rationale */}
      {patch.explanation && (
        <div style={{
          padding: '10px 12px',
          background: '#040711',
          borderRadius: '4px',
          borderLeft: '3px solid #0284c7',
          marginBottom: '14px',
          fontSize: '12px',
          color: '#cbd5e1'
        }}>
          <strong>Proposal Rationale:</strong> {patch.explanation}
        </div>
      )}

      {/* Unified Diff View */}
      <div style={{ marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '5px' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1' }}>
            Unified Code Diff Preview
          </span>
          <span style={{ fontSize: '11px', color: '#64748b' }}>
            Lines starting with (-) are removed, (+) are added
          </span>
        </div>

        <div className="diff-view" style={{ maxHeight: '200px', padding: '6px 0' }}>
          {diffLines.length > 0 ? (
            diffLines.map((line: string, idx: number) => {
              let lineClass = 'diff-line-neutral';
              if (line.startsWith('+') && !line.startsWith('+++')) lineClass = 'diff-line-add';
              else if (line.startsWith('-') && !line.startsWith('---')) lineClass = 'diff-line-del';
              else if (line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++')) lineClass = 'diff-line-info';

              return (
                <div key={idx} className={lineClass}>
                  <span style={{ userSelect: 'none', width: '28px', display: 'inline-block', opacity: 0.5 }}>
                    {idx + 1}
                  </span>
                  <span>{line}</span>
                </div>
              );
            })
          ) : (
            <div style={{ padding: '14px', color: '#64748b', textAlign: 'center' }}>
              No diff available for preview.
            </div>
          )}
        </div>
      </div>

      {/* Feedback text */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '5px', fontWeight: 500 }}>
          Optional Reviewer Comments / Instructions:
        </label>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="E.g., Approved, percentage denominator verified."
          style={{
            width: '100%',
            height: '55px',
            padding: '8px',
            borderRadius: '4px',
            background: '#040711',
            border: '1px solid #1e293b',
            color: '#f8fafc',
            fontSize: '12px',
            fontFamily: 'inherit',
            resize: 'none',
            outline: 'none'
          }}
        />
      </div>

      {/* Decision Buttons */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px' }}>
        <button
          onClick={() => onDecision('rejected', feedback || 'User declined proposed changes.')}
          disabled={loading}
          className="btn-reject"
        >
          <X size={14} />
          <span>Reject & Abort</span>
        </button>

        <button
          onClick={() => onDecision('revision_requested', feedback || 'Please refine patch and re-propose.')}
          disabled={loading}
          className="btn-secondary"
          style={{ borderColor: '#d97706', color: '#fbbf24' }}
        >
          <RotateCcw size={14} />
          <span>Request Revision</span>
        </button>

        <button
          onClick={() => onDecision('approved', feedback || 'Approved by human reviewer.')}
          disabled={loading}
          className="btn-approve"
        >
          <Check size={14} />
          <span>Approve & Apply Patch</span>
        </button>
      </div>
    </div>
  );
};
