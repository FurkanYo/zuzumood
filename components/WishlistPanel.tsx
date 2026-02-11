
import React from 'react';
import { X, Trash2, ExternalLink, Heart } from 'lucide-react';
import { useWishlist } from '../context/WishlistContext';
import { PRODUCTS } from '../services/data';
import { Link } from 'react-router-dom';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const WishlistPanel: React.FC<Props> = ({ isOpen, onClose }) => {
  const { wishlistIds, toggleWishlist } = useWishlist();
  const items = PRODUCTS.filter(p => wishlistIds.includes(p.id));

  return (
    <>
      {/* Overlay */}
      <div 
        className={`fixed inset-0 bg-black/10 backdrop-blur-sm z-[150] transition-opacity duration-700 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`} 
        onClick={onClose}
      />

      {/* Panel */}
      <div className={`fixed top-0 right-0 h-full w-full max-w-md bg-white z-[160] shadow-2xl transition-transform duration-700 ease-in-out transform ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-8 border-b border-gray-100 flex justify-between items-center">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-[0.4em]">Personal Archive</h2>
              <p className="text-[10px] text-muted uppercase tracking-widest mt-1 italic">Your curated selections</p>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-gray-50 transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-8 space-y-12 no-scrollbar">
            {items.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center space-y-6">
                <Heart className="w-12 h-12 text-gray-100" />
                <p className="text-[10px] text-muted uppercase tracking-[0.3em] leading-relaxed max-w-[200px]">
                  Your archive is currently empty. Explore the collective to save your favorite pieces.
                </p>
                <button 
                  onClick={onClose}
                  className="px-8 py-3 border border-black text-[9px] font-bold uppercase tracking-widest hover:bg-black hover:text-white transition-all"
                >
                  Return to Collection
                </button>
              </div>
            ) : (
              items.map(product => (
                <div key={product.id} className="group animate-fade-in">
                  <div className="flex space-x-6">
                    <Link to={`/product/${product.id}`} onClick={onClose} className="w-24 aspect-[3/4] bg-gray-50 overflow-hidden flex-shrink-0">
                      <img src={product.image} className="w-full h-full object-cover grayscale-[30%] group-hover:grayscale-0 transition-all" alt={product.title} />
                    </Link>
                    <div className="flex-1 flex flex-col justify-between py-1">
                      <div>
                        <div className="flex justify-between items-start">
                          <h3 className="text-[10px] font-bold uppercase tracking-widest leading-relaxed pr-4">
                            <Link to={`/product/${product.id}`} onClick={onClose}>{product.title}</Link>
                          </h3>
                          <button 
                            onClick={() => toggleWishlist(product.id)}
                            className="text-gray-300 hover:text-black transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                        <p className="text-[9px] text-muted uppercase tracking-widest mt-2 italic">{product.category}</p>
                      </div>
                      <div className="flex justify-between items-end mt-4">
                        <span className="text-[11px] font-bold tracking-tighter">${product.price.toFixed(2)}</span>
                        <a 
                          href={product.etsyUrl || `https://www.etsy.com/shop/ZuzuMood?search_query=${encodeURIComponent(product.title)}`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[9px] font-bold uppercase tracking-widest border-b border-black pb-0.5 flex items-center group/btn"
                        >
                          ORDER
                          <ExternalLink className="w-2.5 h-2.5 ml-2 opacity-0 group-hover/btn:opacity-100 transition-opacity" />
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {items.length > 0 && (
            <div className="p-8 border-t border-gray-100 bg-gray-50/50">
              <p className="text-[8px] text-center text-muted uppercase tracking-[0.4em] leading-relaxed">
                All curated items are fulfilled via our official Etsy storefront.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
};
