import React, { useState, useEffect } from 'react';
import { 
  Layers, 
  Terminal, 
  FileCode, 
  Play, 
  RotateCcw, 
  Lock, 
  Unlock, 
  CheckCircle2, 
  Search,
  Code
} from 'lucide-react';

export const MCPExplorer: React.FC = () => {
  const [tools, setTools] = useState<any[]>([]);
  const [selectedTool, setSelectedTool] = useState<string>('search_repository');
  const [toolArgs, setToolArgs] = useState<string>('{"query": "calculate_discount", "path_pattern": "*.py"}');
  const [testResult, setTestResult] = useState<any>(null);
  const [sandboxFiles, setSandboxFiles] = useState<any[]>([]);
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [resetting, setResetting] = useState(false);

  const fetchToolsAndFiles = async () => {
    try {
      const [toolsRes, filesRes] = await Promise.all([
        fetch('/api/tools'),
        fetch('/api/sandbox/files')
      ]);

      if (toolsRes.ok) {
        const t = await toolsRes.json();
        setTools(t);
      }
      if (filesRes.ok) {
        const f = await filesRes.json();
        setSandboxFiles(f.files || []);
        if (f.files && f.files.length > 0) {
          setSelectedFile(f.files[0]);
        }
      }
    } catch (e) {
      console.error('Failed to load MCP resources', e);
    }
  };

  useEffect(() => {
    fetchToolsAndFiles();
  }, []);

  const handleSelectTool = (tool: any) => {
    setSelectedTool(tool.name);
    // Preset sample arguments
    if (tool.name === 'search_repository') {
      setToolArgs('{"query": "calculate_discount", "path_pattern": "*.py", "max_results": 10}');
    } else if (tool.name === 'get_project_status') {
      setToolArgs('{"include_tests": true, "include_tasks": true}');
    } else if (tool.name === 'query_project_database') {
      setToolArgs('{"query": "SELECT * FROM project_tasks LIMIT 5;", "limit": 10}');
    } else if (tool.name === 'run_test_suite') {
      setToolArgs('{"test_target": "all", "timeout_seconds": 30}');
    } else if (tool.name === 'propose_file_patch') {
      setToolArgs('{\n  "file_path": "calculator.py",\n  "search_block": "    discount_amount = price * (discount_percent)  # Missing / 100",\n  "replace_block": "    discount_amount = price * (discount_percent / 100.0)  # Fixed fraction",\n  "explanation": "Fix percentage calculation"\n}');
    } else if (tool.name === 'apply_approved_patch') {
      setToolArgs('{"patch_id": "patch-demo", "approval_token": "token-test", "idempotency_key": "idem-1"}');
    }
  };

  const handleExecute = async () => {
    setLoading(true);
    setTestResult(null);
    try {
      let parsed = {};
      try {
        parsed = JSON.parse(toolArgs);
      } catch (err) {
        setTestResult({ error: 'Invalid JSON arguments' });
        setLoading(false);
        return;
      }

      const res = await fetch('/api/tools/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tool_name: selectedTool,
          arguments: parsed
        })
      });

      const data = await res.json();
      setTestResult(data);
      // Refresh files if patched
      if (selectedTool === 'apply_approved_patch') {
        fetchToolsAndFiles();
      }
    } catch (e: any) {
      setTestResult({ error: e.message || 'Execution failed' });
    } finally {
      setLoading(false);
    }
  };

  const resetSandbox = async () => {
    setResetting(true);
    try {
      await fetch('/api/sandbox/reset', { method: 'POST' });
      await fetchToolsAndFiles();
    } finally {
      setResetting(false);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '22px' }}>
      
      {/* Left Column: MCP Tools Registry & Playground */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        <div className="nexus-card" style={{ padding: '22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={18} color="#0ea5e9" />
              <span>Standardized MCP Tool Registry ({tools.length} Tools)</span>
            </h3>
            <span className="badge badge-info" style={{ fontSize: '11px' }}>
              MCP SDK 2.3.0
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', marginBottom: '20px' }}>
            {tools.map((t: any) => {
              const isSelected = selectedTool === t.name;
              return (
                <div
                  key={t.name}
                  onClick={() => handleSelectTool(t)}
                  style={{
                    padding: '12px',
                    borderRadius: '4px',
                    background: isSelected ? 'rgba(14, 165, 233, 0.15)' : 'rgba(15, 23, 42, 0.45)',
                    border: `1px solid ${isSelected ? '#0ea5e9' : '#1e293b'}`,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: isSelected ? '#38bdf8' : '#f8fafc' }}>
                      {t.name}
                    </span>
                    {t.isSensitive ? (
                      <span title="Sensitive Tool"><Lock size={12} color="#f59e0b" /></span>
                    ) : (
                      <span title="Read/Safe Tool"><Unlock size={12} color="#10b981" /></span>
                    )}
                  </div>
                  <p style={{ fontSize: '11px', color: '#94a3b8', lineHeight: 1.3 }}>
                    {t.description}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Playground input */}
          <div style={{ borderTop: '1px solid #1e293b', paddingTop: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1' }}>
                Tool Arguments (JSON):
              </span>
              <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                Selected: <code style={{ color: '#38bdf8' }}>{selectedTool}</code>
              </span>
            </div>

            <textarea
              value={toolArgs}
              onChange={(e) => setToolArgs(e.target.value)}
              rows={4}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '4px',
                background: '#040812',
                border: '1px solid #1e293b',
                color: '#34d399',
                fontSize: '12px',
                fontFamily: 'monospace',
                marginBottom: '12px',
                resize: 'none'
              }}
            />

            <button
              onClick={handleExecute}
              disabled={loading}
              className="btn-primary"
            >
              <Play size={14} fill="white" />
              <span>{loading ? 'Executing...' : 'Invoke MCP Tool'}</span>
            </button>
          </div>

          {/* Test Execution Output */}
          {testResult && (
            <div style={{ marginTop: '16px' }}>
              <span style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                Server Response:
              </span>
              <pre style={{
                background: '#040812',
                padding: '12px',
                borderRadius: '4px',
                fontSize: '11px',
                color: testResult.success ? '#34d399' : '#fca5a5',
                overflowX: 'auto',
                maxHeight: '200px',
                border: `1px solid ${testResult.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`
              }}>
                {JSON.stringify(testResult, null, 2)}
              </pre>
            </div>
          )}

        </div>
      </div>

      {/* Right Column: Sandbox Repository Explorer */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        <div className="nexus-card" style={{ padding: '22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Code size={18} color="#06b6d4" />
              <span>Sandbox Repository Explorer</span>
            </h3>
            <button
              onClick={resetSandbox}
              disabled={resetting}
              className="btn-secondary"
              style={{ fontSize: '11px', padding: '4px 10px' }}
              title="Reset repository files and test db to initial bug state"
            >
              <RotateCcw size={12} />
              <span>{resetting ? 'Resetting...' : 'Reset Bug State'}</span>
            </button>
          </div>

          {/* File Pills */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '14px', flexWrap: 'wrap' }}>
            {sandboxFiles.map((f: any) => {
              const isSelected = selectedFile?.path === f.path;
              return (
                <button
                  key={f.path}
                  onClick={() => setSelectedFile(f)}
                  className={`btn-secondary ${isSelected ? 'nexus-card-active' : ''}`}
                  style={{
                    fontSize: '12px',
                    padding: '5px 12px',
                    fontFamily: 'monospace',
                    background: isSelected ? 'rgba(6, 182, 212, 0.2)' : 'rgba(15, 23, 42, 0.5)',
                    borderColor: isSelected ? '#06b6d4' : 'rgba(56, 96, 160, 0.2)'
                  }}
                >
                  <FileCode size={13} color="#38bdf8" />
                  <span>{f.path}</span>
                </button>
              );
            })}
          </div>

          {/* File Content Viewer */}
          {selectedFile && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontSize: '11px', color: '#94a3b8', fontFamily: 'monospace' }}>
                  {selectedFile.path} ({selectedFile.size} bytes)
                </span>
                <span style={{ fontSize: '11px', color: '#10b981' }}>
                  Read-Only Sandboxed
                </span>
              </div>
              <pre style={{
                background: '#040812',
                padding: '14px',
                borderRadius: '4px',
                fontSize: '12px',
                color: '#cbd5e1',
                overflowX: 'auto',
                maxHeight: '420px',
                border: '1px solid #1e293b',
                lineHeight: 1.45
              }}>
                {selectedFile.content}
              </pre>
            </div>
          )}

        </div>

      </div>

    </div>
  );
};
