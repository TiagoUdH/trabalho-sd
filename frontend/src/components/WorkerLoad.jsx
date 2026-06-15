export default function WorkerLoad({ carga }) {
  const entries = Object.entries(carga);
  if (entries.length === 0) return null;

  const total = entries.reduce((sum, [, n]) => sum + n, 0);

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
        <div className="px-4 py-3 bg-slate-800 border-b border-slate-700">
          <h3 className="text-slate-300 font-medium text-sm">Carga por Nó</h3>
        </div>

        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {entries.map(([no, qtd]) => {
            const pct = Math.round((qtd / total) * 100);
            return (
              <div key={no} className="bg-slate-700/50 rounded-lg p-4 border border-slate-600/30">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-white font-medium text-sm">{no}</span>
                  <span className="text-indigo-400 font-mono font-bold">{qtd}</span>
                </div>
                <div className="w-full bg-slate-600/50 rounded-full h-2">
                  <div
                    className="bg-indigo-500 h-2 rounded-full transition-all duration-700"
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <div className="text-right text-xs text-slate-500 mt-1">{pct}%</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
