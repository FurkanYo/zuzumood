
import React, { useState, useEffect } from 'react';
import { ShoppingBag, Menu, X, Search, Heart } from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { WishlistPanel } from './WishlistPanel';
import { useWishlist } from '../context/WishlistContext';

export const Header: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isWishlistOpen, setIsWishlistOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const { wishlistIds } = useWishlist();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 40);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    setIsMenuOpen(false);
    setIsSearchOpen(false);
    setIsWishlistOpen(false);
    window.scrollTo(0, 0);
  }, [location]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/shop?q=${encodeURIComponent(searchQuery)}`);
      setIsSearchOpen(false);
      setSearchQuery('');
    }
  };

  return (
    <>
      <div className="fixed w-full z-50">
        {/* Top bar */}
        <div className="bg-black text-white text-[8px] py-1.5 text-center font-bold tracking-[0.4em] uppercase">
          Curating the Soul Archive • Redefining Minimalist Luxury
        </div>

        <header className={`transition-all duration-700 ease-in-out ${
          isScrolled || isSearchOpen ? 'bg-white py-4 border-b border-gray-100' : 'bg-transparent py-8'
        }`}>
          <div className="container mx-auto px-6 grid grid-cols-3 items-center">
            
            {/* Left Nav */}
            <nav className="hidden lg:flex items-center space-x-10 text-[9px] font-bold tracking-[0.3em] uppercase">
              <Link to="/shop?cat=teacher" className="hover:text-muted transition-colors italic">Teacher</Link>
              <Link to="/shop?cat=bridal" className="hover:text-muted transition-colors italic">Bridal</Link>
              <Link to="/shop?cat=patriotic" className="hover:text-muted transition-colors italic">Liberty</Link>
              <Link to="/shop" className="hover:text-muted transition-colors">Archive</Link>
              <Link to="/blog" className="hover:text-muted transition-colors">Blog</Link>
            </nav>
            <button className="lg:hidden" onClick={() => setIsMenuOpen(true)}>
              <Menu className="w-5 h-5" />
            </button>

            {/* Center Brand */}
            <div className="flex justify-center">
              <Link to="/" className={`text-2xl md:text-3xl font-serif tracking-[0.2em] uppercase transition-opacity hover:opacity-70 ${isScrolled || isSearchOpen ? 'text-black' : 'text-black md:text-white'}`}>
                ZuzuMood
              </Link>
            </div>

            {/* Right Actions */}
            <div className={`flex items-center justify-end space-x-6 ${isScrolled || isSearchOpen ? 'text-black' : 'text-black md:text-white'}`}>
              <button onClick={() => setIsSearchOpen(!isSearchOpen)} className="group transition-transform hover:scale-110">
                <Search className="w-4 h-4" />
              </button>
              <button onClick={() => setIsWishlistOpen(true)} className="relative group transition-transform hover:scale-110">
                <Heart className={`w-4 h-4 ${wishlistIds.length > 0 ? 'fill-black text-black' : ''}`} />
                {wishlistIds.length > 0 && (
                  <span className="absolute -top-2 -right-2 bg-black text-white text-[7px] w-3.5 h-3.5 rounded-full flex items-center justify-center font-bold">
                    {wishlistIds.length}
                  </span>
                )}
              </button>
              <a href="https://www.etsy.com/shop/ZuzuMood" target="_blank" rel="noreferrer" className="relative group transition-transform hover:scale-110">
                <ShoppingBag className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Search Bar Overlay */}
          {isSearchOpen && (
            <div className="absolute top-full left-0 w-full bg-white border-b border-gray-100 animate-slide-down py-8 px-6">
              <div className="container mx-auto max-w-4xl">
                <form onSubmit={handleSearchSubmit} className="relative">
                  <input 
                    autoFocus
                    type="text" 
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by mood, collection, or design..." 
                    className="w-full text-2xl font-serif italic border-b border-gray-200 pb-4 outline-none focus:border-black transition-colors"
                  />
                  <button type="submit" className="absolute right-0 top-0 mt-1">
                    <Search className="w-6 h-6 text-muted hover:text-black" />
                  </button>
                </form>
                <div className="mt-4 flex space-x-6 text-[9px] font-bold uppercase tracking-widest text-muted">
                  <span>Trending: Teacher Edit</span>
                  <span>Bridal Atelier</span>
                  <span>Comfort Colors</span>
                </div>
              </div>
            </div>
          )}
        </header>
      </div>

      <WishlistPanel isOpen={isWishlistOpen} onClose={() => setIsWishlistOpen(false)} />

      {/* Mobile Menu Overlay */}
      <div className={`fixed inset-0 bg-white z-[100] transition-transform duration-700 ease-in-out ${isMenuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="p-8 h-full flex flex-col">
          <div className="flex justify-between items-center mb-16">
            <span className="text-xl font-serif tracking-widest uppercase">The Archive</span>
            <button onClick={() => setIsMenuOpen(false)}><X className="w-6 h-6" /></button>
          </div>
          <nav className="flex flex-col space-y-10">
            <Link to="/" className="text-3xl font-serif italic">Maison</Link>
            <Link to="/shop" className="text-3xl font-serif italic">All Pieces</Link>
            <Link to="/shop?cat=teacher" className="text-3xl font-serif italic">The Teacher Edit</Link>
            <Link to="/shop?cat=bridal" className="text-3xl font-serif italic">Bridal Atelier</Link>
            <Link to="/shop?cat=patriotic" className="text-3xl font-serif italic">Liberty & Statement</Link>
            <Link to="/shop?cat=healing" className="text-3xl font-serif italic">Stoic & Healing</Link>
            <Link to="/blog" className="text-3xl font-serif italic">Daily Blog</Link>
          </nav>
          <div className="mt-auto border-t border-gray-100 pt-8 flex flex-col space-y-4">
             <div className="flex space-x-8 text-[10px] font-bold uppercase tracking-[0.3em]">
               <a href="https://www.instagram.com" target="_blank" rel="noreferrer">Instagram</a>
               <a href="https://www.etsy.com/shop/ZuzuMood" target="_blank" rel="noreferrer">Etsy Store</a>
             </div>
             <p className="text-[8px] uppercase tracking-widest text-muted">Orders Fulfilled Globally via Etsy</p>
          </div>
        </div>
      </div>
    </>
  );
};
