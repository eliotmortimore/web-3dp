import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { AuthModal } from './components/AuthModal';
import { LogOut, User as UserIcon } from 'lucide-react';
import Home from './pages/Home';
import Admin from './pages/Admin';

function App() {
  const { user, isAdmin, signOut } = useAuth();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  return (
    <Router>
      <div className="min-h-screen bg-gray-900 text-white">
        <nav className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-md sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <Link to="/" className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                Web3DP
              </Link>
              
              <div className="flex items-center gap-4">
                {user ? (
                  <>
                    <div className="flex items-center gap-2 text-sm text-gray-300">
                      <UserIcon size={16} />
                      <span className="hidden sm:inline">{user.email}</span>
                    </div>
                    {isAdmin && (
                      <Link 
                        to="/admin" 
                        className="text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        Admin Dashboard
                      </Link>
                    )}
                    <button
                      onClick={() => signOut()}
                      className="p-2 text-gray-400 hover:text-white transition-colors"
                      title="Sign Out"
                    >
                      <LogOut size={20} />
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setIsAuthModalOpen(true)}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    Sign In
                  </button>
                )}
              </div>
            </div>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/admin" element={isAdmin ? <Admin /> : <Home />} />
        </Routes>

        <AuthModal 
          isOpen={isAuthModalOpen} 
          onClose={() => setIsAuthModalOpen(false)} 
        />
      </div>
    </Router>
  );
}

export default App;
