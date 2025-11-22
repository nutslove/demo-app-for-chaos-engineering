import React, { useEffect, useState } from 'react';
import axios from 'axios';

const ProductList = ({ addToCart }) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        // Node.js Service
        const response = await axios.get('http://localhost:3001/inventory');
        setProducts(response.data.inventory);
        setLoading(false);
      } catch (err) {
        console.error("Failed to fetch products", err);
        setError("Failed to load products. Is the Node.js service running?");
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  if (loading) return <div className="text-center mt-10">Loading products...</div>;
  if (error) return <div className="text-center mt-10 text-red-500">{error}</div>;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Products</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {products.map((product) => (
          <div key={product.id} className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-2">{product.product_name}</h3>
            <p className="text-gray-600 mb-4">Available: {product.quantity}</p>
            <button
              onClick={() => addToCart(product)}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition"
            >
              Add to Cart
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProductList;
