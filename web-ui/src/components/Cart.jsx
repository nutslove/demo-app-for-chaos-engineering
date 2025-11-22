import React from 'react';
import { Link } from 'react-router-dom';

const Cart = ({ cart, clearCart }) => {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Shopping Cart</h2>
      {cart.length === 0 ? (
        <p>Your cart is empty.</p>
      ) : (
        <>
          <div className="bg-white p-6 rounded-lg shadow-md mb-6">
            {cart.map((item, index) => (
              <div key={index} className="flex justify-between items-center border-b py-2 last:border-0">
                <span>{item.product_name}</span>
                <span className="text-gray-500">1</span>
              </div>
            ))}
          </div>
          <div className="flex justify-between">
            <button
              onClick={clearCart}
              className="text-red-500 hover:text-red-700"
            >
              Clear Cart
            </button>
            <Link
              to="/checkout"
              className="bg-green-500 text-white px-6 py-2 rounded hover:bg-green-600 transition"
            >
              Proceed to Checkout
            </Link>
          </div>
        </>
      )}
    </div>
  );
};

export default Cart;
