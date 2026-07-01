import { useEffect, useState } from 'react';
import api from '../lib/api';

export default function BillingCard() {
  const [billing, setBilling] = useState(null);

  useEffect(() => {
    const fetchBilling = async () => {
      const res = await api.get('/billing/current-usage');
      setBilling(res.data);
    };
    fetchBilling();
  }, []);

  if (!billing) return <div className="p-6 bg-white rounded-lg shadow-sm">Loading...</div>;

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Current Billing Cycle</h2>
      
      <div className="flex justify-between items-end mb-6">
        <div>
          <p className="text-sm text-gray-500 uppercase tracking-wide">Amount Due</p>
          <p className="text-4xl font-bold text-gray-900">${billing.current_cost_usd.toFixed(2)}</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500 uppercase tracking-wide">Total Requests</p>
          <p className="text-xl font-semibold text-gray-700">{billing.total_requests.toLocaleString()}</p>
        </div>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div 
          className={`h-2.5 rounded-full ${billing.total_requests > billing.free_tier_allowance ? 'bg-red-500' : 'bg-blue-600'}`} 
          style={{ width: `${Math.min((billing.total_requests / billing.free_tier_allowance) * 100, 100)}%` }}
        ></div>
      </div>
      <p className="text-xs text-gray-500 mt-2">
        {billing.total_requests} / {billing.free_tier_allowance.toLocaleString()} free tier requests used
      </p>
    </div>
  );
}