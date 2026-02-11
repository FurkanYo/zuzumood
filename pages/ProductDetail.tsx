import React, { useMemo, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { PRODUCTS } from '../services/data';
import { ChevronLeft, ChevronRight, Heart, Share2, Ruler, ExternalLink, Truck, ShieldCheck, Store } from 'lucide-react';
import { ProductCard } from '../components/ProductCard';
import { useWishlist } from '../context/WishlistContext';

export const ProductDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const product = PRODUCTS.find((p) => p.id === id);
  const [selectedSize, setSelectedSize] = useState('M');
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const { isInWishlist, toggleWishlist } = useWishlist();
  const recommendationTrackRef = useRef<HTMLDivElement>(null);

  if (!product) return <div className="pt-60 text-center uppercase tracking-[0.5em] text-[10px]">Product not found</div>;

  const isWishlisted = isInWishlist(product.id);
  const sizes = ['XS', 'S', 'M', 'L', 'XL'];
  const productImages = product.images.length > 0 ? product.images : [product.image];

  const recommendations = useMemo(() => {
    const sameCategory = PRODUCTS.filter((p) => p.category === product.category && p.id !== product.id);
    const rest = PRODUCTS.filter((p) => p.category !== product.category && p.id !== product.id);
    return [...sameCategory, ...rest].slice(0, 12);
  }, [product.category, product.id]);

  const etsyUrl = product.etsyUrl || `https://www.etsy.com/shop/ZuzuMood?search_query=${encodeURIComponent(product.title)}`;

  const handleShare = async () => {
    const shareData = {
      title: `${product.title} | ZuzuMood`,
      text: `Check this ZuzuMood product: ${product.title}`,
      url: window.location.href,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
        return;
      } catch {
        // fall back to clipboard
      }
    }

    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(window.location.href);
      window.alert('Product link copied to clipboard.');
      return;
    }

    window.prompt('Copy this product URL:', window.location.href);
  };

  const scrollRecommendations = (direction: 'left' | 'right') => {
    if (!recommendationTrackRef.current) {
      return;
    }
    recommendationTrackRef.current.scrollBy({
      left: direction === 'left' ? -320 : 320,
      behavior: 'smooth',
    });
  };

  return (
    <div className="pt-40 pb-32 bg-white">
      <div className="container mx-auto px-6 mb-12 flex items-center text-[8px] font-bold uppercase tracking-[0.4em] text-muted">
        <Link to="/" className="hover:text-black">Maison</Link>
        <ChevronRight className="w-2.5 h-2.5 mx-3 opacity-30" />
        <Link to="/shop" className="hover:text-black">Shop</Link>
        <ChevronRight className="w-2.5 h-2.5 mx-3 opacity-30" />
        <span className="text-black truncate">{product.title}</span>
      </div>

      <div className="container mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-20 lg:gap-32">
        <div className="space-y-4">
          <div className="aspect-[3/4] bg-gray-50 overflow-hidden relative group">
            <img src={productImages[selectedImageIndex]} className="w-full h-full object-cover" alt={product.title} />
          </div>

          <div className="grid grid-cols-5 gap-3">
            {productImages.map((image, index) => (
              <button
                key={`${product.id}-thumb-${index}`}
                onClick={() => setSelectedImageIndex(index)}
                className={`aspect-square bg-gray-50 overflow-hidden border transition-all ${selectedImageIndex === index ? 'border-black' : 'border-transparent hover:border-gray-300'}`}
                aria-label={`Show image ${index + 1}`}
              >
                <img src={image} className="w-full h-full object-cover" alt={`${product.title} view ${index + 1}`} />
              </button>
            ))}
          </div>

          <a
            href={etsyUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-[9px] font-bold uppercase tracking-widest text-muted hover:text-black transition-colors"
          >
            Official ZuzuMood Etsy Storefront
            <ExternalLink className="w-3 h-3 ml-2" />
          </a>
        </div>

        <div className="flex flex-col">
          <div className="mb-12">
            <span className="text-[9px] font-bold uppercase tracking-[0.4em] text-muted block mb-4 italic">{product.category} Collection</span>
            <h1 className="text-4xl md:text-5xl font-serif tracking-wide uppercase mb-8 leading-snug">{product.title}</h1>
            <div className="text-2xl font-light tracking-tight">
              {product.isOnSale ? (
                <div className="flex items-center space-x-4">
                  <span className="text-black">${product.price.toFixed(2)}</span>
                  <span className="text-muted line-through text-base opacity-40">${product.originalPrice?.toFixed(2)}</span>
                </div>
              ) : (
                <span>${product.price.toFixed(2)}</span>
              )}
            </div>
          </div>

          <div className="mb-12">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-[10px] font-bold uppercase tracking-[0.3em]">Select Size</h3>
              <button className="flex items-center text-[9px] font-bold uppercase tracking-widest text-muted hover:text-black transition-colors">
                <Ruler className="w-3 h-3 mr-2" />
                Size Guide
              </button>
            </div>
            <div className="grid grid-cols-5 border border-gray-100">
              {sizes.map((size) => (
                <button
                  key={size}
                  onClick={() => setSelectedSize(size)}
                  className={`py-4 text-[11px] font-bold transition-all duration-300 ${selectedSize === size ? 'bg-black text-white' : 'hover:bg-gray-50 text-gray-400'}`}
                >
                  {size}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-4 mb-16">
            <a
              href={etsyUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full bg-black text-white py-6 text-[11px] font-bold uppercase tracking-[0.6em] hover:bg-gray-900 transition-all shadow-xl flex items-center justify-center group"
            >
              ORDER
              <ExternalLink className="w-3 h-3 ml-4 opacity-50 group-hover:opacity-100 transition-opacity" />
            </a>
            <p className="text-[8px] text-center text-muted uppercase tracking-widest mt-4">Secure Checkout Fulfilled via Etsy</p>

            <div className="flex space-x-4 pt-8">
              <button
                onClick={() => toggleWishlist(product.id)}
                className={`flex-1 border py-4 flex items-center justify-center space-x-3 text-[9px] font-bold uppercase tracking-widest transition-all duration-300 ${isWishlisted ? 'border-black bg-black text-white' : 'border-gray-200 hover:border-black text-black'}`}
              >
                <Heart className={`w-4 h-4 ${isWishlisted ? 'fill-white' : ''}`} />
                <span>{isWishlisted ? 'Saved to Archive' : 'Save to Wishlist'}</span>
              </button>
              <button onClick={() => { void handleShare(); }} className="w-16 border border-gray-200 flex items-center justify-center hover:border-black transition-colors">
                <Share2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="border-t border-gray-100">
            {[
              { title: 'Composition & Care', content: product.details.join(', ') },
              { title: 'The Narrative', content: product.description },
              { title: 'Redirection Policy', content: 'You are viewing our official Soul Archive lookbook. Clicking ORDER will securely transport you to our verified Etsy shop listing to complete your transaction.' }
            ].map((item, idx) => (
              <details key={idx} className="group">
                <summary className="py-6 border-b border-gray-100 flex justify-between items-center cursor-pointer list-none group-open:border-transparent">
                  <span className="text-[10px] font-bold uppercase tracking-[0.3em]">{item.title}</span>
                  <ExternalLink className="w-3 h-3 text-gray-300 group-hover:text-black transition-transform duration-300 group-open:rotate-45" />
                </summary>
                <div className="pb-8 text-xs text-muted leading-relaxed uppercase tracking-widest pr-12">
                  {item.content}
                </div>
              </details>
            ))}
          </div>

          <div className="mt-12 space-y-6 border-t border-gray-100 pt-10">
            <div className="flex items-start space-x-3">
              <Truck className="w-4 h-4 mt-0.5 text-black" />
              <div>
                <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] mb-3">Shipping and return policies</h3>
                <p className="text-[10px] text-muted uppercase tracking-widest">Ships out within 1–3 business days</p>
                <p className="text-[10px] text-muted uppercase tracking-widest">Returns & exchanges not accepted</p>
                <p className="text-[10px] text-muted uppercase tracking-widest mt-3">Ships from: United States</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <ShieldCheck className="w-4 h-4 mt-0.5 text-black" />
              <div>
                <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] mb-3">Did you know?</h3>
                <p className="text-[10px] text-muted leading-relaxed uppercase tracking-widest">
                  Etsy Purchase Protection helps cover eligible orders if something goes wrong. Etsy also invests in climate solutions like electric trucks and carbon offsets for delivery.
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <Store className="w-4 h-4 mt-0.5 text-black" />
              <div>
                <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] mb-3">Meet your seller</h3>
                <p className="text-[10px] text-muted uppercase tracking-widest">ZuzuMood — Owned by ZULEYHA AKKAN | United States</p>
                <p className="text-[10px] text-muted uppercase tracking-widest">No reviews yet • 0 sales • 1 month on Etsy</p>
                <div className="flex flex-wrap gap-4 mt-3">
                  <a href="https://www.etsy.com/shop/ZuzuMood" target="_blank" rel="noreferrer" className="text-[9px] font-bold uppercase tracking-widest underline-offset-4 hover:underline">Message seller</a>
                  <a href="https://www.etsy.com/shop/ZuzuMood" target="_blank" rel="noreferrer" className="text-[9px] font-bold uppercase tracking-widest underline-offset-4 hover:underline">Follow shop</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {recommendations.length > 0 && (
        <div className="container mx-auto px-6 mt-48 border-t border-gray-50 pt-24">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-3xl font-serif uppercase tracking-widest">More from this shop</h2>
            <div className="flex items-center gap-3">
              <button
                onClick={() => scrollRecommendations('left')}
                className="w-10 h-10 border border-gray-200 rounded-full flex items-center justify-center hover:border-black transition-colors"
                aria-label="Scroll left"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => scrollRecommendations('right')}
                className="w-10 h-10 border border-gray-200 rounded-full flex items-center justify-center hover:border-black transition-colors"
                aria-label="Scroll right"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
          <p className="text-[10px] uppercase tracking-widest text-muted mb-10">You may also like</p>

          <div ref={recommendationTrackRef} className="flex gap-8 overflow-x-auto no-scrollbar scroll-smooth pb-4">
            {recommendations.map((item) => (
              <div key={item.id} className="min-w-[260px] md:min-w-[300px] lg:min-w-[320px]">
                <ProductCard product={item} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
