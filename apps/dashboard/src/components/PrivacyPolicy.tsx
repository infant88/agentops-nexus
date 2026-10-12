import React from 'react';
import { ShieldCheck, Lock, Database, Server } from 'lucide-react';

export const PrivacyPolicy: React.FC = () => {
  return (
    <div className="nexus-card" style={{ padding: '32px', maxWidth: '960px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px', borderBottom: '1px solid #1e293b', paddingBottom: '16px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ShieldCheck size={22} color="#0ea5e9" />
          <span>Privacy Policy</span>
        </h2>
        <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
          Effective Date: October 12, 2026. Version 1.0.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', fontSize: '13px', color: '#cbd5e1', lineHeight: '1.7' }}>
        <section>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
            1. Overview and Scope
          </h3>
          <p>
            AgentOps Nexus is an evaluated AI agent execution and orchestration platform designed for software engineering workflows. This Privacy Policy details how data, repository source code, execution telemetry, and audit records are processed, isolated, and safeguarded within the platform.
          </p>
        </section>

        <section>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
            2. Source Code and Sandbox Isolation
          </h3>
          <p>
            All source code access, unit test execution, and database inspections occur within the designated local sandbox environment. The platform enforces strict directory jail boundaries. Source code files, unified diffs, and project database records are never transmitted to third parties or used to train foundational AI models.
          </p>
        </section>

        <section>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
            3. Telemetry and Execution Observability
          </h3>
          <p>
            The platform captures runtime metrics strictly for debugging, evaluation, and latency benchmarking:
          </p>
          <ul style={{ paddingLeft: '20px', marginTop: '6px' }}>
            <li>Task identifier, status transitions, and step timing measurements.</li>
            <li>Token consumption estimates (input tokens and output tokens).</li>
            <li>Tool invocation records and verified test suite exit codes.</li>
          </ul>
        </section>

        <section>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
            4. Automated Secret Redaction
          </h3>
          <p>
            The MCP server and observability engine incorporate automated secret redaction. Authentication headers, API keys matching known provider patterns, and credential arguments are replaced with <code>[REDACTED]</code> prior to persistence in database audit logs or display in developer traces.
          </p>
        </section>

        <section>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
            5. Human Approval and Authority
          </h3>
          <p>
            Sensitive write operations (including repository patch modifications) are checkpointed and paused. Execution continues only upon explicit human authorization. Users retain complete control over whether modifications are applied or discarded.
          </p>
        </section>

        <section>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
            6. Inquiries and Compliance
          </h3>
          <p>
            For privacy inquiries, audit export requests, or security boundary audits, contact the system administrator or deployment operator.
          </p>
        </section>
      </div>
    </div>
  );
};
