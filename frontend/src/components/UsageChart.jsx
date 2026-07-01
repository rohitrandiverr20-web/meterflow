import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Example data structure expected by Recharts
const dummyData = [
  { date: 'Jun 1', requests: 400 },
  { date: 'Jun 2', requests: 300 },
  { date: 'Jun 3', requests: 550 },
  { date: 'Jun 4', requests: 1200 }, // Spiked over free tier!
  { date: 'Jun 5', requests: 800 },
];

export default function UsageChart({ data = dummyData }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 h-80">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">API Usage (Last 7 Days)</h2>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="date" axisLine={false} tickLine={false} />
          <YAxis axisLine={false} tickLine={false} />
          <Tooltip />
          <Line type="monotone" dataKey="requests" stroke="#2563eb" strokeWidth={3} dot={{ r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}