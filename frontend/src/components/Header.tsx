import React from 'react';

const Header = () => {
  return (
    <header className="bg-white shadow-md">
      <nav className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="text-xl font-semibold text-gray-700">
            <a href="/">1on1 AI Assistant</a>
          </div>
          <div>
            <a href="#" className="text-gray-600 hover:text-blue-500 mx-3">
              History
            </a>
            <a href="#" className="text-gray-600 hover:text-blue-500 mx-3">
              Login
            </a>
          </div>
        </div>
      </nav>
    </header>
  );
};

export default Header;
