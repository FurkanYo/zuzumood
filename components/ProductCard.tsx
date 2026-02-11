
import React from 'react';
import { Link } from 'react-router-dom';
import { Product } from '../types';
import { Heart } from 'lucide-react';
import { useWishlist } from '../context/WishlistContext';

interface Props {
  product: Product;
}

export const ProductCard: React.FC<Props> = ({ product }) => {
  const { isInWishlist, toggleWishlist } = useWishlist();
  const isWishlisted = isInWishlist(product.id);

  return (
    <div className="group">
      <div className="block relative aspect-[3/4] overflow-hidden bg-gray-100">
        <Link to={`/product/${product.id}`} className="block w-full h-full">
          <img 
            src={product.image} 
            alt={product.title} 
            className="w-full h-full object-cover transition-transform duration-1000 ease-out group-hover:scale-105"
          />
        </Link>
        
        {/* Wishlist Toggle */}
        <button 
          onClick={(e) => {
            e.preventDefault();
            toggleWishlist(product.id);
          }}
          className="absolute top-4 right-4 z-10 p-2 group/heart transition-all duration-300"
        >
          <Heart 
            className={`w-4 h-4 transition-all duration-300 ${isWishlisted ? 'fill-black text-black scale-110' : 'text-gray-400 group-hover/heart:text-black group-hover/heart:scale-110'}`} 
          />
        </button>

        {product.isNew && (
          <span className="absolute top-4 left-4 bg-white text-[8px] font-bold uppercase tracking-[0.3em] px-3 py-1.5 shadow-sm pointer-events-none">New</span>
        )}
        
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-500 pointer-events-none" />
      </div>
      
      <div className="mt-6">
        <div className="flex justify-between items-start">
          <div className="flex-1 mr-4">
            <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-gray-900 group-hover:text-muted transition-colors">
              <Link to={`/product/${product.id}`}>{product.title}</Link>
            </h3>
            <p className="text-[9px] text-muted uppercase tracking-widest mt-1.5 italic">{product.category}</p>
          </div>
          <div className="text-[11px] font-medium tracking-tighter">
            {product.isOnSale && product.originalPrice ? (
              <div className="flex flex-col items-end">
                <span className="text-muted line-through opacity-50">${product.originalPrice.toFixed(2)}</span>
                <span className="text-black font-bold">${product.price.toFixed(2)}</span>
              </div>
            ) : (
              <span>${product.price.toFixed(2)}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
