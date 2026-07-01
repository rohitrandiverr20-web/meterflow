import { useState, useEffect } from 'react';
import api from '../lib/api';
import { Key, Trash2, Copy } from 'lucide-react';

export default function KeyManager() {
  const [keys, setKeys] = useState([]);
  const [newRawKey, setNewRawKey] = useState(null);

  // Fetch keys on load (Assuming you add a GET /keys endpoint to FastAPI)
  // useEffect(() => { ... fetch keys and setKeys(data) }, []);

  const generateKey = async () => {
    try {
      const response = await api.post('/keys/');
      setNewRawKey(response.data.api_key);
      // Refresh your keys list here
    } catch (error) {
      console.error("Failed to generate key", error);
    }
  };

  const revokeKey = async (id) => {
    await api.delete(`/keys/${id}`);
    // Update UI to show key is inactive
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-800">API Keys</h2>
        <button 
          onClick={generateKey}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
        >
          + Generate New Key
        </button>
      </div>

      {newRawKey && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
          <p className="text-sm text-green-800 font-medium">Please copy your new key now. You won't be able to see it again!</p>
          <div className="flex items-center mt-2 gap-2">
            <code className="bg-white p-2 rounded border border-green-200 flex-1">{newRawKey}</code>
            <button onClick={() => navigator.clipboard.writeText(newRawKey)} className="p-2 bg-green-100 rounded hover:bg-green-200">
              <Copy size={16} className="text-green-700" />
            </button>
          </div>
        </div>
      )}

      {/* Render your table of existing keys here (Prefix, Status, Created At, Revoke Button) */}
    </div>
  );
}