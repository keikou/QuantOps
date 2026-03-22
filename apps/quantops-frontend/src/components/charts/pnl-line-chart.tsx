'use client';

import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export function PnlLineChart({ data }: { data: Array<{ name: string; value: number }> }) {
  return (
    <div className="card h-72 p-4">
      <div className="mb-3 text-sm text-slate-300">Equity Trend</div>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="name" stroke="#94a3b8" />
          <YAxis stroke="#94a3b8" />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#38bdf8" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
