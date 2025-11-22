import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { useState } from 'react';
import ProductList from './components/ProductList';
import Cart from './components/Cart';
import Checkout from './components/Checkout';

function App() {
  const [cart, setCart] = useState([]);

  const addToCart = (product) => {
    setCart([...cart, product]);
  };

  const clearCart = () => {
    setCart([]);
  };

  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <nav className="bg-white shadow-lg">
          <div className="max-w-6xl mx-auto px-4">
            <div className="flex justify-between">
              <div className="flex space-x-7">
                <div>
                  <Link to="/" className="flex items-center py-4 px-2">
                    <span className="font-semibold text-gray-500 text-lg">ChaosShop</span>
                  </Link>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Link to="/" className="py-2 px-2 font-medium text-gray-500 rounded hover:bg-green-500 hover:text-white transition duration-300">Products</Link>
                <Link to="/cart" className="py-2 px-2 font-medium text-gray-500 rounded hover:bg-green-500 hover:text-white transition duration-300">Cart ({cart.length})</Link>
              </div>
            </div>
          </div>
        </nav>

        <div className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<ProductList addToCart={addToCart} />} />
            <Route path="/cart" element={<Cart cart={cart} clearCart={clearCart} />} />
            <Route path="/checkout" element={<Checkout cart={cart} clearCart={clearCart} />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
