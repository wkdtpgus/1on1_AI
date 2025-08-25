import React from 'react';
import Link from 'next/link';

const Header = () => {
  return (
    <header className="bg-white shadow-md">
      <nav className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="text-xl font-semibold text-gray-700">
            <Link href="/">1on1 AI Assistant</Link>
          </div>
          <div>
            <Link href="#" className="text-gray-600 hover:text-blue-500 mx-3">
              History
            </Link>
            <Link href="#" className="text-gray-600 hover:text-blue-500 mx-3">
              Login
            </Link>
          </div>
        </div>
      </nav>
    </header>
  );
};

export default Header;
