import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const Checkout = ({ cart, clearCart }) => {
  const navigate = useNavigate();
  const [userId, setUserId] = useState('1');
  const [address, setAddress] = useState('123 Main St');
  const [chaosScenario, setChaosScenario] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleCheckout = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    // Group items by product
    const items = {};
    cart.forEach(item => {
      items[item.product_name] = (items[item.product_name] || 0) + 1;
    });

    // For simplicity, we just take the first item to create one order
    // In a real app, we'd loop or create multiple orders
    const firstProduct = Object.keys(items)[0];
    if (!firstProduct) {
      setError("Cart is empty");
      setLoading(false);
      return;
    }

    const orderData = {
      user_id: parseInt(userId),
      product_name: firstProduct,
      quantity: items[firstProduct],
      address: address
    };

    const headers = {};
    if (chaosScenario) {
      headers['X-Chaos-Scenario'] = chaosScenario;
    }

    try {
      // Python Service
      const response = await axios.post('http://localhost:8000/orders', orderData, { headers });
      setResult(response.data);
      clearCart();
    } catch (err) {
      console.error("Checkout failed", err);
      setError(err.response?.data?.detail || err.message || "Checkout failed");
      if (err.response?.data) {
        setResult(err.response.data); // Show partial results even on error
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Checkout</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <form onSubmit={handleCheckout} className="bg-white p-6 rounded-lg shadow-md">
            <div className="mb-4">
              <label className="block text-gray-700 mb-2">User ID</label>
              <input
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="w-full border p-2 rounded"
                required
                type="number"
              />
              <p className="text-xs text-gray-500 mt-1">Tip: Ends with 9 for DB timeout, starts with 4 for Fraud, 666 for Email fail.</p>
            </div>

            <div className="mb-4">
              <label className="block text-gray-700 mb-2">Address</label>
              <input
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                className="w-full border p-2 rounded"
                required
              />
              <p className="text-xs text-gray-500 mt-1">Tip: Include "SLOW" for latency, "ERROR" for shipping failure.</p>
            </div>

            <div className="mb-6">
              <label className="block text-gray-700 mb-2">Chaos Scenario (Header)</label>
              <select
                value={chaosScenario}
                onChange={(e) => setChaosScenario(e.target.value)}
                className="w-full border p-2 rounded"
              >
                <option value="">None</option>
                <option value="high-load">High Load (Latency)</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              className={`w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600 transition ${loading ? 'opacity-50' : ''}`}
            >
              {loading ? 'Processing...' : 'Place Order'}
            </button>
          </form>
        </div>

        <div>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              <strong className="font-bold">Error: </strong>
              <span className="block sm:inline">{error}</span>
            </div>
          )}

          {result && (
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-xl font-bold mb-4">Order Result</h3>
              <pre className="bg-gray-100 p-4 rounded overflow-auto text-sm">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Checkout;
