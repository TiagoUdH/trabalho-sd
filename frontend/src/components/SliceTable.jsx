export default function SliceTable({ detalhes, falhas }) {
  const entries = Object.entries(detalhes);

  if (entries.length === 0 && falhas.length === 0) return null;

  const failedNames = new Set(falhas.map((f) => f.fatia));

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
        <div className="px-4 py-3 bg-slate-800 border-b border-slate-700">
          <h3 className="text-slate-300 font-medium text-sm">Detalhes por Fatia</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="text-xs text-slate-400 uppercase border-b border-slate-700">
                <th className="px-4 py-3 font-medium">Fatia</th>
                <th className="px-4 py-3 font-medium">Nó Responsável</th>
                <th className="px-4 py-3 font-medium">Resultado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {entries.map(([nome, info]) => {
                const isRed = info.encontrou_vermelho;
                const isFailed = failedNames.has(nome);
                return (
                  <tr key={nome} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 text-white font-mono text-sm">{nome}</td>
                    <td className="px-4 py-3 text-slate-300 text-sm">
                      {info.no_responsavel || '—'}
                    </td>
                    <td className="px-4 py-3">
                      {isFailed ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-400 bg-amber-400/10 px-2 py-1 rounded-full">
                          Falha
                        </span>
                      ) : isRed ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-red-400 bg-red-400/10 px-2 py-1 rounded-full">
                          <span className="w-2 h-2 rounded-full bg-red-400" />
                          Vermelho
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded-full">
                          <span className="w-2 h-2 rounded-full bg-emerald-400" />
                          Sem vermelho
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}

              {falhas.map(({ fatia, erro }) => (
                !detalhes[fatia] && (
                  <tr key={`fail-${fatia}`} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 text-slate-500 font-mono text-sm">{fatia}</td>
                    <td className="px-4 py-3 text-slate-500 text-sm">—</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-400 bg-amber-400/10 px-2 py-1 rounded-full"
                        title={erro}>
                        Falha
                      </span>
                    </td>
                  </tr>
                )
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
