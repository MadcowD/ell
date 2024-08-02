export function InvocationInfoPane({ invocation, isFullWidth }) {
    return (
      <div className={`w-full bg-[#0d1117] p-4 border-t border-gray-800 text-sm ${!isFullWidth ? 'max-w-[min(25%,230px)]' : ''}`}>
        <div className="mb-2">
          <p className="text-gray-500">CREATED AT</p>
          <p className="text-gray-300">{new Date(invocation.created_at).toLocaleTimeString()}</p>
        </div>
        <div className="mb-2">
          <p className="text-gray-500">LATENCY</p>
          <p className="text-gray-300">{(invocation.latency_ms / 1000).toFixed(2)}s</p>
        </div>
        <div className="mb-2">
          <p className="text-gray-500">PROMPT TOKENS</p>
          <p className="text-gray-300">
            {invocation.prompt_tokens || "N/A"}
          </p>
        </div>
        <div className="mb-2">
          <p className="text-gray-500">COMPLETION TOKENS</p>
          <p className="text-gray-300">
            {invocation.completion_tokens || "N/A"}
          </p>
        </div>
        <div className="mb-2">
          <p className="text-gray-500">LMP TYPE</p>
          <p className="text-gray-300 bg-blue-900 inline-block px-2 py-0.5 rounded">
            {invocation.lmp.is_lm ? "LM" : "LMP"}
          </p>
        </div>
        <div>
          <p className="text-gray-500">DEPENDENCIES</p>
          <p className="text-gray-300">{invocation.lmp.dependencies}</p>
        </div>
      </div>
    );
  }