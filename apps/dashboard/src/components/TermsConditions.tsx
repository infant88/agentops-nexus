import React from 'react';
import { FileText, CheckCircle2, AlertOctagon } from 'lucide-react';

export const TermsConditions: React.FC = () => {
  return (
    <div className="nexus-card" style={{ padding: '32px', maxWidth: '960px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px', borderBottom: '1px solid #1e293b', paddingBottom: '16px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <FileText size={22} color="#0ea5e9" />
          <span>Terms and Conditions</span>
        </h2>
        <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
          Effective Date: October 12, 2026. Version 1.0.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', fontSize: '13px', color: '#cbd5e1', lineHeight: '1.7' }}>
        <section>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
            1. Acceptance of Terms
          </h3>
          <p>
            By accessing or operating the AgentOps Nexus platform, API services, or dashboard, you agree to comply with and be bound by these Terms and Conditions. If you do not agree, you must not use or deploy this software.
          </p>
        </section>

        <section>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
            2. Permitted Use and Authorization Boundaries
          </h3>
          <p>
            You agree to operate the platform solely within authorized computing environments, directories, and databases. You must not:
          </p>
          <ul style={{ paddingLeft: '20px', marginTop: '6px' }}>
            <li>Attempt to circumvent path canonicalization checks or file jail boundaries.</li>
            <li>Execute arbitrary destructive database modifications through prompt injections.</li>
            <li>Use the platform to access or alter unauthorized third-party infrastructure.</li>
          </ul>
        </section>

        <section>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
            3. Human-in-the-Loop Review Responsibility
          </h3>
          <p>
            The platform provides checkpointed interrupts before applying source code modifications or executing sensitive operations. The operator or designated human reviewer assumes full responsibility for reviewing proposed unified diffs prior to approval.
          </p>
        </section>

        <section>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
            4. Custom Domain and Network Hosting
          </h3>
          <p>
            Operators configuring custom domains, reverse proxies, or cloud deployments are responsible for maintaining valid TLS certificates, secure DNS records, and CORS origin whitelists conforming to standard web security practices.
          </p>
        </section>

        <section>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f8fafc', marginBottom: '8px' }}>
            5. Limitation of Liability
          </h3>
          <p>
            AgentOps Nexus is provided on an "as is" and "as available" basis. To the maximum extent permitted by applicable law, the authors and contributors disclaim all warranties, express or implied, regarding reliability, fitness for a particular purpose, or error-free operation.
          </p>
        </section>
      </div>
    </div>
  );
};
